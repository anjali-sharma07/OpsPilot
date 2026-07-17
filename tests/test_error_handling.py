from fastapi.testclient import TestClient

from app.main import app


def test_upload_returns_consistent_error_for_unsupported_file_type() -> None:
    client = TestClient(app)

    response = client.post(
        "/upload",
        files={"file": ("notes.txt", b"not a pdf", "text/plain")},
    )

    assert response.status_code == 415
    payload = response.json()
    assert payload["error"]["code"] == "unsupported_file_type"
    assert payload["error"]["message"] == "Only PDF files are allowed."
