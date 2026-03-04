from __future__ import annotations

from collections.abc import Sequence
from functools import partial
from typing import cast

from sqlalchemy.orm import Session

from ..models import Cart as CartModel
from ..schema import Cart
from .repository import Repository
from .utils import _delete
from .utils import _get_data
from .utils import _get_data_by_id
from .utils import _insert
from .utils import _update

_insert_method = partial(_insert, CartModel, Cart)
_update_method = partial(_update, CartModel, Cart)
_delete_method = partial(_delete, CartModel, Cart)
_get_method = partial(_get_data, CartModel, Cart)
_get_by_id_method = partial(_get_data_by_id, CartModel, Cart)


class CartController(Repository):
    """Controller implementing CRUD operations for `Cart` resources."""

    def insert_cart(self, session: Session, model: Cart) -> Cart:
        """Insert a cart entry and return created schema."""
        return cast(Cart, _insert_method(session, model))

    def update_cart(self, session: Session, model: Cart) -> Cart | None:
        """Update a cart; return updated schema or None."""
        result = _update_method(session, model)
        return cast(Cart, result) if result else None

    def delete_cart(self, session: Session, id: str) -> Cart | None:
        """Delete a cart by id and return deleted schema or None."""
        result = _delete_method(session, id)
        return cast(Cart, result) if result else None

    def get_carts(
        self,
        session: Session,
        filter: dict[str, object] | None = None,
        Cart_by: Sequence | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[Cart] | None:
        """Fetch carts with optional filters/limit/offset; returns list or None."""
        result = _get_method(session, filter, Cart_by, limit, offset)
        return cast(list[Cart], result) if result else None

    def get_cart_by_id(self, session: Session, id: str) -> Cart | None:
        """Fetch a single cart by id; returns schema or None."""
        result = _get_by_id_method(session, id)
        return cast(Cart, result) if result else None
