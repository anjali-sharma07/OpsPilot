"""
Upload API router.

``DocumentService`` (which internally holds an ``EmbeddingService``) is
retrieved via ``Depends()`` so that the embedding model and ChromaDB client
are **not** loaded at import time.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile

from app.api.utils import APIError, create_error_response
from app.core.container import get_document_service
from app.services.document_service import DocumentService
from app.services.file_service import FileService

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
        raise create_error_response(exc) from exc
    except ValueError as exc:
        raise create_error_response(APIError("invalid_request", str(exc), 400)) from exc

    return {"filename": saved_filename, "path": saved_path, **result}
