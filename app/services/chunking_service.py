from app.core.config import settings


class ChunkingService:
    @staticmethod
    def chunk_text(text: str, chunk_size: int | None = None, overlap: int | None = None) -> list[str]:
        resolved_chunk_size = settings.chunk_size if chunk_size is None else chunk_size
        resolved_overlap = settings.chunk_overlap if overlap is None else overlap

        if resolved_chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero")
        if resolved_overlap < 0:
            raise ValueError("overlap cannot be negative")
        if resolved_overlap >= resolved_chunk_size:
            raise ValueError("overlap must be smaller than chunk_size")

        if not text:
            return []

        chunks: list[str] = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = min(start + resolved_chunk_size, text_length)
            chunk = text[start:end]
            chunks.append(chunk)
            if end == text_length:
                break
            start += resolved_chunk_size - resolved_overlap

        return chunks
