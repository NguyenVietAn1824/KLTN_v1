"""
NLG (Natural Language Generation) service for AQI Agent.

Converts structured query results into natural Vietnamese language answers.
"""

import json
from typing import Any, Dict

from base import AsyncBaseService
from logger import get_logger
from lite_llm import LiteLLMInput, LiteLLMService
from pydantic import BaseModel, Field

from .prompts import NLG_SYSTEM_PROMPT, NLG_USER_PROMPT

logger = get_logger(__name__)


class NLGInput(BaseModel):
    """Input for NLG service."""
    
    question: str = Field(description="Original user question")
    data: Dict[str, Any] = Field(description="Structured data from queries")
    queries: list = Field(default_factory=list, description="List of executed GraphQL queries")


class NLGOutput(BaseModel):
    """Output from NLG service."""
    
    answer: str = Field(description="Natural language answer in Vietnamese")
    error: str = Field(default='', description="Error message if generation failed")


class NLGService(AsyncBaseService):
    """
    Natural Language Generation service.
    
    Uses LLM to generate natural, conversational Vietnamese answers
    from structured query results.
    """
    
    litellm_service: LiteLLMService
    
    def __init__(self, litellm_service: LiteLLMService):
        """
        Initialize NLG service.
        
        Args:
            litellm_service: LiteLLM service for text generation
        """
        super().__init__(litellm_service=litellm_service)
        logger.info('NLG Service initialized')
    
    async def process(self, inputs: NLGInput) -> NLGOutput:
        """
        Generate natural language answer from structured data.
        
        Args:
            inputs: Contains question, data, and queries
            
        Returns:
            NLGOutput with natural language answer
        """
        try:
            logger.info(
                'Starting NLG generation',
                extra={
                    'question': inputs.question,
                    'num_queries': len(inputs.queries),
                    'has_data': bool(inputs.data)
                }
            )
            
            # Format data for prompt
            data_str = self._format_data(inputs.data)
            queries_str = '\n'.join(f"{i+1}. {q}" for i, q in enumerate(inputs.queries))
            
            # Generate answer using LLM
            user_prompt = NLG_USER_PROMPT.format(
                question=inputs.question,
                data=data_str,
                queries=queries_str
            )
            
            llm_input = LiteLLMInput(
                messages=[
                    {'role': 'system', 'content': NLG_SYSTEM_PROMPT},
                    {'role': 'user', 'content': user_prompt}
                ],
                temperature=0.9,  # Higher temperature for more natural, conversational responses
                max_tokens=1000
            )
            
            response = await self.litellm_service.process_async(llm_input)
            
            # Extract answer from response
            if isinstance(response.response, str):
                answer = response.response.strip()
            else:
                # If it's a BaseModel, try to get content
                answer = getattr(response.response, 'content', str(response.response)).strip()
            
            logger.info(
                'NLG generation completed',
                extra={'answer_length': len(answer)}
            )
            
            return NLGOutput(answer=answer)
            
        except Exception as e:
            logger.exception(
                event='NLG generation error',
                extra={'error': str(e)}
            )
            return NLGOutput(
                answer='Xin lỗi, đã xảy ra lỗi khi tạo câu trả lời.',
                error=str(e)
            )
    
    def _format_data(self, data: Dict[str, Any]) -> str:
        """
        Format structured data for LLM prompt.
        
        Args:
            data: Structured query results
            
        Returns:
            Formatted string representation
        """
        if not data:
            return "Không có dữ liệu"
        
        # Try to format nicely
        try:
            formatted_lines = []
            for table_name, records in data.items():
                if not records:
                    continue
                    
                formatted_lines.append(f"\n**Bảng {table_name}:**")
                
                if isinstance(records, list):
                    formatted_lines.append(f"Số lượng: {len(records)} bản ghi")
                    
                    # Show first 10 records
                    for i, record in enumerate(records[:10], 1):
                        formatted_lines.append(f"{i}. {json.dumps(record, ensure_ascii=False)}")
                    
                    if len(records) > 10:
                        formatted_lines.append(f"... và {len(records) - 10} bản ghi nữa")
                else:
                    formatted_lines.append(json.dumps(records, ensure_ascii=False, indent=2))
            
            return '\n'.join(formatted_lines)
            
        except Exception as e:
            logger.warning(f'Error formatting data: {e}')
            return json.dumps(data, ensure_ascii=False, indent=2)
