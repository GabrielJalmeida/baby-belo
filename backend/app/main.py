from fastapi import FastAPI

from app.auth.router import router as auth_router
from app.health.router import router as health_router
from app.shared.config import settings


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)

app.include_router(health_router)
app.include_router(auth_router)