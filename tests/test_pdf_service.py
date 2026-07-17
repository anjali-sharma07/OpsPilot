from pathlib import Path

import fitz

from app.services.pdf_service import PDFService


def test_extract_text_from_pdf(tmp_path: Path) -> None:
    pdf_path = tmp_path / "sample.pdf"
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "OpsPilot PDF extraction")
    document.save(pdf_path)
    document.close()

    extracted_text = PDFService.extract_text(pdf_path)

    assert "OpsPilot PDF extraction" in extracted_text
