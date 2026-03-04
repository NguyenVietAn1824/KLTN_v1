from __future__ import annotations

from collections.abc import Sequence
from functools import partial
from typing import cast

from sqlalchemy.orm import Session

from ..models import Inventory as InventoryModel
from ..schema import Inventory
from .repository import Repository
from .utils import _delete
from .utils import _get_data
from .utils import _get_data_by_id
from .utils import _insert
from .utils import _update

_insert_method = partial(_insert, InventoryModel, Inventory)
_update_method = partial(_update, InventoryModel, Inventory)
_delete_method = partial(_delete, InventoryModel, Inventory)
_get_method = partial(_get_data, InventoryModel, Inventory)
_get_by_id_method = partial(_get_data_by_id, InventoryModel, Inventory)


class InventoryController(Repository):
    """Controller implementing CRUD operations for `Inventory` resources."""

    def insert_inventory(self, session: Session, model: Inventory) -> Inventory:
        """Insert an inventory and return the created schema."""
        return cast(Inventory, _insert_method(session, model))

    def update_inventory(self, session: Session, model: Inventory) -> Inventory | None:
        """Update an inventory; return updated schema or None if not found."""
        result = _update_method(session, model)
        return cast(Inventory, result) if result else None

    def delete_inventory(self, session: Session, id: str) -> Inventory | None:
        """Delete an inventory by id and return deleted schema or None."""
        result = _delete_method(session, id)
        return cast(Inventory, result) if result else None

    def get_inventories(
        self,
        session: Session,
        filter: dict[str, object] | None = None,
        order_by: Sequence | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[Inventory] | None:
        """Fetch inventories with optional filter/order/limit/offset; returns list or None."""
        result = _get_method(session, filter, order_by, limit, offset)
        return cast(list[Inventory], result) if result else None

    def get_inventory_by_id(self, session: Session, id: str) -> Inventory | None:
        """Fetch a single inventory by id; return schema or None."""
        result = _get_by_id_method(session, id)
        return cast(Inventory, result) if result else None
