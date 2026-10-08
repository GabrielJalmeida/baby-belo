from fastapi import FastAPI

from app.auth.router import router as auth_router
from app.health.router import router as health_router
from app.shared.config import settings
from app.core.router import router as core_router
from app.core.unit_router import router as unit_router


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)

app.include_router(core_router)
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(unit_router)