"""
AQI Agent Application Service - Updated for Apollo architecture.

Main orchestrator following Apollo's task-based pattern with LangGraph.
Uses StateGraph to manage planning → sub_agent execution flow.
"""

from typing import Any, Dict, List
from functools import cached_property
from easydict import EasyDict
from langchain_core.runnables import RunnableLambda
from langgraph.graph import END, START, StateGraph

from aqi_agent.domain.aqi_text2graphql.planning import PlanningService
from aqi_agent.domain.aqi_text2graphql.sub_agent import SubAgentService
from aqi_agent.domain.nlg import NLGInput, NLGService
from aqi_agent.shared.state import AQIAgentState
from base import BaseModel, BaseService
from logger import get_logger

logger = get_logger(__name__)


class AQIAgentInput(BaseModel):
    """Input for AQI Agent service."""
    
    question: str  # User's natural language question


class AQIAgentOutput(BaseModel):
    """Output from AQI Agent service."""
    
    answer: str  # Natural language answer
    data: Dict[str, Any]  # Raw query results
    graphql_queries: List[str]  # Executed GraphQL queries
    error: str | None = None


class AQIAgentService(BaseService):
    """
    Main AQI Agent service following Apollo architecture with LangGraph.
    
    Workflow (StateGraph):
    1. planning: Generate TodoList with first_task and optional second_task
    2. sub_agent: Execute current task's sub-questions in parallel
    3. Loop back to sub_agent if second_task exists
    4. NLG: Generate natural language answer from results
    
    State Management:
    - shared_memory: TodoList containing all tasks and their results
    - _task_idx: Current task being processed (1 or 2)
    - _task_number: Total number of tasks (1 or 2)
    """
    
    planning_service: PlanningService
    sub_agent_service: SubAgentService
    nlg_service: NLGService
    
    @property
    def nodes(self) -> EasyDict:
        """Graph node mapping."""
        return EasyDict(
            {
                'planning': self.planning_service.gprocess,
                'sub_agent': self.sub_agent_service.gprocess,
            },
        )
    
    @cached_property
    def base_graph(self):
        """
        Compile and cache the LangGraph workflow.
        
        Graph Architecture:
            START → planning → sub_agent ──┬─(more tasks)─▶ sub_agent
                                           └─(done)─▶ END
        
        Node Functions:
            - planning: Generates TodoList and sets up task tracking
            - sub_agent: Processes all sub-questions in current task (parallel)
        
        Loop Control:
            The sub_agent node increments _task_idx. The conditional edge
            checks if _task_idx <= _task_number to determine looping.
        """
        graph = StateGraph(AQIAgentState)
        
        # Add nodes
        for key, tool in self.nodes.items():
            graph.add_node(key, tool)
        
        # Add edges
        graph.add_edge(START, 'planning')
        graph.add_edge('planning', 'sub_agent')
        
        # Conditional looping for sub_agent
        def _loop_or_end(state: AQIAgentState) -> str:
            """Continue loop if more tasks, else end."""
            task_idx = state.get('_task_idx', 1)
            task_number = state.get('_task_number', 1)
            
            # Check if there are more tasks to process
            # _task_idx is already incremented by sub_agent
            if task_idx <= task_number:
                logger.info(
                    'Looping to next task',
                    extra={'task_idx': task_idx, 'task_number': task_number}
                )
                return 'more'
            else:
                logger.info(
                    'All tasks completed',
                    extra={'task_idx': task_idx, 'task_number': task_number}
                )
                return 'end'
        
        graph.add_conditional_edges(
            'sub_agent',
            _loop_or_end,
            {
                'more': 'sub_agent',
                'end': END,
            },
        )
        
        return graph.compile()
    
    def _merge_data(self, all_data: Dict[str, Any], new_data: Dict[str, Any]) -> None:
        """
        Merge new data into all_data, appending arrays instead of overwriting.
        
        Args:
            all_data: Accumulated data dictionary (modified in place)
            new_data: New data to merge in
        """
        for table_name, records in new_data.items():
            if table_name not in all_data:
                all_data[table_name] = records
            else:
                # If both are lists, append
                if isinstance(all_data[table_name], list) and isinstance(records, list):
                    all_data[table_name].extend(records)
                # If both are dicts, merge recursively
                elif isinstance(all_data[table_name], dict) and isinstance(records, dict):
                    all_data[table_name].update(records)
                # Otherwise, replace
                else:
                    all_data[table_name] = records
    
    def _get_table_descriptions(self) -> Dict[str, str]:
        """Get available table descriptions for planning context."""
        return {
            'distric_stats': 'PRIMARY TABLE for ALL AQI queries! Contains current & historical AQI values (date, hour, aqi_value, pm25_value, district_id)',
            'districts': 'District metadata ONLY (id, name, province_id, normalized_name) - DOES NOT contain AQI values!',
            'air_component': 'Detailed pollutant measurements (PM2.5, PM10, O3, NO2, SO2, CO)',
            'provinces': 'Province-level administrative data',
        }
    
    def _format_answer_fallback(
        self,
        all_data: Dict[str, Any],
    ) -> str:
        """
        Fallback answer formatter when NLG fails.
        
        Args:
            all_data: Merged data from all sub-questions
            
        Returns:
            Simple formatted answer string
        """
        if not all_data:
            return "Tôi không tìm thấy dữ liệu để trả lời câu hỏi của bạn."
        
        answer_parts = []
        
        for table_name, records in all_data.items():
            if not records or not isinstance(records, list):
                continue
            
            answer_parts.append(f"\n**Dữ liệu từ {table_name}:**")
            answer_parts.append(f"Tìm thấy {len(records)} kết quả:")
            
            # Format first few records
            for record in records[:5]:
                if 'aqi_value' in record:
                    # AQI data from distric_stats
                    district_info = record.get('district', {})
                    if isinstance(district_info, dict) and 'name' in district_info:
                        district_name = district_info['name']
                    else:
                        district_name = f"ID {record.get('district_id', 'N/A')}"
                    
                    answer_parts.append(
                        f"  - {district_name}: "
                        f"AQI {record.get('aqi_value')} "
                        f"({record.get('date', 'N/A')} {record.get('hour', 'N/A')}h)"
                    )
                elif 'name' in record and 'id' in record:
                    # District data
                    answer_parts.append(f"  - {record['name']} (ID: {record['id']})")
                elif 'pm25' in record or 'pm10' in record:
                    # Air component data
                    components = []
                    if 'pm25' in record:
                        components.append(f"PM2.5: {record['pm25']}μg/m³")
                    if 'pm10' in record:
                        components.append(f"PM10: {record['pm10']}μg/m³")
                    answer_parts.append(f"  - {', '.join(components)}")
                else:
                    # Generic format
                    answer_parts.append(f"  - {record}")
            
            if len(records) > 5:
                answer_parts.append(f"  ... và {len(records) - 5} kết quả khác")
        
        if not answer_parts:
            return "Tôi tìm thấy dữ liệu nhưng không thể định dạng được."
        
        return '\n'.join(answer_parts)
    
    async def process(self, inputs: AQIAgentInput) -> AQIAgentOutput:
        """
        Process user question through complete Apollo-style workflow using LangGraph.
        
        Args:
            inputs: Contains user's question
            
        Returns:
            AQIAgentOutput with answer, data, queries
        """
        import time
        
        start_time = time.time()
        logger.info(
            'Starting AQI Agent processing',
            extra={'question': inputs.question}
        )
        
        # Get table descriptions for planning context
        context_schema = self._get_table_descriptions()
        
        # Create initial state
        initial_state: AQIAgentState = {
            'raw_question': inputs.question,
            'context_schema': context_schema,
            'shared_memory': None,
            '_task_number': 0,
            '_task_idx': 1,
            'exception': None,
            'response_time': 0.0,
            'final_answer': None,
            'requires_human_intervention': False,
            'clarification_question': None,
        }
        
        # Execute graph
        try:
            logger.info('Executing graph workflow')
            graph = self.base_graph
            final_state: AQIAgentState = await graph.ainvoke(initial_state)
            
            logger.info(
                'Graph execution completed',
                extra={
                    'has_exception': final_state.get('exception') is not None,
                    'has_shared_memory': final_state.get('shared_memory') is not None,
                }
            )
            
            # Check for exceptions
            if final_state.get('exception'):
                error = final_state['exception']
                logger.error(
                    'Graph execution failed',
                    extra={'error': error}
                )
                return AQIAgentOutput(
                    answer=f"Lỗi xử lý: {error.get('error', 'Unknown error')}",
                    data={},
                    graphql_queries=[],
                    error=f"{error.get('where', 'unknown')}: {error.get('error', 'Unknown error')}"
                )
            
            shared_memory = final_state.get('shared_memory')
            if not shared_memory:
                logger.warning('No shared_memory in final state')
                return AQIAgentOutput(
                    answer="Không thể xử lý câu hỏi của bạn.",
                    data={},
                    graphql_queries=[],
                    error="No shared_memory generated"
                )
            
        except Exception as e:
            logger.exception(
                event='Graph execution failed',
                extra={'question': inputs.question, 'error': str(e)}
            )
            return AQIAgentOutput(
                answer=f"Lỗi hệ thống: {str(e)}",
                data={},
                graphql_queries=[],
                error=f"Graph execution error: {str(e)}"
            )
        
        # Extract results from shared_memory
        all_data = {}
        all_queries = []
        
        try:
            # Process first_task results
            for sq in shared_memory.first_task.sub_questions:
                if sq.data:
                    self._merge_data(all_data, sq.data)
                if sq.query:
                    all_queries.append(sq.query)
            
            # Process second_task results if exists
            if shared_memory.second_task:
                for sq in shared_memory.second_task.sub_questions:
                    if sq.data:
                        self._merge_data(all_data, sq.data)
                    if sq.query:
                        all_queries.append(sq.query)
            
            logger.info(
                'Results extracted from shared_memory',
                extra={
                    'num_queries': len(all_queries),
                    'num_tables': len(all_data),
                }
            )
            
        except Exception as e:
            logger.exception(
                event='Failed to extract results from shared_memory',
                extra={'error': str(e)}
            )
            return AQIAgentOutput(
                answer="Không thể trích xuất kết quả.",
                data={},
                graphql_queries=[],
                error=f"Result extraction failed: {str(e)}"
            )
        
        # Generate natural language answer using NLG
        try:
            logger.info('Starting NLG generation')
            
            nlg_result = await self.nlg_service.process(
                NLGInput(
                    question=inputs.question,
                    data=all_data,
                    queries=all_queries
                )
            )
            
            final_answer = nlg_result.answer if not nlg_result.error else self._format_answer_fallback(all_data)
            
            if nlg_result.error:
                logger.warning(
                    'NLG failed, using fallback formatting',
                    extra={'error': nlg_result.error}
                )
            
        except Exception as e:
            logger.exception(
                event='NLG failed',
                extra={'error': str(e)}
            )
            final_answer = self._format_answer_fallback(all_data)
        
        response_time = time.time() - start_time
        
        logger.info(
            'AQI Agent processing completed',
            extra={
                'question': inputs.question,
                'response_time': response_time,
                'num_queries': len(all_queries),
                'answer_length': len(final_answer),
            }
        )
        
        return AQIAgentOutput(
            answer=final_answer,
            data=all_data,
            graphql_queries=all_queries,
            error=None
        )
