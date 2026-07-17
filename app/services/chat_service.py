from typing import Any

from app.services.conversation_service import ConversationService
from app.services.embedding_service import EmbeddingService
from app.services.groq_service import GroqService
from app.services.retrieval_service import RetrievalService


class ChatService:
    def __init__(
        self,
        embedding_service: EmbeddingService,
        groq_service: GroqService,
        retrieval_service: RetrievalService | None = None,
        conversation_service: ConversationService | None = None,
    ) -> None:
        self.groq_service = groq_service
        self.retrieval_service = retrieval_service or RetrievalService(embedding_service)
        self.conversation_service = conversation_service or ConversationService()

    def get_conversation_history(self, session_id: str) -> list[dict[str, str]]:
        return self.conversation_service.get_history(session_id)

    def ask(self, question: str, session_id: str) -> dict[str, Any]:
        if not question or not question.strip():
            raise ValueError("Question must not be empty")

        retrieved_context = self.retrieval_service.retrieve(question, top_k=5)
        conversation_history = self.get_conversation_history(session_id)

        answer = self.groq_service.generate_answer(
            user_question=question,
            retrieved_context=retrieved_context,
            conversation_history=conversation_history,
        )

        self.conversation_service.save_message(session_id, question, answer)

        sources = [
            {
                "document": item.get("filename", ""),
                "page_number": item.get("page_number"),
                "chunk_id": item.get("chunk_id", ""),
                "similarity_score": item.get("similarity_score", 0.0),
            }
            for item in retrieved_context
        ]

        return {
            "answer": answer,
            "sources": sources,
        }
