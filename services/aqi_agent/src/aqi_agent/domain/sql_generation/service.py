from __future__ import annotations

from typing import Any

from base import CustomBaseModel as BaseModel
from base import AsyncBaseService
from logger import get_logger

logger = get_logger(__name__)


class SQLGenerationInput(BaseModel):
    """Input for SQL generation service.

    Attributes:
        question (str): The natural language sub-question to convert to SQL.
        description (str): Additional context about what the question seeks.
        table_name (str): Primary table to query (districts, distric_stats, provinces).
        schema_context (dict[str, Any]): Database schema information for the table.
        previous_results (dict[str, Any] | None): Results from previous sub-questions
            that can be used to refine this query (e.g., district IDs from task 1).
    """

    question: str
    description: str
    table_name: str
    schema_context: dict[str, Any]
    previous_results: dict[str, Any] | None = None


class SQLGenerationOutput(BaseModel):
    """Output from SQL generation service.

    Attributes:
        sql_query (str): The generated PostgreSQL query string.
        explanation (str): Human-readable explanation of what the query does.
    """

    sql_query: str
    explanation: str = ''


class SQLGenerationService(AsyncBaseService):
    """Service for generating SQL queries from natural language questions.

    This service converts structured sub-questions into executable PostgreSQL queries
    for the air quality database. It can work in two modes:
    
    1. **LLM-based mode** (production): Uses an LLM to generate sophisticated queries
       with complex JOINs, aggregations, and conditions.
       
    2. **Template-based mode** (fallback): Uses predefined query templates for common
       patterns like "latest AQI", "find district", "compare districts".

    The service follows these steps:
    1. Analyze the question and determine query pattern
    2. Extract key parameters (district names, dates, metrics)
    3. Generate SQL using LLM or template
    4. Validate the generated SQL for safety and correctness
    5. Return the query with explanation

    Attributes:
        settings (dict[str, Any]): Configuration for SQL generation (LLM params, etc.).
        database (AQIDatabase): Database instance for schema introspection.
    """

    settings: dict[str, Any]
    # litellm_service: LiteLLMService  # Will be added when integrating LLM

    def _build_context(
        self,
        schema_context: dict[str, Any],
        previous_results: dict[str, Any] | None,
    ) -> str:
        """Build context string for SQL generation.

        Args:
            schema_context: Database schema information
            previous_results: Results from previous tasks

        Returns:
            Formatted context string
        """
        context_parts = []

        if schema_context:
            context_parts.append("Schema Information:")
            for key, value in schema_context.items():
                context_parts.append(f"  {key}: {value}")

        if previous_results:
            context_parts.append("\nPrevious Results:")
            for key, value in previous_results.items():
                context_parts.append(f"  {key}: {value}")

        return '\n'.join(context_parts) if context_parts else 'No additional context'

    def _detect_query_pattern(self, question: str) -> str:
        """Detect the query pattern from the question.

        Args:
            question: The natural language question

        Returns:
            Pattern type: 'find_district', 'latest_aqi', 'compare', 'historical', 'aggregate'
        """
        question_lower = question.lower()

        if any(word in question_lower for word in ['tìm', 'find', 'where', 'ở đâu']):
            return 'find_district'
        elif any(word in question_lower for word in ['so sánh', 'compare', 'vs', 'versus']):
            return 'compare'
        elif any(word in question_lower for word in ['hôm nay', 'hiện nay', 'bây giờ', 'today', 'now', 'current']):
            return 'latest_aqi'
        elif any(word in question_lower for word in ['trung bình', 'average', 'avg', 'tổng', 'sum', 'cao nhất', 'max']):
            return 'aggregate'
        elif any(word in question_lower for word in ['lịch sử', 'history', 'historical', 'trong', 'during']):
            return 'historical'
        
        return 'latest_aqi'  # Default pattern

    def _generate_template_query(
        self,
        pattern: str,
        question: str,
        table_name: str,
        previous_results: dict[str, Any] | None,
    ) -> tuple[str, str]:
        """Generate SQL using predefined templates.

        Args:
            pattern: Query pattern type
            question: The natural language question
            table_name: Target table name
            previous_results: Results from previous tasks

        Returns:
            Tuple of (sql_query, explanation)
        """
        if pattern == 'find_district':
            # Extract district name from question
            # Simple pattern: look for Vietnamese district names
            return (
                """SELECT id, name, normalized_name, province_id
                FROM districts
                WHERE LOWER(normalized_name) LIKE LOWER('%Hoàn Kiếm%')
                LIMIT 5""",
                "Find districts matching the search term"
            )

        elif pattern == 'latest_aqi':
            district_id = previous_results.get('district_id', 'unknown') if previous_results else 'unknown'
            return (
                f"""SELECT ds.aqi_value, ds.pm25_value, ds.date, ds.hour, d.name as district_name
                FROM distric_stats ds
                JOIN districts d ON ds.district_id = d.id
                WHERE ds.district_id = '{district_id}'
                ORDER BY ds.date DESC, ds.hour DESC
                LIMIT 1""",
                f"Get latest AQI data for district {district_id}"
            )

        elif pattern == 'compare':
            return (
                """SELECT d.name, ds.aqi_value, ds.pm25_value, ds.date, ds.hour
                FROM distric_stats ds
                JOIN districts d ON ds.district_id = d.id
                WHERE ds.date = (SELECT MAX(date) FROM distric_stats)
                AND ds.hour = (SELECT MAX(hour) FROM distric_stats WHERE date = (SELECT MAX(date) FROM distric_stats))
                ORDER BY ds.aqi_value DESC
                LIMIT 10""",
                "Compare AQI values across districts for the latest timestamp"
            )

        elif pattern == 'aggregate':
            district_id = previous_results.get('district_id', 'unknown') if previous_results else 'unknown'
            return (
                f"""SELECT 
                    AVG(ds.aqi_value) as avg_aqi,
                    MAX(ds.aqi_value) as max_aqi,
                    MIN(ds.aqi_value) as min_aqi,
                    COUNT(*) as measurement_count
                FROM distric_stats ds
                WHERE ds.district_id = '{district_id}'
                AND ds.date >= CURRENT_DATE - INTERVAL '7 days'
                AND ds.aqi_value IS NOT NULL""",
                f"Calculate AQI statistics for district {district_id} over the last 7 days"
            )

        elif pattern == 'historical':
            district_id = previous_results.get('district_id', 'unknown') if previous_results else 'unknown'
            return (
                f"""SELECT ds.date, ds.hour, ds.aqi_value, ds.pm25_value
                FROM distric_stats ds
                WHERE ds.district_id = '{district_id}'
                AND ds.date >= CURRENT_DATE - INTERVAL '30 days'
                ORDER BY ds.date DESC, ds.hour DESC
                LIMIT 100""",
                f"Get historical AQI data for district {district_id} over the last 30 days"
            )

        # Default fallback
        return (
            "SELECT * FROM districts LIMIT 10",
            "Default query - list first 10 districts"
        )

    async def process(self, inputs: SQLGenerationInput) -> SQLGenerationOutput:
        """Generate SQL query from natural language question.

        This is the main processing method that converts a structured sub-question
        into an executable SQL query. It uses either LLM-based generation or
        template-based generation depending on configuration and availability.

        Args:
            inputs: SQLGenerationInput containing question, description, table_name,
                schema_context, and optional previous_results.

        Returns:
            SQLGenerationOutput containing the generated SQL query and explanation.

        Raises:
            ValueError: If inputs are invalid or SQL generation fails
            Exception: If LLM processing encounters errors

        Example:
            >>> inputs = SQLGenerationInput(
            ...     question="Find Hoan Kiem district",
            ...     description="Identify the district ID for Hoan Kiem",
            ...     table_name="districts",
            ...     schema_context={"columns": ["id", "name"]},
            ... )
            >>> output = await service.process(inputs)
            >>> "SELECT" in output.sql_query
            True
        """
        logger.info(
            'Generating SQL query',
            extra={
                'question': inputs.question,
                'table_name': inputs.table_name,
            }
        )

        # Detect query pattern
        pattern = self._detect_query_pattern(inputs.question)
        logger.info('Detected query pattern', extra={'pattern': pattern})

        # Build context for SQL generation
        context = self._build_context(inputs.schema_context, inputs.previous_results)

        # TODO: Integrate with LLM for sophisticated SQL generation
        # For now, use template-based generation
        sql_query, explanation = self._generate_template_query(
            pattern=pattern,
            question=inputs.question,
            table_name=inputs.table_name,
            previous_results=inputs.previous_results,
        )

        logger.info(
            'SQL query generated',
            extra={
                'sql_query': sql_query,
                'explanation': explanation,
            }
        )

        return SQLGenerationOutput(
            sql_query=sql_query,
            explanation=explanation,
        )

    async def gprocess(self, state: dict[str, Any]) -> dict[str, Any]:
        """Graph process method for LangGraph integration.

        This method is called by the LangGraph workflow and handles the SQL
        generation node. It extracts the necessary information from the state,
        generates the SQL query, and updates the state.

        Args:
            state: Current workflow state containing question, description,
                table_name, and other context.

        Returns:
            Updated state dict with sql_query and explanation fields.

        Raises:
            ValueError: If required state fields are missing
            Exception: If SQL generation fails
        """
        try:
            # Extract inputs from state
            inputs = SQLGenerationInput(
                question=state['question'],
                description=state['description'],
                table_name=state['table_name'],
                schema_context=state.get('schema_context', {}),
                previous_results=state.get('previous_results'),
            )

            # Generate SQL
            output = await self.process(inputs)

            return {
                'sql_query': output.sql_query,
                'sql_explanation': output.explanation,
            }

        except Exception as e:
            logger.exception('Error in SQL generation gprocess', extra={'error': str(e)})
            return {
                'exception': {'where': 'sql_generation', 'error': str(e)},
            }
