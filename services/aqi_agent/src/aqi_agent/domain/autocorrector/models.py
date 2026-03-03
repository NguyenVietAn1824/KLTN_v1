"""Data models for autocorrector module."""
from __future__ import annotations

from base import BaseModel


class AutocorrectorInput(BaseModel):
    """Input model for autocorrector service."""

    sql_query: str


class AutocorrectorOutput(BaseModel):
    """Output model for autocorrector service."""

    corrected_sql_query: str
