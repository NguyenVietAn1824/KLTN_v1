from __future__ import annotations

from base import BaseModel
from aqi_agent.shared.models import RetrievedExample


class ExampleRetrievalInput(BaseModel):
    question: str


class ExampleRetrievalOutput(BaseModel):
    examples: list[RetrievedExample]
