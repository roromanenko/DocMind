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
    
    # Qdrant Configuration
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""
    qdrant_collection_name: str = "docmind_chunks"
    qdrant_vector_size: int = 1536
    
    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_max_tokens: int = 4000
    openai_temperature: float = 0.7
    
    # Embeddings
    embedding_model: str = "text-embedding-ada-002"
    embedding_dimension: int = 1536
    embedding_max_batch_size: int = 100
    embedding_max_text_tokens: int = 8192
    
    # Document Processing
    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    
    # Text Cleaning
    text_cleaning_remove_html: bool = True
    text_cleaning_normalize_whitespace: bool = True
    text_cleaning_normalize_punctuation: bool = True
    text_cleaning_remove_control_chars: bool = True
    text_cleaning_unicode_normalization: bool = True
    text_cleaning_min_sentence_length: int = 10
    text_cleaning_min_words: int = 2
    text_cleaning_unicode_format: str = "NFC"
    
    # File Storage
    upload_dir: str = "./uploads"
    temp_dir: str = "./temp"
    
    # Security
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Logging
    log_level: str = "INFO"
    
    # CORS
    allowed_origins: list[str] = ["*"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


# Global settings instance
settings = Settings()
