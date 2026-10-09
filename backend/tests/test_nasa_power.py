from copy import deepcopy
from datetime import date, timedelta

import httpx
import pytest
from pydantic import ValidationError

from app.repositories.solar_resource import MemorySolarResourceCache
from app.schemas.solar_resource import ResourceQuery
from app.schemas.solar_system import today_in_india
from app.services.nasa_power import (
    ENDPOINT,
    PARAMETERS,
    NasaPowerService,
    SolarResourceError,
    coordinate,
    normalize,
)


@pytest.fixture
def query():
    return ResourceQuery(latitude=28.6139, longitude=77.209, date=date(2025, 9, 15))


@pytest.fixture
def payload(query):
    # Synthetic values, with shape and units verified against NASA's live response.
    # These values are not presented as observations of this site/date.
    values = [5.2, 4.1, 2.0, 28.0, 22.0, 34.0, 2.0, 70.0]
    stamp = query.date.strftime("%Y%m%d")
    return {
        "properties": {
            "parameter": {
                name: {stamp: value} for name, value in zip(PARAMETERS, values, strict=True)
            }
        },
        "parameters": {name: {"units": unit} for name, (_, unit) in PARAMETERS.items()},
        "header": {
            "time_standard": "LST",
            "start": stamp,
            "end": stamp,
            "fill_value": -999.0,
            "api": {"version": "v2.10.0"},
            "sources": ["CERES", "MERRA2"],
        },
    }


def test_request_and_identity_units(query, payload):
    requests = []

    def handle(request):
        requests.append(request)
        assert str(request.url).split("?")[0] == ENDPOINT
        assert dict(request.url.params) == {
            "parameters": ",".join(PARAMETERS),
            "community": "RE",
            "latitude": "28.6139",
            "longitude": "77.2090",
            "start": "20250915",
            "end": "20250915",
            "format": "JSON",
            "time-standard": "LST",
        }
        assert request.extensions["timeout"] == {"connect": 5, "read": 20, "write": 20, "pool": 5}
        return httpx.Response(200, json=payload)

    service = NasaPowerService(MemorySolarResourceCache(), transport=httpx.MockTransport(handle))
    result = service.get(query)
    assert result.ghi_kwh_m2_day == 5.2  # No 24x or 1000x conversion.
    assert result.dni_kwh_m2_day == 4.1
    assert result.dhi_kwh_m2_day == 2
    assert result.temp_avg_c == 28
    assert result.temp_min_c == 22
    assert result.temp_max_c == 34
    assert result.wind_speed_2m_avg_m_s == 2
    assert result.relative_humidity_avg_pct == 70
    assert result.time_standard == "LST"
    assert result.status == "complete"
    assert result.missing_fields == ()
    assert result.retrieved_at.utcoffset() == timedelta(0)
    assert service.get(query) == result
    assert len(requests) == 1


@pytest.mark.parametrize(
    "field,value",
    [
        ("latitude", 90.01),
        ("latitude", -90.01),
        ("longitude", 180.01),
        ("longitude", -180.01),
        ("latitude", float("nan")),
        ("longitude", float("inf")),
        ("latitude", float("-inf")),
        ("date", "1983-12-31"),
        ("date", "2025-02-30"),
    ],
)
def test_invalid_query(query, field, value):
    with pytest.raises(ValidationError):
        ResourceQuery(**{**query.model_dump(), field: value})


def test_future_date(query):
    with pytest.raises(ValidationError):
        ResourceQuery(**{**query.model_dump(), "date": today_in_india() + timedelta(days=1)})


@pytest.mark.parametrize("latitude,longitude", [(-90, -180), (90, 180), (0, 0)])
def test_coordinate_boundaries(query, latitude, longitude):
    ResourceQuery(date=query.date, latitude=latitude, longitude=longitude)


@pytest.mark.parametrize(
    "value,expected", [(28.61395, "28.6140"), (-0.00001, "0.0000"), (-28.61395, "-28.6140")]
)
def test_coordinate_precision(value, expected):
    assert coordinate(value) == expected


@pytest.mark.parametrize("parameter", list(PARAMETERS)[1:])
@pytest.mark.parametrize("missing_kind", ["sentinel", "null", "date", "parameter"])
def test_optional_missing_values(query, payload, parameter, missing_kind):
    series = payload["properties"]["parameter"]
    stamp = query.date.strftime("%Y%m%d")
    if missing_kind == "parameter":
        del series[parameter]
    elif missing_kind == "date":
        series[parameter] = {}
    else:
        series[parameter][stamp] = -999 if missing_kind == "sentinel" else None
    result = normalize(payload, query)
    field = PARAMETERS[parameter][0]
    assert getattr(result, field) is None
    assert result.status == "partial"
    assert result.missing_fields == (field,)


@pytest.mark.parametrize("value", [-999, None])
def test_missing_ghi_is_unavailable(query, payload, value):
    payload["properties"]["parameter"]["ALLSKY_SFC_SW_DWN"]["20250915"] = value
    with pytest.raises(SolarResourceError) as failure:
        normalize(payload, query)
    assert failure.value.code == "resource_unavailable"


def test_missing_ghi_parameter(query, payload):
    del payload["properties"]["parameter"]["ALLSKY_SFC_SW_DWN"]
    with pytest.raises(SolarResourceError) as failure:
        normalize(payload, query)
    assert failure.value.code == "missing_required_parameter"


def test_missing_ghi_date(query, payload):
    payload["properties"]["parameter"]["ALLSKY_SFC_SW_DWN"] = {"20250914": 5}
    with pytest.raises(SolarResourceError) as failure:
        normalize(payload, query)
    assert failure.value.code == "resource_unavailable"


def test_response_sentinel_and_zero(query, payload):
    payload["header"]["fill_value"] = -777
    payload["properties"]["parameter"]["ALLSKY_SFC_SW_DNI"]["20250915"] = -777
    payload["properties"]["parameter"]["ALLSKY_SFC_SW_DWN"]["20250915"] = 0
    result = normalize(payload, query)
    assert result.ghi_kwh_m2_day == 0
    assert result.dni_kwh_m2_day is None


@pytest.mark.parametrize("value", [float("nan"), float("inf"), 10**400, -1, "5.2", True, [], {}])
def test_invalid_numeric_value(query, payload, value):
    payload["properties"]["parameter"]["ALLSKY_SFC_SW_DWN"]["20250915"] = value
    with pytest.raises(SolarResourceError) as failure:
        normalize(payload, query)
    assert failure.value.status_code == 502


@pytest.mark.parametrize(
    "parameter,value",
    [("RH2M", 101), ("RH2M", -1), ("WS2M", -1), ("T2M_MIN", -300), ("T2M_MIN", 40)],
)
def test_invalid_physical_ranges(query, payload, parameter, value):
    payload["properties"]["parameter"][parameter]["20250915"] = value
    with pytest.raises(SolarResourceError):
        normalize(payload, query)


@pytest.mark.parametrize("parameter", PARAMETERS)
def test_wrong_units_fail_closed(query, payload, parameter):
    payload["parameters"][parameter]["units"] = "unexpected"
    with pytest.raises(SolarResourceError) as failure:
        normalize(payload, query)
    assert failure.value.code == "upstream_invalid_data"


@pytest.mark.parametrize("bad_payload", [None, [], {}, {"header": []}])
def test_bad_structure(query, bad_payload):
    with pytest.raises(SolarResourceError):
        normalize(bad_payload, query)


@pytest.mark.parametrize(
    "field,value",
    [
        ("time_standard", "UTC"),
        ("start", "20250914"),
        ("end", "20250916"),
        ("fill_value", "-999"),
        ("sources", "CERES"),
        ("api", {}),
    ],
)
def test_bad_header(query, payload, field, value):
    payload["header"][field] = value
    with pytest.raises(SolarResourceError):
        normalize(payload, query)


@pytest.mark.parametrize(
    "status,code,calls",
    [
        (400, "upstream_rejected_request", 1),
        (404, "upstream_rejected_request", 1),
        (422, "upstream_rejected_request", 1),
        (429, "upstream_rate_limited", 1),
        (500, "upstream_unavailable", 2),
        (503, "upstream_unavailable", 2),
    ],
)
def test_http_errors(query, status, code, calls):
    requests, pauses = [], []

    def handle(request):
        requests.append(request)
        return httpx.Response(status, text="private upstream diagnostic")

    service = NasaPowerService(
        MemorySolarResourceCache(), transport=httpx.MockTransport(handle), pause=pauses.append
    )
    with pytest.raises(SolarResourceError) as failure:
        service.get(query)
    assert failure.value.code == code
    assert "private" not in str(failure.value)
    assert len(requests) == calls
    assert len(pauses) == calls - 1


@pytest.mark.parametrize(
    "error,code",
    [
        (httpx.ReadTimeout, "upstream_timeout"),
        (httpx.ConnectTimeout, "upstream_timeout"),
        (httpx.ConnectError, "upstream_unavailable"),
    ],
)
def test_transport_error(query, error, code):
    requests = []

    def handle(request):
        requests.append(request)
        raise error("synthetic failure", request=request)

    service = NasaPowerService(
        MemorySolarResourceCache(), transport=httpx.MockTransport(handle), pause=lambda _: None
    )
    with pytest.raises(SolarResourceError) as failure:
        service.get(query)
    assert failure.value.code == code
    assert len(requests) == 2


def test_transient_failure_recovers(query, payload):
    replies = [httpx.Response(503), httpx.Response(200, json=payload)]
    service = NasaPowerService(
        MemorySolarResourceCache(),
        transport=httpx.MockTransport(lambda _: replies.pop(0)),
        pause=lambda _: None,
    )
    assert service.get(query).status == "complete"
    assert replies == []


def test_invalid_json_not_cached(query, payload):
    replies = [httpx.Response(200, text="not JSON"), httpx.Response(200, json=payload)]
    service = NasaPowerService(
        MemorySolarResourceCache(), transport=httpx.MockTransport(lambda _: replies.pop(0))
    )
    with pytest.raises(SolarResourceError):
        service.get(query)
    assert service.get(query).status == "complete"


def test_cache_rounding_expiry_and_date_separation(query, payload):
    clock, requests = [0.0], []
    cache = MemorySolarResourceCache(clock=lambda: clock[0])

    def handle(request):
        requests.append(request)
        output = deepcopy(payload)
        stamp = request.url.params["start"]
        output["header"]["start"] = output["header"]["end"] = stamp
        for series in output["properties"]["parameter"].values():
            series[stamp] = series.pop("20250915")
        return httpx.Response(200, json=output)

    service = NasaPowerService(cache, transport=httpx.MockTransport(handle))
    service.get(query)
    service.get(ResourceQuery(**{**query.model_dump(), "latitude": 28.61391}))
    assert len(requests) == 1
    service.get(ResourceQuery(**{**query.model_dump(), "longitude": 77.21}))
    service.get(ResourceQuery(**{**query.model_dump(), "date": date(2025, 9, 16)}))
    assert len(requests) == 3
    clock[0] = 86400
    service.get(query)
    assert len(requests) == 4


def test_partial_cache_expires_early(query, payload):
    clock, requests = [0], []
    payload["properties"]["parameter"]["ALLSKY_SFC_SW_DNI"]["20250915"] = -999

    def handle(request):
        requests.append(request)
        return httpx.Response(200, json=payload)

    service = NasaPowerService(
        MemorySolarResourceCache(clock=lambda: clock[0]), transport=httpx.MockTransport(handle)
    )
    service.get(query)
    clock[0] = 3599
    service.get(query)
    assert len(requests) == 1
    clock[0] = 3600
    service.get(query)
    assert len(requests) == 2


def test_cache_eviction(query, payload):
    cache = MemorySolarResourceCache(max_entries=2)
    value = normalize(payload, query)
    cache.put("a", value, 60)
    cache.put("b", value, 60)
    assert cache.get("a") == value
    cache.put("c", value, 60)
    assert cache.get("b") is None
    assert cache.get("a") == value
    assert cache.get("c") == value


def test_busy_service_does_not_call_network(query):
    service = NasaPowerService(
        MemorySolarResourceCache(),
        transport=httpx.MockTransport(lambda _: pytest.fail("Unexpected request")),
    )
    for _ in range(4):
        service._slots.acquire()
    with pytest.raises(SolarResourceError) as failure:
        service.get(query)
    assert failure.value.code == "upstream_busy"
