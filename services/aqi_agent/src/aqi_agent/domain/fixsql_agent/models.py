from __future__ import annotations

from base import BaseModel
from pydantic import Field


class FixSQLModel(BaseModel):
    error_explanation: str = Field(
        ...,
        description='Clear explanation of why the SQL query is incorrect.',
    )
    fixed_sql: str = Field(
        ...,
        description='Corrected SQL query that addresses the identified issues.',
    )
    is_fixed: bool = Field(
        default=False,
        description='Indicates whether the SQL query was successfully fixed.',
    )
