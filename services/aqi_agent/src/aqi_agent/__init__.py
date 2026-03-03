from __future__ import annotations

from contextlib import asynccontextmanager

import uvicorn
from asgi_correlation_id import CorrelationIdMiddleware
from aqi_agent.api.helpers import LoggingMiddleware
from aqi_agent.api.routers.manager import api_router
from aqi_agent.shared.utils import get_settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from lite_llm import LiteLLMService
from logger import get_logger
from logger import setup_logging
from opensearch import OpenSearchService
from pg import SQLDatabase
from redis import Redis  # type: ignore[import-untyped]

setup_logging(json_logs=False)
logger = get_logger('api')

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.settings = settings

    app.state.litellm_service = LiteLLMService(
        settings=app.state.settings.litellm,
    )

    app.state.sql_database = SQLDatabase(
        username=app.state.settings.postgres.username,
        password=app.state.settings.postgres.password,
        host=app.state.settings.postgres.host,
        db=app.state.settings.postgres.db,
    )

    app.state.opensearch_service = OpenSearchService(
        settings=app.state.settings.opensearch,
    )

    app.state.redis_client = Redis(
        host=app.state.settings.redis.host,
        port=app.state.settings.redis.port,
        db=app.state.settings.redis.db,
        password=app.state.settings.redis.password,
        ssl=app.state.settings.redis.ssl,
    )

    yield


app = FastAPI(
    title='AQI Agent API - Air Quality Data Assistant',
    version='1.0',
    lifespan=lifespan,
)


# CORS middleware MUST be added first!
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# add middleware to generate correlation id
app.add_middleware(LoggingMiddleware, logger=logger)
app.add_middleware(CorrelationIdMiddleware)

app.include_router(
    api_router,
)


def main() -> None:
    if settings.deployment_env == 'dev':
        uvicorn.run(
            'aqi_agent:app',
            host=settings.host,
            port=settings.port,
            reload=True,
        )
    else:
        uvicorn.run(
            'aqi_agent:app',
            host=settings.host,
            port=settings.port,
            workers=4,
        )
