from pathlib import Path
from typing import Any

import chromadb
from sentence_transformers import SentenceTransformer

from app.api.utils import APIError
from app.core.config import settings


class EmbeddingService:
    def __init__(
        self,
        model_name: str | None = None,
        persist_directory: str | Path | None = None,
        collection_name: str = "documents",
    ) -> None:
        self.model_name = model_name or settings.embedding_model
        self.persist_directory = Path(persist_directory or settings.chroma_db_path)
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        try:
            self.client = chromadb.PersistentClient(path=str(self.persist_directory))
            self.collection = self.client.get_or_create_collection(name=collection_name)
            self.model = SentenceTransformer(self.model_name)
        except Exception as exc:  # pragma: no cover - defensive external dependency handling
            raise APIError("chroma_db_error", "ChromaDB could not be initialized.", 500) from exc

    def generate_embedding(self, text: str) -> list[float]:
        if not text or not text.strip():
            raise ValueError("Text must not be empty")

        embedding = self.model.encode(text)
        return [float(value) for value in embedding]

    def add_documents(
        self,
        documents: list[str],
        metadatas: list[dict[str, Any]] | None = None,
        ids: list[str] | None = None,
    ) -> None:
        if not documents:
            return

        resolved_ids = ids or [f"doc-{index}" for index in range(len(documents))]
        resolved_metadatas = metadatas or [{} for _ in documents]
        embeddings = [self.generate_embedding(document) for document in documents]

        try:
            self.collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=resolved_metadatas,
                ids=resolved_ids,
            )
        except Exception as exc:  # pragma: no cover - defensive external dependency handling
            raise APIError("chroma_db_error", "ChromaDB could not store the document embeddings.", 500) from exc

    def query(self, query_text: str, n_results: int = 3) -> dict[str, Any]:
        if n_results <= 0:
            raise ValueError("n_results must be greater than zero")

        embedding = self.generate_embedding(query_text)
        try:
            return self.collection.query(query_embeddings=[embedding], n_results=n_results)
        except Exception as exc:  # pragma: no cover - defensive external dependency handling
            raise APIError("chroma_db_error", "ChromaDB could not query the document embeddings.", 500) from exc
