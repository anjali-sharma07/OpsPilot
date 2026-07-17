import os
import re
from pathlib import Path
from fastapi import UploadFile

from app.api.utils import APIError
from app.core.config import settings
from app.services.pdf_service import PDFService

UPLOAD_DIR = Path(settings.upload_directory).expanduser()
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024


class FileService:
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        if not filename:
            raise APIError("invalid_pdf", "Uploaded file is missing a filename.", 400)

        safe_name = os.path.basename(filename).strip()
        safe_name = re.sub(r"[^A-Za-z0-9._-]", "-", safe_name)
        safe_name = safe_name.strip("._-") or "uploaded"

        if safe_name != filename and filename != os.path.basename(filename):
            raise APIError("invalid_pdf", "Invalid file name.", 400)

        if safe_name.lower().endswith(".pdf"):
            return safe_name

        raise APIError("unsupported_file_type", "Only PDF files are allowed.", 415)

    @staticmethod
    def validate_pdf(file: UploadFile) -> str:
        filename = FileService.sanitize_filename(file.filename or "")
        if not filename.lower().endswith(".pdf"):
            raise APIError("unsupported_file_type", "Only PDF files are allowed.", 415)
        return filename

    @staticmethod
    def save_upload(file: UploadFile) -> str:
        filename = FileService.validate_pdf(file)
        target_root = UPLOAD_DIR.resolve()
        target_path = (UPLOAD_DIR / filename).resolve()
        if not str(target_path).startswith(str(target_root)):
            raise APIError("invalid_pdf", "Invalid upload path.", 400)

        total_bytes = 0
        try:
            with target_path.open("wb") as destination:
                while chunk := file.file.read(1024 * 1024):
                    total_bytes += len(chunk)
                    if total_bytes > MAX_UPLOAD_SIZE_BYTES:
                        raise APIError("file_too_large", "File exceeds the maximum allowed size.", 413)
                    destination.write(chunk)
        except OSError as exc:
            raise APIError("file_write_failed", "Could not save the uploaded file.", 500) from exc

        return str(target_path)

    @staticmethod
    def extract_pdf_text(file_path: str | Path) -> str:
        return PDFService.extract_text(file_path)
