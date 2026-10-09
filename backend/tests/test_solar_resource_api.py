from datetime import timedelta
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient

from app.config.settings import Settings
from app.main import create_app
from app.repositories.solar_resource import MemorySolarResourceCache
from app.schemas.solar_system import today_in_india
from app.services.nasa_power import PARAMETERS, NasaPowerService


@pytest.fixture
def client(tmp_path):
    app = create_app(Settings(_env_file=None, database_path=tmp_path / "systems.sqlite3"))
    calls = []

    def respond(request):
        calls.append(request)
        stamp = request.url.params["start"]
        return httpx.Response(
            200,
            json={
                "properties": {"parameter": {parameter: {stamp: 5.0} for parameter in PARAMETERS}},
                "parameters": {
                    parameter: {"units": unit} for parameter, (_, unit) in PARAMETERS.items()
                },
                "header": {
                    "start": stamp,
                    "end": stamp,
                    "time_standard": "LST",
                    "fill_value": -999,
                    "api": {"version": "v2.10.0"},
                    "sources": ["test"],
                },
            },
        )

    app.state.solar_resource_service = NasaPowerService(
        MemorySolarResourceCache(), transport=httpx.MockTransport(respond)
    )
    with TestClient(app) as client:
        yield client, calls


def test_coordinate_endpoint(client):
    client, calls = client
    response = client.get("/solar-resource?latitude=28.61&longitude=77.21&date=2025-09-15")
    assert response.status_code == 200
    assert response.json()["ghi_kwh_m2_day"] == 5
    assert response.json()["time_standard"] == "LST"
    assert "expected_generation" not in response.text
    assert len(calls) == 1


@pytest.mark.parametrize(
    "params",
    [
        "latitude=91&longitude=77",
        "latitude=28&longitude=181",
        "latitude=NaN&longitude=77",
        "latitude=28&longitude=Infinity",
        "latitude=28",
        "latitude=bad&longitude=77",
    ],
)
def test_invalid_coordinates_never_request_nasa(client, params):
    client, calls = client
    assert client.get(f"/solar-resource?{params}&date=2025-09-15").status_code == 422
    assert calls == []


@pytest.mark.parametrize("day", ["1983-12-31", "bad", "2025-02-30", ""])
def test_invalid_dates(client, day):
    client, calls = client
    assert client.get(f"/solar-resource?latitude=28&longitude=77&date={day}").status_code == 422
    assert calls == []


def test_future_date(client):
    client, calls = client
    day = today_in_india() + timedelta(days=1)
    assert client.get(f"/solar-resource?latitude=28&longitude=77&date={day}").status_code == 422
    assert calls == []


def test_system_route_uses_current_saved_coordinates(client):
    client, calls = client
    profile = {
        "capacity_kw": 3,
        "location_label": "Smoke test",
        "latitude": 28.61,
        "longitude": 77.21,
        "install_year": 2020,
        "tilt_degrees": None,
        "azimuth_degrees": None,
    }
    system = client.post("/systems", json=profile).json()
    route = f"/systems/{system['system_id']}"
    response = client.get(f"{route}/solar-resource?date=2025-09-15")
    assert response.status_code == 200
    assert calls[-1].url.params["latitude"] == "28.6100"
    profile.update(latitude=12.9716, longitude=77.5946)
    assert client.put(route, json=profile).status_code == 200
    response = client.get(f"{route}/solar-resource?date=2025-09-15")
    assert response.status_code == 200
    assert response.json()["latitude"] == 12.9716
    assert len(calls) == 2


def test_missing_system_avoids_upstream(client):
    client, calls = client
    assert client.get(f"/systems/{uuid4()}/solar-resource?date=2025-09-15").status_code == 404
    assert client.get("/systems/invalid/solar-resource?date=2025-09-15").status_code == 422
    assert calls == []


@pytest.mark.parametrize(
    "kind,status,code",
    [
        ("timeout", 504, "upstream_timeout"),
        ("invalid", 502, "upstream_invalid_data"),
        ("429", 503, "upstream_rate_limited"),
        ("503", 503, "upstream_unavailable"),
        ("422", 502, "upstream_rejected_request"),
        ("missing", 404, "resource_unavailable"),
    ],
)
def test_http_error_mapping(client, kind, status, code):
    client, _ = client

    def handle(request):
        if kind == "timeout":
            raise httpx.ReadTimeout("sensitive detail", request=request)
        if kind == "invalid":
            return httpx.Response(200, json={})
        if kind == "missing":
            return httpx.Response(
                200,
                json={
                    "header": {
                        "time_standard": "LST",
                        "start": "20250915",
                        "end": "20250915",
                        "fill_value": -999,
                        "api": {"version": "v2"},
                        "sources": ["test"],
                    },
                    "properties": {"parameter": {"ALLSKY_SFC_SW_DWN": {"20250915": -999}}},
                    "parameters": {"ALLSKY_SFC_SW_DWN": {"units": "kW-hr/m^2/day"}},
                },
            )
        return httpx.Response(int(kind), text="sensitive detail")

    client.app.state.solar_resource_service = NasaPowerService(
        MemorySolarResourceCache(), transport=httpx.MockTransport(handle), pause=lambda _: None
    )
    response = client.get("/solar-resource?latitude=28&longitude=77&date=2025-09-15")
    assert response.status_code == status
    assert response.json()["detail"]["code"] == code
    assert "sensitive" not in response.text
