"""
OpsPilot FastAPI application entry point.

Startup behaviour:
  - All heavy services (SentenceTransformer, ChromaDB, Groq) are **not**
    loaded here.  They are lazy-initialised inside the ServiceContainer and
    pulled via FastAPI Depends() on first request.
  - Database tables are created on the ``startup`` lifespan event so the
    SQLAlchemy engine is only instantiated after the process is fully booted,
    not at import time.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.chat import router as chat_router
from app.api.health import router as health_router
from app.api.upload import router as upload_router
from app.api.utils import APIError
from app.core.config import settings


ALLOWED_ORIGINS = [
    # Local development
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    # Vercel production — update this to your actual *.vercel.app URL once known,
    # or set via CORS_ALLOWED_ORIGINS env var after first deploy.
    "https://opspilot-frontend.vercel.app",
    # Vercel branch/preview deployments follow this pattern.
    # Replace <your-vercel-team> if you are on a team account.
    "https://opspilot.vercel.app",
]



@asynccontextmanager
async def lifespan(application: FastAPI):
    """Run startup tasks once the worker is fully booted."""
    # Deferred DB initialisation — creates tables if they don't exist.
    # Importing here (not at module level) keeps Base/engine out of the
    # import path so they aren't created during test collection.
    from app.database.database import Base, get_engine

    Base.metadata.create_all(bind=get_engine())
    yield
    # Shutdown: nothing to clean up (SQLAlchemy engine manages its own pool).


app = FastAPI(title=settings.app_name, lifespan=lifespan)


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
    return {"message": f"Welcome to {settings.app_name}"}