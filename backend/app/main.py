from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.health import router
from app.api.systems import router as systems_router
from app.config.settings import Settings
from app.repositories.systems import SQLiteSystemRepository, StorageUnavailable
from app.services.systems import SystemNotFound, SystemService


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    application = FastAPI(title=settings.app_name, version="0.2.0")
    application.state.system_service = SystemService(SQLiteSystemRepository(settings.database_path))
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT"],
        allow_headers=["Accept", "Content-Type"],
    )
    application.include_router(router)
    application.include_router(systems_router)

    @application.exception_handler(SystemNotFound)
    async def system_not_found(_request, _error):
        return JSONResponse(status_code=404, content={"detail": "Solar system not found"})

    @application.exception_handler(StorageUnavailable)
    async def storage_unavailable(_request, _error):
        return JSONResponse(
            status_code=503,
            content={"detail": "Local storage is unavailable. Please try again shortly."},
        )

    return application


app = create_app()
