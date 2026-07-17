from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "OpsPilot"
    app_version: str = "0.1.0"
    groq_api_key: str | None = Field(default=None, alias="GROQ_API_KEY")
    database_url: str = Field(default="sqlite:///./opspilot.db", alias="DATABASE_URL")
    chroma_db_path: str = Field(default="./chroma_db", alias="CHROMA_DB_PATH")
    embedding_model: str = Field(default="all-MiniLM-L6-v2", alias="EMBEDDING_MODEL")
    groq_model: str = Field(default="llama-3.3-70b-versatile", alias="GROQ_MODEL")
    chunk_size: int = Field(default=800, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=100, alias="CHUNK_OVERLAP")
    upload_directory: str = Field(default="./uploads", alias="UPLOAD_DIRECTORY")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
