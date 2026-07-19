"""
Chat API router.

Service instances are retrieved via FastAPI ``Depends()`` rather than being
instantiated at module-import time.  This means ``SentenceTransformer``,
ChromaDB, and the Groq client are **not** loaded until the first POST /chat
request is received.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.utils import APIError, create_error_response
from app.core.container import get_chat_service
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    try:
        result = chat_service.ask(request.question, request.session_id)
    except APIError as exc:
        raise create_error_response(exc) from exc
    except ValueError as exc:
        raise create_error_response(APIError("invalid_request", str(exc), 400)) from exc

    return ChatResponse(**result)
