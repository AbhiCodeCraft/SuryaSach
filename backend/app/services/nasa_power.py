import math
from collections.abc import Callable
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
from threading import BoundedSemaphore
from time import sleep

import httpx
from pydantic import ValidationError

from app.repositories.solar_resource import SolarResourceCache
from app.schemas.solar_resource import ResourceQuery, SolarWeatherDay

ENDPOINT = "https://power.larc.nasa.gov/api/temporal/daily/point"
# Parameter -> (normalized field, exact NASA RE daily unit). Identity conversions only.
PARAMETERS = {
    "ALLSKY_SFC_SW_DWN": ("ghi_kwh_m2_day", "kW-hr/m^2/day"),
    "ALLSKY_SFC_SW_DNI": ("dni_kwh_m2_day", "kW-hr/m^2/day"),
    "ALLSKY_SFC_SW_DIFF": ("dhi_kwh_m2_day", "kW-hr/m^2/day"),
    "T2M": ("temp_avg_c", "C"),
    "T2M_MIN": ("temp_min_c", "C"),
    "T2M_MAX": ("temp_max_c", "C"),
    "WS2M": ("wind_speed_2m_avg_m_s", "m/s"),
    "RH2M": ("relative_humidity_avg_pct", "%"),
}
CONTRACT = f"v1|{ENDPOINT}|RE|LST|{','.join(PARAMETERS)}"
TIMEOUT = httpx.Timeout(20, connect=5, pool=5)


class SolarResourceError(Exception):
    def __init__(self, code: str, message: str, status_code: int):
        super().__init__(message)
        self.code = code
        self.status_code = status_code


def malformed() -> SolarResourceError:
    return SolarResourceError(
        "upstream_invalid_data", "NASA POWER returned invalid or incompatible data", 502
    )


def unavailable() -> SolarResourceError:
    return SolarResourceError(
        "resource_unavailable",
        "NASA POWER GHI is unavailable for this location and date. Recent data may be delayed.",
        404,
    )


def coordinate(value: float) -> str:
    rounded = Decimal(str(value)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    return format(abs(rounded) if rounded == 0 else rounded, ".4f")


def number(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise malformed()
    return float(value)


def normalize(payload: object, query: ResourceQuery) -> SolarWeatherDay:
    """Accept only the verified daily RE/LST contract; never infer unknown units."""
    try:
        header = payload["header"]
        stamp = query.date.strftime("%Y%m%d")
        if header["time_standard"] != "LST" or header["start"] != stamp or header["end"] != stamp:
            raise malformed()
        sentinel = number(header["fill_value"])
        series = payload["properties"]["parameter"]
        metadata = payload["parameters"]
        if not isinstance(series, dict) or not isinstance(metadata, dict):
            raise malformed()
        version, sources = header["api"]["version"], header["sources"]
        if (
            not isinstance(version, str)
            or not version
            or not isinstance(sources, list)
            or not sources
            or any(not isinstance(source, str) for source in sources)
        ):
            raise malformed()
        values, missing = {}, []
        for parameter, (field, unit) in PARAMETERS.items():
            if parameter not in series:
                if field == "ghi_kwh_m2_day":
                    raise SolarResourceError(
                        "missing_required_parameter", "NASA POWER omitted required GHI", 502
                    )
                value = None
            else:
                if metadata[parameter]["units"] != unit or not isinstance(series[parameter], dict):
                    raise malformed()
                raw = series[parameter].get(stamp)
                value = None if raw is None else number(raw)
                if value == sentinel:
                    value = None
            if value is None:
                if field == "ghi_kwh_m2_day":
                    raise unavailable()
                missing.append(field)
            values[field] = value
        minimum, average, maximum = (values[f"temp_{part}_c"] for part in ("min", "avg", "max"))
        ordered = [value for value in (minimum, average, maximum) if value is not None]
        if ordered != sorted(ordered):
            raise malformed()
        return SolarWeatherDay(
            date=query.date,
            latitude=query.latitude,
            longitude=query.longitude,
            **values,
            status="partial" if missing else "complete",
            missing_fields=tuple(missing),
            upstream_api_version=version,
            upstream_sources=tuple(sources),
            retrieved_at=datetime.now(UTC),
        )
    except (KeyError, TypeError, ValueError, ValidationError) as error:
        raise malformed() from error


class NasaPowerService:
    def __init__(
        self,
        cache: SolarResourceCache,
        *,
        transport: httpx.BaseTransport | None = None,
        pause: Callable[[float], None] = sleep,
    ):
        self._cache = cache
        self._transport = transport
        self._pause = pause
        self._slots = BoundedSemaphore(4)

    def get(self, query: ResourceQuery) -> SolarWeatherDay:
        # Revalidate at the service boundary, including dates after a long-lived caller.
        query = ResourceQuery.model_validate(query.model_dump())
        lat, lon = coordinate(query.latitude), coordinate(query.longitude)
        query = ResourceQuery(latitude=float(lat), longitude=float(lon), date=query.date)
        key = f"{CONTRACT}|{lat}|{lon}|{query.date.isoformat()}"
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        if not self._slots.acquire(timeout=1):
            raise SolarResourceError(
                "upstream_busy", "Solar resource service is busy; retry later", 503
            )
        try:
            cached = self._cache.get(key)
            if cached is not None:
                return cached
            params = {
                "parameters": ",".join(PARAMETERS),
                "community": "RE",
                "latitude": lat,
                "longitude": lon,
                "start": query.date.strftime("%Y%m%d"),
                "end": query.date.strftime("%Y%m%d"),
                "format": "JSON",
                "time-standard": "LST",
            }
            with httpx.Client(timeout=TIMEOUT, transport=self._transport) as client:
                result = self._fetch(client, params, query)
            self._cache.put(key, result, 3600 if result.status == "partial" else 86400)
            return result
        finally:
            self._slots.release()

    def _fetch(self, client: httpx.Client, params: dict, query: ResourceQuery) -> SolarWeatherDay:
        for attempt in range(2):
            try:
                response = client.get(ENDPOINT, params=params)
            except httpx.TimeoutException as error:
                failure = SolarResourceError(
                    "upstream_timeout", "NASA POWER request timed out", 504
                )
                cause = error
            except httpx.RequestError as error:
                failure = SolarResourceError(
                    "upstream_unavailable", "NASA POWER is unreachable", 503
                )
                cause = error
            else:
                if response.status_code == 200:
                    try:
                        payload = response.json()
                    except ValueError as error:
                        raise malformed() from error
                    return normalize(payload, query)
                if response.status_code == 429:
                    raise SolarResourceError(
                        "upstream_rate_limited",
                        "NASA POWER is rate limiting requests; retry later",
                        503,
                    )
                if response.status_code < 500:
                    raise SolarResourceError(
                        "upstream_rejected_request", "NASA POWER rejected the resource request", 502
                    )
                failure = SolarResourceError(
                    "upstream_unavailable", "NASA POWER is unavailable", 503
                )
                cause = None
            if attempt == 0:
                self._pause(0.25)
            else:
                raise failure from cause
        raise AssertionError("Unreachable retry state")
