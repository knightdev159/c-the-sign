"""FastAPI application entrypoint."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
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
