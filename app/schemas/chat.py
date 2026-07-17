from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    session_id: str = Field(..., min_length=1, max_length=128)

    @field_validator("question", "session_id")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Value must not be empty")
        return cleaned


class SourceCitation(BaseModel):
    document: str
    page_number: int | None
    chunk_id: str
    similarity_score: float


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceCitation]
