from __future__ import annotations

from collections.abc import Sequence
from functools import partial
from typing import cast

from sqlalchemy.orm import Session

from ..models import UserAttribute as UserAttributeModel
from ..schema import UserAttribute
from .repository import Repository
from .utils import _delete
from .utils import _get_data
from .utils import _get_data_by_id
from .utils import _insert
from .utils import _update


_insert_method = partial(_insert, UserAttributeModel, UserAttribute)
_update_method = partial(_update, UserAttributeModel, UserAttribute)
_delete_method = partial(_delete, UserAttributeModel, UserAttribute)
_get_method = partial(_get_data, UserAttributeModel, UserAttribute)
_get_by_id_method = partial(_get_data_by_id, UserAttributeModel, UserAttribute)


class UserAttributeController(Repository):
    """Controller implementing CRUD operations for `UserAttribute` resources."""

    def insert_user_attribute(self, session: Session, model: UserAttribute) -> UserAttribute:
        """Insert a user attribute record and return the created schema."""
        return cast(UserAttribute, _insert_method(session, model))

    def update_user_attribute(self, session: Session, model: UserAttribute) -> UserAttribute | None:
        """Update a user attribute; return updated schema or None if not found."""
        result = _update_method(session, model)
        return cast(UserAttribute, result) if result else None

    def delete_user_attribute(self, session: Session, id: str) -> UserAttribute | None:
        """Delete a user attribute by id and return deleted schema or None."""
        result = _delete_method(session, id)
        return cast(UserAttribute, result) if result else None

    def get_user_attributes(
        self,
        session: Session,
        filter: dict[str, object] | None = None,
        order_by: Sequence | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[UserAttribute] | None:
        """Fetch user attribute records with optional filters; returns list or None."""
        result = _get_method(session, filter, order_by, limit, offset)
        return cast(list[UserAttribute], result) if result else None

    def get_user_attribute_by_id(self, session: Session, id: str) -> UserAttribute | None:
        """Fetch a single user attribute by id; returns schema or None."""
        result = _get_by_id_method(session, id)
        return cast(UserAttribute, result) if result else None
