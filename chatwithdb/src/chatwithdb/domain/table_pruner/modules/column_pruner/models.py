from __future__ import annotations

from base import BaseModel


class TableColumnSelection(BaseModel):
    table_name: str
    columns: list[str]


class ColumnPrunerResult(BaseModel):
    results: list[TableColumnSelection]
