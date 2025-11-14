"""Application configuration management."""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    app_name: str = "Flowgate Backend"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"
    
    # Database
    database_url: str
    postgres_user: str = "flowgate"
    postgres_password: str = "flowgate"
    postgres_db: str = "flowgate"
    
    # Redis
    redis_url: str = "redis://redis:6379/0"
    
    # API
    api_v1_prefix: str = "/api/v1"
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # Security
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # OpAMP
    opamp_server_port: int = 4320
    opamp_server_host: str = "0.0.0.0"
    
    # AI/LLM (optional)
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()


