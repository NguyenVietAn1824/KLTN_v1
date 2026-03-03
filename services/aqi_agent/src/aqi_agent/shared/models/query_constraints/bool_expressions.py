"""
Boolean expressions for building GraphQL WHERE clauses.

Adapted from sun_assistant Apollo for KLTN AQI system.
These classes represent recursive boolean logic that can be nested arbitrarily deep.
Includes support for Hasura relationship filtering.
"""

from typing import Any, List, Optional, Union

from base import BaseModel
from pydantic import Field, field_validator

from .op import Op


class Condition(BaseModel):
    """A single comparison condition (field operator value) with optional nested relationship filter."""
    
    field: str = Field(
        description="The field name to compare (e.g., 'aqi_value', 'date', 'district_id') "
                    "OR relationship name for nested filters (e.g., 'district', 'province')"
    )
    op: Optional[Op] = Field(
        default=None,
        description="The comparison operator (e.g., Op.EQ, Op.GT, Op.ILIKE). "
                    "Omit when using nested relationship filter."
    )
    value: Optional[Any] = Field(
        default=None,
        description="The value to compare against. Type depends on operator: "
                    "- EQ/NEQ/GT/GTE/LT/LTE: single value "
                    "- IN/NOT_IN: array of values "
                    "- BETWEEN: [low, high] array "
                    "- LIKE/ILIKE: string pattern "
                    "- IS_NULL/NOT_NULL: None or boolean. "
                    "Omit when using nested relationship filter."
    )
    nested: Optional['Condition'] = Field(
        default=None,
        description="Nested condition for filtering via Hasura relationships. "
                    "Use when field is a relationship name (e.g., 'district'). "
                    "Example: field='district', nested=Condition(field='name', op='_ilike', value='%Ba Đình%')"
    )
    
    @field_validator("value")
    @classmethod
    def validate_operator_value(cls, v: Any, info) -> Any:
        """Validate that value matches operator requirements."""
        # If using nested filter, op and value are optional
        if "nested" in info.data and info.data["nested"] is not None:
            return v
            
        if "op" not in info.data or info.data["op"] is None:
            return v
        
        op = info.data["op"]
        
        # BETWEEN requires array of 2 elements
        if op == Op.BETWEEN:
            if not isinstance(v, list) or len(v) != 2:
                raise ValueError(f"BETWEEN operator requires array of [low, high], got: {v}")
        
        # IN/NOT_IN require array
        elif op in [Op.IN, Op.NOT_IN]:
            if not isinstance(v, list):
                raise ValueError(f"{op.value} operator requires array, got: {type(v)}")
        
        # IS_NULL/NOT_NULL should use None or boolean
        elif op in [Op.IS_NULL, Op.NOT_NULL]:
            if v is not None and not isinstance(v, bool):
                raise ValueError(f"{op.value} operator requires None or boolean, got: {v}")
        
        return v


class BoolAnd(BaseModel):
    """Logical AND of multiple boolean expressions."""
    
    and_: List['BoolExpr'] = Field(
        alias="_and",
        description="List of boolean expressions that must ALL be true"
    )


class BoolOr(BaseModel):
    """Logical OR of multiple boolean expressions."""
    
    or_: List['BoolExpr'] = Field(
        alias="_or",
        description="List of boolean expressions where AT LEAST ONE must be true"
    )


class BoolNot(BaseModel):
    """Logical NOT of a boolean expression."""
    
    not_: 'BoolExpr' = Field(
        alias="_not",
        description="Boolean expression to negate"
    )


# Recursive union type - can nest arbitrarily deep
BoolExpr = Union[Condition, BoolAnd, BoolOr, BoolNot]

# Update forward references for recursive types
BoolAnd.model_rebuild()
BoolOr.model_rebuild()
BoolNot.model_rebuild()
