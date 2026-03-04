from __future__ import annotations

from collections.abc import Sequence
from functools import partial
from typing import cast

from sqlalchemy.orm import Session

from ..models import VariantInventory as VariantInventoryModel
from ..schema import VariantInventory
from .repository import Repository
from .utils import _delete
from .utils import _get_data
from .utils import _get_data_by_id
from .utils import _insert
from .utils import _update

_insert_method = partial(_insert, VariantInventoryModel, VariantInventory)
_update_method = partial(_update, VariantInventoryModel, VariantInventory)
_delete_method = partial(_delete, VariantInventoryModel, VariantInventory)
_get_method = partial(_get_data, VariantInventoryModel, VariantInventory)
_get_by_id_method = partial(_get_data_by_id, VariantInventoryModel, VariantInventory)


class VariantInventoryController(Repository):
    """Controller implementing CRUD operations for `VariantInventory` resources."""

    def insert_variant_inventory(self, session: Session, model: VariantInventory) -> VariantInventory:
        """Insert a variant inventory and return the created schema."""
        return cast(VariantInventory, _insert_method(session, model))

    def update_variant_inventory(self, session: Session, model: VariantInventory) -> VariantInventory | None:
        """Update a variant inventory; return updated schema or None if not found."""
        result = _update_method(session, model)
        return cast(VariantInventory, result) if result else None

    def delete_variant_inventory(self, session: Session, id: str) -> VariantInventory | None:
        """Delete a variant inventory by id and return deleted schema or None."""
        result = _delete_method(session, id)
        return cast(VariantInventory, result) if result else None

    def get_variant_inventories(
        self,
        session: Session,
        filter: dict[str, object] | None = None,
        order_by: Sequence | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[VariantInventory] | None:
        """Fetch variant inventories with optional filter/order/limit/offset; returns list or None."""
        result = _get_method(session, filter, order_by, limit, offset)
        return cast(list[VariantInventory], result) if result else None

    def get_variant_inventory_by_id(self, session: Session, id: str) -> VariantInventory | None:
        """Fetch a single variant inventory by id; return schema or None."""
        result = _get_by_id_method(session, id)
        return cast(VariantInventory, result) if result else None
