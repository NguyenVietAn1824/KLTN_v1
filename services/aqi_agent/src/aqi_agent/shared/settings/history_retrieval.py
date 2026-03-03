from __future__ import annotations

from base import BaseModel


class HistoryRetrievalSettings(BaseModel):
    n_turns: int
