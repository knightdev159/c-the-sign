"""Health check endpoints."""

from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/healthz")
def healthz() -> dict[str, str]:
    settings = get_settings()
    return {"status": "ok", "env": settings.app_env}
