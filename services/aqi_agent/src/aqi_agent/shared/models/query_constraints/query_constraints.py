"""
Query constraints for building complete GraphQL queries.

Adapted from sun_assistant Apollo for KLTN AQI system.
Simplified - no aggregates, no pagination cursor (using simple limit/offset).
"""

from typing import List, Optional

from base import BaseModel
from pydantic import Field, field_validator

from .bool_expressions import BoolExpr
from .order import OrderItem


class QueryConstraints(BaseModel):
    """
    Complete query constraints for GraphQL query generation.
    
    This model encapsulates all aspects of query filtering, sorting, and pagination:
    - where: Boolean expression tree for filtering (AND/OR/NOT/Conditions)
    - order_by: List of fields to sort by with direction
    - limit: Maximum number of results
    - offset: Number of results to skip (for pagination)
    """
    
    where: Optional[BoolExpr] = Field(
        default=None,
        description="Boolean expression tree for filtering results. "
                    "Can be a single Condition or complex nested BoolAnd/BoolOr/BoolNot. "
                    "Example: {field='aqi', op=Op.GT, value=100} "
                    "Example: {_and=[{field='aqi', op=Op.GT, value=100}, {field='date', op=Op.EQ, value='2024-01-15'}]}"
    )
    
    order_by: Optional[List[OrderItem]] = Field(
        default=None,
        description="List of fields to sort by with direction. "
                    "Example: [{field='aqi', dir='desc'}, {field='date', dir='asc'}]"
    )
    
    limit: Optional[int] = Field(
        default=None,
        description="Maximum number of results to return. "
                    "Common values: 10 for top results, 1 for single result, 100 for bulk data"
    )
    
    offset: Optional[int] = Field(
        default=None,
        description="Number of results to skip (for pagination). "
                    "Example: offset=10 with limit=10 gives results 11-20"
    )
    
    @field_validator("where", mode="before")
    @classmethod
    def convert_empty_where(cls, v):
        """Convert empty dict to None."""
        if v == {}:
            return None
        return v
    
    @field_validator("order_by", mode="before")
    @classmethod
    def convert_empty_order_by(cls, v):
        """Convert empty list to None."""
        if v == []:
            return None
        return v
    
    @field_validator("limit")
    @classmethod
    def validate_limit(cls, v: Optional[int]) -> Optional[int]:
        """Ensure limit is positive."""
        if v is not None and v <= 0:
            raise ValueError(f"limit must be positive, got: {v}")
        return v
    
    @field_validator("offset")
    @classmethod
    def validate_offset(cls, v: Optional[int]) -> Optional[int]:
        """Ensure offset is non-negative."""
        if v is not None and v < 0:
            raise ValueError(f"offset must be non-negative, got: {v}")
        return v
