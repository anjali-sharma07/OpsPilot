from typing import Any

from groq import Groq

from app.api.utils import APIError
from app.core.config import settings


class GroqService:
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key or settings.groq_api_key
        self.model = model or settings.groq_model
        self.client = Groq(api_key=self.api_key) if self.api_key else None

    def _get_client(self) -> Groq:
        if self.client is None:
            raise APIError("missing_api_key", "GROQ_API_KEY is not configured.", 500)
        return self.client

    def build_system_prompt(self) -> str:
        return (
            "You are a concise assistant for a document Q&A system. "
            "Answer ONLY using the provided context. "
            "Never use outside knowledge. "
            "If the answer is not available, reply exactly: \"I couldn't find this information in the uploaded documents.\" "
            "Never hallucinate. Keep answers concise and professional."
        )

    def build_messages(
        self,
        user_question: str,
        retrieved_context: list[dict[str, Any]],
        conversation_history: list[dict[str, str]] | None = None,
    ) -> list[dict[str, str]]:
        history_text = ""
        if conversation_history:
            history_text = "\n".join(
                f"User: {entry.get('user', '')}\nAssistant: {entry.get('assistant', '')}"
                for entry in conversation_history
            )

        context_text = "\n\n".join(
            f"Context {index + 1}: {item.get('chunk', '')}"
            for index, item in enumerate(retrieved_context)
        )

        return [
            {"role": "system", "content": self.build_system_prompt()},
            {
                "role": "user",
                "content": (
                    f"Question: {user_question}\n\n"
                    f"Conversation History:\n{history_text}\n\n"
                    f"Retrieved Context:\n{context_text}"
                ),
            },
        ]

    def generate_answer(
        self,
        user_question: str,
        retrieved_context: list[dict[str, Any]],
        conversation_history: list[dict[str, str]] | None = None,
    ) -> str:
        messages = self.build_messages(user_question, retrieved_context, conversation_history)
        client = self._get_client()
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.1,
                max_tokens=300,
            )
        except Exception as exc:  # pragma: no cover - defensive external API handling
            raise APIError("groq_api_failure", "The Groq service failed to generate a response.", 502) from exc
        return response.choices[0].message.content or ""
