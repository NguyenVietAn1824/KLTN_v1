from __future__ import annotations

from collections.abc import Sequence
from functools import partial
from typing import cast

from sqlalchemy.orm import Session

from ..models import Brand as BrandModel
from ..schema import Brand
from .repository import Repository
from .utils import _delete
from .utils import _get_data
from .utils import _get_data_by_id
from .utils import _insert
from .utils import _update

_insert_method = partial(_insert, BrandModel, Brand)
_update_method = partial(_update, BrandModel, Brand)
_delete_method = partial(_delete, BrandModel, Brand)
_get_method = partial(_get_data, BrandModel, Brand)
_get_by_id_method = partial(_get_data_by_id, BrandModel, Brand)


class BrandController(Repository):
    """Controller implementing CRUD operations for `Brand` resources."""

    def insert_brand(self, session: Session, model: Brand) -> Brand:
        """Insert a brand and return the created schema."""
        return cast(Brand, _insert_method(session, model))

    def update_brand(self, session: Session, model: Brand) -> Brand | None:
        """Update a brand; return updated schema or None if not found."""
        result = _update_method(session, model)
        return cast(Brand, result) if result else None

    def delete_brand(self, session: Session, id: str) -> Brand | None:
        """Delete a brand by id and return deleted schema or None."""
        result = _delete_method(session, id)
        return cast(Brand, result) if result else None

    def get_brands(
        self,
        session: Session,
        filter: dict[str, object] | None = None,
        order_by: Sequence | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[Brand] | None:
        """Fetch brands with optional filter/order/limit/offset; returns list or None."""
        result = _get_method(session, filter, order_by, limit, offset)
        return cast(list[Brand], result) if result else None

    def get_brand_by_id(self, session: Session, id: str) -> Brand | None:
        """Fetch a single brand by id; return schema or None."""
        result = _get_by_id_method(session, id)
        return cast(Brand, result) if result else None
