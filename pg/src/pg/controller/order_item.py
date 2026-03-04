from __future__ import annotations

from collections.abc import Sequence
from functools import partial
from typing import cast

from sqlalchemy.orm import Session

from ..models import OrderItem as OrderItemModel
from ..schema import OrderItem
from .repository import Repository
from .utils import _delete
from .utils import _get_data
from .utils import _get_data_by_id
from .utils import _insert
from .utils import _update

_insert_method = partial(_insert, OrderItemModel, OrderItem)
_update_method = partial(_update, OrderItemModel, OrderItem)
_delete_method = partial(_delete, OrderItemModel, OrderItem)
_get_method = partial(_get_data, OrderItemModel, OrderItem)
_get_by_id_method = partial(_get_data_by_id, OrderItemModel, OrderItem)


class OrderItemController(Repository):
    """Controller implementing CRUD operations for `OrderItem` resources."""

    def insert_order_item(self, session: Session, model: OrderItem) -> OrderItem:
        """Insert a order item entry and return created schema."""
        return cast(OrderItem, _insert_method(session, model))

    def update_order_item(self, session: Session, model: OrderItem) -> OrderItem | None:
        """Update a order item; return updated schema or None."""
        result = _update_method(session, model)
        return cast(OrderItem, result) if result else None

    def delete_order_item(self, session: Session, id: str) -> OrderItem | None:
        """Delete a order item by id and return deleted schema or None."""
        result = _delete_method(session, id)
        return cast(OrderItem, result) if result else None

    def get_order_items(
        self,
        session: Session,
        filter: dict[str, object] | None = None,
        OrderItem_by: Sequence | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[OrderItem] | None:
        """Fetch order items with optional filters/limit/offset; returns list or None."""
        result = _get_method(session, filter, OrderItem_by, limit, offset)
        return cast(list[OrderItem], result) if result else None

    def get_order_item_by_id(self, session: Session, id: str) -> OrderItem | None:
        """Fetch a single order item by id; returns schema or None."""
        result = _get_by_id_method(session, id)
        return cast(OrderItem, result) if result else None
