import logging.config
from enum import Enum
from typing import Any, Dict, Optional

from pydantic_settings import BaseSettings


class LogFormatter(str, Enum):
    """
    Possible values for the Log Formatter
    """

    text = "text"
    json = "json"


class Settings(BaseSettings):
    """
    Application Settings
    """

    APPLICATION_NAME: str = "MessagingApi"

    # Logging settings
    LOG_LEVEL: str = "DEBUG"  # Default to DEBUG if not set
    LOG_FORMATTER: LogFormatter = LogFormatter.text  # Default to TEXT if not set

    # Define the logging configuration
    # TODO: add file handler?
    LOGGING_CONFIG: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": "pythonjsonlogger.json.JsonFormatter",  # JSON Formatter
                "fmt": "%(asctime)s %(name)s %(levelname)s %(message)s",  # Define fields for JSON
                "json_indent": 4,
            },
            "text": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Standard text log format
            },
        },
        "handlers": {
            "console": {
                "level": "DEBUG",  # Default log level for console
                "class": "logging.StreamHandler",
                "formatter": LogFormatter.text,  # Default formatter is 'text'
            },
        },
        "loggers": {
            "uvicorn": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            "app": {
                "handlers": ["console"],
                "level": "DEBUG",
                "propagate": False,
            },
        },
    }

    # Twilio
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_WEBHOOKS_VALIDATION_ENABLED: bool = True
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None

    # AI Model
    AI_MODEL: str = "google-gla:gemini-1.5-flash"
    GOOGLE_API_KEY: Optional[str] = None

    # Reminders
    REMINDER_DAYS: int = 90


settings = Settings()  # type: ignore

#
# Logging Configuration
#

# Set log level from environment (or defaults to DEBUG)
settings.LOGGING_CONFIG["handlers"]["console"]["level"] = settings.LOG_LEVEL
settings.LOGGING_CONFIG["loggers"]["uvicorn"]["level"] = settings.LOG_LEVEL
settings.LOGGING_CONFIG["loggers"]["app"]["level"] = settings.LOG_LEVEL

# Set the formatter dynamically based on LOG_FORMATTER setting
if settings.LOG_FORMATTER == LogFormatter.json:
    settings.LOGGING_CONFIG["handlers"]["console"]["formatter"] = "json"
elif settings.LOG_FORMATTER == LogFormatter.text:
    settings.LOGGING_CONFIG["handlers"]["console"]["formatter"] = "text"

# Apply the logging configuration from the settings class
logging.config.dictConfig(settings.LOGGING_CONFIG)
