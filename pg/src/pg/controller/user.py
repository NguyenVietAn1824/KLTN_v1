from __future__ import annotations

from collections.abc import Sequence
from functools import partial
from typing import cast

from sqlalchemy.orm import Session

from ..models import User as UserModel
from ..schema import User
from .repository import Repository
from .utils import _delete
from .utils import _get_data
from .utils import _get_data_by_id
from .utils import _insert
from .utils import _update

_insert_method = partial(_insert, UserModel, User)
_update_method = partial(_update, UserModel, User)
_delete_method = partial(_delete, UserModel, User)
_get_method = partial(_get_data, UserModel, User)
_get_by_id_method = partial(_get_data_by_id, UserModel, User)


class UserController(Repository):
    """Controller implementing CRUD operations for `User` resources."""

    def insert_user(self, session: Session, model: User) -> User:
        """Insert user

        Args:
            session (Session): Database Session
            model (User): User model

        Returns:
            User: inserted user
        """
        return cast(User, _insert_method(session, model))

    def update_user(self, session: Session, model: User) -> User | None:
        """Update user

        Args:
            session (Session): Database Session
            model (User): User model

        Returns:
            User | None: updated user or None if no update
        """
        result = _update_method(session, model)
        return cast(User, result) if result else None

    def delete_user(self, session: Session, id: str) -> User | None:
        """Delete user

        Args:
            session (Session): Database Session
            model (User): User model

        Returns:
            User | None: deleted user or None if no update
        """
        result = _delete_method(session, id)
        return cast(User, result) if result else None

    def get_users(
        self,
        session: Session,
        filter: dict[str, object] | None = None,
        order_by: Sequence | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[User] | None:
        """Get users

        Args:
            session (Session): Database Session
            filter (dict[str, object] | None, optional): filter kwargs, if None will apply no filter. Defaults to None.
            limit (int | None, optional): Limit results returned, if None will return all results. Defaults to None.
        Returns:
            list[User] | None: users fetched, None if not found
        """
        result = _get_method(session, filter, order_by, limit, offset)
        return cast(list[User], result) if result else None

    def get_user_by_id(self, session: Session, id: str) -> User | None:
        """Get user by id

        Args:
            session (Session): Database Session
            id (int): user id

        Returns:
            User: user fetched
        """
        result = _get_by_id_method(session, id)
        return cast(User, result) if result else None
