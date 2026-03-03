from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class AutocorrectorSettings(BaseModel):
    redis_key_prefix: str = 'frequent_values:'
    fuzzy_threshold: int = 70
    max_fuzzy_matches: Optional[int] = 5
