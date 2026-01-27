from __future__ import annotations

"""GraphQL Query Builder Service - Build complete GraphQL query strings.

This service constructs valid GraphQL queries from selected fields and conditions,
following Hasura query syntax.
"""

from typing import Any

from base import CustomBaseModel as BaseModel
from base import AsyncBaseService


class QueryBuilderInput(BaseModel):
    """Input for query builder.

    Attributes:
        table_name (str): Target table name
        selected_fields (list[str]): Fields to select
        where_conditions (dict): Where clause conditions
        order_by (list[dict] | None): Order by clauses
        limit (int | None): Result limit
    """

    table_name: str
    selected_fields: list[str]
    where_conditions: dict[str, Any]
    order_by: list[dict[str, Any]] | None = None
    limit: int | None = None


class QueryBuilderOutput(BaseModel):
    """Output from query builder.

    Attributes:
        graphql_query (str): Complete GraphQL query string
    """

    graphql_query: str


class QueryBuilderService(AsyncBaseService):
    """Service for building GraphQL queries.

    Constructs valid Hasura GraphQL queries with proper syntax for where clauses,
    order_by, limit, and nested relationships.

    Attributes:
        settings (dict[str, Any]): Configuration settings
    """

    settings: dict[str, Any] = {}

    def _format_where_clause(self, where_conditions: dict[str, Any]) -> str:
        """Format where conditions as GraphQL syntax.

        Args:
            where_conditions: Dictionary of where conditions

        Returns:
            str: Formatted where clause string

        Example:
            >>> where = {'district_id': {'_eq': '001'}, 'date': {'_eq': '2026-01-15'}}
            >>> formatted = service._format_where_clause(where)
            >>> print(formatted)
            'where: {district_id: {_eq: "001"}, date: {_eq: "2026-01-15"}}'
        """
        if not where_conditions:
            return ''

        def format_value(v):
            if isinstance(v, str):
                return f'"{v}"'
            elif isinstance(v, dict):
                items = [f'{k}: {format_value(val)}' for k, val in v.items()]
                return '{' + ', '.join(items) + '}'
            elif isinstance(v, list):
                formatted_items = [format_value(item) for item in v]
                return '[' + ', '.join(formatted_items) + ']'
            else:
                return str(v)

        items = []
        for key, value in where_conditions.items():
            formatted = f'{key}: {format_value(value)}'
            items.append(formatted)

        return 'where: {' + ', '.join(items) + '}'

    def _format_order_by(self, order_by: list[dict[str, Any]] | None) -> str:
        """Format order_by as GraphQL syntax.

        Args:
            order_by: List of order_by dictionaries

        Returns:
            str: Formatted order_by string

        Example:
            >>> order = [{'date': 'desc'}, {'hour': 'desc'}]
            >>> formatted = service._format_order_by(order)
            >>> print(formatted)
            'order_by: [{date: desc}, {hour: desc}]'
        """
        if not order_by:
            return ''

        items = []
        for clause in order_by:
            for field, direction in clause.items():
                items.append(f'{{{field}: {direction}}}')

        return 'order_by: [' + ', '.join(items) + ']'

    def _format_limit(self, limit: int | None) -> str:
        """Format limit as GraphQL syntax.

        Args:
            limit: Limit value

        Returns:
            str: Formatted limit string

        Example:
            >>> formatted = service._format_limit(10)
            >>> print(formatted)
            'limit: 10'
        """
        if limit is None:
            return ''

        return f'limit: {limit}'

    def _build_field_selection(
        self,
        fields: list[str],
        table_name: str,
    ) -> str:
        """Build field selection part of query with nested relationships.

        Args:
            fields: List of field names
            table_name: Target table name

        Returns:
            str: Field selection string with indentation

        Example:
            >>> fields = ['id', 'name', 'aqi_value']
            >>> selection = service._build_field_selection(fields, 'distric_stats')
        """
        field_lines = []

        for field in fields:
            field_lines.append(f'    {field}')

        # Add nested relationships for certain tables
        if table_name == 'distric_stats':
            # Include district name for context
            field_lines.append('    district {')
            field_lines.append('      id')
            field_lines.append('      name')
            field_lines.append('    }')

        elif table_name == 'districts':
            # Include province name if needed
            # field_lines.append('    province {')
            # field_lines.append('      id')
            # field_lines.append('      name')
            # field_lines.append('    }')
            pass

        return '\n'.join(field_lines)

    async def process(self, inputs: QueryBuilderInput) -> QueryBuilderOutput:
        """Build complete GraphQL query.

        Args:
            inputs: Query builder input with fields and conditions

        Returns:
            Query builder output with GraphQL query string

        Example:
            >>> inputs = QueryBuilderInput(
            ...     table_name='distric_stats',
            ...     selected_fields=['aqi_value', 'date'],
            ...     where_conditions={'district_id': {'_eq': '001'}},
            ...     order_by=[{'date': 'desc'}],
            ...     limit=1
            ... )
            >>> output = await service.process(inputs)
            >>> print(output.graphql_query)
        """
        # Build query arguments
        args = []

        where_clause = self._format_where_clause(inputs.where_conditions)
        if where_clause:
            args.append(where_clause)

        order_by_clause = self._format_order_by(inputs.order_by)
        if order_by_clause:
            args.append(order_by_clause)

        limit_clause = self._format_limit(inputs.limit)
        if limit_clause:
            args.append(limit_clause)

        args_string = ', '.join(args)
        if args_string:
            args_string = f'({args_string})'

        # Build field selection
        field_selection = self._build_field_selection(
            inputs.selected_fields,
            inputs.table_name,
        )

        # Construct full query
        query = f"""query {{
  {inputs.table_name}{args_string} {{
{field_selection}
  }}
}}"""

        return QueryBuilderOutput(graphql_query=query)

    async def gprocess(self, state: dict[str, Any]) -> dict[str, Any]:
        """Graph process method for LangGraph.

        Args:
            state: Current state with fields and conditions

        Returns:
            Updated state with graphql_query

        Example:
            >>> state = {
            ...     'table_name': 'distric_stats',
            ...     'selected_fields': ['aqi_value'],
            ...     'where_conditions': {'district_id': {'_eq': '001'}},
            ...     'order_by': [{'date': 'desc'}],
            ...     'limit': 1
            ... }
            >>> result = await service.gprocess(state)
            >>> print(result['graphql_query'])
        """
        try:
            inputs = QueryBuilderInput(
                table_name=state['table_name'],
                selected_fields=state['selected_fields'],
                where_conditions=state.get('where_conditions', {}),
                order_by=state.get('order_by'),
                limit=state.get('limit'),
            )

            output = await self.process(inputs)

            return {
                'graphql_query': output.graphql_query,
            }

        except Exception as e:
            return {
                'exception': {'where': 'query_builder', 'error': str(e)},
            }
