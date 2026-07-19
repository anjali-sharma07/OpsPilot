"""
Upload API router.

``DocumentService`` (which internally holds an ``EmbeddingService``) is
retrieved via ``Depends()`` so that the embedding model and ChromaDB client
are **not** loaded at import time.  Both are pre-warmed during app startup,
so by the time this endpoint is called they are already in memory.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, File, UploadFile

from app.api.utils import APIError, create_error_response
from app.core.container import get_document_service
from app.services.document_service import DocumentService
from app.services.file_service import FileService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("")
def upload_pdf(
    file: UploadFile = File(...),
    document_service: DocumentService = Depends(get_document_service),
) -> dict[str, object]:
    try:
        saved_filename = FileService.validate_pdf(file)
        saved_path = FileService.save_upload(file)
        result = document_service.ingest_pdf(saved_path, saved_filename)
    except APIError as exc:
        logger.error(
            "Upload failed [%s]: %s (status=%s)",
            exc.code, exc.message, exc.status_code,
        )
        raise create_error_response(exc) from exc
    except ValueError as exc:
        logger.error("Upload validation error: %s", exc)
        raise create_error_response(APIError("invalid_request", str(exc), 400)) from exc
    except Exception as exc:
        # Catch-all: log the full traceback so it appears in Render's log
        # stream.  Without this, unexpected errors silently become 500s with
        # no visibility into what actually went wrong.
        logger.exception("Upload unexpected error for file '%s'", getattr(file, 'filename', ''))
        raise create_error_response(
            APIError("upload_failed", f"An unexpected error occurred: {exc}", 500)
        ) from exc

    logger.info(
        "Upload complete: filename=%s chunks=%s",
        saved_filename,
        result.get("chunk_count"),
    )
    return {"filename": saved_filename, "path": saved_path, **result}
