"""Application configuration management"""
from functools import lru_cache
from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # API Configuration
    app_name: str = "Pharo Reviewer Agent API"
    app_version: str = "1.0.0"
    debug: bool = False

    # Google AI Configuration
    google_api_key: str = ""  # Required for Gemini

    # Gemini Model Configuration
    model_id: str = "gemini-3-pro-preview"

    # Pharo MCP Server Configuration
    pharo_server_url: str = "http://localhost:8086"
    pharo_mcp_server_command: str = "uv"
    pharo_mcp_server_args: List[str] = ["run", "pharo-smalltalk-interop-mcp-server"]
    pharo_mcp_server_cwd: str = ""  # Path to pharo-smalltalk-interop-mcp-server
    pharo_mcp_timeout: int = 30

    # Agent Configuration
    max_validation_iterations: int = 3

    # CORS Configuration (parsed from comma-separated strings in .env)
    cors_origins: List[str] = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False
    )

    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins - can be comma-separated string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v

    @field_validator('cors_allow_methods', mode='before')
    @classmethod
    def parse_cors_methods(cls, v):
        """Parse CORS methods - can be comma-separated string or list"""
        if isinstance(v, str):
            return [method.strip() for method in v.split(',')]
        return v

    @field_validator('cors_allow_headers', mode='before')
    @classmethod
    def parse_cors_headers(cls, v):
        """Parse CORS headers - can be comma-separated string or list"""
        if isinstance(v, str):
            return [header.strip() for header in v.split(',')]
        return v


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
