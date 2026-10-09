import json
import sqlite3
from collections.abc import Iterator
from contextlib import closing, contextmanager
from dataclasses import asdict
from datetime import date, datetime
from pathlib import Path
from typing import Protocol

from app.models.solar_system import SolarSystem


class StorageUnavailable(Exception):
    pass


class SystemRepository(Protocol):
    def create(self, system: SolarSystem) -> None: ...
    def get(self, system_id: str, owner_id: str) -> SolarSystem | None: ...
    def list(self, owner_id: str) -> list[SolarSystem]: ...
    def update(self, system: SolarSystem) -> bool: ...


class SQLiteSystemRepository:
    def __init__(self, path: Path):
        self.path = path

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with closing(sqlite3.connect(self.path, timeout=5)) as connection:
                with connection:
                    connection.execute(
                        "CREATE TABLE IF NOT EXISTS systems ("
                        "system_id TEXT PRIMARY KEY, owner_id TEXT NOT NULL, "
                        "created_at TEXT NOT NULL, profile TEXT NOT NULL)"
                    )
                    yield connection
        except (sqlite3.Error, OSError) as error:
            raise StorageUnavailable from error

    @staticmethod
    def decode(raw: str) -> SolarSystem:
        data = json.loads(raw)
        if data["install_date"]:
            data["install_date"] = date.fromisoformat(data["install_date"])
        for key in ("created_at", "updated_at"):
            data[key] = datetime.fromisoformat(data[key])
        return SolarSystem(**data)

    def create(self, system: SolarSystem) -> None:
        with self.connection() as connection:
            connection.execute(
                "INSERT INTO systems VALUES (?, ?, ?, ?)",
                (
                    system.system_id,
                    system.owner_id,
                    system.created_at.isoformat(),
                    json.dumps(asdict(system), default=str),
                ),
            )

    def get(self, system_id: str, owner_id: str) -> SolarSystem | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT profile FROM systems WHERE system_id = ? AND owner_id = ?",
                (system_id, owner_id),
            ).fetchone()
        return self.decode(row[0]) if row else None

    def list(self, owner_id: str) -> list[SolarSystem]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT profile FROM systems WHERE owner_id = ? "
                "ORDER BY created_at DESC, system_id DESC",
                (owner_id,),
            ).fetchall()
        return [self.decode(row[0]) for row in rows]

    def update(self, system: SolarSystem) -> bool:
        with self.connection() as connection:
            cursor = connection.execute(
                "UPDATE systems SET profile = ? WHERE system_id = ? AND owner_id = ?",
                (json.dumps(asdict(system), default=str), system.system_id, system.owner_id),
            )
            return cursor.rowcount == 1
