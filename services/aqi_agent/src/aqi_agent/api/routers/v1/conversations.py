from __future__ import annotations

from aqi_agent.api.helpers.exception_handler import ExceptionHandler
from aqi_agent.shared.utils import get_resources
from fastapi import APIRouter
from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from logger import get_logger
from pg.model import Conversation as ConversationModel
from pg.model import Message as MessageModel

conversations_router = APIRouter()
logger = get_logger(__name__)


@conversations_router.get('/conversations')
async def list_conversations(request: Request, email: str) -> JSONResponse:
    exception_handler = ExceptionHandler(logger=logger.bind(), service_name=__name__)
    try:
        resources = get_resources(request)
        with resources.sql_database.get_session() as session:
            users = resources.sql_database.get_users(session, filter={'email': email})
            user = users[0] if users else None
            if not user:
                return exception_handler.handle_unauthorized_error(
                    message='Invalid email', extra={'email': email},
                )

            conversations = resources.sql_database.get_conversations(
                session,
                filter={'user_id': user.id},
                order_by=[ConversationModel.created_at.desc()],
            ) or []

        items = [
            {
                'id': c.id,
                'title': c.title,
                'created_at': c.created_at.isoformat() if c.created_at else None,
            }
            for c in conversations
        ]
        return exception_handler.handle_success({'conversations': items})
    except Exception as e:
        return exception_handler.handle_exception(
            e=f'list_conversations failed: {e!s}', extra={'email': email},
        )


@conversations_router.get('/conversations/{conversation_id}/messages')
async def list_messages(request: Request, conversation_id: str, email: str) -> JSONResponse:
    exception_handler = ExceptionHandler(logger=logger.bind(), service_name=__name__)
    try:
        resources = get_resources(request)
        with resources.sql_database.get_session() as session:
            users = resources.sql_database.get_users(session, filter={'email': email})
            user = users[0] if users else None
            if not user:
                return exception_handler.handle_unauthorized_error(
                    message='Invalid email', extra={'email': email},
                )

            conv = resources.sql_database.get_conversation_by_id(session, conversation_id)
            if not conv or conv.user_id != user.id:
                return exception_handler.handle_not_found_error(
                    message='Conversation not found',
                    extra={'conversation_id': conversation_id},
                )

            messages = resources.sql_database.get_messages(
                session,
                filter={'conversation_id': conversation_id},
                order_by=[MessageModel.created_at.asc()],
            ) or []

        items = [
            {
                'id': m.id,
                'question': m.question,
                'answer': m.answer,
                'created_at': m.created_at.isoformat() if m.created_at else None,
            }
            for m in messages
        ]
        return exception_handler.handle_success({'messages': items})
    except Exception as e:
        return exception_handler.handle_exception(
            e=f'list_messages failed: {e!s}',
            extra={'conversation_id': conversation_id, 'email': email},
        )
