import os
import unittest
from io import BytesIO

from fastapi.testclient import TestClient

from app.main import app
from app.services.file_service import UPLOAD_DIR


class UploadApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def tearDown(self) -> None:
        test_file = UPLOAD_DIR / "sample.pdf"
        if test_file.exists():
            test_file.unlink()

    def test_upload_accepts_pdf(self) -> None:
        response = self.client.post(
            "/upload",
            files={"file": ("sample.pdf", BytesIO(b"%PDF-1.4\n"), "application/pdf")},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue((UPLOAD_DIR / "sample.pdf").exists())
        self.assertIn("sample.pdf", response.json()["filename"])

    def test_upload_rejects_non_pdf(self) -> None:
        response = self.client.post(
            "/upload",
            files={"file": ("sample.txt", BytesIO(b"hello"), "text/plain")},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Only PDF files are allowed", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
