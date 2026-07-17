from typing import Any

from app.services.embedding_service import EmbeddingService


class RetrievalService:
    def __init__(self, embedding_service: EmbeddingService) -> None:
        self.embedding_service = embedding_service

    def retrieve(self, question: str, top_k: int = 5) -> list[dict[str, Any]]:
        if not question or not question.strip():
            raise ValueError("Question must not be empty")
        if top_k <= 0:
            raise ValueError("top_k must be greater than zero")

        response = self.embedding_service.query(question, n_results=top_k)
        results: list[dict[str, Any]] = []

        documents = response.get("documents", [[]])[0]
        metadatas = response.get("metadatas", [[]])[0]
        distances = response.get("distances", [[]])[0]

        for index, document in enumerate(documents):
            metadata = metadatas[index] if index < len(metadatas) else {}
            distance = distances[index] if index < len(distances) else 0.0
            similarity_score = max(0.0, 1.0 - distance)

            results.append(
                {
                    "chunk": document,
                    "similarity_score": round(similarity_score, 4),
                    "filename": metadata.get("filename", ""),
                    "page_number": metadata.get("page_number"),
                    "chunk_id": metadata.get("chunk_id", ""),
                }
            )

        return results
