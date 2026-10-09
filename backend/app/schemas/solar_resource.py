from datetime import date
from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator

from app.schemas.solar_system import today_in_india

Latitude = Annotated[float, Field(ge=-90, le=90, allow_inf_nan=False)]
Longitude = Annotated[float, Field(ge=-180, le=180, allow_inf_nan=False)]
NonNegative = Annotated[float, Field(ge=0)]


class ResourceDateQuery(BaseModel):
    date: date

    @field_validator("date")
    @classmethod
    def supported_date(cls, value: date) -> date:
        if value < date(1984, 1, 1) or value > today_in_india():
            raise ValueError("Date must be from 1984-01-01 through today in India")
        return value


class ResourceQuery(ResourceDateQuery):
    latitude: Latitude
    longitude: Longitude


class SolarWeatherDay(BaseModel):
    model_config = ConfigDict(frozen=True, allow_inf_nan=False)

    date: date
    latitude: Latitude
    longitude: Longitude
    ghi_kwh_m2_day: NonNegative
    dni_kwh_m2_day: NonNegative | None
    dhi_kwh_m2_day: NonNegative | None
    temp_avg_c: float | None
    temp_min_c: float | None
    temp_max_c: float | None
    wind_speed_2m_avg_m_s: NonNegative | None
    relative_humidity_avg_pct: Annotated[float, Field(ge=0, le=100)] | None
    source: Literal["NASA_POWER"] = "NASA_POWER"
    time_standard: Literal["LST"] = "LST"
    temporal_resolution: Literal["daily"] = "daily"
    status: Literal["complete", "partial"]
    missing_fields: tuple[str, ...]
    upstream_api_version: str
    upstream_sources: tuple[str, ...]
    retrieved_at: AwareDatetime

    @field_validator("temp_avg_c", "temp_min_c", "temp_max_c")
    @classmethod
    def physical_temperature(cls, value: float | None) -> float | None:
        if value is not None and value < -273.15:
            raise ValueError("Temperature is below absolute zero")
        return value
