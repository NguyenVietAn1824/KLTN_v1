from __future__ import annotations

"""Text2GraphQL Sub-Agent Service - Orchestrate GraphQL generation pipeline.

This service coordinates the complete workflow from question to GraphQL execution:
1. Field Selection - Determine what fields to retrieve
2. Condition Selection - Generate where/order_by/limit conditions
3. Query Builder - Construct complete GraphQL query
4. Execution - Execute query via Hasura

Mirrors Apollo's sub-agent pattern for text2graphql.
"""

from typing import Any

from base import CustomBaseModel as BaseModel
from base import AsyncBaseService

from aqi_agent.domain.graphql_generation import (
    FieldSelectionService,
    FieldSelectionInput,
    ConditionSelectionService,
    ConditionSelectionInput,
    QueryBuilderService,
    QueryBuilderInput,
    ExecutionService,
    ExecutionInput,
)


class SubAgentInput(BaseModel):
    """Input for sub-agent processing.

    Attributes:
        question (str): Original user question
        sub_question (str): Current sub-question to process
        table_name (str): Target table name
        intent (str): Question intent (e.g., 'get_current_aqi', 'compare_districts')
        previous_results (dict): Results from previous tasks in workflow
    """

    question: str
    sub_question: str
    table_name: str
    intent: str
    previous_results: dict[str, Any] = {}


class SubAgentOutput(BaseModel):
    """Output from sub-agent processing.

    Attributes:
        data (dict): Query results
        row_count (int): Number of rows returned
        graphql_query (str): The executed GraphQL query
    """

    data: dict[str, Any]
    row_count: int
    graphql_query: str


class Text2GraphQLSubAgentService(AsyncBaseService):
    """Sub-agent service for Text to GraphQL conversion.

    Orchestrates the complete pipeline to convert a natural language question
    into a GraphQL query and execute it.

    Attributes:
        field_selection_service (FieldSelectionService): Field selection service
        condition_selection_service (ConditionSelectionService): Condition selection service
        query_builder_service (QueryBuilderService): Query builder service
        execution_service (ExecutionService): Execution service
    """

    field_selection_service: FieldSelectionService
    condition_selection_service: ConditionSelectionService
    query_builder_service: QueryBuilderService
    execution_service: ExecutionService

    async def process(self, inputs: SubAgentInput) -> SubAgentOutput:
        """Process sub-question through complete Text2GraphQL pipeline.

        Args:
            inputs: Sub-agent input with question and context

        Returns:
            Sub-agent output with query results

        Raises:
            Exception: If any step in the pipeline fails

        Example:
            >>> inputs = SubAgentInput(
            ...     question="Không khí ở Hoàn Kiếm hôm nay thế nào?",
            ...     sub_question="Lấy dữ liệu AQI của quận Hoàn Kiếm hôm nay",
            ...     table_name="distric_stats",
            ...     intent="get_current_aqi",
            ...     previous_results={"district_id": "001"}
            ... )
            >>> output = await service.process(inputs)
            >>> print(output.data)
        """
        # Step 1: Field Selection
        # Determine which fields to retrieve based on the question
        field_input = FieldSelectionInput(
            question=inputs.sub_question,
            table_name=inputs.table_name,
        )
        field_output = await self.field_selection_service.process(field_input)

        # Step 2: Condition Selection
        # Generate where clauses, order_by, and limit
        condition_input = ConditionSelectionInput(
            question=inputs.sub_question,
            table_name=inputs.table_name,
            intent=inputs.intent,
            previous_results=inputs.previous_results,
        )
        condition_output = await self.condition_selection_service.process(
            condition_input,
        )

        # Step 3: Query Building
        # Construct complete GraphQL query string
        query_input = QueryBuilderInput(
            table_name=inputs.table_name,
            selected_fields=field_output.selected_fields,
            where_conditions=condition_output.where_conditions,
            order_by=condition_output.order_by,
            limit=condition_output.limit,
        )
        query_output = await self.query_builder_service.process(query_input)

        # Step 4: Execution
        # Execute query through Hasura
        execution_input = ExecutionInput(
            graphql_query=query_output.graphql_query,
            table_name=inputs.table_name,
        )
        execution_output = await self.execution_service.process(execution_input)

        return SubAgentOutput(
            data=execution_output.data,
            row_count=execution_output.row_count,
            graphql_query=query_output.graphql_query,
        )

    async def gprocess(self, state: dict[str, Any]) -> dict[str, Any]:
        """Graph process method for LangGraph.

        Args:
            state: Current state with question and context

        Returns:
            Updated state with query results

        Example:
            >>> state = {
            ...     'question': 'Không khí ở Hoàn Kiếm hôm nay thế nào?',
            ...     'sub_question': 'Lấy dữ liệu AQI của quận Hoàn Kiếm hôm nay',
            ...     'table_name': 'distric_stats',
            ...     'intent': 'get_current_aqi',
            ...     'previous_results': {'district_id': '001'}
            ... }
            >>> result = await service.gprocess(state)
            >>> print(result['data'])
        """
        try:
            inputs = SubAgentInput(
                question=state['question'],
                sub_question=state.get('sub_question', state['question']),
                table_name=state['table_name'],
                intent=state.get('intent', 'query'),
                previous_results=state.get('previous_results', {}),
            )

            output = await self.process(inputs)

            return {
                'data': output.data,
                'row_count': output.row_count,
                'graphql_query': output.graphql_query,
                'sub_agent_completed': True,
            }

        except Exception as e:
            return {
                'exception': {'where': 'text2graphql_sub_agent', 'error': str(e)},
                'data': {},
                'row_count': 0,
                'sub_agent_completed': False,
            }
