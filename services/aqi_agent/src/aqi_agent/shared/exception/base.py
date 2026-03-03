from __future__ import annotations


class BaseAppException(Exception):
    def __init__(
        self,
        message: str = 'An error occurred',
        code: int = 500,
        details: dict | None = None,
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict:
        return {
            'error': self.__class__.__name__,
            'message': self.message,
            'code': self.code,
            'details': self.details,
        }
