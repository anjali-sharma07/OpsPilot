import os

from app.core.config import Settings


def test_settings_reads_environment_variables(monkeypatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "test-groq-key")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./test.db")
    monkeypatch.setenv("CHROMA_DB_PATH", "./custom_chroma")
    monkeypatch.setenv("EMBEDDING_MODEL", "custom-embedding-model")
    monkeypatch.setenv("GROQ_MODEL", "custom-groq-model")
    monkeypatch.setenv("CHUNK_SIZE", "123")
    monkeypatch.setenv("CHUNK_OVERLAP", "45")
    monkeypatch.setenv("UPLOAD_DIRECTORY", "./custom_uploads")

    settings = Settings()

    assert settings.groq_api_key == "test-groq-key"
    assert settings.database_url == "sqlite:///./test.db"
    assert settings.chroma_db_path == "./custom_chroma"
    assert settings.embedding_model == "custom-embedding-model"
    assert settings.groq_model == "custom-groq-model"
    assert settings.chunk_size == 123
    assert settings.chunk_overlap == 45
    assert settings.upload_directory == "./custom_uploads"
