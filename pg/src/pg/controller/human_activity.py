from __future__ import annotations

from collections.abc import Sequence
from functools import partial
from typing import cast

from sqlalchemy.orm import Session

from ..models import HumanActivity as HumanActivityModel
from ..schema import HumanActivity
from .repository import Repository
from .utils import _delete
from .utils import _get_data
from .utils import _get_data_by_id
from .utils import _insert
from .utils import _update

_insert_method = partial(_insert, HumanActivityModel, HumanActivity)
_update_method = partial(_update, HumanActivityModel, HumanActivity)
_delete_method = partial(_delete, HumanActivityModel, HumanActivity)
_get_method = partial(_get_data, HumanActivityModel, HumanActivity)
_get_by_id_method = partial(_get_data_by_id, HumanActivityModel, HumanActivity)


class HumanActivityController(Repository):
    """Controller implementing CRUD operations for `HumanActivity` resources."""

    def insert_human_activity(self, session: Session, model: HumanActivity) -> HumanActivity:
        """Insert a human activity log entry and return created schema."""
        return cast(HumanActivity, _insert_method(session, model))

    def update_human_activity(self, session: Session, model: HumanActivity) -> HumanActivity | None:
        """Update a human activity log; return updated schema or None."""
        result = _update_method(session, model)
        return cast(HumanActivity, result) if result else None

    def delete_human_activity(self, session: Session, id: str) -> HumanActivity | None:
        """Delete a human activity log by id and return deleted schema or None."""
        result = _delete_method(session, id)
        return cast(HumanActivity, result) if result else None

    def get_human_activities(
        self,
        session: Session,
        filter: dict[str, object] | None = None,
        order_by: Sequence | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[HumanActivity] | None:
        """Fetch human activity logs with optional filters/limit/offset; returns list or None."""
        result = _get_method(session, filter, order_by, limit, offset)
        return cast(list[HumanActivity], result) if result else None

    def get_human_activity_by_id(self, session: Session, id: str) -> HumanActivity | None:
        """Fetch a single human activity log by id; returns schema or None."""
        result = _get_by_id_method(session, id)
        return cast(HumanActivity, result) if result else None
