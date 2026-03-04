from __future__ import annotations

from collections.abc import Sequence
from functools import partial
from typing import cast

from sqlalchemy.orm import Session

from ..models import ProductVariant as ProductVariantModel
from ..schema import ProductVariant
from .repository import Repository
from .utils import _delete
from .utils import _get_data
from .utils import _get_data_by_id
from .utils import _insert
from .utils import _update

_insert_method = partial(_insert, ProductVariantModel, ProductVariant)
_update_method = partial(_update, ProductVariantModel, ProductVariant)
_delete_method = partial(_delete, ProductVariantModel, ProductVariant)
_get_method = partial(_get_data, ProductVariantModel, ProductVariant)
_get_by_id_method = partial(_get_data_by_id, ProductVariantModel, ProductVariant)


class ProductVariantController(Repository):
    """Controller implementing CRUD operations for `ProductVariant` resources."""

    def insert_product_variant(self, session: Session, model: ProductVariant) -> ProductVariant:
        """Insert a product variant and return the created schema."""
        return cast(ProductVariant, _insert_method(session, model))

    def update_product_variant(self, session: Session, model: ProductVariant) -> ProductVariant | None:
        """Update a product variant; return updated schema or None if not found."""
        result = _update_method(session, model)
        return cast(ProductVariant, result) if result else None

    def delete_product_variant(self, session: Session, id: str) -> ProductVariant | None:
        """Delete a product variant by id and return deleted schema or None."""
        result = _delete_method(session, id)
        return cast(ProductVariant, result) if result else None

    def get_product_variants(
        self,
        session: Session,
        filter: dict[str, object] | None = None,
        order_by: Sequence | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[ProductVariant] | None:
        """Fetch product variants with optional filter/order/limit/offset; returns list or None."""
        result = _get_method(session, filter, order_by, limit, offset)
        return cast(list[ProductVariant], result) if result else None

    def get_product_variant_by_id(self, session: Session, id: str) -> ProductVariant | None:
        """Fetch a single product variant by id; return schema or None."""
        result = _get_by_id_method(session, id)
        return cast(ProductVariant, result) if result else None
