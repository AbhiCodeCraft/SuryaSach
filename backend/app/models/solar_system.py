from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class SystemProfile:
    capacity_kw: float
    location_label: str
    latitude: float
    longitude: float
    install_date: date | None
    install_year: int | None
    tilt_degrees: float | None
    azimuth_degrees: float | None
    vendor_name: str | None


@dataclass(frozen=True)
class SolarSystem(SystemProfile):
    system_id: str
    owner_id: str
    created_at: datetime
    updated_at: datetime
