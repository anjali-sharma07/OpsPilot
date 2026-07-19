from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api.chat import router as chat_router
from app.api.health import router as health_router
from app.api.upload import router as upload_router
from app.api.utils import APIError
from app.core.config import Settings

settings = Settings()

app = FastAPI(title=settings.app_name)


ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# CORS spec rule: allow_headers=["*"] is INVALID when allow_credentials=True.
# Browsers (Chrome/Firefox) will silently drop Access-Control-Allow-Origin
# when they detect this illegal combination. Always enumerate headers explicitly.
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Content-Type", "Authorization", "Accept", "Origin", "X-Requested-With"],
    expose_headers=["Content-Type"],
)


app.include_router(health_router)
app.include_router(upload_router)
app.include_router(chat_router)


@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    # FastAPI exception handlers bypass CORSMiddleware on the response path.
    # We must manually add the CORS header so browsers can read error responses.
    origin = request.headers.get("origin", "")
    headers = {}
    if origin in ALLOWED_ORIGINS:
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"
        headers["Vary"] = "Origin"
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
            }
        },
        headers=headers,
    )


@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.app_name}"
    }