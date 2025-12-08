"""Configuration management for the RAG chatbot backend."""
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
    api_version: str = "0.5.0"
    debug: bool = False
    
    # Gemini API Configuration
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-2.5-flash"
    gemini_temperature: float = 0.7
    gemini_embedding_model: str = "models/text-embedding-004"
    
    # Firestore Configuration
    gcp_project_id: Optional[str] = None
    gcp_location: str = "global"
    firestore_collection: str = "documents"
    
    # Text Processing Configuration
    chunk_size: int = 1000
    chunk_overlap: int = 200
    
    # RAG Configuration
    rag_enabled: bool = True
    rag_top_k: int = 5  # Number of document chunks to retrieve
    rag_similarity_threshold: float = 0.0  # Minimum similarity score (0.0 = no threshold)
    
    # System Prompt
    system_prompt: str = (
        "You are a helpful AI assistant. Provide clear, concise, and accurate answers. "
        "If you don't know something, say so honestly."
    )
    
    # IP Whitelist Configuration for Ingestion
    ingestion_ip_whitelist: str = ""  # Comma-separated list of IPs or CIDR ranges
    ingestion_enabled: bool = True
    
    def get_ip_whitelist(self) -> list[str]:
        """Parse IP whitelist from comma-separated string."""
        if not self.ingestion_ip_whitelist:
            return []
        return [ip.strip() for ip in self.ingestion_ip_whitelist.split(",") if ip.strip()]


# Global settings instance
settings = Settings()

