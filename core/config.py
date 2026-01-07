"""
Configuration management using Pydantic Settings
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # API Keys
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/contracts",
        env="DATABASE_URL"
    )

    # AWS Configuration
    aws_access_key_id: Optional[str] = Field(
        default=None, env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = Field(
        default=None, env="AWS_SECRET_ACCESS_KEY")
    aws_region: str = Field(default="us-east-1", env="AWS_REGION")
    s3_bucket_name: Optional[str] = Field(default=None, env="S3_BUCKET_NAME")

    # Application Settings
    environment: str = Field(default="development", env="ENVIRONMENT")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    # Agent Configuration
    default_model: str = Field(
        default="gpt-4-turbo-preview", env="DEFAULT_MODEL")
    default_temperature: float = Field(default=0.3, env="DEFAULT_TEMPERATURE")
    max_tokens: int = Field(default=4096, env="MAX_TOKENS")

    # API Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_reload: bool = Field(default=True, env="API_RELOAD")

    # File Upload Limits
    max_file_size_mb: int = Field(default=50, env="MAX_FILE_SIZE_MB")
    allowed_file_types: list = Field(
        default=["application/pdf", "text/plain"],
        env="ALLOWED_FILE_TYPES"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create settings singleton"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
