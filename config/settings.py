"""
Application configuration management using Pydantic Settings.
Handles environment-based configuration with validation.
"""

from typing import Optional
from pydantic import BaseSettings, Field, validator
import os


class TwilioSettings(BaseSettings):
    """Twilio-specific configuration settings."""
    
    account_sid: str = Field(..., env="TWILIO_ACCOUNT_SID")
    auth_token: str = Field(..., env="TWILIO_AUTH_TOKEN")
    conversations_service_sid: str = Field(..., env="TWILIO_CONVERSATIONS_SERVICE_SID")
    webhook_secret: Optional[str] = Field(None, env="WEBHOOK_SECRET")

    class Config:
        env_prefix = "TWILIO_"


class OpenAISettings(BaseSettings):
    """OpenAI-specific configuration settings."""
    
    api_key: str = Field(..., env="OPENAI_API_KEY")
    model: str = Field(default="gpt-4o-mini", env="OPENAI_MODEL")
    max_tokens: Optional[int] = Field(default=1000, env="OPENAI_MAX_TOKENS")
    temperature: float = Field(default=0.7, env="OPENAI_TEMPERATURE")

    class Config:
        env_prefix = "OPENAI_"


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    
    url: str = Field(default="sqlite:///./conversations.db", env="DATABASE_URL")
    echo: bool = Field(default=False, env="DATABASE_ECHO")
    pool_size: int = Field(default=5, env="DATABASE_POOL_SIZE")
    max_overflow: int = Field(default=10, env="DATABASE_MAX_OVERFLOW")

    class Config:
        env_prefix = "DATABASE_"


class RedisSettings(BaseSettings):
    """Redis configuration for session storage."""
    
    url: Optional[str] = Field(default="redis://localhost:6379", env="REDIS_URL")
    decode_responses: bool = Field(default=True)
    max_connections: int = Field(default=20, env="REDIS_MAX_CONNECTIONS")

    class Config:
        env_prefix = "REDIS_"


class SecuritySettings(BaseSettings):
    """Security-related configuration."""
    
    webhook_secret: Optional[str] = Field(None, env="WEBHOOK_SECRET")
    rate_limit_per_minute: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    max_concurrent_conversations: int = Field(default=100, env="MAX_CONCURRENT_CONVERSATIONS")

    class Config:
        env_prefix = "SECURITY_"


class AgentSettings(BaseSettings):
    """AI Agent configuration settings."""
    
    max_conversation_history: int = Field(default=50, env="MAX_CONVERSATION_HISTORY")
    conversation_timeout_minutes: int = Field(default=30, env="CONVERSATION_TIMEOUT_MINUTES")
    typing_indicator_timeout_seconds: int = Field(default=10, env="TYPING_INDICATOR_TIMEOUT_SECONDS")
    config_file_path: str = Field(default="config/agent_config.yml", env="AGENT_CONFIG_PATH")

    class Config:
        env_prefix = "AGENT_"


class ApplicationSettings(BaseSettings):
    """Main application configuration that combines all settings."""
    
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # Sub-configurations
    twilio: TwilioSettings = TwilioSettings()
    openai: OpenAISettings = OpenAISettings()
    database: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    security: SecuritySettings = SecuritySettings()
    agent: AgentSettings = AgentSettings()

    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level is one of the standard logging levels."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


def get_settings() -> ApplicationSettings:
    """
    Get application settings singleton.
    
    Returns:
        ApplicationSettings: Configured application settings
    """
    # TODO: Implement caching if needed for performance
    return ApplicationSettings()


# Global settings instance
settings = get_settings()