from pathlib import Path

import fitz

from app.api.utils import APIError


class PDFService:
    @staticmethod
    def extract_text(file_path: str | Path) -> str:
        try:
            document = fitz.open(file_path)
        except FileNotFoundError as exc:
            raise APIError("invalid_pdf", "The uploaded PDF could not be found.", 400) from exc
        except RuntimeError as exc:
            raise APIError("corrupted_pdf", "The uploaded PDF is corrupted or unreadable.", 422) from exc
        except ValueError as exc:
            raise APIError("invalid_pdf", "The uploaded file is not a valid PDF.", 400) from exc

        try:
            text_chunks = [page.get_text() for page in document]
            extracted_text = "\n\n".join(chunk for chunk in text_chunks if chunk)
            if not extracted_text.strip():
                raise APIError("empty_pdf", "The uploaded PDF does not contain any extractable text.", 422)
            return extracted_text
        except RuntimeError as exc:
            raise APIError("corrupted_pdf", "The uploaded PDF is corrupted or unreadable.", 422) from exc
        finally:
            document.close()
