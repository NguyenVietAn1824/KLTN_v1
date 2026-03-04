from __future__ import annotations

from collections.abc import Sequence
from functools import partial
from typing import cast

from sqlalchemy.orm import Session

from ..model import Message as MessageModel
from .schemas import Message
from .utils import _delete
from .utils import _get_data
from .utils import _get_data_by_id
from .utils import _insert
from .utils import _update

from logger import get_logger

logger = get_logger(__name__)

_insert_method = partial(_insert, logger, MessageModel, Message)
_update_method = partial(_update, logger, MessageModel, Message)
_delete_method = partial(_delete, logger, MessageModel, Message)
_get_method = partial(_get_data, logger, MessageModel, Message)
_get_by_id_method = partial(_get_data_by_id, logger, MessageModel, Message)


class MessageController:
    """Controller implementing CRUD operations for Message resources."""

    def insert_message(self, session: Session, model: Message) -> Message:
        """Insert a new message record."""
        return cast(Message, _insert_method(session, model))

    def update_message(self, session: Session, model: Message) -> Message | None:
        """Update an existing message record."""
        result = _update_method(session, model)
        return cast(Message, result) if result else None

    def delete_message(self, session: Session, id: str) -> Message | None:
        """Delete a message record by ID."""
        result = _delete_method(session, id)
        return cast(Message, result) if result else None

    def get_message_by_id(self, session: Session, id: str) -> Message | None:
        """Get a message by ID."""
        result = _get_by_id_method(session, id)
        return cast(Message, result) if result else None

    def get_messages(
        self,
        session: Session,
        filter: dict[str, object] | None = None,
        order_by: Sequence | None = None,
        limit: int | None = None,
    ) -> list[Message] | None:
        """Get messages with optional filtering and ordering."""
        result = _get_method(session, filter, order_by, limit)
        return cast(list[Message], result) if result else None
