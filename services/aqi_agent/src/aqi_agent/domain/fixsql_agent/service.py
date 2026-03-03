from __future__ import annotations

from base import BaseModel
from base import BaseService
from aqi_agent.domain.planner.models import SubTaskModel
from aqi_agent.shared.models.state import ChatwithDBState
from aqi_agent.shared.settings import FixSQLAgentSettings
from fastapi.encoders import jsonable_encoder
from litellm import CompletionMessage
from litellm import LiteLLMInput
from litellm import LiteLLMService
from litellm import MessageRole
from logger import get_logger
from pydantic import Field

from .models import FixSQLModel
from .prompts import FIXSQL_SYSTEM_PROMPT
from .prompts import FIXSQL_USER_PROMPT

logger = get_logger(__name__)


class FixSQLInput(BaseModel):
    """Input model for the FixSQL Service."""

    rephrased_question: str = Field(
        default='',
        description='A rephrased version of the user question to clarify intent.',
    )

    sql_query: str = Field(
        ...,
        description='The SQL query that failed execution and needs to be analyzed.',
    )
    execution_error: str = Field(
        ...,
        description='Error message from the failed SQL execution to analyze.',
    )
    subtasks: list[SubTaskModel] = Field(
        default_factory=list,
        description='Subtasks generated from the initial planning phase.',
    )
    planning_summary: str = Field(
        default='',
        description='Summary of the initial planning analysis.',
    )
    db_schema: str = Field(
        default='',
        description='Database schema information for context.',
    )


class FixSQLOutput(BaseModel):
    """Output model for the FixSQL Service."""

    error_explanation: str = Field(
        default='',
        description='A clear explanation of why the SQL execution error occurred.',
    )
    fixed_sql: str = Field(
        default='',
        description='A corrected SQL query that addresses the identified issues.',
    )
    is_fixed: bool = Field(
        default=False,
        description='Indicates whether the SQL query was successfully fixed.',
    )


class FixSQLService(BaseService):
    """
    FixSQL Service for Text-to-SQL systems.

    This service analyzes failed SQL queries and provides corrections by:
    1. Identifying the root cause of SQL execution errors.
    2. Generating corrected SQL queries based on the original planning context.

    The service uses the planning summary and subtasks to understand the original
    intent and produces syntactically and semantically correct SQL queries.

    Attributes:
        litellm_service: The LLM service for processing natural language requests.
        settings: Configuration settings for the FixSQL service.
    """

    litellm_service: LiteLLMService
    settings: FixSQLAgentSettings

    @staticmethod
    def _format_subtasks(subtasks: list[SubTaskModel]) -> str:
        """
        Format subtasks into a string representation for the prompt.

        Args:
            subtasks: List of subtask models to format.

        Returns:
            A formatted string representation of subtasks.
        """
        if not subtasks:
            return 'No subtasks available.'

        formatted_tasks = []
        for task in subtasks:
            task_str = (
                f'- Task ID: {task.task_id}\n'
                f'  Description: {task.description}\n'
                f'  Depends on: {", ".join(task.depends_on) if task.depends_on else "None"}\n'
                f'  SQL Hint: {task.sql_hint or "None"}'
            )
            formatted_tasks.append(task_str)

        return '\n'.join(formatted_tasks)

    async def process(self, inputs: FixSQLInput) -> FixSQLOutput:
        """
        Process a request to analyze and fix a failed SQL query.

        Args:
            inputs: The input data containing the failed SQL query,
                   execution error, subtasks, and planning summary.

        Returns:
            A FixSQLOutput containing the error explanation,
            fixed SQL query, and fix status.
        """
        try:
            subtasks_str = self._format_subtasks(inputs.subtasks)

            user_prompt = FIXSQL_USER_PROMPT.format(
                rephrased_question=inputs.rephrased_question,
                sql_query=inputs.sql_query,
                execution_error=inputs.execution_error,
                planning_summary=inputs.planning_summary or 'No planning summary available.',
                subtasks=subtasks_str,
                db_schema=inputs.db_schema,
            )

            messages: list[CompletionMessage] = [
                CompletionMessage(
                    role=MessageRole.SYSTEM,
                    content=FIXSQL_SYSTEM_PROMPT,
                ),
                CompletionMessage(
                    role=MessageRole.USER,
                    content=user_prompt,
                ),
            ]

            response = await self.litellm_service.process_async(
                inputs=LiteLLMInput(
                    message=messages,
                    return_type=FixSQLModel,
                    frequency_penalty=self.settings.frequency_penalty,
                    n=self.settings.n,
                    model=self.settings.model,
                    presence_penalty=self.settings.presence_penalty,
                ),
            )

            fixsql_result: FixSQLModel = FixSQLModel(
                **jsonable_encoder(response.response),
            )

            logger.info(
                'FixSQL agent result',
                extra={
                    'is_fixed': fixsql_result.is_fixed,
                    'error_explanation': fixsql_result.error_explanation if fixsql_result.error_explanation else '',
                    'has_fixed_sql': bool(fixsql_result.fixed_sql),
                },
            )

            return FixSQLOutput(
                error_explanation=fixsql_result.error_explanation,
                fixed_sql=fixsql_result.fixed_sql,
                is_fixed=bool(fixsql_result.fixed_sql),
            )
        except Exception as e:
            logger.warning(
                'Error processing fix SQL request',
                extra={
                    'error': str(e),
                    'input_sql': inputs.sql_query,
                    'execution_error': inputs.execution_error,
                },
            )
            return FixSQLOutput(
                error_explanation=f'Failed to analyze SQL error: {e!s}',
                fixed_sql='',
                is_fixed=False,
            )

    async def gprocess(self, state: ChatwithDBState) -> dict:
        """
        Wrapper method for executing fix SQL analysis within the LangGraph state graph.

        Args:
            state: The ChatwithDBState containing SQL query, execution error,
                   and planning context.

        Returns:
            dict containing 'fixsql_agent_state' with the fix SQL results.
        """
        try:
            rephrased_state = state.get('rephrased_state', {})
            rephrased_question = rephrased_state.get(
                'rephrased_main_question',
                state.get('question', ''),
            )

            sql_execution_state = state.get('sql_execution_state', {})
            sql_generator_state = state.get('sql_generator_state', {})
            failed_sql = sql_generator_state.get('sql_query', '')
            execution_error = sql_execution_state.get('error_message', '')

            planner_state = state.get('planner_state', {})
            planning_summary = planner_state.get('planning_summary', '')
            subtasks_data = planner_state.get('subtasks', [])

            table_pruner_state = state.get('table_pruner_state', {})
            db_schema = table_pruner_state.get('pruned_schema', '')

            subtasks = [
                SubTaskModel(
                    task_id=t.get('task_id', ''),
                    description=t.get('description', ''),
                    depends_on=t.get('depends_on', []),
                    sql_hint=t.get('sql_hint', ''),
                )
                for t in subtasks_data
            ] if subtasks_data else []

            fixsql_result = await self.process(
                inputs=FixSQLInput(
                    rephrased_question=rephrased_question,
                    sql_query=failed_sql,
                    execution_error=execution_error if execution_error else 'No execution error message available.',
                    subtasks=subtasks,
                    planning_summary=planning_summary,
                    db_schema=db_schema,
                ),
            )

            return {
                'fixsql_agent_state': {
                    'error_explanation': fixsql_result.error_explanation,
                    'is_fixed': fixsql_result.is_fixed,
                },
                'sql_generator_state': {
                    'sql_query': fixsql_result.fixed_sql.replace('.createdAt', '."createdAt"'),
                },
            }
        except Exception as e:
            logger.warning(
                'Failed to process fix SQL analysis in gprocess, using fallback values.',
                extra={
                    'error': str(e),
                    'original_sql': state.get('sql_generator_state', {}).get('sql_query'),
                },
            )
            return {
                'fixsql_agent_state': {
                    'error_explanation': f'Failed to analyze SQL error: {e!s}',
                    'fixed_sql': '',
                    'is_fixed': False,
                },
            }
