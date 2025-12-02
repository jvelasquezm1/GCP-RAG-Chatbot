"""Configuration management for the RAG chatbot backend."""
import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with validation."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )
    
    # API Configuration
    api_title: str = "GCP RAG Chatbot API"
    api_version: str = "0.3.0"
    debug: bool = False
    
    # Gemini API Configuration
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-2.5-flash"
    gemini_temperature: float = 0.7
    
    # System Prompt
    system_prompt: str = (
        "You are a helpful AI assistant. Provide clear, concise, and accurate answers. "
        "If you don't know something, say so honestly."
    )
    
    # CORS Configuration
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]
    
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v


# Global settings instance
settings = Settings()

