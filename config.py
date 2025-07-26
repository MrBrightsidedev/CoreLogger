import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration settings."""
    
    # Database
    database_url: str = "sqlite:///./corelogger.db"
    database_echo: bool = False
    
    # API
    api_host: str = "localhost"
    api_port: int = 8000
    api_reload: bool = False
    api_title: str = "CoreLogger API"
    api_description: str = "Eidos OS Logging Module API"
    api_version: str = "0.1.0"
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Storage
    data_dir: Path = Path("./data")
    backup_dir: Optional[Path] = None
    
    # Features
    enable_emotions: bool = True
    enable_importance_scoring: bool = True
    max_content_length: int = 10000
    default_importance: float = 0.5
    
    # AI API Keys
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",  # Allow extra fields from environment
    }


# Global settings instance
settings = Settings()

# Ensure data directory exists
settings.data_dir.mkdir(exist_ok=True)
if settings.backup_dir:
    settings.backup_dir.mkdir(exist_ok=True)
