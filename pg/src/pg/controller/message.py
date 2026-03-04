from __future__ import annotations

from collections.abc import Sequence
from functools import partial
from typing import cast

from sqlalchemy.orm import Session

from ..models import Message as MessageModel
from ..schema import Message
from .repository import Repository
from .utils import _delete
from .utils import _get_data
from .utils import _get_data_by_id
from .utils import _insert
from .utils import _update

_insert_method = partial(_insert, MessageModel, Message)
_update_method = partial(_update, MessageModel, Message)
_delete_method = partial(_delete, MessageModel, Message)
_get_method = partial(_get_data, MessageModel, Message)
_get_by_id_method = partial(_get_data_by_id, MessageModel, Message)


class MessageController(Repository):
    """Controller implementing CRUD operations for `Message` resources."""

    def insert_message(self, session: Session, model: Message) -> Message:
        """Insert a new message row and return the created schema."""
        return cast(Message, _insert_method(session, model))

    def update_message(self, session: Session, model: Message) -> Message | None:
        """Update an existing message; return updated schema or None."""
        result = _update_method(session, model)
        return cast(Message, result) if result else None

    def delete_message(self, session: Session, id: str) -> Message | None:
        """Delete a message by id and return the deleted schema or None."""
        result = _delete_method(session, id)
        return cast(Message, result) if result else None

    def get_messages(
        self,
        session: Session,
        filter: dict[str, object] | None = None,
        order_by: Sequence | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[Message] | None:
        """Fetch messages with optional filter/order/limit/offset; returns list or None."""
        result = _get_method(session, filter, order_by, limit, offset)
        return cast(list[Message], result) if result else None

    def get_message_by_id(self, session: Session, id: str) -> Message | None:
        """Fetch a single message by id; returns schema or None."""
        result = _get_by_id_method(session, id)
        return cast(Message, result) if result else None
