from __future__ import annotations

from collections.abc import Sequence
from functools import partial
from typing import cast

from sqlalchemy.orm import Session

from ..models import Address as AddressModel
from ..schema import Address
from .repository import Repository
from .utils import _delete
from .utils import _get_data
from .utils import _get_data_by_id
from .utils import _insert
from .utils import _update

_insert_method = partial(_insert, AddressModel, Address)
_update_method = partial(_update, AddressModel, Address)
_delete_method = partial(_delete, AddressModel, Address)
_get_method = partial(_get_data, AddressModel, Address)
_get_by_id_method = partial(_get_data_by_id, AddressModel, Address)


class AddressController(Repository):
    """Controller implementing CRUD operations for `Address` resources."""

    def insert_address(self, session: Session, model: Address) -> Address:
        """Insert an address and return the created schema."""
        return cast(Address, _insert_method(session, model))

    def update_address(self, session: Session, model: Address) -> Address | None:
        """Update an address; return updated schema or None if not found."""
        result = _update_method(session, model)
        return cast(Address, result) if result else None

    def delete_address(self, session: Session, id: str) -> Address | None:
        """Delete an address by id and return deleted schema or None."""
        result = _delete_method(session, id)
        return cast(Address, result) if result else None

    def get_addresses(
        self,
        session: Session,
        filter: dict[str, object] | None = None,
        order_by: Sequence | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[Address] | None:
        """Fetch addresses with optional filter/order/limit/offset; returns list or None."""
        result = _get_method(session, filter, order_by, limit, offset)
        return cast(list[Address], result) if result else None

    def get_address_by_id(self, session: Session, id: str) -> Address | None:
        """Fetch a single address by id; return schema or None."""
        result = _get_by_id_method(session, id)
        return cast(Address, result) if result else None
