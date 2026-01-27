from __future__ import annotations

"""Field Selection Service - Select GraphQL fields for queries.

This service determines which fields to include in a GraphQL SELECT based on
the sub-question and table schema.
"""

from typing import Any

from base import CustomBaseModel as BaseModel
from base import AsyncBaseService


class FieldSelectionInput(BaseModel):
    """Input for field selection.

    Attributes:
        question (str): The sub-question being processed
        table_name (str): Target table for the query
        table_schema (dict): Schema information for the table
    """

    question: str
    table_name: str
    table_schema: dict[str, Any]


class FieldSelectionOutput(BaseModel):
    """Output from field selection.

    Attributes:
        selected_fields (list[str]): List of field names to include in query
    """

    selected_fields: list[str]


class FieldSelectionService(AsyncBaseService):
    """Service for selecting appropriate GraphQL fields.

    Analyzes the question and table schema to determine which fields
    should be included in the GraphQL query SELECT clause.

    Attributes:
        settings (dict[str, Any]): Configuration settings
    """

    settings: dict[str, Any]

    def _get_default_fields(self, table_name: str) -> list[str]:
        """Get default fields for a table.

        Args:
            table_name (str): Name of the table

        Returns:
            list[str]: Default field names to select

        Example:
            >>> fields = service._get_default_fields('districts')
            >>> print(fields)  # ['id', 'name', 'province_id']
        """
        # Default fields per table
        defaults = {
            'districts': ['id', 'name', 'normalized_name', 'province_id'],
            'distric_stats': ['id', 'date', 'hour', 'aqi_value', 'pm25_value', 'district_id'],
            'provinces': ['id', 'name'],
            'air_component': ['id', 'name', 'description'],
        }

        return defaults.get(table_name, ['id'])

    def _extract_requested_metrics(self, question: str) -> list[str]:
        """Extract metrics mentioned in the question.

        Args:
            question (str): The question text

        Returns:
            list[str]: List of metric field names

        Example:
            >>> metrics = service._extract_requested_metrics("Get AQI and PM2.5")
            >>> print(metrics)  # ['aqi_value', 'pm25_value']
        """
        q_lower = question.lower()
        metrics = []

        if 'aqi' in q_lower or 'chỉ số' in q_lower:
            metrics.append('aqi_value')

        if 'pm2.5' in q_lower or 'pm25' in q_lower or 'bụi' in q_lower:
            metrics.append('pm25_value')

        if 'date' in q_lower or 'ngày' in q_lower or 'thời gian' in q_lower:
            metrics.extend(['date', 'hour'])

        return metrics

    async def process(self, inputs: FieldSelectionInput) -> FieldSelectionOutput:
        """Select fields for GraphQL query.

        Args:
            inputs: Field selection input with question and schema

        Returns:
            Field selection output with selected fields

        Example:
            >>> inputs = FieldSelectionInput(
            ...     question="Get latest AQI",
            ...     table_name="distric_stats",
            ...     table_schema={...}
            ... )
            >>> output = await service.process(inputs)
            >>> print(output.selected_fields)
        """
        # Start with default fields
        fields = self._get_default_fields(inputs.table_name)

        # Add requested metrics
        requested_metrics = self._extract_requested_metrics(inputs.question)
        for metric in requested_metrics:
            if metric not in fields:
                fields.append(metric)

        # For districts queries, ensure we have name for display
        if inputs.table_name == 'districts' and 'name' not in fields:
            fields.append('name')

        # For stats queries, ensure we have district relationship
        if inputs.table_name == 'distric_stats':
            # We might want to include nested district info
            # This will be handled in query builder with relationships
            pass

        return FieldSelectionOutput(selected_fields=fields)

    async def gprocess(self, state: dict[str, Any]) -> dict[str, Any]:
        """Graph process method for LangGraph.

        Args:
            state: Current state with question and table_name

        Returns:
            Updated state with selected_fields

        Example:
            >>> state = {'question': 'Get AQI', 'table_name': 'distric_stats'}
            >>> result = await service.gprocess(state)
            >>> print(result['selected_fields'])
        """
        try:
            inputs = FieldSelectionInput(
                question=state['question'],
                table_name=state['table_name'],
                table_schema=state.get('table_schema', {}),
            )

            output = await self.process(inputs)

            return {
                'selected_fields': output.selected_fields,
            }

        except Exception as e:
            return {
                'exception': {'where': 'field_selection', 'error': str(e)},
            }
