from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response

from app.models.solar_system import SolarSystem, SystemProfile
from app.schemas.solar_system import SystemResponse, SystemWrite
from app.services.systems import SystemService

router = APIRouter(prefix="/systems", tags=["systems"])


def get_service(request: Request) -> SystemService:
    return request.app.state.system_service


Service = Annotated[SystemService, Depends(get_service)]


@router.post("", response_model=SystemResponse, status_code=201)
def create_system(body: SystemWrite, response: Response, service: Service) -> SolarSystem:
    system = service.create(SystemProfile(**body.model_dump()))
    response.headers["Location"] = f"/systems/{system.system_id}"
    return system


@router.get("", response_model=list[SystemResponse])
def list_systems(service: Service) -> list[SolarSystem]:
    return service.list()


@router.get("/{system_id}", response_model=SystemResponse)
def get_system(system_id: UUID, service: Service) -> SolarSystem:
    return service.get(str(system_id))


@router.put("/{system_id}", response_model=SystemResponse)
def update_system(system_id: UUID, body: SystemWrite, service: Service) -> SolarSystem:
    return service.update(str(system_id), SystemProfile(**body.model_dump()))
