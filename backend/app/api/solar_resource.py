from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request

from app.api.systems import Service as SystemService
from app.schemas.solar_resource import ResourceDateQuery, ResourceQuery, SolarWeatherDay
from app.services.nasa_power import NasaPowerService

router = APIRouter(tags=["solar-resource"])


def get_resource_service(request: Request) -> NasaPowerService:
    return request.app.state.solar_resource_service


Service = Annotated[NasaPowerService, Depends(get_resource_service)]


@router.get("/solar-resource", response_model=SolarWeatherDay)
def solar_resource(query: Annotated[ResourceQuery, Query()], service: Service) -> SolarWeatherDay:
    """Independent gridded resource data for a NASA local solar day (not an IST day)."""
    return service.get(query)


@router.get("/systems/{system_id}/solar-resource", response_model=SolarWeatherDay)
def system_solar_resource(
    system_id: UUID,
    query: Annotated[ResourceDateQuery, Query()],
    systems: SystemService,
    service: Service,
) -> SolarWeatherDay:
    """Fetch resource data at the saved system's coordinates; no generation calculation."""
    system = systems.get(str(system_id))
    return service.get(
        ResourceQuery(latitude=system.latitude, longitude=system.longitude, date=query.date)
    )
