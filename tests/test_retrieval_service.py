from pathlib import Path

from app.services.embedding_service import EmbeddingService
from app.services.retrieval_service import RetrievalService


def test_retrieval_service_returns_ranked_chunks(tmp_path: Path) -> None:
    embedding_service = EmbeddingService(
        persist_directory=tmp_path / "chroma",
        collection_name="retrieval-test",
    )
    embedding_service.add_documents(
        documents=["Alpha beta gamma", "Delta epsilon zeta"],
        metadatas=[
            {"filename": "doc-a.pdf", "page_number": 1},
            {"filename": "doc-b.pdf", "page_number": 2},
        ],
        ids=["chunk-1", "chunk-2"],
    )

    retrieval_service = RetrievalService(embedding_service=embedding_service)
    results = retrieval_service.retrieve("alpha", top_k=2)

    assert len(results) == 2
    assert results[0]["filename"] == "doc-a.pdf"
    assert results[0]["page_number"] == 1
    assert "similarity_score" in results[0]
    assert results[0]["similarity_score"] >= 0
