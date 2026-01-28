"""
Application Configuration
Reads from environment variables and .env file
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings."""
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 7777
    DEBUG: bool = True
    
    # API Keys
    GOOGLE_API_KEY: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
