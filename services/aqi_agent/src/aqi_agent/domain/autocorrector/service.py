"""Autocorrector service for SQL query processing and corrections."""
from __future__ import annotations

from base import BaseService
from aqi_agent.domain.autocorrector.models import AutocorrectorInput
from aqi_agent.domain.autocorrector.models import AutocorrectorOutput
from aqi_agent.shared.settings import AutocorrectorSettings
from aqi_agent.shared.tools import PythonExecutor
from logger import get_logger
from redis import Redis  # type: ignore[import-untyped]

from .fuzzy_corrector import FuzzyCorrectorService

logger = get_logger(__name__)


class AutocorrectorService(BaseService):
    """Service for SQL query autocorrection and processing."""

    redis_client: Redis
    settings: AutocorrectorSettings

    @property
    def fuzzy_corrector(self) -> FuzzyCorrectorService:
        return FuzzyCorrectorService(
            redis_client=self.redis_client, settings=self.settings,
        )

    def _process_python_expressions(self, sql_query: str) -> str:
        """Process Python expressions within SQL query."""
        try:
            return PythonExecutor.process_sql_with_python_tags(sql_query)
        except ValueError as e:
            logger.error(f'Python expression processing failed: {e}')
            raise

    def process(self, input: AutocorrectorInput) -> AutocorrectorOutput:
        """
        Process SQL query to handle Python expressions and corrections.

        Pipeline:
        1. Process <python>...</python> expressions
        2. Correct WHERE clause values via fuzzy matching with Redis cache
        """
        try:
            # Step 1: Process Python expressions in SQL query
            corrected_sql = self._process_python_expressions(input.sql_query)

            # Step 2: Correct WHERE clause values using fuzzy matching
            corrected_sql = self.fuzzy_corrector.process(
                AutocorrectorInput(sql_query=corrected_sql),
            ).corrected_sql_query

            return AutocorrectorOutput(corrected_sql_query=corrected_sql)
        except ValueError as e:
            logger.warning(f'SQL correction failed: {e}')
            # Return original query if correction fails
            return AutocorrectorOutput(corrected_sql_query=input.sql_query)
