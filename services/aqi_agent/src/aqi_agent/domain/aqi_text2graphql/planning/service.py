"""
Planning Service for KLTN AQI Text2GraphQL system.

Decomposes user questions into structured tasks using LiteLLM.
Adapted from sun_assistant Apollo planning service.
"""

from typing import Any, Dict

from aqi_agent.shared.model import TodoList
from base import BaseModel, AsyncBaseService
from lite_llm import CompletionMessage, LiteLLMInput, LiteLLMService, Role
from logger import get_logger

from .prompts import PLANNING_SYSTEM_PROMPT, PLANNING_USER_PROMPT

logger = get_logger(__name__)


class PlanningInput(BaseModel):
    """Input for planning service."""
    
    raw_question: str
    context_schema: Dict[str, str]  # table_name -> description


class PlanningOutput(BaseModel):
    """Output from planning service."""
    
    todo_list: TodoList


class PlanningService(AsyncBaseService):
    """
    Planning service that decomposes user questions into structured tasks.
    
    Uses LiteLLM with structured output (response_format=TodoList) to ensure
    type-safe task generation.
    """
    
    litellm_service: LiteLLMService
    
    def _build_conversation(
        self,
        context: str,
        question: str,
    ) -> list[CompletionMessage]:
        """
        Build structured conversation messages for LLM-based planning.
        
        Args:
            context: Formatted table schemas
            question: User's raw question
            
        Returns:
            List of conversation messages (system + user)
        """
        return [
            CompletionMessage(
                role=Role.SYSTEM,
                content=PLANNING_SYSTEM_PROMPT,
            ),
            CompletionMessage(
                role=Role.USER,
                content=PLANNING_USER_PROMPT.format(
                    question=question,
                    context=context,
                ),
            ),
        ]
    
    def _format_context(self, context_schema: Dict[str, str]) -> str:
        """
        Format context schema into a standardized string representation.
        
        Args:
            context_schema: Dictionary mapping table names to descriptions
            
        Returns:
            Formatted string with each table on a new line
        """
        if not context_schema:
            return ''
        
        return '\n'.join(
            f'- Table {table_name}: {description}'
            for table_name, description in context_schema.items()
        )
    
    async def process(self, inputs: PlanningInput) -> PlanningOutput:
        """
        Generate a structured TodoList from a raw question.
        
        Uses LiteLLM with response_format=TodoList for structured output.
        
        Args:
            inputs: Contains raw_question and context_schema
            
        Returns:
            PlanningOutput with generated TodoList
            
        Raises:
            ValueError: If inputs are invalid or LLM processing fails
        """
        # Validate inputs
        if not inputs.raw_question or not inputs.raw_question.strip():
            logger.warning(
                'Empty raw_question provided',
                extra={'raw_question': inputs.raw_question}
            )
            raise ValueError('raw_question cannot be empty')
        
        if not inputs.context_schema or len(inputs.context_schema) == 0:
            logger.warning(
                'Empty context schema provided',
                extra={'raw_question': inputs.raw_question}
            )
            # Return empty TodoList
            return PlanningOutput(
                todo_list=TodoList(tasks=[], summary="No tables available")
            )
        
        # Format context schema
        context = self._format_context(inputs.context_schema)
        
        # Build conversation
        messages = self._build_conversation(context, inputs.raw_question)
        
        # Call LiteLLM with structured output
        try:
            logger.info(
                'Calling LiteLLM for planning',
                extra={'question': inputs.raw_question}
            )
            
            response = await self.litellm_service.process_async(
                inputs=LiteLLMInput(
                    messages=messages,
                    response_format=TodoList,  # CRITICAL: Structured output
                ),
            )
            
            # Response is already parsed by LiteLLMService
            todo_list = response.response
            if not isinstance(todo_list, TodoList):
                raise ValueError(f'Invalid response type: {type(todo_list)}')
            
            num_first_task_sqs = len(todo_list.first_task.sub_questions)
            num_second_task_sqs = len(todo_list.second_task.sub_questions) if todo_list.second_task else 0
            
            logger.info(
                'Planning completed successfully',
                extra={
                    'question': inputs.raw_question,
                    'num_first_task_sub_questions': num_first_task_sqs,
                    'num_second_task_sub_questions': num_second_task_sqs
                }
            )
            
            return PlanningOutput(todo_list=todo_list)
            
        except Exception as e:
            logger.exception(
                event='LLM processing error in planning',
                extra={
                    'raw_question': inputs.raw_question,
                    'error': str(e)
                },
            )
            raise ValueError(f'Planning failed: {e}') from e
