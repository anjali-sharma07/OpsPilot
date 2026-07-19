"""
DocumentService — orchestrates PDF ingestion into ChromaDB.

The ``EmbeddingService`` dependency is **injected** rather than constructed
internally, preventing a duplicate model-load when the container already
holds the singleton instance.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.services.file_service import FileService
from app.services.pdf_service import PDFService


class DocumentService:
    def __init__(
        self,
        file_service: FileService | None = None,
        pdf_service: PDFService | None = None,
        chunking_service: ChunkingService | None = None,
        embedding_service: EmbeddingService | None = None,
    ) -> None:
        self.pdf_service = pdf_service or PDFService
        self.chunking_service = chunking_service or ChunkingService
        # NOTE: Do NOT fall back to ``EmbeddingService()`` here.
        # The caller (container.document_service or a test) must inject a
        # concrete instance.  This avoids a second SentenceTransformer load.
        if embedding_service is None:
            raise ValueError(
                "DocumentService requires an EmbeddingService instance. "
                "Use the ServiceContainer or inject one explicitly."
            )
        self.embedding_service: EmbeddingService = embedding_service

    def ingest_pdf(self, file_path: str | Path, filename: str) -> dict[str, Any]:
        extracted_text = self.pdf_service.extract_text(file_path)
        chunks = self.chunking_service.chunk_text(extracted_text)

        documents: list[str] = []
        metadatas: list[dict[str, Any]] = []
        ids: list[str] = []

        for index, chunk in enumerate(chunks):
            chunk_id = f"{Path(filename).stem}-{index + 1}"
            documents.append(chunk)
            metadatas.append(
                {
                    "filename": filename,
                    "page_number": 1,
                    "chunk_id": chunk_id,
                }
            )
            ids.append(chunk_id)

        self.embedding_service.add_documents(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
        )

        return {
            "filename": filename,
            "chunk_count": len(chunks),
            "stored_in_chroma": True,
        }
