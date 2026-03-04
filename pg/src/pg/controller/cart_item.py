from __future__ import annotations

from collections.abc import Sequence
from functools import partial
from typing import cast

from sqlalchemy.orm import Session

from ..models import CartItem as CartItemModel
from ..schema import CartItem
from .repository import Repository
from .utils import _delete
from .utils import _get_data
from .utils import _get_data_by_id
from .utils import _insert
from .utils import _update

_insert_method = partial(_insert, CartItemModel, CartItem)
_update_method = partial(_update, CartItemModel, CartItem)
_delete_method = partial(_delete, CartItemModel, CartItem)
_get_method = partial(_get_data, CartItemModel, CartItem)
_get_by_id_method = partial(_get_data_by_id, CartItemModel, CartItem)


class CartItemController(Repository):
    """Controller implementing CRUD operations for `CartItem` resources."""

    def insert_cart_item(self, session: Session, model: CartItem) -> CartItem:
        """Insert a cart item entry and return created schema."""
        return cast(CartItem, _insert_method(session, model))

    def update_cart_item(self, session: Session, model: CartItem) -> CartItem | None:
        """Update a cart item; return updated schema or None."""
        result = _update_method(session, model)
        return cast(CartItem, result) if result else None

    def delete_cart_item(self, session: Session, id: str) -> CartItem | None:
        """Delete a cart item by id and return deleted schema or None."""
        result = _delete_method(session, id)
        return cast(CartItem, result) if result else None

    def get_cart_items(
        self,
        session: Session,
        filter: dict[str, object] | None = None,
        CartItem_by: Sequence | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[CartItem] | None:
        """Fetch cart items with optional filters/limit/offset; returns list or None."""
        result = _get_method(session, filter, CartItem_by, limit, offset)
        return cast(list[CartItem], result) if result else None

    def get_cart_item_by_id(self, session: Session, id: str) -> CartItem | None:
        """Fetch a single cart item by id; returns schema or None."""
        result = _get_by_id_method(session, id)
        return cast(CartItem, result) if result else None
