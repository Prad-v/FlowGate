"""Application configuration management"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings"""

    # Application
    app_name: str = "Flowgate Backend"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"

    # Database
    database_url: str = "postgresql://flowgate:flowgate@localhost:5432/flowgate"

    # Redis (optional)
    redis_url: str | None = "redis://localhost:6379/0"

    # Security
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # OpAMP Server
    opamp_server_host: str = "0.0.0.0"
    opamp_server_port: int = 4321

    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Multi-tenancy
    default_org_id: str = "default-org"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

