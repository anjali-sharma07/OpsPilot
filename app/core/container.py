"""
Dependency-injection container for heavy singleton services.

Every expensive resource (SentenceTransformer, ChromaDB client, Groq client)
is wrapped in a ``functools.cached_property`` on a single ``ServiceContainer``
instance. The property is evaluated **only** on first access — never at import
time — keeping startup RAM near zero.

Usage inside FastAPI routes::

    from fastapi import Depends
    from app.core.container import get_embedding_service

    @router.post("/foo")
    def foo(svc: EmbeddingService = Depends(get_embedding_service)):
        ...
"""

from __future__ import annotations

import threading
from functools import cached_property
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.chat_service import ChatService
    from app.services.document_service import DocumentService
    from app.services.embedding_service import EmbeddingService
    from app.services.groq_service import GroqService
    from app.services.retrieval_service import RetrievalService


class ServiceContainer:
    """Thread-safe, lazy singleton container for all heavy services.

    ``cached_property`` is thread-safe in CPython 3.12+ due to per-slot
    locking.  On Render Free (single Uvicorn worker) this is a non-issue, but
    the explicit lock below guards the first-load window for async frameworks
    that may attempt concurrent initialisation.
    """

    _lock: threading.Lock = threading.Lock()

    # ------------------------------------------------------------------
    # Embedding / Vector store (most expensive: ~350 MB on first access)
    # ------------------------------------------------------------------

    @cached_property
    def embedding_service(self) -> "EmbeddingService":
        # Imported here so that SentenceTransformer + torch are NOT loaded
        # when this module is first imported — only when this property is
        # accessed for the very first time.
        from app.services.embedding_service import EmbeddingService

        return EmbeddingService()

    # ------------------------------------------------------------------
    # Groq HTTP client (lightweight, but still deferred for consistency)
    # ------------------------------------------------------------------

    @cached_property
    def groq_service(self) -> "GroqService":
        from app.services.groq_service import GroqService

        return GroqService()

    # ------------------------------------------------------------------
    # Retrieval (depends on embedding_service — shares the same instance)
    # ------------------------------------------------------------------

    @cached_property
    def retrieval_service(self) -> "RetrievalService":
        from app.services.retrieval_service import RetrievalService

        return RetrievalService(embedding_service=self.embedding_service)

    # ------------------------------------------------------------------
    # Chat (orchestrates retrieval + groq + conversation)
    # ------------------------------------------------------------------

    @cached_property
    def chat_service(self) -> "ChatService":
        from app.services.chat_service import ChatService

        return ChatService(
            embedding_service=self.embedding_service,
            groq_service=self.groq_service,
            retrieval_service=self.retrieval_service,
        )

    # ------------------------------------------------------------------
    # Document ingestion (shares embedding_service singleton)
    # ------------------------------------------------------------------

    @cached_property
    def document_service(self) -> "DocumentService":
        from app.services.document_service import DocumentService

        return DocumentService(embedding_service=self.embedding_service)


# Single global container — the one and only instance for the process lifetime.
container = ServiceContainer()


# ---------------------------------------------------------------------------
# FastAPI Depends()-compatible provider functions
# ---------------------------------------------------------------------------

def get_embedding_service() -> "EmbeddingService":
    """FastAPI dependency: returns the lazy-initialised EmbeddingService."""
    return container.embedding_service


def get_groq_service() -> "GroqService":
    """FastAPI dependency: returns the lazy-initialised GroqService."""
    return container.groq_service


def get_chat_service() -> "ChatService":
    """FastAPI dependency: returns the lazy-initialised ChatService."""
    return container.chat_service


def get_document_service() -> "DocumentService":
    """FastAPI dependency: returns the lazy-initialised DocumentService."""
    return container.document_service
