from __future__ import annotations

from base import BaseModel


class HumanInterventSettings(BaseModel):
    model: str
    frequency_penalty: int = 0
    n: int = 1
    presence_penalty: int = 0
    temperature: int = 0
    top_p: int = 1
    max_completion_tokens: int
