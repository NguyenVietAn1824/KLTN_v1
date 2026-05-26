from __future__ import annotations

from fastapi import APIRouter

from .v1 import aqi_agent_router
from .v1 import auth_router
from .v1 import conversations_router

api_router = APIRouter(prefix='/v1')

api_router.include_router(aqi_agent_router, tags=['aqi_agent'])
api_router.include_router(auth_router, tags=['auth'])
api_router.include_router(conversations_router, tags=['conversations'])
