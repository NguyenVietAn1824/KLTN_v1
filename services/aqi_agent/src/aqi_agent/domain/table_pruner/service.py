from __future__ import annotations
from typing import Any
from base import BaseService
from base import BaseModel
from lite_llm import LiteLLMService
from opensearch import OpenSearchService
from opensearch import AddDocumentInput
from lite_llm import LiteLLMEmbeddingInput
from aqi_agent.shared.settings.table_pruner import TablePrunerSettings
from logger import get_logger


logger = get_logger(__name__)


class TableIndexerInput(BaseModel):
    index_body: dict[str, Any]
    search_pipeline_body: dict[str, Any]
    mdl: dict[str, Any]


class TableIndexerOutput(BaseModel):
    success: bool
    
class TableIndexerService(BaseService):

    lite_llm: LiteLLMService
    opensearch: OpenSearchService
    settings: TablePrunerSettings


    def create_search_pipeline(self, pipeline_id: str, pipeline_body: dict[str, Any]) -> bool:

        try:
            result = self.opensearch.create_search_pipeline(
                pipeline_id=pipeline_id,
                pipeline_body=pipeline_body,
            )
            if not result:
                logger.warning(f'OpenSearch search pipeline already exists: {pipeline_id}')
                logger.info(f'Created OpenSearch search pipeline: {pipeline_id}')

            return result
        except Exception as e:
            logger.exception(
                'Failed to create OpenSearch search pipeline',
                extra={
                    'pipeline_id': pipeline_id,
                    'pipeline_body': pipeline_body,
                },
            )
            raise e
        
    def create_index(self, index_name: str, index_body: dict[str, Any]) -> bool:
        """
        Create OpenSearch index for storing table descriptions and embeddings.

        Args:
            index_name (str): The name of the OpenSearch index to create.
            index_body (dict[str, Any]): The body of the index configuration.

        Raises:
            e: If the index creation fails.

        Returns:
            bool: True if the index was created successfully, False if it already exists or creation failed.
        """
        try:
            result = self.opensearch.create_index(
                index_name=index_name,
                index_body=index_body,
            )
            if not result:
                logger.warning(f'OpenSearch index already exists: {index_name}')
            logger.info(f'Created OpenSearch index: {index_name}')

            return result
        except Exception as e:
            logger.exception(
                'Failed to create OpenSearch index',
                extra={
                    'index_name': index_name,
                    'index_body': index_body,
                },
            )
            raise e
    
    async def index_tables(self, mdl: dict) -> bool:
        """
        Index table descriptions and embeddings into OpenSearch. For each table in the MDL, generate an embedding for its description and index it along with metadata about the table.

        Args:
            mdl (dict): The MDL containing table models to be indexed.

        Raises:
            e: If embedding generation or indexing fails.

        Returns:
            bool: True if the tables were indexed successfully, False otherwise.
        """
        documents: list[AddDocumentInput] = []
        for model in mdl['models']:
            try:
                text = model['properties']['description']
                embedding_output = await self.lite_llm.embedding_async(
                    inputs=LiteLLMEmbeddingInput(
                        input=text,
                        embedding_model=self.opensearch.settings.embedding_model,
                        encoding_format=self.opensearch.settings.encoding_format,
                        dimensions=self.opensearch.settings.dimensions,
                    ),
                )
                documents.append(
                    AddDocumentInput(
                        text=text,
                        embedding=embedding_output.vector,
                        metadata={
                            'table_name': model['name'],
                            'columns': model['columns'],
                        },
                    ),
                )
            except Exception as e:
                logger.warning(
                    'Failed to generate embedding for table description',
                    extra={
                        'table_model': model,
                        'error': str(e),
                    },
                )

        if not documents:
            logger.warning('No documents to index into OpenSearch')
            return False

        try:
            result = self.opensearch.add_documents(
                documents=documents,
                index_name=self.settings.index_name,
            )
            if not result:
                logger.warning('Documents indexing was not successful')
            logger.info(f'Indexed {len(documents)} table descriptions into OpenSearch')

            return result
        except Exception as e:
            logger.exception(
                'Failed to index table descriptions into OpenSearch',
                extra={
                    'documents': documents,
                    'index_name': self.settings.index_name,
                },
            )
            raise e
    
    async def process(self, inputs: TableIndexerInput) -> TableIndexerOutput:
        """
        Main processing function for the TableIndexerService. This function orchestrates the creation of the OpenSearch index, indexing of table descriptions, and creation of the search pipeline.

        Args:
            inputs (TableIndexerInput): The input data for the table indexing process.

        Returns:
            TableIndexerOutput: The output data for the table indexing process.
        """
        _ = self.create_index(
            index_name=self.settings.index_name,
            index_body=inputs.index_body,
        )

        index_tables_result = await self.index_tables(
            mdl=inputs.mdl,
        )

        _ = self.create_search_pipeline(
            pipeline_id=self.settings.search_pipeline,
            pipeline_body=inputs.search_pipeline_body,
        )

        return TableIndexerOutput(success=index_tables_result)