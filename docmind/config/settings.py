"""
Application settings configuration.
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings

# Load .env file explicitly
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ .env file loaded successfully")
except ImportError:
    print("⚠️ python-dotenv not available, using system environment variables")
except Exception as e:
    print(f"⚠️ Error loading .env file: {e}")



class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    app_name: str = "DocMind"
    app_version: str = "0.1.0"
    debug: bool = False
    
    # Database
    database_url: str = "postgresql://postgres:password@localhost:5432/docmind"
    database_echo: bool = False
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # Qdrant Cloud Configuration
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""
    qdrant_collection_name: str = "docmind_chunks"
    qdrant_vector_size: int = 384
    
    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_max_tokens: int = 4000
    openai_temperature: float = 0.7
    
    # Embeddings
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    
    # Document Processing
    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    
    # File Storage
    upload_dir: str = "./uploads"
    temp_dir: str = "./temp"
    
    # Security
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    # CORS
    allowed_origins: list[str] = ["http://localhost:3000"]
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
