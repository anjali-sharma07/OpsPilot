from fastapi import APIRouter

from app.api.utils import APIError, create_error_response
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService
from app.services.embedding_service import EmbeddingService
from app.services.groq_service import GroqService
from app.services.retrieval_service import RetrievalService

router = APIRouter(prefix="/chat", tags=["chat"])

embedding_service = EmbeddingService()
groq_service = GroqService()
retrieval_service = RetrievalService(embedding_service=embedding_service)
chat_service = ChatService(
    embedding_service=embedding_service,
    groq_service=groq_service,
    retrieval_service=retrieval_service,
)


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    try:
        result = chat_service.ask(request.question, request.session_id)
    except APIError as exc:
        raise create_error_response(exc) from exc
    except ValueError as exc:
        raise create_error_response(APIError("invalid_request", str(exc), 400)) from exc

    return ChatResponse(**result)
