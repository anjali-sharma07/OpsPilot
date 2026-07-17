from pathlib import Path

import fitz

from app.services.document_service import DocumentService
from app.services.embedding_service import EmbeddingService


def test_document_service_ingests_pdf(tmp_path: Path) -> None:
    pdf_path = tmp_path / "sample.pdf"
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "OpsPilot ingestion pipeline")
    document.save(pdf_path)
    document.close()

    service = DocumentService(embedding_service=EmbeddingService(persist_directory=tmp_path / "chroma", collection_name="test-docs"))
    result = service.ingest_pdf(pdf_path, "sample.pdf")

    assert result["stored_in_chroma"] is True
    assert result["chunk_count"] >= 1
