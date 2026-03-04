from __future__ import annotations

from collections.abc import Sequence
from functools import partial
from typing import cast

from sqlalchemy.orm import Session

from ..models import Payment as PaymentModel
from ..schema import Payment
from .repository import Repository
from .utils import _delete
from .utils import _get_data
from .utils import _get_data_by_id
from .utils import _insert
from .utils import _update

_insert_method = partial(_insert, PaymentModel, Payment)
_update_method = partial(_update, PaymentModel, Payment)
_delete_method = partial(_delete, PaymentModel, Payment)
_get_method = partial(_get_data, PaymentModel, Payment)
_get_by_id_method = partial(_get_data_by_id, PaymentModel, Payment)


class PaymentController(Repository):
    """Controller implementing CRUD operations for `Payment` resources."""

    def insert_payment(self, session: Session, model: Payment) -> Payment:
        """Insert a payment entry and return created schema."""
        return cast(Payment, _insert_method(session, model))

    def update_payment(self, session: Session, model: Payment) -> Payment | None:
        """Update a payment; return updated schema or None."""
        result = _update_method(session, model)
        return cast(Payment, result) if result else None

    def delete_payment(self, session: Session, id: str) -> Payment | None:
        """Delete a payment by id and return deleted schema or None."""
        result = _delete_method(session, id)
        return cast(Payment, result) if result else None

    def get_payments(
        self,
        session: Session,
        filter: dict[str, object] | None = None,
        Payment_by: Sequence | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[Payment] | None:
        """Fetch payments with optional filters/limit/offset; returns list or None."""
        result = _get_method(session, filter, Payment_by, limit, offset)
        return cast(list[Payment], result) if result else None

    def get_payment_by_id(self, session: Session, id: str) -> Payment | None:
        """Fetch a single payment by id; returns schema or None."""
        result = _get_by_id_method(session, id)
        return cast(Payment, result) if result else None
