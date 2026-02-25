from __future__ import annotations

from base import BaseModel
from pydantic import HttpUrl
from pydantic import SecretStr


class LiteLLMSetting(BaseModel):
    url: HttpUrl
    token: SecretStr
    model: str
    embedding_model: str
    frequency_penalty: int
    n: int
    presence_penalty: int
    temperature: int
    top_p: int
    max_completion_tokens: int
    encoding_format: str
    dimensions: int
    max_length: int
    timeout: int
    connect_timeout: int
    max_connections: int
    max_keepalive_connections: int
    context_window: int
    condition_model: str
