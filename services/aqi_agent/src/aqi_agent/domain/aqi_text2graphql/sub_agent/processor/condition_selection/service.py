"""
Condition Selection Service for KLTN AQI Text2GraphQL system.

Generates QueryConstraints (WHERE, ORDER BY, LIMIT) using LiteLLM.
Adapted from sun_assistant Apollo condition_selection service.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from aqi_agent.shared.model import QueryConstraints
from base import BaseModel, AsyncBaseService
from lite_llm import CompletionMessage, LiteLLMInput, LiteLLMService, Role
from logger import get_logger

from .prompts import CONDITION_SELECTION_SYSTEM_PROMPT, CONDITION_SELECTION_USER_PROMPT

logger = get_logger(__name__)


class ConditionSelectionInput(BaseModel):
    """Input for condition selection service."""
    
    fields: List[Dict[str, Any]]  # Selected fields from field_selection
    question: str
    description: str


class ConditionSelectionOutput(BaseModel):
    """Output from condition selection service."""
    
    conditions: Optional[QueryConstraints]


class ConditionSelectionService(AsyncBaseService):
    """
    Condition selection service that generates query constraints.
    
    Uses LiteLLM with structured output (response_format=QueryConstraints) to
    generate WHERE clauses, ORDER BY, and LIMIT.
    """
    
    litellm_service: LiteLLMService
    
    def _build_conversation(
        self,
        context: str,
        question: str,
        description: str,
        today: str,
    ) -> List[CompletionMessage]:
        """
        Build structured conversation messages for condition selection.
        
        Args:
            context: Selected fields as string
            question: User's question
            description: Task description
            today: Today's date string
            
        Returns:
            List of conversation messages
        """
        return [
            CompletionMessage(
                role=Role.SYSTEM,
                content=CONDITION_SELECTION_SYSTEM_PROMPT.format(today=today),
            ),
            CompletionMessage(
                role=Role.USER,
                content=CONDITION_SELECTION_USER_PROMPT.format(
                    question=question,
                    description=description,
                    context=context,
                    today=today,
                ),
            ),
        ]
    
    async def process(self, inputs: ConditionSelectionInput) -> ConditionSelectionOutput:
        """
        Generate query constraints using LLM.
        
        Uses LiteLLM with response_format=QueryConstraints for structured output.
        
        Args:
            inputs: Contains fields, question, description
            
        Returns:
            ConditionSelectionOutput with generated QueryConstraints
        """
        # Check if fields are provided
        if not inputs.fields:
            logger.warning(
                'Empty fields provided for condition selection',
                extra={'question': inputs.question}
            )
            return ConditionSelectionOutput(conditions=None)
        
        # Get today's date for context
        today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Convert fields to string and truncate if needed
        context_str = str(inputs.fields)[:4000]  # Limit context length
        
        # Build conversation
        try:
            messages = self._build_conversation(
                context_str,
                inputs.question,
                inputs.description,
                today,
            )
        except Exception as e:
            logger.exception(
                event='Error building conversation',
                extra={
                    'question': inputs.question,
                    'error': str(e)
                }
            )
            return ConditionSelectionOutput(conditions=None)
        
        # Call LiteLLM with structured output
        try:
            logger.info(
                'Calling LiteLLM for condition selection',
                extra={'question': inputs.question}
            )
            
            response = await self.litellm_service.process_async(
                inputs=LiteLLMInput(
                    messages=messages,
                    response_format=QueryConstraints,  # CRITICAL: Structured output
                ),
            )
            
            # Parse response into QueryConstraints
            if isinstance(response.response, QueryConstraints):
                conditions = response.response
            else:
                conditions = QueryConstraints(**response.response)
            
            logger.info(
                'Condition selection completed',
                extra={
                    'question': inputs.question,
                    'has_where': conditions.where is not None,
                    'has_order_by': conditions.order_by is not None,
                    'limit': conditions.limit,
                    'offset': conditions.offset,
                }
            )
            
            return ConditionSelectionOutput(conditions=conditions)
            
        except Exception as e:
            logger.exception(
                event='LLM processing error in condition selection',
                extra={
                    'question': inputs.question,
                    'fields': inputs.fields,
                    'error': str(e)
                },
            )
            return ConditionSelectionOutput(conditions=None)
