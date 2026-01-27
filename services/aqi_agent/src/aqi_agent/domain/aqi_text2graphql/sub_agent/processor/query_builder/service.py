"""
Query Builder Service for KLTN AQI Text2GraphQL system.

Builds GraphQL query strings from field selections and query constraints.
This service does NOT use LLM - it's pure string formatting logic.
Adapted from sun_assistant Apollo query_builder.
"""

from typing import Any, Dict, List, Optional

from aqi_agent.shared.model import BoolAnd, BoolExpr, BoolNot, BoolOr, Condition, QueryConstraints
from base import BaseModel, BaseService
from logger import get_logger

logger = get_logger(__name__)


class QueryBuilderInput(BaseModel):
    """Input for query builder service."""
    
    table_name: str
    fields: List[Dict[str, Any]]  # Selected fields with paths
    conditions: Optional[QueryConstraints]


class QueryBuilderOutput(BaseModel):
    """Output from query builder service."""
    
    query: str  # GraphQL query string


class QueryBuilderService(BaseService):
    """
    Query builder service that converts selections into GraphQL queries.
    
    This is a pure string formatting service - NO LLM involved.
    Follows Hasura GraphQL syntax.
    """
    
    def _build_field_selection(self, fields: List[Dict[str, Any]]) -> str:
        """
        Build GraphQL field selection from field list.
        
        Converts flat field list with paths into nested GraphQL structure.
        
        Args:
            fields: List of field dicts with 'path', 'selected', 'description'
            
        Returns:
            GraphQL field selection string
            
        Example:
            Input: [
                {'path': 'id', 'selected': True},
                {'path': 'name', 'selected': True},
                {'path': 'district.name', 'selected': True},
                {'path': 'district.id', 'selected': True}
            ]
            Output: "id name district { id name }"
        """
        # Filter only selected fields
        selected = [f['path'] for f in fields if f.get('selected') is True]
        
        if not selected:
            return ''
        
        # Build nested structure
        nested_fields = {}
        simple_fields = []
        
        for path in selected:
            if '.' not in path:
                # Simple field
                simple_fields.append(path)
            else:
                # Nested field - group by parent
                parts = path.split('.', 1)  # Split only on first dot
                parent = parts[0]
                child = parts[1]
                
                if parent not in nested_fields:
                    nested_fields[parent] = []
                nested_fields[parent].append(child)
        
        # Build output
        field_parts = simple_fields.copy()
        
        # Add nested fields
        for parent, children in nested_fields.items():
            # Recursively handle nested children
            nested_str = self._format_nested_fields(children)
            field_parts.append(f'{parent} {{ {nested_str} }}')
        
        return ' '.join(field_parts)
    
    def _format_nested_fields(self, fields: list) -> str:
        """
        Recursively format nested fields.
        
        Args:
            fields: List of field paths (may contain dots for deeper nesting)
            
        Returns:
            Formatted nested field string
        """
        nested_fields = {}
        simple_fields = []
        
        for field in fields:
            if '.' not in field:
                simple_fields.append(field)
            else:
                parts = field.split('.', 1)
                parent = parts[0]
                child = parts[1]
                
                if parent not in nested_fields:
                    nested_fields[parent] = []
                nested_fields[parent].append(child)
        
        # Build output
        parts = simple_fields.copy()
        
        for parent, children in nested_fields.items():
            nested_str = self._format_nested_fields(children)
            parts.append(f'{parent} {{ {nested_str} }}')
        
        return ' '.join(parts)
    
    def _format_condition(self, cond: Condition) -> str:
        """
        Format a single Condition into Hasura GraphQL syntax.
        Supports nested relationship filters.
        
        Args:
            cond: Condition with field, op, value, and optional nested
            
        Returns:
            GraphQL condition string
            
        Examples:
            Simple: Condition(field='aqi_value', op='_gt', value=100)
            Output: "aqi_value: {_gt: 100}"
            
            Nested: Condition(field='district', nested=Condition(field='name', op='_ilike', value='%Ba Đình%'))
            Output: "district: {name: {_ilike: \"%Ba Đình%\"}}"
        """
        field = cond.field
        
        # Handle nested relationship filter
        if cond.nested:
            nested_str = self._format_condition(cond.nested)
            return f'{field}: {{{nested_str}}}'
        
        # Handle regular condition
        if cond.op is None or cond.value is None:
            logger.warning(f'Condition missing op or value: {cond}')
            return ''
            
        op = cond.op.value  # Get enum value like "_gt"
        value = cond.value
        
        # Format value based on type
        if value is None:
            formatted_value = 'null'
        elif isinstance(value, bool):
            formatted_value = 'true' if value else 'false'
        elif isinstance(value, str):
            # Escape quotes
            formatted_value = f'"{value}"'
        elif isinstance(value, list):
            # Array
            formatted_items = []
            for v in value:
                if isinstance(v, str):
                    formatted_items.append(f'"{v}"')
                else:
                    formatted_items.append(str(v))
            formatted_value = f'[{", ".join(formatted_items)}]'
        else:
            formatted_value = str(value)
        
        return f'{field}: {{{op}: {formatted_value}}}'
    
    def _format_bool_expr(self, expr: BoolExpr) -> str:
        """
        Recursively format a BoolExpr into Hasura GraphQL syntax.
        
        Args:
            expr: BoolExpr (Condition, BoolAnd, BoolOr, BoolNot)
            
        Returns:
            GraphQL where clause string
        """
        if isinstance(expr, Condition):
            return self._format_condition(expr)
        
        elif isinstance(expr, BoolAnd):
            # _and: [{cond1}, {cond2}]
            formatted_conditions = [
                f'{{{self._format_bool_expr(c)}}}'
                for c in expr.and_
            ]
            return f'_and: [{", ".join(formatted_conditions)}]'
        
        elif isinstance(expr, BoolOr):
            # _or: [{cond1}, {cond2}]
            formatted_conditions = [
                f'{{{self._format_bool_expr(c)}}}'
                for c in expr.or_
            ]
            return f'_or: [{", ".join(formatted_conditions)}]'
        
        elif isinstance(expr, BoolNot):
            # _not: {cond}
            return f'_not: {{{self._format_bool_expr(expr.not_)}}}'
        
        else:
            logger.warning(f'Unknown BoolExpr type: {type(expr)}')
            return ''
    
    def _build_where_clause(self, conditions: Optional[QueryConstraints]) -> str:
        """
        Build WHERE clause from QueryConstraints.
        
        Args:
            conditions: QueryConstraints with where/order_by/limit
            
        Returns:
            GraphQL where argument string
        """
        if not conditions or not conditions.where:
            return ''
        
        where_expr = self._format_bool_expr(conditions.where)
        return f'where: {{{where_expr}}}'
    
    def _build_order_by_clause(self, conditions: Optional[QueryConstraints]) -> str:
        """
        Build ORDER BY clause from QueryConstraints.
        
        Args:
            conditions: QueryConstraints with order_by
            
        Returns:
            GraphQL order_by argument string
        """
        if not conditions or not conditions.order_by:
            return ''
        
        order_items = []
        for item in conditions.order_by:
            order_items.append(f'{{{item.field}: {item.dir}}}')
        
        return f'order_by: [{", ".join(order_items)}]'
    
    def _build_limit_clause(self, conditions: Optional[QueryConstraints]) -> str:
        """
        Build LIMIT clause from QueryConstraints.
        
        Args:
            conditions: QueryConstraints with limit
            
        Returns:
            GraphQL limit argument string
        """
        if not conditions or conditions.limit is None:
            return ''
        
        return f'limit: {conditions.limit}'
    
    def _build_offset_clause(self, conditions: Optional[QueryConstraints]) -> str:
        """
        Build OFFSET clause from QueryConstraints.
        
        Args:
            conditions: QueryConstraints with offset
            
        Returns:
            GraphQL offset argument string
        """
        if not conditions or conditions.offset is None:
            return ''
        
        return f'offset: {conditions.offset}'
    
    def build_query(self, inputs: QueryBuilderInput) -> QueryBuilderOutput:
        """
        Build complete GraphQL query string.
        
        Args:
            inputs: Contains table_name, fields, conditions
            
        Returns:
            QueryBuilderOutput with GraphQL query string
        """
        table_name = inputs.table_name
        
        # Build field selection
        field_selection = self._build_field_selection(inputs.fields)
        if not field_selection:
            logger.warning(f'No fields selected for table {table_name}')
            field_selection = 'id'  # Fallback to id
        
        # Build query arguments
        args = []
        
        where_clause = self._build_where_clause(inputs.conditions)
        if where_clause:
            args.append(where_clause)
        
        order_by_clause = self._build_order_by_clause(inputs.conditions)
        if order_by_clause:
            args.append(order_by_clause)
        
        limit_clause = self._build_limit_clause(inputs.conditions)
        if limit_clause:
            args.append(limit_clause)
        
        offset_clause = self._build_offset_clause(inputs.conditions)
        if offset_clause:
            args.append(offset_clause)
        
        # Combine into query
        args_str = ', '.join(args) if args else ''
        
        if args_str:
            query = f'''query {{
  {table_name}({args_str}) {{
    {field_selection}
  }}
}}'''
        else:
            query = f'''query {{
  {table_name} {{
    {field_selection}
  }}
}}'''
        
        logger.info(
            'Query built successfully',
            extra={
                'table_name': table_name,
                'num_fields': len([f for f in inputs.fields if f.get('selected')]),
                'has_where': bool(where_clause),
                'has_order_by': bool(order_by_clause),
                'has_limit': bool(limit_clause),
            }
        )
        
        return QueryBuilderOutput(query=query)
    
    def process(self, inputs: QueryBuilderInput) -> QueryBuilderOutput:
        """Process method required by BaseService."""
        return self.build_query(inputs)
