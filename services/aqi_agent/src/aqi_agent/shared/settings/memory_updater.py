from __future__ import annotations

from base import BaseModel


class ConversationSummarizerSettings(BaseModel):
    model: str
    frequency_penalty: int = 0
    n: int = 1
    presence_penalty: int = 0
    temperature: int = 0
    top_p: int = 1
    max_completion_tokens: int


class ConversationTitleGeneratorSettings(BaseModel):
    model: str
    frequency_penalty: int = 0
    n: int = 1
    presence_penalty: int = 0
    temperature: int = 0
    top_p: int = 1
    max_completion_tokens: int


class MemoryUpdaterSettings(BaseModel):
    recent_messages: int
    conversation_summarizer: ConversationSummarizerSettings
    conversation_title_generator: ConversationTitleGeneratorSettings
