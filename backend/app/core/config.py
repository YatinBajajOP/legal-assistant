import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "Legal Assistant Backend"
    API_V1_STR: str = "/api/v1"

    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS - Angular dev server origins by default.
    CORS_ORIGINS: list[str] = ["http://localhost:4200", "http://127.0.0.1:4200"]

    # OpenAI
    OPENAI_API_KEY: str
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSIONS: int = 1536
    LLM_MODEL: str = "gpt-4o-mini"

    # Mock/static user, until real auth is implemented.
    MOCK_USER_EMAIL: str = "demo@legal-assistant.local"
    MOCK_USER_FULL_NAME: str = "Demo User"

    # Storage
    UPLOAD_DIR: str = "storage/uploads"
    GENERATED_DIR: str = "storage/generated"

    # Resolution plan template resources (bundled with the app).
    RESOLUTION_PLAN_TEMPLATE_JSON_PATH: str = "app/resources/resolution_plan/resolution_plan_template.json"
    RESOLUTION_PLAN_TEMPLATE_DOCX_PATH: str = "app/resources/resolution_plan/ResolutionPlanTemplate.docx"

    # Chunking
    CHUNK_TARGET_TOKENS: int = 800
    CHUNK_OVERLAP_TOKENS: int = 150
    CHUNK_MAX_TOKENS: int = 1200

    # Embeddings
    EMBEDDING_BATCH_SIZE: int = 64
    MAX_CONCURRENT_EMBEDDING_BATCHES: int = 4

    # RAG / LLM orchestration
    RETRIEVAL_TOP_K: int = 8
    MAX_CONCURRENT_LLM_CALLS: int = 4
    QUESTION_GROUP_SIZE: int = 6
    LLM_MAX_RETRIES: int = 3

    @property
    def upload_dir_path(self) -> str:
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)
        return self.UPLOAD_DIR

    @property
    def generated_dir_path(self) -> str:
        os.makedirs(self.GENERATED_DIR, exist_ok=True)
        return self.GENERATED_DIR


settings = Settings()
