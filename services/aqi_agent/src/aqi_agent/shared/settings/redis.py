from __future__ import annotations

from pydantic import BaseModel


class RedisSettings(BaseModel):
    host: str = 'localhost'
    port: int = 6379
    db: int = 0
    password: str | None = None
    ssl: bool = False
