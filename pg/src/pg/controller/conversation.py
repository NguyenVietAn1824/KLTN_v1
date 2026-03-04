from __future__ import annotations

from collections.abc import Sequence
from functools import partial
from typing import cast

from sqlalchemy.orm import Session

from ..models import Conversation as ConversationModel
from ..schema import Conversation
from .repository import Repository
from .utils import _delete
from .utils import _get_data
from .utils import _get_data_by_id
from .utils import _insert
from .utils import _update

_insert_method = partial(_insert, ConversationModel, Conversation)
_update_method = partial(_update, ConversationModel, Conversation)
_delete_method = partial(_delete, ConversationModel, Conversation)
_get_method = partial(_get_data, ConversationModel, Conversation)
_get_by_id_method = partial(_get_data_by_id, ConversationModel, Conversation)


class ConversationController(Repository):
    """Controller implementing CRUD operations for `Conversation` resources.

    Provides methods to insert, update, delete and fetch conversations using
    SQLAlchemy sessions and Pydantic schemas.
    """

    def insert_conversation(self, session: Session, model: Conversation) -> Conversation:
        """Insert conversation

        Args:
            session (Session): Database Session
            model (Conversation): conversation model

        Returns:
            Conversation: inserted conversation
        """
        return cast(Conversation, _insert_method(session, model))

    def update_conversation(self, session: Session, model: Conversation) -> Conversation | None:
        """Update conversation

        Args:
            session (Session): Database Session
            model (Conversation): conversation model

        Returns:
            Conversation | None: updated conversation or None if no update
        """
        result = _update_method(session, model)
        return cast(Conversation, result) if result else None

    def delete_conversation(self, session: Session, id: str) -> Conversation | None:
        """Delete conversation

        Args:
            session (Session): Database Session
            model (Conversation): conversation model

        Returns:
            Conversation | None: deleted conversation or None if no update
        """
        result = _delete_method(session, id)
        return cast(Conversation, result) if result else None

    def get_conversations(
        self,
        session: Session,
        filter: dict[str, object] | None = None,
        order_by: Sequence | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[Conversation] | None:
        """Get conversations

        Args:
            session (Session): Database Session
            filter (dict[str, object] | None, optional): filter kwargs, if None will apply no filter. Defaults to None.
            limit (int | None, optional): Limit results returned, if None will return all results. Defaults to None.
        Returns:
            list[conversation] | None: conversations fetched, None if not found
        """
        result = _get_method(session, filter, order_by, limit, offset)
        return cast(list[Conversation], result) if result else None

    def get_conversation_by_id(self, session: Session, id: str) -> Conversation | None:
        """Get conversation by id

        Args:
            session (Session): Database Session
            id (int): conversation id

        Returns:
            Conversation: conversation fetched
        """
        result = _get_by_id_method(session, id)
        return cast(Conversation, result) if result else None
