from __future__ import annotations

from typing import Any

from base import CustomBaseModel as BaseModel
from base import AsyncBaseService


class SQLExecutionInput(BaseModel):
    """Input for SQL execution service.

    Attributes:
        sql_query (str): The SQL query string to execute.
        table_name (str): The primary table being queried (for logging/context).
    """

    sql_query: str
    table_name: str


class SQLExecutionOutput(BaseModel):
    """Output from SQL execution service.

    Attributes:
        data (list[dict[str, Any]]): Query results as list of row dictionaries.
        row_count (int): Number of rows returned.
        execution_time_ms (float): Query execution time in milliseconds.
    """

    data: list[dict[str, Any]]
    row_count: int
    execution_time_ms: float


class SQLExecutionService(AsyncBaseService):
    """Service for executing SQL queries against the AQI database.

    This service handles the safe execution of generated SQL queries, including:
    - Query validation (prevent dangerous operations)
    - Connection management  
    - Result formatting
    - Error handling
    - Performance monitoring

    Attributes:
        database (AQIDatabase): Database connection instance from pg library.
    """

    database: Any  # AQIDatabase from pg library

    def _validate_query(self, sql_query: str) -> None:
        """Validate SQL query for safety.

        Ensures the query:
        - Is a SELECT statement
        - Does not contain dangerous keywords (DELETE, UPDATE, DROP, etc.)
        - Does not contain malicious patterns

        Args:
            sql_query: The SQL query to validate

        Raises:
            ValueError: If query is unsafe or invalid
        """
        sql_upper = sql_query.upper().strip()

        # Must be a SELECT query
        if not sql_upper.startswith('SELECT'):
            raise ValueError('Only SELECT queries are allowed')

        # Check for dangerous keywords
        dangerous_keywords = [
            'DELETE', 'UPDATE', 'INSERT', 'DROP', 'ALTER', 'CREATE',
            'TRUNCATE', 'GRANT', 'REVOKE', 'EXEC', 'EXECUTE',
        ]

        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                raise ValueError(f'Dangerous keyword detected: {keyword}')

    async def process(self, inputs: SQLExecutionInput) -> SQLExecutionOutput:
        """Execute SQL query and return results.

        Args:
            inputs: SQLExecutionInput containing the query to execute

        Returns:
            SQLExecutionOutput with query results and metadata

        Raises:
            ValueError: If query is invalid or unsafe
            Exception: If query execution fails

        Example:
            >>> inputs = SQLExecutionInput(
            ...     sql_query="SELECT * FROM districts LIMIT 5",
            ...     table_name="districts"
            ... )
            >>> output = await service.process(inputs)
            >>> output.row_count <= 5
            True
        """
        import time

        # Validate query for safety
        self._validate_query(inputs.sql_query)

        start_time = time.time()

        # Execute query using database session
        with self.database.get_session() as session:
            result = session.execute(inputs.sql_query)
            
            # Fetch all results
            rows = result.fetchall()
            
            # Convert to list of dicts
            if rows:
                columns = result.keys()
                data = [dict(zip(columns, row)) for row in rows]
            else:
                data = []

        execution_time_ms = (time.time() - start_time) * 1000

        return SQLExecutionOutput(
            data=data,
            row_count=len(data),
            execution_time_ms=execution_time_ms,
        )

    async def gprocess(self, state: dict[str, Any]) -> dict[str, Any]:
        """Graph process method for LangGraph integration.

        Args:
            state: Current workflow state containing sql_query

        Returns:
            Updated state dict with query results

        Raises:
            ValueError: If sql_query is missing from state
            Exception: If query execution fails
        """
        try:
            if 'sql_query' not in state:
                raise ValueError('Missing required field: sql_query')

            inputs = SQLExecutionInput(
                sql_query=state['sql_query'],
                table_name=state.get('table_name', 'unknown'),
            )

            output = await self.process(inputs)

            return {
                'data': output.data,
                'row_count': output.row_count,
                'execution_time_ms': output.execution_time_ms,
            }

        except Exception as e:
            return {
                'exception': {'where': 'sql_execution', 'error': str(e)},
                'data': [],
                'row_count': 0,
            }
