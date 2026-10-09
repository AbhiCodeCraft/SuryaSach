"""Opt-in live checks. NASA's values may change as source data is revised."""

import os
from datetime import date, timedelta

import pytest

from app.repositories.solar_resource import MemorySolarResourceCache
from app.schemas.solar_resource import ResourceQuery
from app.schemas.solar_system import today_in_india
from app.services.nasa_power import NasaPowerService

pytestmark = [
    pytest.mark.external,
    pytest.mark.skipif(
        os.getenv("NASA_SMOKE") != "1", reason="Set NASA_SMOKE=1 for live NASA checks"
    ),
]


@pytest.mark.parametrize(
    "name,latitude,longitude",
    [
        ("Delhi", 28.6139, 77.209),
        ("Jaipur", 26.9124, 75.7873),
        ("Bengaluru", 12.9716, 77.5946),
    ],
)
def test_real_indian_resource(name, latitude, longitude):
    day = date.fromisoformat(
        os.getenv("NASA_SMOKE_DATE", str(today_in_india() - timedelta(days=30)))
    )
    service = NasaPowerService(MemorySolarResourceCache())
    result = service.get(ResourceQuery(latitude=latitude, longitude=longitude, date=day))
    print(name, result.model_dump_json())
    # Broad order-of-magnitude checks, not hard-coded site observations.
    assert 0 < result.ghi_kwh_m2_day < 15
    if result.temp_avg_c is not None:
        assert -30 < result.temp_avg_c < 60
    assert result.source == "NASA_POWER"
    assert result.time_standard == "LST"
