from __future__ import annotations

from collections.abc import Sequence
from functools import partial
from typing import cast

from sqlalchemy.orm import Session

from ..models import UserAuthentication as UserAuthenticationModel
from ..schema import UserAuthentication
from .repository import Repository
from .utils import _delete
from .utils import _get_data
from .utils import _get_data_by_id
from .utils import _insert
from .utils import _update

_insert_method = partial(_insert, UserAuthenticationModel, UserAuthentication)
_update_method = partial(_update, UserAuthenticationModel, UserAuthentication)
_delete_method = partial(_delete, UserAuthenticationModel, UserAuthentication)
_get_method = partial(_get_data, UserAuthenticationModel, UserAuthentication)
_get_by_id_method = partial(_get_data_by_id, UserAuthenticationModel, UserAuthentication)


class UserAuthenticationController(Repository):
    """Controller implementing CRUD operations for `UserAuthentication` resources."""

    def insert_user_authentication(self, session: Session, model: UserAuthentication) -> UserAuthentication:
        """Insert user authentication

        Args:
            session (Session): Database Session
            model (UserAuthentication): UserAuthentication model

        Returns:
            UserAuthentication: inserted user authentication
        """
        return cast(UserAuthentication, _insert_method(session, model))

    def update_user_authentication(self, session: Session, model: UserAuthentication) -> UserAuthentication | None:
        """Update user authentication

        Args:
            session (Session): Database Session
            model (UserAuthentication): UserAuthentication model

        Returns:
            UserAuthentication | None: updated user authentication or None if no update
        """
        result = _update_method(session, model)
        return cast(UserAuthentication, result) if result else None

    def delete_user_authentication(self, session: Session, id: str) -> UserAuthentication | None:
        """Delete user authentication

        Args:
            session (Session): Database Session
            id (str): user authentication id

        Returns:
            UserAuthentication | None: deleted user authentication or None if not found
        """
        result = _delete_method(session, id)
        return cast(UserAuthentication, result) if result else None

    def get_user_authentications(
        self,
        session: Session,
        filter: dict[str, object] | None = None,
        order_by: Sequence | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[UserAuthentication] | None:
        """Get user authentications

        Args:
            session (Session): Database Session
            filter (dict[str, object] | None, optional): filter kwargs, if None will apply no filter. Defaults to None.
            order_by (Sequence | None, optional): order by columns. Defaults to None.
            limit (int | None, optional): Limit results returned, if None will return all results. Defaults to None.
            offset (int | None, optional): Offset results. Defaults to None.

        Returns:
            list[UserAuthentication] | None: user authentications fetched, None if not found
        """
        result = _get_method(session, filter, order_by, limit, offset)
        return cast(list[UserAuthentication], result) if result else None

    def get_user_authentication_by_id(self, session: Session, id: str) -> UserAuthentication | None:
        """Get user authentication by id

        Args:
            session (Session): Database Session
            id (str): user authentication id

        Returns:
            UserAuthentication | None: user authentication fetched or None if not found
        """
        result = _get_by_id_method(session, id)
        return cast(UserAuthentication, result) if result else None

    def get_user_authentication_by_username(self, session: Session, username: str) -> UserAuthentication | None:
        """Get user authentication by username (email)

        Args:
            session (Session): Database Session
            username (str): username (email) to search for

        Returns:
            UserAuthentication | None: user authentication fetched or None if not found
        """
        result = self.get_user_authentications(session, filter={'username': username})
        return result[0] if result else None
