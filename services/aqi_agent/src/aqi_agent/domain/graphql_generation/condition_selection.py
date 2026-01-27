from __future__ import annotations

"""Condition Selection Service - Generate GraphQL where/order_by/limit conditions.

This service creates the filtering, ordering, and limiting conditions for GraphQL queries
based on the sub-question and context.
"""

from datetime import date
from typing import Any

from base import CustomBaseModel as BaseModel
from base import AsyncBaseService


class ConditionSelectionInput(BaseModel):
    """Input for condition selection.

    Attributes:
        question (str): The sub-question being processed
        description (str): Additional context about the question
        table_name (str): Target table for the query
        selected_fields (list[str]): Fields already selected for the query
        previous_results (dict | None): Results from previous tasks
    """

    question: str
    description: str
    table_name: str
    selected_fields: list[str]
    previous_results: dict[str, Any] | None = None


class ConditionSelectionOutput(BaseModel):
    """Output from condition selection.

    Attributes:
        where_conditions (dict): GraphQL where conditions
        order_by (list[dict] | None): GraphQL order_by clauses
        limit (int | None): Result limit
    """

    where_conditions: dict[str, Any]
    order_by: list[dict[str, Any]] | None = None
    limit: int | None = None


class ConditionSelectionService(AsyncBaseService):
    """Service for generating GraphQL query conditions.

    Analyzes the question and context to generate appropriate where clauses,
    ordering, and limits for the GraphQL query.

    Attributes:
        settings (dict[str, Any]): Configuration settings
    """

    settings: dict[str, Any]

    def _extract_district_filter(
        self,
        question: str,
        previous_results: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        """Extract district_id filter from question or previous results.

        Args:
            question: The question text
            previous_results: Results from Task 1 (district search)

        Returns:
            dict: District filter condition or None

        Example:
            >>> filter = service._extract_district_filter(
            ...     "Get AQI", 
            ...     {"district_id": "001"}
            ... )
            >>> print(filter)  # {'district_id': {'_eq': '001'}}
        """
        # Check previous results for district_id (from Task 1)
        if previous_results and 'district_id' in previous_results:
            return {'district_id': {'_eq': previous_results['district_id']}}

        if previous_results and 'district_ids' in previous_results:
            return {'district_id': {'_in': previous_results['district_ids']}}

        return None

    def _extract_date_filter(self, question: str) -> dict[str, Any] | None:
        """Extract date filter from question.

        Args:
            question: The question text

        Returns:
            dict: Date filter condition or None

        Example:
            >>> filter = service._extract_date_filter("AQI hôm nay")
            >>> print(filter)  # {'date': {'_eq': '2026-01-15'}}
        """
        q_lower = question.lower()

        if any(word in q_lower for word in ['hôm nay', 'today', 'hiện nay', 'current']):
            today = date.today().isoformat()
            return {'date': {'_eq': today}}

        # Could add more sophisticated date parsing here
        return None

    def _extract_name_search(self, question: str) -> dict[str, Any] | None:
        """Extract name search pattern from question.

        Args:
            question: The question text

        Returns:
            dict: Name search condition or None

        Example:
            >>> filter = service._extract_name_search("Find Hoàn Kiếm district")
            >>> print(filter)  # {'name': {'_ilike': '%Hoàn Kiếm%'}}
        """
        # Extract district name patterns
        # Simple approach: look for capitalized Vietnamese words
        import re

        # Pattern for Vietnamese district names (capitalized words with Vietnamese diacritics)
        pattern = r'[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ][a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]+(?:\s+[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ][a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]+)*'

        matches = re.findall(pattern, question)

        # Filter out common words
        common_words = ['Find', 'Get', 'Show', 'AQI', 'PM25', 'Tìm', 'Lấy', 'Hiển']
        district_names = [m for m in matches if m not in common_words]

        if district_names:
            # Use the first matched name
            name = district_names[0]
            return {
                '_or': [
                    {'name': {'_ilike': f'%{name}%'}},
                    {'normalized_name': {'_ilike': f'%{name.lower()}%'}},
                ]
            }

        return None

    def _determine_order_by(
        self,
        question: str,
        table_name: str,
    ) -> list[dict[str, Any]] | None:
        """Determine order_by clause from question.

        Args:
            question: The question text
            table_name: Target table name

        Returns:
            list: Order by clauses or None

        Example:
            >>> order = service._determine_order_by("latest AQI", "distric_stats")
            >>> print(order)  # [{'date': 'desc'}, {'hour': 'desc'}]
        """
        q_lower = question.lower()

        # For distric_stats, default to latest first
        if table_name == 'distric_stats':
            if any(word in q_lower for word in ['latest', 'current', 'mới nhất', 'hiện tại']):
                return [{'date': 'desc'}, {'hour': 'desc'}]

            if any(word in q_lower for word in ['oldest', 'first', 'cũ nhất']):
                return [{'date': 'asc'}, {'hour': 'asc'}]

            # Default: latest first
            return [{'date': 'desc'}, {'hour': 'desc'}]

        # For districts, order by name
        if table_name == 'districts':
            return [{'name': 'asc'}]

        return None

    def _determine_limit(self, question: str, table_name: str) -> int | None:
        """Determine result limit from question.

        Args:
            question: The question text
            table_name: Target table name

        Returns:
            int: Limit value or None

        Example:
            >>> limit = service._determine_limit("latest AQI", "distric_stats")
            >>> print(limit)  # 1
        """
        q_lower = question.lower()

        # Look for explicit numbers
        import re
        numbers = re.findall(r'\d+', question)
        if numbers:
            return int(numbers[0])

        # Implicit limits based on question type
        if any(word in q_lower for word in ['latest', 'current', 'mới nhất', 'hiện tại']):
            return 1

        # For search queries, limit to reasonable number
        if table_name == 'districts' and 'find' in q_lower:
            return 5

        return None

    async def process(self, inputs: ConditionSelectionInput) -> ConditionSelectionOutput:
        """Generate GraphQL query conditions.

        Args:
            inputs: Condition selection input

        Returns:
            Condition selection output with where/order_by/limit

        Example:
            >>> inputs = ConditionSelectionInput(
            ...     question="Get latest AQI for district",
            ...     table_name="distric_stats",
            ...     selected_fields=['aqi_value', 'date'],
            ...     previous_results={'district_id': '001'}
            ... )
            >>> output = await service.process(inputs)
            >>> print(output.where_conditions)
        """
        where_conditions = {}

        # Add district filter (from previous task or question)
        district_filter = self._extract_district_filter(
            inputs.question,
            inputs.previous_results,
        )
        if district_filter:
            where_conditions.update(district_filter)

        # Add date filter
        date_filter = self._extract_date_filter(inputs.question)
        if date_filter:
            where_conditions.update(date_filter)

        # Add name search (for districts table)
        if inputs.table_name == 'districts':
            name_search = self._extract_name_search(inputs.question)
            if name_search:
                where_conditions.update(name_search)

        # Determine order_by
        order_by = self._determine_order_by(inputs.question, inputs.table_name)

        # Determine limit
        limit = self._determine_limit(inputs.question, inputs.table_name)

        return ConditionSelectionOutput(
            where_conditions=where_conditions,
            order_by=order_by,
            limit=limit,
        )

    async def gprocess(self, state: dict[str, Any]) -> dict[str, Any]:
        """Graph process method for LangGraph.

        Args:
            state: Current state

        Returns:
            Updated state with conditions

        Example:
            >>> state = {
            ...     'question': 'Get latest AQI',
            ...     'table_name': 'distric_stats',
            ...     'selected_fields': ['aqi_value'],
            ...     'previous_results': {'district_id': '001'}
            ... }
            >>> result = await service.gprocess(state)
        """
        try:
            inputs = ConditionSelectionInput(
                question=state['question'],
                description=state.get('description', ''),
                table_name=state['table_name'],
                selected_fields=state['selected_fields'],
                previous_results=state.get('previous_results'),
            )

            output = await self.process(inputs)

            return {
                'where_conditions': output.where_conditions,
                'order_by': output.order_by,
                'limit': output.limit,
            }

        except Exception as e:
            return {
                'exception': {'where': 'condition_selection', 'error': str(e)},
            }
