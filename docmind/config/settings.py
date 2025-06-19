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
    debug: bool = Field(default=False, env="DEBUG")
    
    # Database
    database_url: str = Field(env="DATABASE_URL")
    database_echo: bool = Field(default=False, env="DATABASE_ECHO")
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    
    # Qdrant Cloud Configuration
    qdrant_url: str = Field(env="QDRANT_URL")
    qdrant_api_key: str = Field(env="QDRANT_API_KEY")
    qdrant_collection_name: str = Field(default="docmind_chunks", env="QDRANT_COLLECTION_NAME")
    qdrant_vector_size: int = Field(default=384, env="QDRANT_VECTOR_SIZE")
    
    # OpenAI
    openai_api_key: str = Field(env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o", env="OPENAI_MODEL")
    openai_max_tokens: int = Field(default=4000, env="OPENAI_MAX_TOKENS")
    openai_temperature: float = Field(default=0.7, env="OPENAI_TEMPERATURE")
    
    # Embeddings
    embedding_model: str = Field(default="all-MiniLM-L6-v2", env="EMBEDDING_MODEL")
    embedding_dimension: int = Field(default=384, env="EMBEDDING_DIMENSION")
    
    # Document Processing
    chunk_size: int = Field(default=1000, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, env="CHUNK_OVERLAP")
    max_file_size: int = Field(default=100 * 1024 * 1024, env="MAX_FILE_SIZE")  # 100MB
    
    # File Storage
    upload_dir: str = Field(default="./uploads", env="UPLOAD_DIR")
    temp_dir: str = Field(default="./temp", env="TEMP_DIR")
    
    # Security
    secret_key: str = Field(env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    
    # CORS
    allowed_origins: list[str] = Field(default=["http://localhost:3000"], env="ALLOWED_ORIGINS")
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings() 