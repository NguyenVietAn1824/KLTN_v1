from __future__ import annotations

"""GraphQL Query Execution Service - Execute queries via Hasura.

This service executes GraphQL queries through HasuraService and handles
the response formatting.
"""

from typing import Any

from base import CustomBaseModel as BaseModel
from base import AsyncBaseService

from aqi_agent.infra.hasura import HasuraService


class ExecutionInput(BaseModel):
    """Input for query execution.

    Attributes:
        graphql_query (str): The GraphQL query to execute
        table_name (str): Target table name (for logging)
    """

    graphql_query: str
    table_name: str


class ExecutionOutput(BaseModel):
    """Output from query execution.

    Attributes:
        data (dict): Query results
        row_count (int): Number of rows returned
    """

    data: dict[str, Any]
    row_count: int


class ExecutionService(AsyncBaseService):
    """Service for executing GraphQL queries.

    Executes queries through HasuraService and formats the response.

    Attributes:
        hasura_service (HasuraService): Hasura service instance
    """

    hasura_service: HasuraService

    async def process(self, inputs: ExecutionInput) -> ExecutionOutput:
        """Execute GraphQL query.

        Args:
            inputs: Execution input with GraphQL query

        Returns:
            Execution output with query results

        Raises:
            Exception: If query execution fails

        Example:
            >>> inputs = ExecutionInput(
            ...     graphql_query='query { districts { id name } }',
            ...     table_name='districts'
            ... )
            >>> output = await service.process(inputs)
            >>> print(output.data)
        """
        # Execute query through Hasura
        result = await self.hasura_service.execute_query(inputs.graphql_query)

        # Extract data for the table
        data = result.get('data', {})
        table_data = data.get(inputs.table_name, [])

        row_count = len(table_data) if isinstance(table_data, list) else 1

        return ExecutionOutput(
            data=data,
            row_count=row_count,
        )

    async def gprocess(self, state: dict[str, Any]) -> dict[str, Any]:
        """Graph process method for LangGraph.

        Args:
            state: Current state with graphql_query

        Returns:
            Updated state with query results

        Example:
            >>> state = {
            ...     'graphql_query': 'query { districts { id name } }',
            ...     'table_name': 'districts'
            ... }
            >>> result = await service.gprocess(state)
            >>> print(result['data'])
        """
        try:
            if 'graphql_query' not in state:
                raise ValueError('Missing graphql_query in state')

            inputs = ExecutionInput(
                graphql_query=state['graphql_query'],
                table_name=state.get('table_name', 'unknown'),
            )

            output = await self.process(inputs)

            return {
                'data': output.data,
                'row_count': output.row_count,
            }

        except Exception as e:
            return {
                'exception': {'where': 'execution', 'error': str(e)},
                'data': {},
                'row_count': 0,
            }
