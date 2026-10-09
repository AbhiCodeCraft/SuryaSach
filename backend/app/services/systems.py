from dataclasses import asdict
from datetime import UTC, datetime
from uuid import uuid4

from app.models.solar_system import SolarSystem, SystemProfile
from app.repositories.systems import SystemRepository


class SystemNotFound(Exception):
    pass


class SystemService:
    def __init__(self, repository: SystemRepository, owner_id: str = "local-owner"):
        self.repository = repository
        self.owner_id = owner_id

    def create(self, profile: SystemProfile) -> SolarSystem:
        now = datetime.now(UTC)
        system = SolarSystem(
            **asdict(profile),
            system_id=str(uuid4()),
            owner_id=self.owner_id,
            created_at=now,
            updated_at=now,
        )
        self.repository.create(system)
        return system

    def get(self, system_id: str) -> SolarSystem:
        system = self.repository.get(system_id, self.owner_id)
        if system is None:
            raise SystemNotFound
        return system

    def list(self) -> list[SolarSystem]:
        return self.repository.list(self.owner_id)

    def update(self, system_id: str, profile: SystemProfile) -> SolarSystem:
        existing = self.get(system_id)
        system = SolarSystem(
            **asdict(profile),
            system_id=existing.system_id,
            owner_id=existing.owner_id,
            created_at=existing.created_at,
            updated_at=datetime.now(UTC),
        )
        if not self.repository.update(system):
            raise SystemNotFound
        return system
