"""
Simple structured logger for KLTN project.

Provides basic logging with structured context support.
"""

import logging
import sys
from typing import Any, Dict, Optional


class StructuredLogger:
    """
    Structured logger that supports extra context.
    
    Wraps Python's standard logging with structured logging capabilities.
    """
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        
        # Set default level if not configured
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def _format_message(self, msg: str, extra: Optional[Dict[str, Any]] = None) -> str:
        """Format message with extra context."""
        if extra:
            extra_str = ' | '.join(f'{k}={v}' for k, v in extra.items())
            return f'{msg} | {extra_str}'
        return msg
    
    def debug(self, msg: str, extra: Optional[Dict[str, Any]] = None):
        """Log debug message."""
        self.logger.debug(self._format_message(msg, extra))
    
    def info(self, msg: str, extra: Optional[Dict[str, Any]] = None):
        """Log info message."""
        self.logger.info(self._format_message(msg, extra))
    
    def warning(self, msg: str, extra: Optional[Dict[str, Any]] = None):
        """Log warning message."""
        self.logger.warning(self._format_message(msg, extra))
    
    def error(self, msg: str, extra: Optional[Dict[str, Any]] = None):
        """Log error message."""
        self.logger.error(self._format_message(msg, extra))
    
    def exception(
        self, 
        msg: Optional[str] = None,
        event: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None
    ):
        """Log exception with traceback."""
        message = msg or event or 'Exception occurred'
        self.logger.exception(self._format_message(message, extra))


def get_logger(name: str) -> StructuredLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        StructuredLogger instance
    """
    return StructuredLogger(name)
