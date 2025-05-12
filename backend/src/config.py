from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    REDIS_URL: str
    VECTOR_DB_URL: str
    LLAMA_URL: str
    LOG_LEVEL: str
    DOCUMENTS_PATH: str
    VECTOR_DB_API_KEY: Optional[str] = None
    VECTOR_DB_ENV: str = "local"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()