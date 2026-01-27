"""Dependency injection for AQI Agent API.

Provides singleton instances of services for FastAPI dependency injection.
"""

import os
from functools import lru_cache

from aqi_agent.application import AQIAgentService
from aqi_agent.domain.aqi_text2graphql.planning import PlanningService
from aqi_agent.domain.aqi_text2graphql.sub_agent import SubAgentService
from aqi_agent.domain.nlg import NLGService
from aqi_agent.domain.aqi_text2graphql.sub_agent.processor.condition_selection import (
    ConditionSelectionService,
)
from aqi_agent.domain.aqi_text2graphql.sub_agent.processor.execution import (
    ExecutionService,
)
from aqi_agent.domain.aqi_text2graphql.sub_agent.processor.field_selection import (
    FieldSelectionService,
)
from aqi_agent.domain.aqi_text2graphql.sub_agent.processor.query_builder import (
    QueryBuilderService,
)
from aqi_agent.infra.hasura import HasuraService, HasuraSettings
from lite_llm import LiteLLMService, LiteLLMSetting


@lru_cache
def get_litellm_service() -> LiteLLMService:
    """Get LiteLLM service singleton.
    
    Returns:
        LiteLLMService instance
    """
    settings = LiteLLMSetting(
        url=os.getenv('LITELLM_URL', 'https://api.openai.com/v1'),
        token=os.getenv('OPENAI_API_KEY', ''),
        model=os.getenv('LLM_MODEL', 'gpt-4o-mini'),
        frequency_penalty=float(os.getenv('LLM_FREQUENCY_PENALTY', '0.0')),
        n=int(os.getenv('LLM_N', '1')),
        temperature=float(os.getenv('LLM_TEMPERATURE', '0.0')),
        top_p=float(os.getenv('LLM_TOP_P', '1.0')),
        max_completion_tokens=int(os.getenv('LLM_MAX_TOKENS', '4096')),
        dimension=int(os.getenv('LLM_DIMENSION', '1536')),
    )
    return LiteLLMService(litellm_setting=settings)


@lru_cache
def get_hasura_service() -> HasuraService:
    """Get Hasura service singleton.

    Returns:
        HasuraService instance
    """
    settings = HasuraSettings(
        endpoint=os.getenv('HASURA_URL', 'http://localhost:8080/v1/graphql'),
        admin_secret=os.getenv('HASURA_ADMIN_SECRET', 'myadminsecretkey'),
    )
    return HasuraService(settings=settings)


@lru_cache
def get_field_selection_service() -> FieldSelectionService:
    """Get field selection service singleton.

    Returns:
        FieldSelectionService instance
    """
    litellm_service = get_litellm_service()
    return FieldSelectionService(litellm_service=litellm_service)


@lru_cache
def get_condition_selection_service() -> ConditionSelectionService:
    """Get condition selection service singleton.

    Returns:
        ConditionSelectionService instance
    """
    litellm_service = get_litellm_service()
    return ConditionSelectionService(litellm_service=litellm_service)


@lru_cache
def get_query_builder_service() -> QueryBuilderService:
    """Get query builder service singleton.

    Returns:
        QueryBuilderService instance
    """
    return QueryBuilderService()


@lru_cache
def get_execution_service() -> ExecutionService:
    """Get execution service singleton.

    Returns:
        ExecutionService instance
    """
    hasura_service = get_hasura_service()
    return ExecutionService(hasura_service=hasura_service)


@lru_cache
def get_sub_agent_service() -> SubAgentService:
    """Get sub-agent service singleton.

    Returns:
        SubAgentService instance
    """
    field_selection_service = get_field_selection_service()
    condition_selection_service = get_condition_selection_service()
    query_builder_service = get_query_builder_service()
    execution_service = get_execution_service()

    return SubAgentService(
        field_selection_service=field_selection_service,
        condition_selection_service=condition_selection_service,
        query_builder_service=query_builder_service,
        execution_service=execution_service,
    )


@lru_cache
def get_planning_service() -> PlanningService:
    """Get planning service singleton.

    Returns:
        PlanningService instance
    """
    litellm_service = get_litellm_service()
    return PlanningService(litellm_service=litellm_service)


@lru_cache
def get_nlg_service() -> NLGService:
    """Get NLG service singleton.
    
    Returns:
        NLGService instance
    """
    litellm_service = get_litellm_service()
    return NLGService(litellm_service=litellm_service)


@lru_cache
def get_aqi_agent_service() -> AQIAgentService:
    """Get AQI Agent service singleton.
    
    Returns:
        AQIAgentService instance
    """
    planning_service = get_planning_service()
    sub_agent_service = get_sub_agent_service()
    nlg_service = get_nlg_service()
    
    return AQIAgentService(
        planning_service=planning_service,
        sub_agent_service=sub_agent_service,
        nlg_service=nlg_service,
    )
