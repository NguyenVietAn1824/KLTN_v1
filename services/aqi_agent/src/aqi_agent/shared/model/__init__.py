"""
Shared models for KLTN AQI Agent.

Adapted from sun_assistant Apollo architecture.
"""

from .planning import SubQuestion, Task, TodoList
from .query_constraints import (
    BoolAnd,
    BoolExpr,
    BoolNot,
    BoolOr,
    Condition,
    NullsPos,
    Op,
    OrderItem,
    PaginationCursor,
    QueryConstraints,
    SortDir,
)
from .schemas import AirComponent, DistricStats, Districts, Provinces, Tables

__all__ = [
    # Query constraints
    "QueryConstraints",
    "BoolExpr",
    "Condition",
    "BoolAnd",
    "BoolOr",
    "BoolNot",
    "Op",
    "OrderItem",
    "SortDir",
    "NullsPos",
    "PaginationCursor",
    
    # Schemas
    "Tables",
    "Provinces",
    "Districts",
    "DistricStats",
    "AirComponent",
    
    # Planning
    "TodoList",
    "Task",
    "SubQuestion",
]
