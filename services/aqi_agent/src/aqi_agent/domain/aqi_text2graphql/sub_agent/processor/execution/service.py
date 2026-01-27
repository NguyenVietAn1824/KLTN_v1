"""
Execution Service for KLTN AQI Text2GraphQL system.

Executes GraphQL queries against Hasura and returns results.
Uses existing HasuraService from infra layer.
"""

from typing import Any, Dict, Optional

from aqi_agent.infra.hasura import HasuraService
from base import BaseModel, BaseService
from logger import get_logger

logger = get_logger(__name__)


class ExecutionInput(BaseModel):
    """Input for execution service."""
    
    query: str  # GraphQL query string


class ExecutionOutput(BaseModel):
    """Output from execution service."""
    
    data: Optional[Dict[str, Any]]
    error: Optional[str] = None


class ExecutionService(BaseService):
    """
    Execution service that runs GraphQL queries against Hasura.
    
    This service wraps the HasuraService from infra layer.
    """
    
    hasura_service: HasuraService
    
    async def execute(self, inputs: ExecutionInput) -> ExecutionOutput:
        """
        Execute a GraphQL query against Hasura.
        
        Args:
            inputs: Contains GraphQL query string
            
        Returns:
            ExecutionOutput with query results or error
        """
        if not inputs.query or not inputs.query.strip():
            logger.warning('Empty query provided for execution')
            return ExecutionOutput(
                data=None,
                error='Empty query'
            )
        
        try:
            logger.info(
                'Executing GraphQL query',
                extra={'query_preview': inputs.query[:200]}
            )
            
            # Execute via HasuraService
            result = await self.hasura_service.execute_query(inputs.query)
            
            # Check for errors in result
            if 'errors' in result:
                error_msg = str(result['errors'])
                logger.error(
                    'GraphQL execution returned errors',
                    extra={
                        'query': inputs.query,
                        'errors': result['errors']
                    }
                )
                return ExecutionOutput(
                    data=result.get('data'),
                    error=error_msg
                )
            
            # Success
            logger.info(
                'Query executed successfully',
                extra={'has_data': 'data' in result}
            )
            
            return ExecutionOutput(
                data=result.get('data'),
                error=None
            )
            
        except Exception as e:
            logger.exception(
                event='Error executing GraphQL query',
                extra={
                    'query': inputs.query,
                    'error': str(e)
                },
            )
            return ExecutionOutput(
                data=None,
                error=f'Execution failed: {str(e)}'
            )
    
    def process(self, inputs: ExecutionInput) -> ExecutionOutput:
        """Process method required by BaseService."""
        return self.execute(inputs)
