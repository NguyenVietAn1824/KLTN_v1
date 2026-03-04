from __future__ import annotations

from collections.abc import Sequence
from functools import partial
from typing import cast

from sqlalchemy.orm import Session

from ..models import City as CityModel
from ..schema import City
from .repository import Repository
from .utils import _delete
from .utils import _get_data
from .utils import _get_data_by_id
from .utils import _insert
from .utils import _update

_insert_method = partial(_insert, CityModel, City)
_update_method = partial(_update, CityModel, City)
_delete_method = partial(_delete, CityModel, City)
_get_method = partial(_get_data, CityModel, City)
_get_by_id_method = partial(_get_data_by_id, CityModel, City)


class CityController(Repository):
    """Controller implementing CRUD operations for `City` resources."""

    def insert_city(self, session: Session, model: City) -> City:
        """Insert a city and return the created schema."""
        return cast(City, _insert_method(session, model))

    def update_city(self, session: Session, model: City) -> City | None:
        """Update a city; return updated schema or None if not found."""
        result = _update_method(session, model)
        return cast(City, result) if result else None

    def delete_city(self, session: Session, id: str) -> City | None:
        """Delete a city by id and return deleted schema or None."""
        result = _delete_method(session, id)
        return cast(City, result) if result else None

    def get_cities(
        self,
        session: Session,
        filter: dict[str, object] | None = None,
        order_by: Sequence | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[City] | None:
        """Fetch cities with optional filter/order/limit/offset; returns list or None."""
        result = _get_method(session, filter, order_by, limit, offset)
        return cast(list[City], result) if result else None

    def get_city_by_id(self, session: Session, id: str) -> City | None:
        """Fetch a single city by id; return schema or None."""
        result = _get_by_id_method(session, id)
        return cast(City, result) if result else None
