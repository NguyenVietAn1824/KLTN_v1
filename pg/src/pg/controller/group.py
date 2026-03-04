from __future__ import annotations

from collections.abc import Sequence
from functools import partial
from typing import cast

from sqlalchemy.orm import Session

from ..models import Group as GroupModel
from ..schema import Group
from .repository import Repository
from .utils import _delete
from .utils import _get_data
from .utils import _get_data_by_id
from .utils import _insert
from .utils import _update

_insert_method = partial(_insert, GroupModel, Group)
_update_method = partial(_update, GroupModel, Group)
_delete_method = partial(_delete, GroupModel, Group)
_get_method = partial(_get_data, GroupModel, Group)
_get_by_id_method = partial(_get_data_by_id, GroupModel, Group)


class GroupController(Repository):
    """Controller implementing CRUD operations for `Group` resources."""

    def insert_group(self, session: Session, model: Group) -> Group:
        """Insert a group and return the created schema."""
        return cast(Group, _insert_method(session, model))

    def update_group(self, session: Session, model: Group) -> Group | None:
        """Update a group; return updated schema or None."""
        result = _update_method(session, model)
        return cast(Group, result) if result else None

    def delete_group(self, session: Session, id: str) -> Group | None:
        """Delete a group by id and return deleted schema or None."""
        result = _delete_method(session, id)
        return cast(Group, result) if result else None

    def get_groups(
        self,
        session: Session,
        filter: dict[str, object] | None = None,
        order_by: Sequence | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[Group] | None:
        """Fetch groups with optional filters; return list or None."""
        result = _get_method(session, filter, order_by, limit, offset)
        return cast(list[Group], result) if result else None

    def get_group_by_id(self, session: Session, id: str) -> Group | None:
        """Fetch a group by id; return schema or None."""
        result = _get_by_id_method(session, id)
        return cast(Group, result) if result else None
