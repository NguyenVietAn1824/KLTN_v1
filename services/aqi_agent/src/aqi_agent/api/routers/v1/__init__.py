from __future__ import annotations

from .aqi_agent import aqi_agent_router
from .auth import auth_router
from .conversations import conversations_router


__all__ = [
    'aqi_agent_router',
    'auth_router',
    'conversations_router',
]
