from __future__ import annotations

from collections.abc import Sequence
from functools import partial
from typing import cast

from sqlalchemy.orm import Session

from ..model import User as UserModel
from .schemas import User
from .utils import _delete
from .utils import _get_data
from .utils import _get_data_by_id
from .utils import _insert
from .utils import _update

from logger import get_logger

logger = get_logger(__name__)

_insert_method = partial(_insert, logger, UserModel, User)
_update_method = partial(_update, logger, UserModel, User)
_delete_method = partial(_delete, logger, UserModel, User)
_get_method = partial(_get_data, logger, UserModel, User)
_get_by_id_method = partial(_get_data_by_id, logger, UserModel, User)


class UserController:
    """Controller implementing CRUD operations for User resources."""

    def insert_user(self, session: Session, model: User) -> User:
        """Insert a new user record."""
        return cast(User, _insert_method(session, model))

    def update_user(self, session: Session, model: User) -> User | None:
        """Update an existing user record."""
        result = _update_method(session, model)
        return cast(User, result) if result else None

    def delete_user(self, session: Session, id: str) -> User | None:
        """Delete a user record by ID."""
        result = _delete_method(session, id)
        return cast(User, result) if result else None

    def get_user_by_id(self, session: Session, id: str) -> User | None:
        """Get a user by ID."""
        result = _get_by_id_method(session, id)
        return cast(User, result) if result else None

    def get_users(
        self,
        session: Session,
        filter: dict[str, object] | None = None,
        order_by: Sequence | None = None,
        limit: int | None = None,
    ) -> list[User] | None:
        """Get users with optional filtering and ordering."""
        result = _get_method(session, filter, order_by, limit)
        return cast(list[User], result) if result else None
