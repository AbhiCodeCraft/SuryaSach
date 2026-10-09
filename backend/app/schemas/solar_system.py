from datetime import date, datetime, timedelta, timezone
from typing import Annotated, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

INDIA_TIMEZONE = timezone(timedelta(hours=5, minutes=30))


def today_in_india() -> date:
    return datetime.now(INDIA_TIMEZONE).date()


FiniteNumber = Annotated[float, Field(strict=True, allow_inf_nan=False)]


class SystemWrite(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    capacity_kw: Annotated[FiniteNumber, Field(gt=0, le=100)]
    location_label: str = Field(min_length=1, max_length=120)
    latitude: Annotated[FiniteNumber, Field(ge=-90, le=90)]
    longitude: Annotated[FiniteNumber, Field(ge=-180, le=180)]
    install_date: date | None = None
    install_year: int | None = Field(default=None, strict=True, ge=1900)
    tilt_degrees: Annotated[FiniteNumber, Field(ge=0, le=90)] | None = None
    azimuth_degrees: Annotated[FiniteNumber, Field(ge=0, lt=360)] | None = None
    vendor_name: str | None = Field(default=None, max_length=120)

    @field_validator("install_date", mode="before")
    @classmethod
    def require_iso_date(cls, value: object) -> object:
        if value is not None and not isinstance(value, (str, date)):
            raise ValueError("Use an ISO calendar date (YYYY-MM-DD)")
        return value

    @field_validator("vendor_name")
    @classmethod
    def blank_vendor_is_unknown(cls, value: str | None) -> str | None:
        return value or None

    @model_validator(mode="after")
    def validate_installation(self) -> Self:
        if (self.install_date is None) == (self.install_year is None):
            raise ValueError("Provide either an installation date or an installation year")
        today = today_in_india()
        if self.install_date and not date(1900, 1, 1) <= self.install_date <= today:
            raise ValueError("Installation date must be between 1900-01-01 and today in India")
        if self.install_year is not None and self.install_year > today.year:
            raise ValueError("Installation year must not be in the future")
        return self


class SystemResponse(SystemWrite):
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

    system_id: UUID
    owner_id: str
    created_at: datetime
    updated_at: datetime
