"""
OpsPilot FastAPI application entry point.

Startup behaviour:
  - Database tables are created on the lifespan startup event.
  - The SentenceTransformer model and ChromaDB client are pre-warmed
    synchronously during startup (inside run_in_executor so the event loop
    is not blocked).  This prevents the first POST /upload from triggering
    model loading inside a 30-second HTTP request window and getting a 502.
  - All other services remain lazy and are pulled via FastAPI Depends() on
    first request.
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.chat import router as chat_router
from app.api.health import router as health_router
from app.api.upload import router as upload_router
from app.api.utils import APIError
from app.core.config import settings

logger = logging.getLogger(__name__)


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


def _prewarm_embedding() -> None:
    """Load SentenceTransformer + ChromaDB synchronously.

    Called from the lifespan startup via ``run_in_executor`` so the asyncio
    event loop is never blocked.  The lifespan awaits this function, which
    means the app does NOT start accepting requests until the model is ready.

    WHY THIS IS REQUIRED ON RENDER FREE:
    Loading ``SentenceTransformer("all-MiniLM-L6-v2")`` takes 60–120 s on a
    cold Render Free instance (torch init + reading ~90 MB of weights).
    Render's HTTP request timeout is 30 s.  If model loading is triggered
    inside the first POST /upload handler the timeout fires first → 502.
    Pre-warming during startup avoids this entirely.
    """
    from app.core.container import container

    try:
        logger.info("Pre-warming SentenceTransformer model (%s)…", settings.embedding_model)
        # Accessing _model triggers the cached_property → loads torch + weights.
        _ = container.embedding_service._model
        logger.info("SentenceTransformer model loaded.")

        logger.info("Pre-warming ChromaDB client…")
        # Accessing _client triggers chromadb.PersistentClient creation.
        _ = container.embedding_service._client
        logger.info("ChromaDB client ready.")
    except Exception:
        # Log the full traceback so it appears in Render's log stream.
        # Do NOT re-raise — a pre-warm failure should not abort startup;
        # lazy init will still attempt initialisation on the first request.
        logger.exception(
            "Embedding pre-warm failed. The first upload request will attempt "
            "lazy initialisation and may be slow or timeout."
        )


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Run startup tasks once the worker is fully booted."""
    # 1. Create DB tables (fast — just DDL if tables don't exist).
    from app.database.database import Base, get_engine

    Base.metadata.create_all(bind=get_engine())

    # 2. Pre-warm embedding model in a thread pool executor.
    #    run_in_executor keeps the event loop free while the CPU/IO-bound
    #    model load runs in a background thread.
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _prewarm_embedding)

    yield
    # Shutdown: nothing to clean up.


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