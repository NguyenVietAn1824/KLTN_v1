from __future__ import annotations

"""Main entry point for AQI Agent Service.

FastAPI application with AQI question answering endpoints.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from aqi_agent.api import router

# Load .env file from project root (KLTN/.env)
# Path: services/aqi_agent/src/aqi_agent/main.py -> ../../../../.env
env_path = Path(__file__).resolve().parent.parent.parent.parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
else:
    # Fallback: try loading from current directory
    load_dotenv()


def create_app() -> FastAPI:
    """Create FastAPI application.

    Returns:
        Configured FastAPI app
    """
    app = FastAPI(
        title='AQI Agent Service',
        description='Air Quality Index question answering service using Text2GraphQL',
        version='1.0.0',
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )

    # Include routers
    app.include_router(router)

    return app


app = create_app()


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(
        'aqi_agent.main:app',
        host='0.0.0.0',
        port=8000,
        reload=True,
    )
