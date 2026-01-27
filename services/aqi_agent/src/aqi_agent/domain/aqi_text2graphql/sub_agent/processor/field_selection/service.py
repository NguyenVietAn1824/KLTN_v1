"""
Field Selection Service for KLTN AQI Text2GraphQL system.

Selects which fields to include in GraphQL queries using LiteLLM.
Adapted from sun_assistant Apollo field_selection service.
"""

import json
from typing import Any, Dict, List, Optional, get_type_hints

from aqi_agent.shared.model.schemas import Tables
from base import BaseModel, AsyncBaseService
from lite_llm import CompletionMessage, LiteLLMInput, LiteLLMService, Role
from logger import get_logger

from .prompts import FIELD_SELECTION_SYSTEM_PROMPT, FIELD_SELECTION_USER_PROMPT

logger = get_logger(__name__)


class FieldSelectionInput(BaseModel):
    """Input for field selection service."""
    
    table_name: str
    question: str
    description: str


class FieldSelectionOutput(BaseModel):
    """Output from field selection service."""
    
    fields: Optional[List[Dict[str, Any]]]


class FieldSelectionService(AsyncBaseService):
    """
    Field selection service that determines which fields to include in queries.
    
    Uses LiteLLM with structured output (response_format=TableSchema) to get
    field selections as boolean values.
    """
    
    litellm_service: LiteLLMService
    
    def _build_conversation(
        self,
        schema: str,
        question: str,
        description: str,
    ) -> List[CompletionMessage]:
        """
        Build structured conversation messages for field selection.
        
        Args:
            schema: JSON schema of the table
            question: User's question
            description: Task description
            
        Returns:
            List of conversation messages
        """
        return [
            CompletionMessage(
                role=Role.SYSTEM,
                content=FIELD_SELECTION_SYSTEM_PROMPT,
            ),
            CompletionMessage(
                role=Role.USER,
                content=FIELD_SELECTION_USER_PROMPT.format(
                    question=question,
                    description=description,
                    schema=schema,
                ),
            ),
        ]
    
    async def get_table_model(self, table_name: str) -> Optional[type[BaseModel]]:
        """
        Get the Pydantic model class for a table name.
        
        Args:
            table_name: Name of the table (e.g., 'districts', 'distric_stats')
            
        Returns:
            Model class or None if not found
        """
        try:
            # Get type hints from Tables class
            type_map = get_type_hints(Tables)
            
            # Find matching table
            for field_name, model_class in type_map.items():
                if field_name == table_name:
                    # Extract the actual model from Optional[Model]
                    if hasattr(model_class, '__args__'):
                        # It's Optional[Model], get the Model
                        return model_class.__args__[0]
                    return model_class
            
            logger.warning(f'Table {table_name} not found in Tables schema')
            return None
            
        except Exception as e:
            logger.exception(
                event='Error getting table model',
                extra={'table_name': table_name, 'error': str(e)}
            )
            return None
    
    def _serialize_fields(
        self,
        model: BaseModel,
        prefix: str = '',
    ) -> List[Dict[str, Any]]:
        """
        Recursively flatten a Pydantic model into field metadata.
        
        Converts boolean field values into list of selected fields with paths.
        
        Args:
            model: The field selection model (with true/false values)
            prefix: Parent field path for nested fields
            
        Returns:
            List of field metadata dicts with path, selected, description
        """
        serialized: List[Dict[str, Any]] = []
        
        for field_name, field_info in model.model_fields.items():
            path = f'{prefix}.{field_name}' if prefix else field_name
            value = getattr(model, field_name)
            desc = field_info.description
            
            # Nested model (relationship)
            if isinstance(value, BaseModel):
                serialized.extend(self._serialize_fields(value, path))
                continue
            
            # List of models
            elif isinstance(value, list):
                if value:
                    for idx, item in enumerate(value):
                        item_path = f'{path}[{idx}]'
                        if isinstance(item, BaseModel):
                            serialized.extend(self._serialize_fields(item, item_path))
                        else:
                            serialized.append({
                                'path': item_path,
                                'selected': item,
                                'description': desc,
                            })
                else:
                    # Empty list
                    serialized.append({
                        'path': path,
                        'selected': value,
                        'description': desc,
                    })
                continue
            
            # Primitive value (bool, str, int, etc.)
            serialized.append({
                'path': path,
                'selected': value,
                'description': desc,
            })
        
        return serialized
    
    async def process(self, inputs: FieldSelectionInput) -> FieldSelectionOutput:
        """
        Select relevant fields for a query using LLM.
        
        Uses LiteLLM with response_format=TableModel for structured output.
        
        Args:
            inputs: Contains table_name, question, description
            
        Returns:
            FieldSelectionOutput with selected fields list
        """
        # Get table model
        table_model = await self.get_table_model(inputs.table_name)
        if table_model is None:
            logger.warning(f'No model found for table: {inputs.table_name}')
            return FieldSelectionOutput(fields=None)
        
        # Generate JSON schema
        try:
            schema = table_model.model_json_schema()
            schema['additionalProperties'] = False
            schema_str = json.dumps(schema, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.exception(
                event='Error generating schema',
                extra={'table_name': inputs.table_name, 'error': str(e)}
            )
            return FieldSelectionOutput(fields=None)
        
        # Build conversation
        messages = self._build_conversation(
            schema_str[:4000],  # Limit context length
            inputs.question,
            inputs.description,
        )
        
        # Call LiteLLM with structured output
        try:
            logger.info(
                'Calling LiteLLM for field selection',
                extra={
                    'table_name': inputs.table_name,
                    'question': inputs.question
                }
            )
            
            response = await self.litellm_service.process_async(
                inputs=LiteLLMInput(
                    messages=messages,
                    response_format=table_model,  # CRITICAL: Structured output
                ),
            )
            
            # Parse response into table model
            if isinstance(response.response, BaseModel):
                fields_model = response.response
            else:
                fields_model = table_model(**response.response)
            
            # Serialize into field list
            serialized_fields = self._serialize_fields(fields_model)
            
            logger.info(
                'Field selection completed',
                extra={
                    'table_name': inputs.table_name,
                    'num_fields_selected': sum(
                        1 for f in serialized_fields if f['selected'] is True
                    )
                }
            )
            
            return FieldSelectionOutput(fields=serialized_fields)
            
        except Exception as e:
            logger.exception(
                event='LLM processing error in field selection',
                extra={
                    'table_name': inputs.table_name,
                    'question': inputs.question,
                    'error': str(e)
                },
            )
            return FieldSelectionOutput(fields=None)
