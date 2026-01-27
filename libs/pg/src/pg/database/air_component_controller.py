from __future__ import annotations

"""Air component controller for database operations.

This module provides CRUD operations for the air_component table which defines
the different air quality metrics that can be measured (AQI, PM2.5, PM10, etc.).
"""

from collections.abc import Sequence
from functools import partial
from typing import cast

from sqlalchemy.orm import Session

from ..model import AirComponent as AirComponentModel
from .repository import Repository
from .schemas import AirComponent
from .utils import _delete, _get_data, _get_data_by_id, _insert, _update

# Simple logger
class SimpleLogger:
    def info(self, msg, **kwargs):
        print(f"INFO: {msg}")
    def debug(self, msg, **kwargs):
        pass
    def exception(self, msg, **kwargs):
        print(f"ERROR: {msg}")

logger = SimpleLogger()

# Create partial functions
_insert_method = partial(_insert, logger, AirComponentModel, AirComponent)
_update_method = partial(_update, logger, AirComponentModel, AirComponent)
_delete_method = partial(_delete, logger, AirComponentModel, AirComponent)
_get_method = partial(_get_data, logger, AirComponentModel, AirComponent)
_get_by_id_method = partial(_get_data_by_id, logger, AirComponentModel, AirComponent)


class AirComponentController(Repository):
    """Controller for air component database operations.

    Provides CRUD operations for the air_component table which stores
    metadata about different air quality metrics.
    """

    def insert_air_component(self, session: Session, model: AirComponent) -> AirComponent:
        """Insert a new air component record."""
        return cast(AirComponent, _insert_method(session, model))

    def update_air_component(self, session: Session, model: AirComponent) -> AirComponent | None:
        """Update an existing air component record."""
        result = _update_method(session, model)
        return cast(AirComponent, result) if result else None

    def delete_air_component(self, session: Session, id: int) -> AirComponent | None:
        """Delete an air component by ID."""
        result = _delete_method(session, id)
        return cast(AirComponent, result) if result else None

    def get_air_components(
        self,
        session: Session,
        filter: dict[str, object] | None = None,
        order_by: Sequence | None = None,
        limit: int | None = None,
    ) -> list[AirComponent] | None:
        """Get air components with optional filtering and ordering."""
        result = _get_method(session, filter, order_by, limit)
        return cast(list[AirComponent], result) if result else None

    def get_air_component_by_id(self, session: Session, id: int) -> AirComponent | None:
        """Get an air component by ID."""
        result = _get_by_id_method(session, id)
        return cast(AirComponent, result) if result else None

    def get_air_component_by_name(
        self,
        session: Session,
        name: str,
    ) -> AirComponent | None:
        """Get an air component by name.

        Args:
            session: Active database session
            name: Component name (e.g., 'AQI', 'PM2.5')

        Returns:
            AirComponent if found, None otherwise

        Example:
            >>> component = controller.get_air_component_by_name(session, 'AQI')
        """
        components = self.get_air_components(session, filter={'name': name})
        return components[0] if components else None
