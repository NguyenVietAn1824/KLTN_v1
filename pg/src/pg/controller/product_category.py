from __future__ import annotations

from collections.abc import Sequence
from functools import partial
from typing import cast

from sqlalchemy.orm import Session

from ..models import ProductCategory as ProductCategoryModel
from ..schema import ProductCategory
from .repository import Repository
from .utils import _delete
from .utils import _get_data
from .utils import _get_data_by_id
from .utils import _insert
from .utils import _update


_insert_method = partial(_insert, ProductCategoryModel, ProductCategory)
_update_method = partial(_update, ProductCategoryModel, ProductCategory)
_delete_method = partial(_delete, ProductCategoryModel, ProductCategory)
_get_method = partial(_get_data, ProductCategoryModel, ProductCategory)
_get_by_id_method = partial(_get_data_by_id, ProductCategoryModel, ProductCategory)


class ProductCategoryController(Repository):
    """Controller implementing CRUD operations for `ProductCategory` resources."""

    def insert_product_category(self, session: Session, model: ProductCategory) -> ProductCategory:
        """Insert a product-category link and return the created schema."""
        return cast(ProductCategory, _insert_method(session, model))

    def update_product_category(self, session: Session, model: ProductCategory) -> ProductCategory | None:
        """Update a product-category entry; return updated schema or None."""
        result = _update_method(session, model)
        return cast(ProductCategory, result) if result else None

    def delete_product_category(self, session: Session, id: str) -> ProductCategory | None:
        """Delete a product-category relation by id; return deleted schema or None."""
        result = _delete_method(session, id)
        return cast(ProductCategory, result) if result else None

    def get_product_categories(
        self,
        session: Session,
        filter: dict[str, object] | None = None,
        order_by: Sequence | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[ProductCategory] | None:
        """Fetch product-category relations with optional filters; returns list or None."""
        result = _get_method(session, filter, order_by, limit, offset)
        return cast(list[ProductCategory], result) if result else None

    def get_product_category_by_id(self, session: Session, id: str) -> ProductCategory | None:
        """Fetch a single product-category record by id or return None."""
        result = _get_by_id_method(session, id)
        return cast(ProductCategory, result) if result else None
