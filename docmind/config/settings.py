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
    qdrant_vector_size: int = 1536
    
    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_max_tokens: int = 4000
    openai_temperature: float = 0.7
    
    # Embeddings
    embedding_model: str = "text-embedding-ada-002"
    embedding_dimension: int = 1536
    
    # Embedding batching and limits
    embedding_max_tokens_per_batch: int = 8000  # Max tokens per batch for OpenAI embedding
    embedding_max_batch_size: int = 100         # Max texts per batch
    embedding_max_text_tokens: int = 8192       # Max tokens per single text (OpenAI limit)
    embedding_batch_base_delay: float = 0.1     # Base delay (seconds) between embedding batches
    embedding_batch_jitter_min: float = 0.8     # Min jitter multiplier for delay
    embedding_batch_jitter_max: float = 1.2     # Max jitter multiplier for delay
    
    # Document Processing
    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    
    # Text Cleaning Settings
    text_cleaning_remove_html: bool = True
    text_cleaning_normalize_whitespace: bool = True
    text_cleaning_normalize_punctuation: bool = True
    text_cleaning_remove_control_chars: bool = True
    text_cleaning_unicode_normalization: bool = True
    text_cleaning_min_sentence_length: int = 10
    text_cleaning_min_words: int = 2
    text_cleaning_unicode_format: str = "NFC"  # NFC, NFD, NFKC, NFKD
    
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
    allowed_origins: list[str] = ["*"]  # Allow all origins for development
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
