from __future__ import annotations

from collections.abc import Sequence
from functools import partial
from typing import cast

from sqlalchemy.orm import Session

from ..model import Conversation as ConversationModel
from .schemas import Conversation
from .utils import _delete
from .utils import _get_data
from .utils import _get_data_by_id
from .utils import _insert
from .utils import _update

from logger import get_logger

logger = get_logger(__name__)

_insert_method = partial(_insert, logger, ConversationModel, Conversation)
_update_method = partial(_update, logger, ConversationModel, Conversation)
_delete_method = partial(_delete, logger, ConversationModel, Conversation)
_get_method = partial(_get_data, logger, ConversationModel, Conversation)
_get_by_id_method = partial(_get_data_by_id, logger, ConversationModel, Conversation)


class ConversationController:
    """Controller implementing CRUD operations for Conversation resources."""

    def insert_conversation(self, session: Session, model: Conversation) -> Conversation:
        """Insert a new conversation record."""
        return cast(Conversation, _insert_method(session, model))

    def update_conversation(self, session: Session, model: Conversation) -> Conversation | None:
        """Update an existing conversation record."""
        result = _update_method(session, model)
        return cast(Conversation, result) if result else None

    def delete_conversation(self, session: Session, id: str) -> Conversation | None:
        """Delete a conversation record by ID."""
        result = _delete_method(session, id)
        return cast(Conversation, result) if result else None

    def get_conversation_by_id(self, session: Session, id: str) -> Conversation | None:
        """Get a conversation by ID."""
        result = _get_by_id_method(session, id)
        return cast(Conversation, result) if result else None

    def get_conversations(
        self,
        session: Session,
        filter: dict[str, object] | None = None,
        order_by: Sequence | None = None,
        limit: int | None = None,
    ) -> list[Conversation] | None:
        """Get conversations with optional filtering and ordering."""
        result = _get_method(session, filter, order_by, limit)
        return cast(list[Conversation], result) if result else None
