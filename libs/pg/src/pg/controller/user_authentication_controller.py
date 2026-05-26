from __future__ import annotations

from collections.abc import Sequence
from functools import partial
from typing import cast

from sqlalchemy.orm import Session

from ..model import UserAuthentication as UserAuthenticationModel
from .schemas import UserAuthentication
from .utils import _delete
from .utils import _get_data
from .utils import _get_data_by_id
from .utils import _insert
from .utils import _update

from logger import get_logger

logger = get_logger(__name__)

_insert_method = partial(_insert, logger, UserAuthenticationModel, UserAuthentication)
_update_method = partial(_update, logger, UserAuthenticationModel, UserAuthentication)
_delete_method = partial(_delete, logger, UserAuthenticationModel, UserAuthentication)
_get_method = partial(_get_data, logger, UserAuthenticationModel, UserAuthentication)
_get_by_id_method = partial(_get_data_by_id, logger, UserAuthenticationModel, UserAuthentication)


class UserAuthenticationController:
    """Controller implementing CRUD operations for UserAuthentication resources."""

    def insert_user_authentication(self, session: Session, model: UserAuthentication) -> UserAuthentication:
        return cast(UserAuthentication, _insert_method(session, model))

    def update_user_authentication(self, session: Session, model: UserAuthentication) -> UserAuthentication | None:
        result = _update_method(session, model)
        return cast(UserAuthentication, result) if result else None

    def delete_user_authentication(self, session: Session, id: str) -> UserAuthentication | None:
        result = _delete_method(session, id)
        return cast(UserAuthentication, result) if result else None

    def get_user_authentication_by_id(self, session: Session, id: str) -> UserAuthentication | None:
        result = _get_by_id_method(session, id)
        return cast(UserAuthentication, result) if result else None

    def get_user_authentications(
        self,
        session: Session,
        filter: dict[str, object] | None = None,
        order_by: Sequence | None = None,
        limit: int | None = None,
    ) -> list[UserAuthentication] | None:
        result = _get_method(session, filter, order_by, limit)
        return cast(list[UserAuthentication], result) if result else None
