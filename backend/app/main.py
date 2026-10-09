from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.health import router
from app.api.solar_resource import router as solar_resource_router
from app.api.systems import router as systems_router
from app.config.settings import Settings
from app.repositories.solar_resource import MemorySolarResourceCache
from app.repositories.systems import SQLiteSystemRepository, StorageUnavailable
from app.services.nasa_power import NasaPowerService, SolarResourceError
from app.services.systems import SystemNotFound, SystemService


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    application = FastAPI(title=settings.app_name, version="0.3.0")
    application.state.system_service = SystemService(SQLiteSystemRepository(settings.database_path))
    application.state.solar_resource_service = NasaPowerService(MemorySolarResourceCache())
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT"],
        allow_headers=["Accept", "Content-Type"],
    )
    application.include_router(router)
    application.include_router(systems_router)
    application.include_router(solar_resource_router)

    @application.exception_handler(SolarResourceError)
    async def solar_resource_error(_request: Request, error: SolarResourceError) -> JSONResponse:
        return JSONResponse(
            status_code=error.status_code,
            content={"detail": {"code": error.code, "message": str(error)}},
        )

    @application.exception_handler(SystemNotFound)
    async def system_not_found(_request: Request, _error: SystemNotFound) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": "Solar system not found"})

    @application.exception_handler(StorageUnavailable)
    async def storage_unavailable(_request: Request, _error: StorageUnavailable) -> JSONResponse:
        return JSONResponse(
            status_code=503,
            content={"detail": "Local storage is unavailable. Please try again shortly."},
        )

    @application.exception_handler(RequestValidationError)
    async def invalid_request(_request: Request, error: RequestValidationError) -> JSONResponse:
        # Keep useful field errors without echoing private inputs or non-JSON numeric values.
        details = [{key: item[key] for key in ("loc", "msg", "type")} for item in error.errors()]
        return JSONResponse(status_code=422, content={"detail": details})

    return application


app = create_app()
