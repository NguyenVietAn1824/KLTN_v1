from __future__ import annotations

from fastapi import APIRouter

from .v1 import aqi_agent_router

api_router = APIRouter(prefix='/v1')

api_router.include_router(aqi_agent_router, tags=['aqi_agent'])
