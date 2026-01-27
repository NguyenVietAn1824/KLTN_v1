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
    
    async def gprocess(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Graph process method for LangGraph integration.
        
        Executes a single sub-question from the current task in shared_memory.
        Updates the sub-question's data and query fields directly.
        
        Args:
            state: Graph state containing shared_memory, _task_idx
            
        Returns:
            Updated state with modified shared_memory
        """
        shared_memory = state.get('shared_memory')
        task_idx = state.get('_task_idx', 1)
        
        if not shared_memory:
            logger.error('No shared_memory in state')
            return {
                'exception': {
                    'where': 'sub_agent',
                    'error': 'No shared_memory found',
                }
            }
        
        # Get current task
        if task_idx == 1:
            current_task = shared_memory.first_task
        elif task_idx == 2 and shared_memory.second_task:
            current_task = shared_memory.second_task
        else:
            logger.warning(
                'Invalid task_idx or no second_task',
                extra={'task_idx': task_idx}
            )
            return {}
        
        # Process all sub-questions in parallel
        import asyncio
        
        async def process_sub_question(sq_idx: int):
            """Process a single sub-question."""
            sub_q = current_task.sub_questions[sq_idx]
            
            logger.info(
                'Processing sub-question',
                extra={
                    'task_idx': task_idx,
                    'sq_idx': sq_idx,
                    'question': sub_q.question,
                    'table': sub_q.table_name,
                }
            )
            
            try:
                result = await self.process(
                    SubAgentInput(
                        question=sub_q.question,
                        description=sub_q.description,
                        table_name=sub_q.table_name,
                    )
                )
                
                # Update sub-question in-place
                sub_q.data = result.data
                sub_q.query = result.query
                
                if result.error:
                    logger.warning(
                        'Sub-question failed',
                        extra={
                            'sq_idx': sq_idx,
                            'error': result.error,
                        }
                    )
                
                return True
                
            except Exception as e:
                logger.exception(
                    event='Sub-question processing error',
                    extra={
                        'sq_idx': sq_idx,
                        'question': sub_q.question,
                        'error': str(e),
                    }
                )
                sub_q.data = {}
                sub_q.query = ''
                return False
        
        # Execute all sub-questions in parallel
        try:
            num_sqs = len(current_task.sub_questions)
            logger.info(
                'Starting parallel sub-question processing',
                extra={
                    'task_idx': task_idx,
                    'num_sub_questions': num_sqs,
                }
            )
            
            await asyncio.gather(
                *[process_sub_question(i) for i in range(num_sqs)]
            )
            
            logger.info(
                'Completed parallel sub-question processing',
                extra={'task_idx': task_idx}
            )
            
            return {
                'shared_memory': shared_memory,
                '_task_idx': task_idx + 1,  # Increment for next iteration
            }
            
        except Exception as e:
            logger.exception(
                event='Parallel processing failed',
                extra={'task_idx': task_idx, 'error': str(e)}
            )
            return {
                'exception': {
                    'where': 'sub_agent',
                    'error': str(e),
                }
            }
