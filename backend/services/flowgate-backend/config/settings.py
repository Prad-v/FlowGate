from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = "Flowgate Control Plane"
    app_version: str = "0.1.0"
    debug: bool = False
    
    # Database
    database_url: str = "postgresql://flowgate:flowgate@localhost:5432/flowgate"
    database_pool_size: int = 10
    database_max_overflow: int = 20
    
    # Redis
    redis_url: Optional[str] = "redis://localhost:6379/0"
    redis_enabled: bool = True
    
    # OpAMP Server
    opamp_server_host: str = "0.0.0.0"
    opamp_server_port: int = 4320
    
    # API
    api_v1_prefix: str = "/api/v1"
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # Security
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # AI/LLM (optional)
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

