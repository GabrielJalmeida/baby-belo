from fastapi import APIRouter


router = APIRouter(
    prefix="/api/v1/health",
    tags=["health"],
)


@router.get("")
def health() -> dict[str, str]:
    return {"status": "ok"}