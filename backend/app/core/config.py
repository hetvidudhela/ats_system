from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "ATS Backend"
    API_VERSION: str = "v1"
    DEBUG: bool = True

    # Server
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # File Upload
    MAX_FILE_SIZE_MB: int = 5
    UPLOAD_DIR: str = "uploads"

    # AI Assistant (Gemini) Settings
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-3.8-flash"

    # Tell Pydantic where to load environment variables from
    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )



settings = Settings()
