from fastapi.testclient import TestClient

from app.config.settings import Settings
from app.main import create_app


def make_client() -> TestClient:
    return TestClient(create_app(Settings(_env_file=None, cors_origins=["http://localhost:3000"])))


def test_health() -> None:
    with make_client() as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "surya-sach-api"}


def test_allowed_origin() -> None:
    with make_client() as client:
        response = client.get("/health", headers={"Origin": "http://localhost:3000"})
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_unknown_origin_has_no_cors_permission() -> None:
    with make_client() as client:
        response = client.get("/health", headers={"Origin": "https://untrusted.example"})
    assert "access-control-allow-origin" not in response.headers


def test_cors_preflight() -> None:
    with make_client() as client:
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_settings_read_environment(monkeypatch) -> None:
    monkeypatch.setenv("CORS_ORIGINS", '["https://surya.example"]')
    monkeypatch.setenv("API_PORT", "8001")
    settings = Settings(_env_file=None)
    assert settings.cors_origins == ["https://surya.example"]
    assert settings.api_port == 8001
