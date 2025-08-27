"""
Logging utilities for structured JSON logging with proper configuration.
Provides consistent logging setup across the application with contextual information.
"""

import logging
import logging.config
import sys
from datetime import datetime
from typing import Any, Dict, Optional
import json
from pathlib import Path

from config.settings import settings


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.
    
    Formats log records as JSON with consistent field names and structure.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.
        
        Args:
            record: Log record to format
            
        Returns:
            JSON formatted log string
        """
        # Base log data
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception information if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields from the log record
        if hasattr(record, '__dict__'):
            for key, value in record.__dict__.items():
                # Skip standard log record attributes
                if key not in {
                    'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                    'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                    'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                    'thread', 'threadName', 'processName', 'process', 'getMessage'
                }:
                    try:
                        # Ensure the value is JSON serializable
                        json.dumps(value)
                        log_data[key] = value
                    except (TypeError, ValueError):
                        # If not serializable, convert to string
                        log_data[key] = str(value)
        
        return json.dumps(log_data, ensure_ascii=False)


class ContextFilter(logging.Filter):
    """
    Filter to add contextual information to log records.
    
    Adds application-wide context like request IDs, user IDs, etc.
    """
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Add contextual information to log record.
        
        Args:
            record: Log record to enhance
            
        Returns:
            True to include the record, False to exclude
        """
        # Add application context
        record.app_name = "twilio-openai-conversations"
        record.app_version = "1.0.0"
        record.environment = "development" if settings.debug else "production"
        
        # Add request context if available (will be set by middleware)
        if not hasattr(record, 'request_id'):
            record.request_id = None
        
        if not hasattr(record, 'conversation_sid'):
            record.conversation_sid = None
        
        if not hasattr(record, 'session_id'):
            record.session_id = None
        
        return True


def setup_logging() -> None:
    """
    Setup application logging configuration.
    
    Configures structured JSON logging for production and readable console
    logging for development.
    """
    # Determine log level
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Logging configuration
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": JSONFormatter,
            },
            "console": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            }
        },
        "filters": {
            "context_filter": {
                "()": ContextFilter,
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": sys.stdout,
                "formatter": "json" if not settings.debug else "console",
                "level": log_level,
                "filters": ["context_filter"]
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "logs/application.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "formatter": "json",
                "level": log_level,
                "filters": ["context_filter"]
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "logs/error.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "formatter": "json",
                "level": "ERROR",
                "filters": ["context_filter"]
            }
        },
        "loggers": {
            # Application loggers
            "src": {
                "handlers": ["console", "file", "error_file"],
                "level": log_level,
                "propagate": False
            },
            "config": {
                "handlers": ["console", "file", "error_file"],
                "level": log_level,
                "propagate": False
            },
            # Third-party library loggers
            "uvicorn": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False
            },
            "uvicorn.access": {
                "handlers": ["file"],
                "level": "INFO",
                "propagate": False
            },
            "fastapi": {
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": False
            },
            "twilio": {
                "handlers": ["console", "file"],
                "level": "WARNING",  # Reduce Twilio SDK noise
                "propagate": False
            },
            "openai": {
                "handlers": ["console", "file"],
                "level": "WARNING",  # Reduce OpenAI SDK noise
                "propagate": False
            },
            "sqlalchemy": {
                "handlers": ["file"],
                "level": "WARNING",  # Reduce SQLAlchemy noise
                "propagate": False
            }
        },
        "root": {
            "handlers": ["console", "file", "error_file"],
            "level": log_level
        }
    }
    
    # Apply logging configuration
    logging.config.dictConfig(config)
    
    # Log initialization
    logger = logging.getLogger(__name__)
    logger.info("Logging configuration initialized", extra={
        "log_level": settings.log_level,
        "debug_mode": settings.debug
    })


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


class LoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter that adds consistent contextual information to all log messages.
    
    Useful for adding request-specific or session-specific context to all logs
    within a particular scope.
    """
    
    def __init__(self, logger: logging.Logger, extra: Dict[str, Any]):
        """
        Initialize logger adapter with extra context.
        
        Args:
            logger: Base logger instance
            extra: Dictionary of extra context to add to all log messages
        """
        super().__init__(logger, extra)
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """
        Process log message and add extra context.
        
        Args:
            msg: Log message
            kwargs: Keyword arguments
            
        Returns:
            Tuple of (message, kwargs) with extra context added
        """
        # Merge extra context into kwargs
        if 'extra' in kwargs:
            kwargs['extra'].update(self.extra)
        else:
            kwargs['extra'] = self.extra.copy()
        
        return msg, kwargs


def get_contextual_logger(name: str, **context) -> LoggerAdapter:
    """
    Get a logger adapter with additional context.
    
    Args:
        name: Logger name
        **context: Additional context to include in all log messages
        
    Returns:
        LoggerAdapter with contextual information
    """
    base_logger = get_logger(name)
    return LoggerAdapter(base_logger, context)


def log_function_call(func_name: str, args: Dict[str, Any], logger: logging.Logger) -> None:
    """
    Log function call with arguments (useful for debugging).
    
    Args:
        func_name: Name of the function being called
        args: Dictionary of function arguments
        logger: Logger instance to use
    """
    # Sanitize arguments to avoid logging sensitive information
    sanitized_args = {}
    sensitive_keys = {'password', 'token', 'key', 'secret', 'auth', 'credential'}
    
    for key, value in args.items():
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            sanitized_args[key] = "[REDACTED]"
        elif isinstance(value, str) and len(value) > 100:
            sanitized_args[key] = value[:97] + "..."
        else:
            sanitized_args[key] = value
    
    logger.debug(f"Function call: {func_name}", extra={
        "function_name": func_name,
        "arguments": sanitized_args
    })


def log_performance(func_name: str, duration_ms: float, logger: logging.Logger, 
                   threshold_ms: float = 1000.0) -> None:
    """
    Log function performance metrics.
    
    Args:
        func_name: Name of the function
        duration_ms: Execution duration in milliseconds
        logger: Logger instance to use
        threshold_ms: Threshold for warning about slow operations
    """
    log_level = logging.WARNING if duration_ms > threshold_ms else logging.INFO
    
    logger.log(log_level, f"Performance: {func_name} completed in {duration_ms:.2f}ms", extra={
        "function_name": func_name,
        "duration_ms": duration_ms,
        "performance_warning": duration_ms > threshold_ms
    })