from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from base import BaseModel


class MessageRole(str, Enum):
    USER_ROLE = 'user'
    ASSISTANT_ROLE = 'assistant'


class Answer(BaseModel):
    answer: str


class Question(BaseModel):
    question: str


class QAMemoryPair(BaseModel):
    qa_list: tuple[Question, Answer] | None = None
    timestamp: Optional[datetime] = None

    def simplize(self) -> list[dict[str, str]]:
        if self.qa_list is None:
            return []
        return [
            {'role': MessageRole.USER_ROLE, 'content': self.qa_list[0].question},
            {'role': MessageRole.ASSISTANT_ROLE, 'content': self.qa_list[1].answer},
        ]
