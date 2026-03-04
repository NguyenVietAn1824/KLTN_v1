from __future__ import annotations

from collections.abc import Sequence
from functools import partial
from typing import cast

from sqlalchemy.orm import Session

from ..models import RecommendItems as RecommendItemsModel
from ..schema import RecommendItems
from .repository import Repository
from .utils import _delete
from .utils import _get_data
from .utils import _get_data_by_id
from .utils import _insert
from .utils import _update


_insert_method = partial(_insert, RecommendItemsModel, RecommendItems)
_update_method = partial(_update, RecommendItemsModel, RecommendItems)
_delete_method = partial(_delete, RecommendItemsModel, RecommendItems)
_get_method = partial(_get_data, RecommendItemsModel, RecommendItems)
_get_by_id_method = partial(_get_data_by_id, RecommendItemsModel, RecommendItems)


class RecommendItemsController(Repository):
    """Controller implementing CRUD operations for `RecommendItems` resources."""

    def insert_recommend_items(self, session: Session, model: RecommendItems) -> RecommendItems:
        """Insert a recommend-items relation and return created schema."""
        return cast(RecommendItems, _insert_method(session, model))

    def update_recommend_items(self, session: Session, model: RecommendItems) -> RecommendItems | None:
        """Update a recommend-items entry; return updated schema or None."""
        result = _update_method(session, model)
        return cast(RecommendItems, result) if result else None

    def delete_recommend_items(self, session: Session, id: str) -> RecommendItems | None:
        """Delete recommend-items by id and return deleted schema or None."""
        result = _delete_method(session, id)
        return cast(RecommendItems, result) if result else None

    def get_recommend_items(
        self,
        session: Session,
        filter: dict[str, object] | None = None,
        order_by: Sequence | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[RecommendItems] | None:
        """Fetch recommend-items records with optional filter/order/limit/offset; returns list or None."""
        result = _get_method(session, filter, order_by, limit, offset)
        return cast(list[RecommendItems], result) if result else None

    def get_recommend_items_by_id(self, session: Session, id: str) -> RecommendItems | None:
        """Fetch a single recommend-items record by id or return None."""
        result = _get_by_id_method(session, id)
        return cast(RecommendItems, result) if result else None
