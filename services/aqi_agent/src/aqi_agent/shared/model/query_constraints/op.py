"""
Query operators for building GraphQL conditions.

Adapted from sun_assistant Apollo for KLTN AQI system.
"""

from enum import Enum


class Op(str, Enum):
    """Comparison operators for building query conditions."""
    
    # Equality operators
    EQ = "_eq"  # Equal to
    NEQ = "_neq"  # Not equal to
    
    # Comparison operators
    GT = "_gt"  # Greater than
    GTE = "_gte"  # Greater than or equal to
    LT = "_lt"  # Less than
    LTE = "_lte"  # Less than or equal to
    
    # Array operators
    IN = "_in"  # Value in array
    NOT_IN = "_nin"  # Value not in array
    
    # Range operator
    BETWEEN = "_between"  # Value between two values [low, high]
    
    # Text search operators
    LIKE = "_like"  # SQL LIKE pattern matching (case-sensitive)
    ILIKE = "_ilike"  # SQL ILIKE pattern matching (case-insensitive)
    
    # Null operators
    IS_NULL = "_is_null"  # Field is null
    NOT_NULL = "_is_not_null"  # Field is not null
