from __future__ import annotations

"""Text2GraphQL Planning Service - Decompose questions into structured tasks.

This service analyzes natural language questions about air quality and generates
a TodoList with structured tasks and sub-questions, following Apollo's planning pattern.
"""

from typing import Any

from base import CustomBaseModel as BaseModel
from base import AsyncBaseService


class Text2GraphQLPlanningInput(BaseModel):
    """Input for Text2GraphQL planning service.

    Attributes:
        raw_question (str): User's natural language question about air quality
        context_schema (dict[str, Any]): Available Hasura tables with descriptions
    """

    raw_question: str
    context_schema: dict[str, Any]


class Text2GraphQLPlanningOutput(BaseModel):
    """Output from Text2GraphQL planning service.

    Attributes:
        todo_list (TodoList): Structured planning with tasks and sub-questions
    """

    from aqi_agent.shared.model.text2sql_models import TodoList

    todo_list: TodoList


class Text2GraphQLPlanningService(AsyncBaseService):
    """Service for planning Text2GraphQL workflow.

    Analyzes air quality questions and creates a structured TodoList following
    Apollo's pattern:
    - Task 1: Entity identification (find districts, dates)
    - Task 2 (optional): Data collection using Task 1 results

    This version uses heuristics and patterns for Vietnamese AQI questions.
    Can be enhanced with LLM for more sophisticated planning.

    Attributes:
        settings (dict[str, Any]): Configuration settings
    """

    settings: dict[str, Any]

    def _detect_intent(self, question: str) -> str:
        """Detect question intent from natural language.

        Args:
            question (str): User's question

        Returns:
            str: Intent type - 'current_aqi', 'compare', 'historical', 'search'

        Example:
            >>> intent = service._detect_intent("AQI Hoàn Kiếm hôm nay")
            >>> print(intent)  # 'current_aqi'
        """
        q_lower = question.lower()

        # Search/find district
        if any(word in q_lower for word in ['tìm', 'find', 'search', 'ở đâu', 'where']):
            return 'search'

        # Compare districts
        if any(word in q_lower for word in ['so sánh', 'compare', 'vs', 'versus', 'hay', 'hơn']):
            return 'compare'

        # Historical/trend
        if any(word in q_lower for word in ['lịch sử', 'history', 'xu hướng', 'trend', 'thay đổi']):
            return 'historical'

        # Current AQI (default)
        return 'current_aqi'

    def _extract_district_names(self, question: str) -> list[str]:
        """Extract district names from question.

        Args:
            question (str): User's question

        Returns:
            list[str]: List of district names found

        Example:
            >>> districts = service._extract_district_names("So sánh AQI Hoàn Kiếm và Ba Đình")
            >>> print(districts)  # ['Hoàn Kiếm', 'Ba Đình']
        """
        # Common Hanoi districts
        hanoi_districts = [
            'Ba Đình', 'Hoàn Kiếm', 'Tây Hồ', 'Long Biên', 'Cầu Giấy',
            'Đống Đa', 'Hai Bà Trưng', 'Hoàng Mai', 'Thanh Xuân',
            'Nam Từ Liêm', 'Bắc Từ Liêm', 'Hà Đông',
        ]

        found = []
        for district in hanoi_districts:
            if district.lower() in question.lower():
                found.append(district)

        return found

    def _requires_two_tasks(self, intent: str, question: str) -> bool:
        """Determine if question requires 2 tasks (entity identification + data collection).

        Args:
            intent (str): Question intent type
            question (str): User's question

        Returns:
            bool: True if 2 tasks needed, False if 1 task sufficient

        Example:
            >>> needs_two = service._requires_two_tasks('current_aqi', 'AQI Hoàn Kiếm')
            >>> print(needs_two)  # True (need to find district first, then get AQI)
        """
        # If district name is explicitly mentioned, need Task 1 to find district_id
        if self._extract_district_names(question):
            return True

        # Compare always needs 2 tasks
        if intent == 'compare':
            return True

        # Search only needs 1 task
        if intent == 'search':
            return False

        return True

    async def process(self, inputs: Text2GraphQLPlanningInput) -> Text2GraphQLPlanningOutput:
        """Generate TodoList from user question.

        Args:
            inputs: Planning input with question and schema context

        Returns:
            Planning output with structured TodoList

        Raises:
            ValueError: If question is empty or invalid

        Example:
            >>> inputs = Text2GraphQLPlanningInput(
            ...     raw_question="AQI Hoàn Kiếm hôm nay thế nào?",
            ...     context_schema={"districts": "...", "distric_stats": "..."}
            ... )
            >>> output = await service.process(inputs)
            >>> print(output.todo_list.first_task.sub_questions[0].question)
        """
        from aqi_agent.shared.model.text2sql_models import TodoList, Task, SubQuestion

        if not inputs.raw_question or not inputs.raw_question.strip():
            raise ValueError('raw_question cannot be empty')

        question = inputs.raw_question
        intent = self._detect_intent(question)
        district_names = self._extract_district_names(question)

        # Task 1: Find district(s)
        if district_names:
            if len(district_names) == 1:
                task1_question = f"Find district ID for '{district_names[0]}'"
                task1_desc = f"Search districts table to get the ID of {district_names[0]}"
            else:
                task1_question = f"Find district IDs for {', '.join(district_names)}"
                task1_desc = f"Search districts table to get IDs of multiple districts"
        else:
            task1_question = "Search for districts matching the question"
            task1_desc = "Find relevant districts from the districts table"

        sub_q1 = SubQuestion(
            question=task1_question,
            description=task1_desc,
            table_name="districts",
        )

        first_task = Task(sub_questions=[sub_q1])

        # Task 2: Get AQI data (if needed)
        if self._requires_two_tasks(intent, question):
            if intent == 'current_aqi':
                task2_question = "Get latest AQI data for the found district(s)"
                task2_desc = "Query distric_stats table for most recent AQI measurements"
            elif intent == 'compare':
                task2_question = "Get current AQI for all found districts to compare"
                task2_desc = "Query distric_stats for latest data of multiple districts"
            elif intent == 'historical':
                task2_question = "Get historical AQI data for the found district(s)"
                task2_desc = "Query distric_stats for time series data"
            else:
                task2_question = "Get AQI data for the identified district(s)"
                task2_desc = "Retrieve air quality measurements from distric_stats"

            sub_q2 = SubQuestion(
                question=task2_question,
                description=task2_desc,
                table_name="distric_stats",
            )

            second_task = Task(sub_questions=[sub_q2])
            todo_list = TodoList(first_task=first_task, second_task=second_task)
        else:
            todo_list = TodoList(first_task=first_task, second_task=None)

        return Text2GraphQLPlanningOutput(todo_list=todo_list)

    async def gprocess(self, state: dict[str, Any]) -> dict[str, Any]:
        """Graph process method for LangGraph integration.

        Args:
            state (dict): Current workflow state with raw_question

        Returns:
            dict: Updated state with shared_memory (TodoList) and _task_number

        Raises:
            ValueError: If raw_question missing from state

        Example:
            >>> state = {'raw_question': 'AQI Hoàn Kiếm hôm nay?'}
            >>> result = await service.gprocess(state)
            >>> print(result['_task_number'])  # 2
        """
        if 'raw_question' not in state:
            raise ValueError('Missing required field: raw_question')

        # Get available tables from Hasura
        # TODO: Could integrate with HasuraService to get actual schema
        context_schema = {
            'districts': 'Contains district information (id, name, province_id, normalized_name)',
            'distric_stats': 'Contains AQI measurements (date, hour, district_id, aqi_value, pm25_value)',
            'provinces': 'Contains province information',
            'air_component': 'Air quality component types',
        }

        planning_input = Text2GraphQLPlanningInput(
            raw_question=state['raw_question'],
            context_schema=context_schema,
        )

        planning_output = await self.process(planning_input)
        todo_list = planning_output.todo_list

        task_number = 2 if todo_list.second_task is not None else 1

        return {
            'shared_memory': todo_list,
            '_task_number': task_number,
            '_task_idx': 1,  # Start with task 1
        }
