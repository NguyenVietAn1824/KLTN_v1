from __future__ import annotations

from base import BaseModel
from base import BaseService
from aqi_agent.shared.models.state import ChatwithDBState
from aqi_agent.shared.models.state import SQLExecutionState
from aqi_agent.shared.settings import SQLExecutionSettings
from logger import get_logger
from pg import SQLDatabase
from pydantic import Field
from sqlalchemy import text

from .utils import SQLExecutionMessage

logger = get_logger(__name__)


class SQLExecutionHandlerInput(BaseModel):
    sql_query: str = Field(..., description='The SQL query to be executed.')


class SQLExecutionHandlerOutput(BaseModel):
    execution_result: str | None = Field(None, description='The result of the SQL execution if successful.')
    error_message: str | None = Field(None, description='Error message if the SQL execution failed.')
    number_of_rows: int | None = Field(None, description='Number of rows returned by the SQL execution, if applicable.')


class SQLExecutionHandlerService(BaseService):
    sql_database: SQLDatabase
    settings: SQLExecutionSettings

    async def process(self, inputs: SQLExecutionHandlerInput) -> SQLExecutionHandlerOutput:
        """Execute the provided SQL query using the configured SQLDatabase."""
        if not inputs.sql_query or not inputs.sql_query.strip():
            logger.warning(SQLExecutionMessage.EMPTY_QUERY.value)

            return SQLExecutionHandlerOutput(
                execution_result=None,
                error_message=SQLExecutionMessage.EMPTY_QUERY.value,
            )
        try:
            with self.sql_database.get_session() as session:
                result = session.execute(text(inputs.sql_query))
                result = result.fetchall()
                number_of_rows = len(result)
                execution_result = str(result) if number_of_rows <= self.settings.max_rows else str(result[:self.settings.max_rows]) + f'... (and {number_of_rows - self.settings.max_rows} more rows)'

                logger.info(SQLExecutionMessage.SUCCESS.value, extra={'sql_query': inputs.sql_query, 'number_of_rows': number_of_rows})

        except Exception as e:
            logger.warning(
                SQLExecutionMessage.EXECUTION_FAILED.value.format(error_message=str(e)),
                extra={'sql_query': inputs.sql_query},
            )
            return SQLExecutionHandlerOutput(execution_result=None, error_message=str(e), number_of_rows=None)

        return SQLExecutionHandlerOutput(execution_result=execution_result, error_message=None, number_of_rows=number_of_rows)

    async def gprocess(self, state: ChatwithDBState) -> dict:
        """Wrapper method for executing SQL within the LangGraph state graph."""
        try:
            sql_query = state.get('sql_validator_state', {}).get('sanitized_query', '')

            execution_results = await self.process(
                inputs=SQLExecutionHandlerInput(
                    sql_query=sql_query,
                ),
            )

            return {
                'sql_execution_state': SQLExecutionState(
                    execution_result=execution_results.execution_result,
                    error_message=execution_results.error_message,
                    number_of_rows=execution_results.number_of_rows,
                ),
            }
        except Exception as e:
            logger.warning(
                SQLExecutionMessage.UNEXPECTED_ERROR.value.format(error_message=str(e)),
                extra={'sql_query': state.get('sql_validator_state', {}).get('sanitized_query', '')},
            )
            return {
                'sql_execution_state': SQLExecutionState(
                    execution_result=None,
                    error_message=SQLExecutionMessage.UNEXPECTED_ERROR.value.format(error_message=str(e)),
                    number_of_rows=None,
                ),
            }
