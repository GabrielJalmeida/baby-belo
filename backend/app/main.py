from fastapi import FastAPI

from app.auth.router import router as auth_router
from app.health.router import router as health_router
from app.shared.config import settings

from app.core.router import router as core_router
from app.core.unit_router import router as unit_router
from app.core.item_router import router as item_router
from app.core.movement_router import router as movement_router

from app.custom.categoria_router import router as categoria_router
from app.core.stock_router import router as stock_router
from app.core.inventory_router import router as inventory_router
from app.custom.campo_router import router as campo_router
from app.custom.campo_opcao_router import router as campo_opcao_router
from app.custom.valor_item_router import router as valor_item_router
from app.custom.item_categoria_router import router as item_categoria_router

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)

app.include_router(core_router)
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(unit_router)
app.include_router(item_router)
app.include_router(movement_router)
app.include_router(stock_router)
app.include_router(inventory_router)
app.include_router(categoria_router)
app.include_router(campo_router)
app.include_router(campo_opcao_router)
app.include_router(valor_item_router)
app.include_router(item_categoria_router)
