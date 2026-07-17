from datetime import datetime
from typing import Any

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.utils import APIError
from app.database.database import SessionLocal
from app.models.conversation_message import ConversationMessage


class ConversationService:
    def __init__(self, session_factory: type[Session] | None = None, max_history_turns: int = 6) -> None:
        self.session_factory = session_factory or SessionLocal
        self.max_history_turns = max_history_turns

    def save_message(self, session_id: str, question: str, answer: str) -> None:
        try:
            with self.session_factory() as db:
                message = ConversationMessage(
                    session_id=session_id,
                    question=question,
                    answer=answer,
                    timestamp=datetime.utcnow(),
                )
                db.add(message)
                db.commit()
        except SQLAlchemyError as exc:
            raise APIError("database_failure", "The conversation history could not be saved.", 500) from exc

    def get_history(self, session_id: str) -> list[dict[str, Any]]:
        try:
            with self.session_factory() as db:
                messages = (
                    db.query(ConversationMessage)
                    .filter(ConversationMessage.session_id == session_id)
                    .order_by(ConversationMessage.timestamp.asc())
                    .all()
                )
        except SQLAlchemyError as exc:
            raise APIError("database_failure", "The conversation history could not be loaded.", 500) from exc

        history = [
            {
                "user": message.question,
                "assistant": message.answer,
            }
            for message in messages
        ]
        if self.max_history_turns > 0 and len(history) > self.max_history_turns:
            return history[-self.max_history_turns:]
        return history
