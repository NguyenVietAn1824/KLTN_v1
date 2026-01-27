from __future__ import annotations

"""Province controller for database operations.

This module provides CRUD operations for the provinces table following
the sun_assistant Repository pattern with utility functions.
"""

from collections.abc import Sequence
from functools import partial
from typing import cast

from sqlalchemy.orm import Session

from ..model import Province as ProvinceModel
from .repository import Repository
from .schemas import Province
from .utils import _delete
from .utils import _get_data
from .utils import _get_data_by_id
from .utils import _insert
from .utils import _update

# Create a simple logger for this module
# TODO: Replace with proper logger import when available
class SimpleLogger:
    def info(self, msg, **kwargs):
        print(f"INFO: {msg}")
    def debug(self, msg, **kwargs):
        pass
    def exception(self, msg, **kwargs):
        print(f"ERROR: {msg}")

logger = SimpleLogger()

# Create partial functions with pre-filled logger and model/schema types
_insert_method = partial(_insert, logger, ProvinceModel, Province)
_update_method = partial(_update, logger, ProvinceModel, Province)
_delete_method = partial(_delete, logger, ProvinceModel, Province)
_get_method = partial(_get_data, logger, ProvinceModel, Province)
_get_by_id_method = partial(_get_data_by_id, logger, ProvinceModel, Province)


class ProvinceController(Repository):
    """Controller for province database operations.

    Provides CRUD operations for provinces table using utility functions
    to reduce boilerplate code. All methods use the Repository pattern.
    """

    def insert_province(self, session: Session, model: Province) -> Province:
        """Insert a new province record.

        Args:
            session: Active database session
            model: Province schema instance to insert

        Returns:
            Inserted province with all fields populated

        Example:
            >>> province = Province(id='01', name='Hà Nội')
            >>> result = controller.insert_province(session, province)
        """
        return cast(Province, _insert_method(session, model))

    def update_province(self, session: Session, model: Province) -> Province | None:
        """Update an existing province record.

        Args:
            session: Active database session
            model: Province schema with updated data (must include id)

        Returns:
            Updated province, or None if province not found

        Example:
            >>> province = Province(id='01', name='Hà Nội Updated')
            >>> result = controller.update_province(session, province)
        """
        result = _update_method(session, model)
        return cast(Province, result) if result else None

    def delete_province(self, session: Session, id: str) -> Province | None:
        """Delete a province by ID.

        Args:
            session: Active database session
            id: Province ID to delete

        Returns:
            Deleted province data, or None if not found

        Example:
            >>> deleted = controller.delete_province(session, '01')
        """
        result = _delete_method(session, id)
        return cast(Province, result) if result else None

    def get_provinces(
        self,
        session: Session,
        filter: dict[str, object] | None = None,
        order_by: Sequence | None = None,
        limit: int | None = None,
    ) -> list[Province] | None:
        """Get provinces with optional filtering and ordering.

        Args:
            session: Active database session
            filter: Dictionary of filter conditions (e.g., {'name': 'Hà Nội'})
            order_by: Sequence of SQLAlchemy order_by clauses
            limit: Maximum number of results to return

        Returns:
            List of provinces matching criteria, or None if none found

        Example:
            >>> # Get all provinces
            >>> provinces = controller.get_provinces(session)
            >>> 
            >>> # Get provinces with limit
            >>> provinces = controller.get_provinces(session, limit=10)
        """
        result = _get_method(session, filter, order_by, limit)
        return cast(list[Province], result) if result else None

    def get_province_by_id(self, session: Session, id: str) -> Province | None:
        """Get a province by its ID.

        Args:
            session: Active database session
            id: Province ID to fetch

        Returns:
            Province if found, None otherwise

        Example:
            >>> province = controller.get_province_by_id(session, '01')
        """
        result = _get_by_id_method(session, id)
        return cast(Province, result) if result else None
