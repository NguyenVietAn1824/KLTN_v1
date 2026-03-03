from __future__ import annotations

from datetime import datetime
from typing import Any

from base import BaseModel
from base import BaseService
from chatwithdb.domain.table_pruner.modules.column_pruner.models import ColumnPrunerResult
from chatwithdb.domain.table_pruner.modules.column_pruner.prompts import COLUMN_SELECTION_SYSTEM_PROMPT
from chatwithdb.domain.table_pruner.modules.column_pruner.prompts import COLUMN_SELECTION_USER_PROMPT
from chatwithdb.shared.settings import TablePrunerSettings
from litellm import CompletionMessage
from litellm import LiteLLMInput
from litellm import LiteLLMService
from litellm import MessageRole
from logger import get_logger

logger = get_logger(__name__)


class ColumnPrunerInput(BaseModel):
    question: str
    retrieved_tables: list[dict[str, Any]]


class ColumnPrunerOutput(BaseModel):
    pruned_schema: str
    column_selection: ColumnPrunerResult


class ColumnPrunerService(BaseService):
    litellm_service: LiteLLMService
    settings: TablePrunerSettings

    def _build_ddl_schema(self, retrieved_tables: list[dict[str, Any]]) -> str:
        """
        Build DDL schema string from retrieved OpenSearch results.

        Args:
            retrieved_tables (list[dict[str, Any]]): List of table results from OpenSearch search

        Returns:
            str: DDL formatted schema string
        """
        ddl_statements = []

        for table_result in retrieved_tables:
            source = table_result.get('_source', {})
            metadata = source.get('metadata', {})
            table_name = metadata.get('table_name', 'unknown_table')
            columns = metadata.get('columns', [])

            if not columns:
                continue

            column_definitions = []
            for col in columns:
                col_name = col.get('name', 'unknown')
                col_type = col.get('type', 'VARCHAR')
                properties = col.get('properties', {})
                description = properties.get('description', '')
                examples = properties.get('example', [])

                col_def = f'    {col_name} {col_type}'

                comments = []
                if description:
                    comments.append(description)
                if examples:
                    example_str = ', '.join(str(e) for e in examples)
                    comments.append(f'Example: {example_str}')

                if comments:
                    col_def += f"  -- {'; '.join(comments)}"

                column_definitions.append(col_def)

            ddl = f'CREATE TABLE {table_name} (\n'
            ddl += ',\n'.join(column_definitions)
            ddl += '\n);'

            ddl_statements.append(ddl)

        return '\n\n'.join(ddl_statements)

    def _build_pruned_schema(
        self,
        retrieved_tables: list[dict[str, Any]],
        column_selection: ColumnPrunerResult,
    ) -> str:
        """
        Build pruned DDL schema with only selected columns.

        Args:
            retrieved_tables (list[dict[str, Any]]): List of table results from OpenSearch search
            column_selection (ColumnPrunerResult): Selected columns from LLM

        Returns:
            str: DDL formatted schema string with only selected columns
        """
        selection_map = {
            result.table_name: result.columns
            for result in column_selection.results
        }

        ddl_statements = []

        for table_result in retrieved_tables:
            source = table_result.get('_source', {})
            metadata = source.get('metadata', {})
            table_name = metadata.get('table_name', 'unknown_table')
            columns = metadata.get('columns', [])

            if table_name not in selection_map:
                continue

            selected_column_names = selection_map[table_name]

            if not selected_column_names:
                continue

            column_definitions = []
            for col in columns:
                col_name = col.get('name', 'unknown')

                if col_name not in selected_column_names:
                    continue

                col_type = col.get('type', 'VARCHAR')
                properties = col.get('properties', {})
                description = properties.get('description', '')
                examples = properties.get('example', [])

                col_def = f'    {col_name} {col_type}'

                comments = []
                if description:
                    comments.append(description)
                if examples:
                    example_str = ', '.join(str(e) for e in examples)
                    comments.append(f'Example: {example_str}')

                if comments:
                    col_def += f"  -- {'; '.join(comments)}"

                column_definitions.append(col_def)

            column_definitions.append('    createdAt DATETIME  -- Timestamp when the record was created')

            if column_definitions:
                ddl = f'CREATE TABLE {table_name} (\n'
                ddl += ',\n'.join(column_definitions)
                ddl += '\n);'
                ddl_statements.append(ddl)

        return '\n\n'.join(ddl_statements)

    async def process(self, inputs: ColumnPrunerInput) -> ColumnPrunerOutput:
        """
        Process column pruning for retrieved tables.

        Args:
            inputs (ColumnPrunerInput): ColumnPrunerInput containing question and retrieved tables

        Returns:
            ColumnPrunerOutput: ColumnPrunerOutput with pruned schema and column selection details
        """
        try:
            schema = self._build_ddl_schema(inputs.retrieved_tables)
        except Exception as e:
            logger.exception(
                'Failed to build DDL schema from retrieved tables',
                extra={
                    'question': inputs.question,
                    'retrieved_tables': inputs.retrieved_tables,
                    'error': str(e),
                },
            )
            raise e

        if not schema:
            logger.warning(
                'No schema built from retrieved tables',
                extra={'question': inputs.question},
            )
            return ColumnPrunerOutput(
                pruned_schema='',
                column_selection=ColumnPrunerResult(results=[]),
            )

        try:
            llm_output = await self.litellm_service.process_async(
                inputs=LiteLLMInput(
                    message=[
                        CompletionMessage(
                            role=MessageRole.SYSTEM,
                            content=COLUMN_SELECTION_SYSTEM_PROMPT,
                        ),
                        CompletionMessage(
                            role=MessageRole.USER,
                            content=COLUMN_SELECTION_USER_PROMPT.format(
                                schema=schema,
                                question=inputs.question,
                                current_date=datetime.now().strftime('%Y-%m-%d %H:%M'),
                            ),
                        ),
                    ],
                    return_type=ColumnPrunerResult,
                    frequency_penalty=self.settings.frequency_penalty,
                    n=self.settings.n,
                    model=self.settings.model,
                    presence_penalty=self.settings.presence_penalty,
                ),
            )

            if isinstance(llm_output.response, ColumnPrunerResult):
                column_selection = llm_output.response
            else:
                logger.exception(
                    'Unexpected response type from LLM',
                    extra={
                        'response_type': type(llm_output.response).__name__,
                        'response': str(llm_output.response),
                    },
                )
                raise ValueError(f'Expected ColumnPrunerResult, got {type(llm_output.response).__name__}')

            pruned_schema = self._build_pruned_schema(
                retrieved_tables=inputs.retrieved_tables,
                column_selection=column_selection,
            )

            return ColumnPrunerOutput(
                pruned_schema=pruned_schema,
                column_selection=column_selection,
            )

        except Exception as e:
            logger.exception(
                'Failed to prune columns using LLM',
                extra={
                    'question': inputs.question,
                    'schema_length': len(schema),
                    'error': str(e),
                },
            )
            raise e
