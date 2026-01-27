"""
Sub-Agent Service for KLTN AQI Text2GraphQL system.

Orchestrates the text2graphql workflow using LangGraph.
Adapted from sun_assistant Apollo sub_agent service.
"""

from typing import Any, Dict

from base import BaseModel, AsyncBaseService
from langgraph.graph import END, START, StateGraph
from logger import get_logger

from .processor.condition_selection import ConditionSelectionService
from .processor.execution import ExecutionService
from .processor.field_selection import FieldSelectionService
from .processor.query_builder import QueryBuilderService
from .state import SubAgentState

logger = get_logger(__name__)


class SubAgentInput(BaseModel):
    """Input for sub-agent processing."""
    
    question: str
    description: str
    table_name: str


class SubAgentOutput(BaseModel):
    """Output from sub-agent processing."""
    
    question: str
    data: Dict[str, Any]
    query: str
    error: str | None = None


class SubAgentService(AsyncBaseService):
    """
    Sub-agent service that orchestrates text2graphql workflow.
    
    Uses LangGraph to create a state machine with nodes:
    1. field_selection - Select fields using LLM
    2. condition_selection - Generate WHERE/ORDER BY/LIMIT using LLM
    3. query_builder - Build GraphQL string (no LLM)
    4. execution - Execute query via Hasura (no LLM)
    """
    
    field_selection_service: FieldSelectionService
    condition_selection_service: ConditionSelectionService
    query_builder_service: QueryBuilderService
    execution_service: ExecutionService
    
    async def _field_selection_node(self, state: SubAgentState) -> Dict[str, Any]:
        """
        Node: Select fields from table schema.
        
        Uses LLM to determine which fields to include in query.
        """
        logger.info('Executing field_selection node', extra={'table': state['table_name']})
        
        from .processor.field_selection import FieldSelectionInput
        
        result = await self.field_selection_service.process(
            FieldSelectionInput(
                table_name=state['table_name'],
                question=state['question'],
                description=state['description'],
            )
        )
        
        return {'fields': result.fields}
    
    async def _condition_selection_node(self, state: SubAgentState) -> Dict[str, Any]:
        """
        Node: Generate query constraints (WHERE, ORDER BY, LIMIT).
        
        Uses LLM to determine filtering and sorting logic.
        """
        logger.info('Executing condition_selection node')
        
        if not state.get('fields'):
            logger.warning('No fields selected, skipping condition selection')
            return {'conditions': None}
        
        from .processor.condition_selection import ConditionSelectionInput
        
        result = await self.condition_selection_service.process(
            ConditionSelectionInput(
                fields=state['fields'],
                question=state['question'],
                description=state['description'],
            )
        )
        
        return {'conditions': result.conditions}
    
    async def _query_builder_node(self, state: SubAgentState) -> Dict[str, Any]:
        """
        Node: Build GraphQL query string.
        
        Pure string formatting - no LLM.
        """
        logger.info('Executing query_builder node')
        
        if not state.get('fields'):
            logger.error('Cannot build query without fields')
            return {
                'query': '',
                'error': 'No fields selected'
            }
        
        from .processor.query_builder import QueryBuilderInput
        
        result = self.query_builder_service.build_query(
            QueryBuilderInput(
                table_name=state['table_name'],
                fields=state['fields'],
                conditions=state.get('conditions'),
            )
        )
        
        return {'query': result.query}
    
    async def _execution_node(self, state: SubAgentState) -> Dict[str, Any]:
        """
        Node: Execute GraphQL query via Hasura.
        
        No LLM - direct HTTP call.
        """
        logger.info('Executing execution node')
        
        if not state.get('query'):
            logger.error('Cannot execute without query')
            return {
                'data': None,
                'error': 'No query to execute'
            }
        
        from .processor.execution import ExecutionInput
        
        result = await self.execution_service.execute(
            ExecutionInput(query=state['query'])
        )
        
        return {
            'data': result.data,
            'error': result.error
        }
    
    def _build_graph(self) -> StateGraph:
        """
        Build LangGraph workflow.
        
        Flow: START → field_selection → condition_selection → query_builder → execution → END
        """
        workflow = StateGraph(SubAgentState)
        
        # Add nodes
        workflow.add_node('field_selection', self._field_selection_node)
        workflow.add_node('condition_selection', self._condition_selection_node)
        workflow.add_node('query_builder', self._query_builder_node)
        workflow.add_node('execution', self._execution_node)
        
        # Add edges (linear flow)
        workflow.add_edge(START, 'field_selection')
        workflow.add_edge('field_selection', 'condition_selection')
        workflow.add_edge('condition_selection', 'query_builder')
        workflow.add_edge('query_builder', 'execution')
        workflow.add_edge('execution', END)
        
        return workflow.compile()
    
    async def process(self, inputs: SubAgentInput) -> SubAgentOutput:
        """
        Process a sub-question through the complete workflow.
        
        Args:
            inputs: Contains question, description, table_name
            
        Returns:
            SubAgentOutput with query results
        """
        logger.info(
            'Starting sub-agent processing',
            extra={
                'question': inputs.question,
                'table': inputs.table_name
            }
        )
        
        # Build graph
        graph = self._build_graph()
        
        # Initial state
        initial_state: SubAgentState = {
            'question': inputs.question,
            'description': inputs.description,
            'table_name': inputs.table_name,
            'fields': None,
            'conditions': None,
            'query': '',
            'data': None,
            'error': None,
        }
        
        # Execute workflow
        try:
            final_state = await graph.ainvoke(initial_state)
            
            logger.info(
                'Sub-agent processing completed',
                extra={
                    'has_data': final_state.get('data') is not None,
                    'has_error': final_state.get('error') is not None
                }
            )
            
            return SubAgentOutput(
                question=inputs.question,
                data=final_state.get('data') or {},
                query=final_state.get('query', ''),
                error=final_state.get('error'),
            )
            
        except Exception as e:
            logger.exception(
                event='Sub-agent workflow failed',
                extra={
                    'question': inputs.question,
                    'error': str(e)
                }
            )
            return SubAgentOutput(
                question=inputs.question,
                data={},
                query='',
                error=f'Workflow failed: {str(e)}'
            )
