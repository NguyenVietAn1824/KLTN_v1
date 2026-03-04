from __future__ import annotations

from collections.abc import Sequence
from functools import partial
from typing import cast

from sqlalchemy.orm import Session

from ..models import Product as ProductModel
from ..schema import Product
from .repository import Repository
from .utils import _delete
from .utils import _get_data
from .utils import _get_data_by_id
from .utils import _insert
from .utils import _update

_insert_method = partial(_insert, ProductModel, Product)
_update_method = partial(_update, ProductModel, Product)
_delete_method = partial(_delete, ProductModel, Product)
_get_method = partial(_get_data, ProductModel, Product)
_get_by_id_method = partial(_get_data_by_id, ProductModel, Product)


class ProductController(Repository):
    """Controller implementing CRUD operations for `Product` resources."""

    def insert_product(self, session: Session, model: Product) -> Product:
        """Insert a product and return the created schema."""
        return cast(Product, _insert_method(session, model))

    def update_product(self, session: Session, model: Product) -> Product | None:
        """Update a product; return updated schema or None if not found."""
        result = _update_method(session, model)
        return cast(Product, result) if result else None

    def delete_product(self, session: Session, id: str) -> Product | None:
        """Delete a product by id and return deleted schema or None."""
        result = _delete_method(session, id)
        return cast(Product, result) if result else None

    def get_products(
        self,
        session: Session,
        filter: dict[str, object] | None = None,
        order_by: Sequence | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[Product] | None:
        """Fetch products with optional filter/order/limit/offset; returns list or None."""
        result = _get_method(session, filter, order_by, limit, offset)
        return cast(list[Product], result) if result else None

    def get_product_by_id(self, session: Session, id: str) -> Product | None:
        """Fetch a single product by id; return schema or None."""
        result = _get_by_id_method(session, id)
        return cast(Product, result) if result else None
