from __future__ import annotations

from base import BaseModel


class Example(BaseModel):
    id: str
    question: str
    sql_query: str


class RetrievedExample(Example):
    score: float
