"""
EmbeddingService — wraps SentenceTransformer + ChromaDB with lazy init.

``__init__`` stores **only** lightweight config strings.  The expensive
objects (``chromadb.PersistentClient``, ``chromadb.Collection``, and the
``SentenceTransformer`` model) are created on first access via
``@functools.cached_property``.  This means importing this module costs
virtually zero RAM; the ~350 MB hit arrives only when the first embedding
is actually requested.
"""

from __future__ import annotations

import logging
import time
from functools import cached_property
from pathlib import Path
from typing import Any

from app.api.utils import APIError
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(
        self,
        model_name: str | None = None,
        persist_directory: str | Path | None = None,
        collection_name: str = "documents",
    ) -> None:
        # Store only lightweight config — no heavy objects are created here.
        self.model_name: str = model_name or settings.embedding_model
        self._persist_directory: Path = Path(persist_directory or settings.chroma_db_path)
        self._collection_name: str = collection_name

    # ------------------------------------------------------------------
    # Lazy heavy properties
    # ------------------------------------------------------------------

    @cached_property
    def _client(self):
        """ChromaDB PersistentClient — created on first access."""
        import chromadb

        self._persist_directory.mkdir(parents=True, exist_ok=True)
        logger.info("Initialising ChromaDB PersistentClient at %s…", self._persist_directory)
        t0 = time.monotonic()
        try:
            client = chromadb.PersistentClient(path=str(self._persist_directory))
            logger.info("ChromaDB ready in %.1f s.", time.monotonic() - t0)
            return client
        except Exception as exc:  # pragma: no cover
            raise APIError("chroma_db_error", "ChromaDB could not be initialized.", 500) from exc

    @cached_property
    def _collection(self):
        """ChromaDB Collection — created on first access."""
        try:
            return self._client.get_or_create_collection(name=self._collection_name)
        except Exception as exc:  # pragma: no cover
            raise APIError("chroma_db_error", "ChromaDB could not be initialized.", 500) from exc

    @cached_property
    def _model(self):
        """SentenceTransformer model — loaded on first access (~200–350 MB)."""
        from sentence_transformers import SentenceTransformer

        logger.info("Loading SentenceTransformer model '%s'…", self.model_name)
        t0 = time.monotonic()
        try:
            model = SentenceTransformer(self.model_name)
            logger.info("SentenceTransformer '%s' loaded in %.1f s.", self.model_name, time.monotonic() - t0)
            return model
        except Exception as exc:  # pragma: no cover
            raise APIError("chroma_db_error", "SentenceTransformer model could not be loaded.", 500) from exc

    # ------------------------------------------------------------------
    # Public API (unchanged from original)
    # ------------------------------------------------------------------

    def generate_embedding(self, text: str) -> list[float]:
        if not text or not text.strip():
            raise ValueError("Text must not be empty")

        embedding = self._model.encode(text)
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
            self._collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=resolved_metadatas,
                ids=resolved_ids,
            )
        except Exception as exc:  # pragma: no cover
            raise APIError("chroma_db_error", "ChromaDB could not store the document embeddings.", 500) from exc

    def query(self, query_text: str, n_results: int = 3) -> dict[str, Any]:
        if n_results <= 0:
            raise ValueError("n_results must be greater than zero")

        embedding = self.generate_embedding(query_text)
        try:
            return self._collection.query(query_embeddings=[embedding], n_results=n_results)
        except Exception as exc:  # pragma: no cover
            raise APIError("chroma_db_error", "ChromaDB could not query the document embeddings.", 500) from exc
