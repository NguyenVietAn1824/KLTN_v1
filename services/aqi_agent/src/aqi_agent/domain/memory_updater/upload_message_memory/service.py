from __future__ import annotations

from typing import Optional

from base import BaseModel
from base import BaseService
from aqi_agent.shared.models.memory import Answer
from aqi_agent.shared.models.memory import QAMemoryPair
from aqi_agent.shared.models.memory import Question
from logger import get_logger
from pg import SQLDatabase
from sqlalchemy import text

logger = get_logger(__name__)


class UploadMessageMemoryInput(BaseModel):
    conversation_id: str
    user_id: str
    question: str
    answer: str
    generated_sql: Optional[str] = None
    sql_result: Optional[str] = None


class UploadMessageMemoryService(BaseService):
    database: SQLDatabase

    async def process(self, inputs: UploadMessageMemoryInput) -> QAMemoryPair:
        query = text("""
            INSERT INTO conversation_messages (
                conversation_id, user_id, question, answer, generated_sql, sql_result
            )
            VALUES (:conversation_id, :user_id, :question, :answer, :generated_sql, :sql_result)
            RETURNING id, created_at
        """)

        try:
            async with self.database.engine.begin() as conn:
                result = await conn.execute(
                    query,
                    {
                        'conversation_id': inputs.conversation_id,
                        'user_id': inputs.user_id,
                        'question': inputs.question,
                        'answer': inputs.answer,
                        'generated_sql': inputs.generated_sql,
                        'sql_result': inputs.sql_result,
                    },
                )
                row = result.fetchone()

            logger.info(
                'Message memory uploaded successfully',
                extra={
                    'conversation_id': inputs.conversation_id,
                    'message_id': str(row.id) if row else None,
                },
            )

            return QAMemoryPair(
                question=Question(content=inputs.question),
                answer=Answer(
                    content=inputs.answer,
                    generated_sql=inputs.generated_sql,
                    sql_result=inputs.sql_result,
                ),
            )
        except Exception as e:
            logger.error(
                'Failed to upload message memory',
                extra={
                    'conversation_id': inputs.conversation_id,
                    'error': str(e),
                },
            )
            return QAMemoryPair(
                question=Question(content=inputs.question),
                answer=Answer(
                    content=inputs.answer,
                    generated_sql=inputs.generated_sql,
                    sql_result=inputs.sql_result,
                ),
            )
