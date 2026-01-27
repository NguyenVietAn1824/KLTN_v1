from __future__ import annotations

"""API Routes for AQI Agent Service.

Provides REST endpoints for asking air quality questions.
"""

from typing import Any
from fastapi import APIRouter, Depends

from base import BaseModel

from aqi_agent.application import AQIAgentService, AQIAgentInput, AQIAgentOutput
from aqi_agent.api.dependencies import get_aqi_agent_service


router = APIRouter(prefix='/aqi-agent', tags=['AQI Agent'])


class AskQuestionRequest(BaseModel):
    """Request model for asking a question.

    Attributes:
        question (str): The air quality question to answer
    """

    question: str


class AskQuestionResponse(BaseModel):
    """Response model for question answer.

    Attributes:
        answer (str): Natural language answer
        data (dict): Raw query results
        graphql_queries (list): Executed GraphQL queries
    """

    answer: str
    data: dict[str, Any]
    graphql_queries: list[str]


@router.post('/ask', response_model=AskQuestionResponse)
async def ask_question(
    request: AskQuestionRequest,
    service: AQIAgentService = Depends(get_aqi_agent_service),
) -> AskQuestionResponse:
    """Ask a question about air quality.

    Args:
        request: Question request
        service: AQI agent service instance

    Returns:
        Question response with answer and data

    Example:
        >>> POST /aqi-agent/ask
        >>> {"question": "Không khí ở Hoàn Kiếm hôm nay thế nào?"}
        >>> Response: {
        ...     "answer": "Chất lượng không khí ở Hoàn Kiếm vào 2026-01-15: AQI = 45 (Tốt)",
        ...     "data": {...},
        ...     "graphql_queries": [...]
        ... }
    """
    inputs = AQIAgentInput(question=request.question)
    output = await service.process(inputs)

    return AskQuestionResponse(
        answer=output.answer,
        data=output.data,
        graphql_queries=output.graphql_queries,
    )


@router.get('/health')
async def health_check() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        Health status
    """
    return {'status': 'healthy', 'service': 'aqi-agent'}
