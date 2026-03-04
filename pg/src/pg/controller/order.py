from __future__ import annotations

from collections.abc import Sequence
from functools import partial
from typing import cast

from sqlalchemy.orm import Session

from ..models import Order as OrderModel
from ..schema import Order
from .repository import Repository
from .utils import _delete
from .utils import _get_data
from .utils import _get_data_by_id
from .utils import _insert
from .utils import _update

_insert_method = partial(_insert, OrderModel, Order)
_update_method = partial(_update, OrderModel, Order)
_delete_method = partial(_delete, OrderModel, Order)
_get_method = partial(_get_data, OrderModel, Order)
_get_by_id_method = partial(_get_data_by_id, OrderModel, Order)


class OrderController(Repository):
    """Controller implementing CRUD operations for `Order` resources."""

    def insert_order(self, session: Session, model: Order) -> Order:
        """Insert a order entry and return created schema."""
        return cast(Order, _insert_method(session, model))

    def update_order(self, session: Session, model: Order) -> Order | None:
        """Update a order; return updated schema or None."""
        result = _update_method(session, model)
        return cast(Order, result) if result else None

    def delete_order(self, session: Session, id: str) -> Order | None:
        """Delete a order by id and return deleted schema or None."""
        result = _delete_method(session, id)
        return cast(Order, result) if result else None

    def get_orders(
        self,
        session: Session,
        filter: dict[str, object] | None = None,
        order_by: Sequence | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[Order] | None:
        """Fetch orders with optional filters/limit/offset; returns list or None."""
        result = _get_method(session, filter, order_by, limit, offset)
        return cast(list[Order], result) if result else None

    def get_order_by_id(self, session: Session, id: str) -> Order | None:
        """Fetch a single order by id; returns schema or None."""
        result = _get_by_id_method(session, id)
        return cast(Order, result) if result else None
