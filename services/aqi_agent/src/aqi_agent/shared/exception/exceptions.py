from __future__ import annotations

from .base import BaseAppException


class ValidationException(BaseAppException):
    def __init__(self, message: str = 'Invalid data', details: dict | None = None):
        super().__init__(message=message, code=400, details=details)


class UnauthorizedException(BaseAppException):
    def __init__(self, message: str = 'Unauthorized', details: dict | None = None):
        super().__init__(message=message, code=401, details=details)


class NotFoundException(BaseAppException):
    def __init__(self, message: str = 'Not found', details: dict | None = None):
        super().__init__(message=message, code=404, details=details)
