"""
Application configuration management using Pydantic Settings.
Handles environment-based configuration with validation.
"""

from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
import os


class ApplicationSettings(BaseSettings):
    """Main application configuration that loads all settings from environment."""
    
    # Application Configuration
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # Twilio Configuration
    twilio_account_sid: str = Field(..., env="TWILIO_ACCOUNT_SID")
    twilio_auth_token: str = Field(..., env="TWILIO_AUTH_TOKEN")
    twilio_conversations_service_sid: str = Field(..., env="TWILIO_CONVERSATIONS_SERVICE_SID")
    
    # OpenAI Configuration
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", env="OPENAI_MODEL")
    openai_max_tokens: Optional[int] = Field(default=1000, env="OPENAI_MAX_TOKENS")
    openai_temperature: float = Field(default=0.7, env="OPENAI_TEMPERATURE")
    
    # Database Configuration
    database_url: str = Field(default="sqlite:///./conversations.db", env="DATABASE_URL")
    database_echo: bool = Field(default=False, env="DATABASE_ECHO")
    database_pool_size: int = Field(default=5, env="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=10, env="DATABASE_MAX_OVERFLOW")
    
    # Redis Configuration
    redis_url: Optional[str] = Field(default="redis://localhost:6379", env="REDIS_URL")
    redis_decode_responses: bool = Field(default=True)
    redis_max_connections: int = Field(default=20, env="REDIS_MAX_CONNECTIONS")
    
    # Security Configuration
    webhook_secret: Optional[str] = Field(None, env="WEBHOOK_SECRET")
    rate_limit_per_minute: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    max_concurrent_conversations: int = Field(default=100, env="MAX_CONCURRENT_CONVERSATIONS")
    
    # Agent Configuration
    max_conversation_history: int = Field(default=50, env="MAX_CONVERSATION_HISTORY")
    conversation_timeout_minutes: int = Field(default=30, env="CONVERSATION_TIMEOUT_MINUTES")
    typing_indicator_timeout_seconds: int = Field(default=10, env="TYPING_INDICATOR_TIMEOUT_SECONDS")
    agent_config_file_path: str = Field(default="config/agent_config.yml", env="AGENT_CONFIG_PATH")

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level is one of the standard logging levels."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }
    
    # Convenience properties for backward compatibility
    @property
    def twilio(self):
        """Access Twilio settings via dot notation."""
        class TwilioProxy:
            def __init__(self, settings):
                self.account_sid = settings.twilio_account_sid
                self.auth_token = settings.twilio_auth_token
                self.conversations_service_sid = settings.twilio_conversations_service_sid
                self.webhook_secret = settings.webhook_secret
        return TwilioProxy(self)
    
    @property
    def openai(self):
        """Access OpenAI settings via dot notation."""
        class OpenAIProxy:
            def __init__(self, settings):
                self.api_key = settings.openai_api_key
                self.model = settings.openai_model
                self.max_tokens = settings.openai_max_tokens
                self.temperature = settings.openai_temperature
        return OpenAIProxy(self)
    
    @property
    def database(self):
        """Access Database settings via dot notation."""
        class DatabaseProxy:
            def __init__(self, settings):
                self.url = settings.database_url
                self.echo = settings.database_echo
                self.pool_size = settings.database_pool_size
                self.max_overflow = settings.database_max_overflow
        return DatabaseProxy(self)
    
    @property
    def redis(self):
        """Access Redis settings via dot notation."""
        class RedisProxy:
            def __init__(self, settings):
                self.url = settings.redis_url
                self.decode_responses = settings.redis_decode_responses
                self.max_connections = settings.redis_max_connections
        return RedisProxy(self)
    
    @property
    def security(self):
        """Access Security settings via dot notation."""
        class SecurityProxy:
            def __init__(self, settings):
                self.webhook_secret = settings.webhook_secret
                self.rate_limit_per_minute = settings.rate_limit_per_minute
                self.max_concurrent_conversations = settings.max_concurrent_conversations
        return SecurityProxy(self)
    
    @property
    def agent(self):
        """Access Agent settings via dot notation."""
        class AgentProxy:
            def __init__(self, settings):
                self.max_conversation_history = settings.max_conversation_history
                self.conversation_timeout_minutes = settings.conversation_timeout_minutes
                self.typing_indicator_timeout_seconds = settings.typing_indicator_timeout_seconds
                self.config_file_path = settings.agent_config_file_path
        return AgentProxy(self)


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