"""Logging Configuration

Provides structured logging setup with appropriate levels for different environments.
Following the patterns from coding-standards.md for comprehensive logging.
"""

import logging
import logging.config
import sys
from pathlib import Path
from typing import Dict, Any
import json
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record):
        """Format log record as JSON."""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ["name", "msg", "args", "levelname", "levelno", "pathname", 
                          "filename", "module", "lineno", "funcName", "created", "msecs", 
                          "relativeCreated", "thread", "threadName", "processName", 
                          "process", "getMessage", "exc_info", "exc_text", "stack_info"]:
                log_entry[key] = value
        
        return json.dumps(log_entry, ensure_ascii=False)


def get_logging_config(log_level: str = "INFO", environment: str = "development") -> Dict[str, Any]:
    """Get logging configuration for different environments.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        environment: Environment name (development, production, testing).
        
    Returns:
        Logging configuration dictionary.
    """
    
    # Ensure logs directory exists
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "simple": {
                "format": "%(levelname)s - %(name)s - %(message)s"
            },
            "json": {
                "()": JSONFormatter
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "simple" if environment == "development" else "json",
                "stream": sys.stdout
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "detailed",
                "filename": f"logs/rag_chatbot_{environment}.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8"
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "detailed",
                "filename": f"logs/rag_chatbot_errors_{environment}.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8"
            }
        },
        "loggers": {
            # Root logger
            "": {
                "level": log_level,
                "handlers": ["console", "file", "error_file"]
            },
            # RAG system specific loggers
            "src": {
                "level": log_level,
                "handlers": ["console", "file", "error_file"],
                "propagate": False
            },
            "src.retrieval": {
                "level": log_level,
                "handlers": ["console", "file", "error_file"],
                "propagate": False
            },
            "src.generation": {
                "level": log_level,
                "handlers": ["console", "file", "error_file"],
                "propagate": False
            },
            "src.processing": {
                "level": log_level,
                "handlers": ["console", "file", "error_file"],
                "propagate": False
            },
            "src.api": {
                "level": log_level,
                "handlers": ["console", "file", "error_file"],
                "propagate": False
            },
            # External libraries - reduce noise
            "openai": {
                "level": "WARNING",
                "handlers": ["file"],
                "propagate": False
            },
            "httpx": {
                "level": "WARNING",
                "handlers": ["file"],
                "propagate": False
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False
            },
            "fastapi": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False
            }
        }
    }
    
    # Development environment adjustments
    if environment == "development":
        config["loggers"][""]["level"] = "DEBUG"
        config["loggers"]["src"]["level"] = "DEBUG"
        config["handlers"]["console"]["formatter"] = "detailed"
    
    # Production environment adjustments
    elif environment == "production":
        config["handlers"]["console"]["formatter"] = "json"
        # Add additional handlers for production monitoring
        config["handlers"]["syslog"] = {
            "class": "logging.handlers.SysLogHandler",
            "level": "INFO",
            "formatter": "json",
            "address": "/dev/log"
        }
        
        # Add syslog to all loggers
        for logger_config in config["loggers"].values():
            if "handlers" in logger_config:
                logger_config["handlers"].append("syslog")
    
    return config


def setup_logging(log_level: str = "INFO", environment: str = "development") -> None:
    """Setup logging configuration.
    
    Args:
        log_level: Logging level to use.
        environment: Environment name for configuration selection.
    """
    config = get_logging_config(log_level, environment)
    logging.config.dictConfig(config)
    
    # Log initial setup message
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured for {environment} environment with level {log_level}")


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name.
    
    Args:
        name: Logger name, typically __name__ from calling module.
        
    Returns:
        Configured logger instance.
    """
    return logging.getLogger(name)