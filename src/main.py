"""FastAPI Application Entry Point

Main application entry point for the RAG insurance chatbot system.
Initializes configuration, logging, and imports the complete FastAPI application.
"""

import logging
import uvicorn

from .config import ConfigFactory, set_config, ConfigurationError
from .logging_config import setup_logging
from .api import app

# Initialize configuration and logging
try:
    config = ConfigFactory.load_from_env()
    set_config(config)
    setup_logging(config.log_level, config.environment)
    logger = logging.getLogger(__name__)
    logger.info("RAG Insurance Chatbot starting up...")
except ConfigurationError as e:
    print(f"Configuration error: {e}")
    raise

# The FastAPI app is imported from .api module


if __name__ == "__main__":
    from .config import get_config
    config = get_config()
    uvicorn.run(
        "src.main:app",
        host=config.api.host,
        port=config.api.port,
        log_level=config.log_level.lower(),
        reload=config.api.debug
    )