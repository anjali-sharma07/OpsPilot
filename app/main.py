from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.api.chat import router as chat_router
from app.api.health import router as health_router
from app.api.upload import router as upload_router
from app.api.utils import APIError
from app.core.config import Settings

settings = Settings()
app = FastAPI(title=settings.app_name)
app.include_router(health_router)
app.include_router(upload_router)
app.include_router(chat_router)


@app.exception_handler(APIError)
async def api_error_handler(_, exc: APIError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.get("/")
def root() -> dict[str, str]:
    return {"message": f"Welcome to {settings.app_name}"}
