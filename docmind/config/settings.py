"""
Application settings configuration.
"""
import os
from typing import Optional
from pydantic import Field
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

# Set Qdrant Cloud values directly if not in environment
# if not os.getenv("QDRANT_URL"):
#     os.environ["QDRANT_URL"] = "https://d5b99c4d-824a-4438-8fdb-32c398a6ccba.eu-central-1-0.aws.cloud.qdrant.io"
#     print("✅ QDRANT_URL set from fallback")

# if not os.getenv("QDRANT_API_KEY"):
#     os.environ["QDRANT_API_KEY"] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.O52OojDBVrPeKqwIrIEwh_l2accpyhaoD_zgBIZBgOc"
#     print("✅ QDRANT_API_KEY set from fallback")


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    app_name: str = "DocMind"
    app_version: str = "0.1.0"
    debug: bool = False
    
    # Database
    database_url: str = "sqlite:///./docmind.db"
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