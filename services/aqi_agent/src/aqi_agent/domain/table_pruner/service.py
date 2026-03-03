from __future__ import annotations

from typing import Any

from base import BaseModel
from base import BaseService
from aqi_agent.domain.table_pruner.modules.column_pruner import ColumnPrunerInput
from aqi_agent.domain.table_pruner.modules.column_pruner import ColumnPrunerService
from aqi_agent.domain.table_pruner.modules.column_pruner.models import ColumnPrunerResult
from aqi_agent.domain.table_pruner.modules.table_indexer import TableIndexerInput
from aqi_agent.domain.table_pruner.modules.table_indexer import TableIndexerService
from aqi_agent.domain.table_pruner.modules.table_retrieval import TableRetrievalInput
from aqi_agent.domain.table_pruner.modules.table_retrieval import TableRetrievalService
from aqi_agent.shared.models.state import ChatwithDBState
from aqi_agent.shared.models.state import TablePrunerState
from aqi_agent.shared.settings import TablePrunerSettings
from lite_llm import LiteLLMService
from logger import get_logger
from opensearch import OpenSearchService

logger = get_logger(__name__)


class TablePrunerInput(BaseModel):
    question: str


class TablePrunerOutput(BaseModel):
    pruned_schema: str
    retrieved_tables: list[dict[str, Any]]
    column_selection: ColumnPrunerResult


class TablePrunerIndexInput(BaseModel):
    index_body: dict[str, Any]
    search_pipeline_body: dict[str, Any]
    mdl: dict[str, Any]


class TablePrunerService(BaseService):
    opensearch_service: OpenSearchService
    litellm_service: LiteLLMService
    table_pruner_settings: TablePrunerSettings

    _table_indexer: TableIndexerService | None = None
    _table_retrieval: TableRetrievalService | None = None
    _column_pruner: ColumnPrunerService | None = None

    @property
    def table_indexer(self) -> TableIndexerService:
        if self._table_indexer is None:
            self._table_indexer = TableIndexerService(
                opensearch_service=self.opensearch_service,
                litellm_service=self.litellm_service,
                settings=self.table_pruner_settings,
            )
        return self._table_indexer

    @property
    def table_retrieval(self) -> TableRetrievalService:
        if self._table_retrieval is None:
            self._table_retrieval = TableRetrievalService(
                opensearch_service=self.opensearch_service,
                litellm_service=self.litellm_service,
                settings=self.table_pruner_settings,
            )
        return self._table_retrieval

    @property
    def column_pruner(self) -> ColumnPrunerService:
        if self._column_pruner is None:
            self._column_pruner = ColumnPrunerService(
                litellm_service=self.litellm_service,
                settings=self.table_pruner_settings,
            )
        return self._column_pruner

    async def index_tables(self, inputs: TablePrunerIndexInput) -> bool:
        """
        Index table descriptions into OpenSearch for later retrieval.

        Args:
            inputs (TablePrunerIndexInput): TablePrunerIndexInput containing index configuration and MDL

        Returns:
            bool: True if indexing was successful
        """
        logger.info('Starting table indexing process')

        result = await self.table_indexer.process(
            inputs=TableIndexerInput(
                index_body=inputs.index_body,
                search_pipeline_body=inputs.search_pipeline_body,
                mdl=inputs.mdl,
            ),
        )

        logger.info(f'Table indexing completed: {result.success}')
        return result.success

    async def process(self, inputs: TablePrunerInput) -> TablePrunerOutput:
        """
        Process the table pruning pipeline:
        1. Retrieve relevant tables from OpenSearch using hybrid search
        2. Prune columns using LLM to select only relevant columns

        Args:
            inputs (TablePrunerInput): TablePrunerInput containing the user question

        Returns:
            TablePrunerOutput: TablePrunerOutput with pruned schema and selection details
        """
        logger.info(
            'Starting table pruning pipeline',
            extra={'question': inputs.question},
        )

        # Step 1: Retrieve relevant tables
        logger.info('Retrieving relevant tables from OpenSearch')
        retrieval_output = await self.table_retrieval.process(
            inputs=TableRetrievalInput(query=inputs.question),
        )

        if not retrieval_output.results:
            logger.warning(
                'No tables retrieved from OpenSearch',
                extra={'question': inputs.question},
            )
            return TablePrunerOutput(
                pruned_schema='',
                retrieved_tables=[],
                column_selection=ColumnPrunerResult(results=[]),
            )

        logger.info(
            f'Retrieved {len(retrieval_output.results)} tables',
            extra={
                'question': inputs.question,
                'table_count': len(retrieval_output.results),
            },
        )

        # Step 2: Prune columns using LLM
        logger.info('Pruning columns using LLM')
        pruner_output = await self.column_pruner.process(
            inputs=ColumnPrunerInput(
                question=inputs.question,
                retrieved_tables=retrieval_output.results,
            ),
        )

        logger.info(
            'Table pruning pipeline completed',
            extra={
                'question': inputs.question,
                'pruned_schema': pruner_output.pruned_schema,
            },
        )

        return TablePrunerOutput(
            pruned_schema=pruner_output.pruned_schema,
            retrieved_tables=retrieval_output.results,
            column_selection=pruner_output.column_selection,
        )

    async def gprocess(self, state: ChatwithDBState) -> dict:
        """
        Graph processing method for table pruner.
        This method is designed to be invoked as part of a state graph execution.
        It extracts necessary information from the input state, performs table pruning,
        and returns the updated state with pruned schema and column selection details.
        Args:
            state: The input state containing conversation_id and other relevant information.
        Returns:
            Updated state dictionary with table pruning results.
        """
        logger.info('Starting table pruner with state: ', extra={'state': state})
        try:
            inputs = TablePrunerInput(question=state.get('rephrased_state', {}).get('rephrased_main_question', ''))
            output = await self.process(inputs)
        except Exception as e:
            logger.exception('Error in TablePrunerService: ', extra={'error': str(e)})
            return {
                'table_pruner_state': TablePrunerState(
                    pruned_schema='',
                    retrieved_tables=[],
                    column_selection=[],
                ),
            }
        return {
            'table_pruner_state': TablePrunerState(
                pruned_schema=output.pruned_schema,
                retrieved_tables=output.retrieved_tables,
                column_selection=[r.model_dump() for r in output.column_selection.results],
            ),
        }
