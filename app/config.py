"""
Application configuration settings
Loads environment variables and provides app configuration
"""
from typing import List, Union
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    """Application settings from environment variables"""

    # Database
    DATABASE_URL: str

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 43200  # 30 days

    # OpenAI
    OPENAI_API_KEY: str

    # API
    API_V1_PREFIX: str = "/api"
    PROJECT_NAME: str = "Wishlist API"
    DEBUG: bool = False

    # CORS
    BACKEND_CORS_ORIGINS: Union[str, List[str]] = "http://localhost:5173"

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        """Parse CORS origins from string to list"""
        if isinstance(v, str):
            # Strip quotes if present
            v = v.strip('"').strip("'")
            # Split by comma and return list
            return [i.strip() for i in v.split(",") if i.strip()]
        if isinstance(v, list):
            return v
        # Default fallback
        return ["http://localhost:5173"]

    class Config:
        env_file = ".env"
        case_sensitive = True


# Create global settings instance
settings = Settings()
