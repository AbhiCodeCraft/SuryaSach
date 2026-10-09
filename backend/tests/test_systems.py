from datetime import timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.config.settings import Settings
from app.main import create_app
from app.repositories.systems import SQLiteSystemRepository, StorageUnavailable
from app.schemas.solar_system import today_in_india
from app.services.systems import SystemService


@pytest.fixture
def settings(tmp_path):
    return Settings(_env_file=None, database_path=tmp_path / "profiles.sqlite3")


@pytest.fixture
def client(settings):
    with TestClient(create_app(settings)) as client:
        yield client


@pytest.fixture
def profile():
    return {
        "capacity_kw": 3,
        "location_label": "  Delhi rooftop  ",
        "latitude": 28.6139,
        "longitude": 77.209,
        "install_date": "2020-04-15",
        "tilt_degrees": 25,
        "azimuth_degrees": 180,
        "vendor_name": "  Solar Installer  ",
    }


def test_create_get_update_and_list(client, profile):
    response = client.post("/systems", json=profile)
    assert response.status_code == 201
    created = response.json()
    url = f"/systems/{created['system_id']}"
    assert response.headers["location"] == url
    assert created["location_label"] == "Delhi rooftop"
    assert created["vendor_name"] == "Solar Installer"
    assert created["owner_id"] == "local-owner"
    assert created["created_at"] == created["updated_at"]
    assert client.get(url).json() == created
    assert client.get("/systems").json() == [created]

    updated = client.put(url, json={**profile, "capacity_kw": 5, "azimuth_degrees": None})
    assert updated.status_code == 200
    assert updated.json()["capacity_kw"] == 5
    assert updated.json()["azimuth_degrees"] is None
    assert updated.json()["created_at"] == created["created_at"]
    assert updated.json()["updated_at"] >= created["updated_at"]
    assert client.get(url).json() == updated.json()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("capacity_kw", 0),
        ("capacity_kw", -1),
        ("capacity_kw", 100.01),
        ("capacity_kw", True),
        ("capacity_kw", "NaN"),
        ("capacity_kw", "Infinity"),
        ("latitude", -90.01),
        ("latitude", 90.01),
        ("longitude", -180.01),
        ("longitude", 180.01),
        ("tilt_degrees", -0.1),
        ("tilt_degrees", 90.1),
        ("azimuth_degrees", -0.1),
        ("azimuth_degrees", 360),
        ("location_label", "   "),
        ("location_label", "x" * 121),
        ("vendor_name", "x" * 121),
        ("install_date", "1899-12-31"),
        ("install_date", "not a date"),
        ("install_date", 0),
    ],
)
def test_invalid_profiles_rejected_for_create_and_update(client, profile, field, value):
    created = client.post("/systems", json=profile).json()
    invalid = {**profile, field: value}
    assert client.post("/systems", json=invalid).status_code == 422
    url = f"/systems/{created['system_id']}"
    assert client.put(url, json=invalid).status_code == 422
    assert client.get(url).json() == created


def test_future_date_rejected(client, profile):
    profile["install_date"] = (today_in_india() + timedelta(days=1)).isoformat()
    assert client.post("/systems", json=profile).status_code == 422


def test_today_and_numeric_boundaries_accepted(client, profile):
    profile.update(
        capacity_kw=100,
        latitude=-90,
        longitude=180,
        tilt_degrees=0,
        azimuth_degrees=0,
        install_date=today_in_india().isoformat(),
    )
    assert client.post("/systems", json=profile).status_code == 201
    profile.update(latitude=90, longitude=-180, tilt_degrees=90, azimuth_degrees=359.99)
    assert client.post("/systems", json=profile).status_code == 201


def test_unknown_and_optional_values_preserved(client, profile):
    for field in ("tilt_degrees", "azimuth_degrees", "vendor_name"):
        profile.pop(field)
    result = client.post("/systems", json=profile)
    assert result.status_code == 201
    for field in ("tilt_degrees", "azimuth_degrees", "vendor_name"):
        assert result.json()[field] is None
    profile["vendor_name"] = "  "
    assert client.post("/systems", json=profile).json()["vendor_name"] is None


def test_year_only_does_not_invent_date(client, profile):
    profile.pop("install_date")
    profile["install_year"] = 2020
    result = client.post("/systems", json=profile)
    assert result.status_code == 201
    assert result.json()["install_year"] == 2020
    assert result.json()["install_date"] is None
    for year in (1899, today_in_india().year + 1, True, 2020.5):
        assert client.post("/systems", json={**profile, "install_year": year}).status_code == 422


def test_installation_precision_required(client, profile):
    assert client.post("/systems", json={**profile, "install_year": 2020}).status_code == 422
    profile.pop("install_date")
    assert client.post("/systems", json=profile).status_code == 422


def test_missing_and_malformed_id(client, profile):
    for method in ("get", "put"):
        kwargs = {"json": profile} if method == "put" else {}
        assert getattr(client, method)(f"/systems/{uuid4()}", **kwargs).status_code == 404
        assert getattr(client, method)("/systems/not-a-uuid", **kwargs).status_code == 422


def test_cannot_supply_owner_or_metadata(client, profile):
    for field in ("owner_id", "system_id", "created_at", "updated_at"):
        assert client.post("/systems", json={**profile, field: "forged"}).status_code == 422


def test_persists_across_application_restarts(settings, profile):
    with TestClient(create_app(settings)) as first:
        created = first.post("/systems", json=profile).json()
    with TestClient(create_app(settings)) as restarted:
        assert restarted.get(f"/systems/{created['system_id']}").json() == created


def test_storage_failure_is_useful_and_does_not_leak_path(client, monkeypatch):
    def fail(*args):
        raise StorageUnavailable("private filesystem details")

    monkeypatch.setattr(client.app.state.system_service.repository, "list", fail)
    response = client.get("/systems")
    assert response.status_code == 503
    assert "private" not in response.text


def test_repository_filters_owner(client, settings, profile):
    system = client.post("/systems", json=profile).json()
    other = SystemService(SQLiteSystemRepository(settings.database_path), owner_id="another-owner")
    assert other.list() == []
    assert other.repository.get(system["system_id"], "another-owner") is None


@pytest.mark.parametrize("method", ["POST", "PUT"])
def test_write_cors_preflight(client, method):
    response = client.options(
        "/systems",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": method,
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
