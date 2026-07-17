from fastapi import APIRouter, File, UploadFile

from app.api.utils import APIError, create_error_response
from app.services.document_service import DocumentService
from app.services.file_service import FileService

router = APIRouter(prefix="/upload", tags=["upload"])
document_service = DocumentService()


@router.post("")
def upload_pdf(file: UploadFile = File(...)) -> dict[str, object]:
    try:
        saved_filename = FileService.validate_pdf(file)
        saved_path = FileService.save_upload(file)
        result = document_service.ingest_pdf(saved_path, saved_filename)
    except APIError as exc:
        raise create_error_response(exc) from exc
    except ValueError as exc:
        raise create_error_response(APIError("invalid_request", str(exc), 400)) from exc

    return {"filename": saved_filename, "path": saved_path, **result}
