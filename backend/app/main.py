"""FastAPI application entrypoint."""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import get_settings
from app.services.provider_errors import (
    ProviderAuthenticationError,
    ProviderConfigurationError,
    ProviderServiceError,
)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://0.0.0.0:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(ProviderAuthenticationError)
    @app.exception_handler(ProviderConfigurationError)
    async def handle_provider_configuration_error(
        request: Request,
        exc: ProviderAuthenticationError | ProviderConfigurationError,
    ) -> JSONResponse:
        return JSONResponse(status_code=503, content={"detail": str(exc)})

    @app.exception_handler(ProviderServiceError)
    async def handle_provider_service_error(
        request: Request,
        exc: ProviderServiceError,
    ) -> JSONResponse:
        return JSONResponse(status_code=502, content={"detail": str(exc)})

    app.include_router(api_router)

    static_dir = Path(__file__).resolve().parent / "static"
    index_file = static_dir / "index.html"
    assets_dir = static_dir / "assets"

    if static_dir.exists() and index_file.exists():
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

        @app.get("/")
        def frontend_index() -> FileResponse:
            return FileResponse(index_file)

    else:
        @app.get("/")
        def root() -> JSONResponse:
            return JSONResponse({"message": "NG12 API running", "docs": "/docs"})

    return app


app = create_app()
