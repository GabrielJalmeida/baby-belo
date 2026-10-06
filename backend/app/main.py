from fastapi import FastAPI


app = FastAPI(
    title="Estoque Flex API",
    version="0.1.0",
)


@app.get("/api/v1/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}