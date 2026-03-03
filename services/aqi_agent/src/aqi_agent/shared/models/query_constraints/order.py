"""
Query ordering and sorting models.

Adapted from sun_assistant Apollo for KLTN AQI system.
"""

from typing import Literal, Optional

from base import BaseModel
from pydantic import Field


# Type literals for sorting
SortDir = Literal["asc", "desc"]
NullsPos = Literal["first", "last"]


class OrderItem(BaseModel):
    """Represents a single ordering specification for query results."""
    
    field: str = Field(
        description="The field name to sort by (e.g., 'aqi', 'date', 'district_name')"
    )
    dir: SortDir = Field(
        default="asc",
        description="Sort direction: 'asc' for ascending, 'desc' for descending"
    )
    nulls: Optional[NullsPos] = Field(
        default=None,
        description="Position of null values: 'first' or 'last'"
    )


class PaginationCursor(BaseModel):
    """Cursor-based pagination (simplified from Apollo, not used initially)."""
    
    first: Optional[int] = Field(
        default=None,
        description="Number of items to fetch from the start"
    )
    after: Optional[str] = Field(
        default=None,
        description="Cursor to fetch items after"
    )
    last: Optional[int] = Field(
        default=None,
        description="Number of items to fetch from the end"
    )
    before: Optional[str] = Field(
        default=None,
        description="Cursor to fetch items before"
    )
