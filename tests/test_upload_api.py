import unittest
from io import BytesIO

import fitz

from fastapi.testclient import TestClient

from app.main import app
from app.services.file_service import UPLOAD_DIR


def _make_pdf_bytes() -> bytes:
    """Create a minimal but valid PDF with one text page using PyMuPDF."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "OpsPilot upload test document")
    buf = BytesIO()
    doc.save(buf)
    doc.close()
    buf.seek(0)
    return buf.read()


class UploadApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def tearDown(self) -> None:
        test_file = UPLOAD_DIR / "sample.pdf"
        try:
            if test_file.exists():
                test_file.unlink()
        except PermissionError:
            # On Windows the file handle may still be held by the upload
            # machinery; skip the cleanup — the next test run will overwrite it.
            pass

    def test_upload_accepts_pdf(self) -> None:
        response = self.client.post(
            "/upload",
            files={"file": ("sample.pdf", _make_pdf_bytes(), "application/pdf")},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue((UPLOAD_DIR / "sample.pdf").exists())
        self.assertIn("sample.pdf", response.json()["filename"])

    def test_upload_rejects_non_pdf(self) -> None:
        response = self.client.post(
            "/upload",
            files={"file": ("sample.txt", BytesIO(b"hello"), "text/plain")},
        )

        # FileService raises APIError("unsupported_file_type", ..., 415)
        self.assertEqual(response.status_code, 415)
        payload = response.json()
        self.assertIn("Only PDF files are allowed", payload["error"]["message"])


if __name__ == "__main__":
    unittest.main()
