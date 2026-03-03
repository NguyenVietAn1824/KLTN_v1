from __future__ import annotations

from base import BaseModel


class TableColumnSelection(BaseModel):
    table_name: str
    table_selection_reason: str
    columns: list[str]
    column_reasoning: list[str]


class ColumnPrunerResult(BaseModel):
    results: list[TableColumnSelection]
