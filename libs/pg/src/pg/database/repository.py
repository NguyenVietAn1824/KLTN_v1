from __future__ import annotations

"""Repository abstract base class defining database operations interface.

This module defines the Repository pattern interface that all controller classes
must implement. It follows the sun_assistant architecture for consistent database
access patterns across the application.
"""

from abc import ABC
from abc import abstractmethod
from collections.abc import Sequence

from sqlalchemy.orm import Session

from .schemas import District
from .schemas import DistricStats
from .schemas import Province
from .schemas import AirComponent


class Repository(ABC):
    """Abstract repository interface for database operations.

    Defines CRUD operations that must be implemented by controller classes.
    Each entity type (District, DistricStats, etc.) has its own set of methods.
    """

    # PROVINCE OPERATIONS
    @abstractmethod
    def insert_province(self, session: Session, model: Province) -> Province:
        """Insert a new province record.

        Args:
            session: Active database session
            model: Province schema instance to insert

        Returns:
            Inserted province with database-generated fields populated
        """
        raise NotImplementedError()

    @abstractmethod
    def update_province(self, session: Session, model: Province) -> Province | None:
        """Update an existing province record.

        Args:
            session: Active database session
            model: Province schema instance with updated data

        Returns:
            Updated province, or None if not found
        """
        raise NotImplementedError()

    @abstractmethod
    def delete_province(self, session: Session, id: str) -> Province | None:
        """Delete a province record by ID.

        Args:
            session: Active database session
            id: Province ID to delete

        Returns:
            Deleted province, or None if not found
        """
        raise NotImplementedError()

    @abstractmethod
    def get_province_by_id(self, session: Session, id: str) -> Province | None:
        """Get a province by ID.

        Args:
            session: Active database session
            id: Province ID to fetch

        Returns:
            Province if found, None otherwise
        """
        raise NotImplementedError()

    @abstractmethod
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
            filter: Dictionary of filter conditions
            order_by: Sequence of order_by clauses
            limit: Maximum number of results

        Returns:
            List of provinces, or None if none found
        """
        raise NotImplementedError()

    # DISTRICT OPERATIONS
    @abstractmethod
    def insert_district(self, session: Session, model: District) -> District:
        """Insert a new district record."""
        raise NotImplementedError()

    @abstractmethod
    def update_district(self, session: Session, model: District) -> District | None:
        """Update an existing district record."""
        raise NotImplementedError()

    @abstractmethod
    def delete_district(self, session: Session, id: str) -> District | None:
        """Delete a district record by ID."""
        raise NotImplementedError()

    @abstractmethod
    def get_district_by_id(self, session: Session, id: str) -> District | None:
        """Get a district by ID."""
        raise NotImplementedError()

    @abstractmethod
    def get_districts(
        self,
        session: Session,
        filter: dict[str, object] | None = None,
        order_by: Sequence | None = None,
        limit: int | None = None,
    ) -> list[District] | None:
        """Get districts with optional filtering and ordering."""
        raise NotImplementedError()

    # DISTRIC_STATS OPERATIONS
    @abstractmethod
    def insert_distric_stats(self, session: Session, model: DistricStats) -> DistricStats:
        """Insert a new district statistics record."""
        raise NotImplementedError()

    @abstractmethod
    def update_distric_stats(self, session: Session, model: DistricStats) -> DistricStats | None:
        """Update an existing district statistics record."""
        raise NotImplementedError()

    @abstractmethod
    def delete_distric_stats(self, session: Session, id: int) -> DistricStats | None:
        """Delete a district statistics record by ID."""
        raise NotImplementedError()

    @abstractmethod
    def get_distric_stats_by_id(self, session: Session, id: int) -> DistricStats | None:
        """Get district statistics by ID."""
        raise NotImplementedError()

    @abstractmethod
    def get_distric_stats(
        self,
        session: Session,
        filter: dict[str, object] | None = None,
        order_by: Sequence | None = None,
        limit: int | None = None,
    ) -> list[DistricStats] | None:
        """Get district statistics with optional filtering and ordering."""
        raise NotImplementedError()

    # AIR_COMPONENT OPERATIONS
    @abstractmethod
    def insert_air_component(self, session: Session, model: AirComponent) -> AirComponent:
        """Insert a new air component record."""
        raise NotImplementedError()

    @abstractmethod
    def update_air_component(self, session: Session, model: AirComponent) -> AirComponent | None:
        """Update an existing air component record."""
        raise NotImplementedError()

    @abstractmethod
    def delete_air_component(self, session: Session, id: int) -> AirComponent | None:
        """Delete an air component record by ID."""
        raise NotImplementedError()

    @abstractmethod
    def get_air_component_by_id(self, session: Session, id: int) -> AirComponent | None:
        """Get air component by ID."""
        raise NotImplementedError()

    @abstractmethod
    def get_air_components(
        self,
        session: Session,
        filter: dict[str, object] | None = None,
        order_by: Sequence | None = None,
        limit: int | None = None,
    ) -> list[AirComponent] | None:
        """Get air components with optional filtering and ordering."""
        raise NotImplementedError()
