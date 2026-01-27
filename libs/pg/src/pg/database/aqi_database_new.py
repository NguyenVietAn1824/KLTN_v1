from __future__ import annotations

"""Main AQI database class combining all controllers.

This module provides the main database interface for the KLTN air quality system,
following the sun_assistant SQLDatabase pattern. It combines all controller classes
through multiple inheritance and provides session management.
"""

from contextlib import contextmanager
from functools import cached_property

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from ..model import Base
from .province_controller import ProvinceController
from .district_new_controller import DistrictController
from .distric_stats_new_controller import DistricStatsController
from .air_component_controller import AirComponentController


class AQIDatabase(
    ProvinceController,
    DistrictController,
    DistricStatsController,
    AirComponentController,
):
    """Main database class for AQI operations following sun_assistant pattern.

    Combines all controller classes through multiple inheritance, providing
    a single unified interface for all database operations. Each controller
    implements the Repository pattern for its respective entity.

    This class follows the exact pattern from sun_assistant's SQLDatabase:
    - Multiple inheritance from all controllers
    - Cached sessionmaker for connection pooling
    - Context manager for session lifecycle
    - Health check functionality

    Attributes:
        username (str): PostgreSQL username
        password (str): PostgreSQL password
        host (str): Database host address
        port (int): Database port (default: 5432)
        db (str): Database name

    Example:
        >>> db = AQIDatabase(
        ...     username='postgres',
        ...     password='password',
        ...     host='localhost',
        ...     port=5432,
        ...     db='aqi_db'
        ... )
        >>> with db.get_session() as session:
        ...     districts = db.get_districts(session, limit=10)
    """

    @cached_property
    def sessionmaker(self) -> sessionmaker:
        """Create and cache sessionmaker with engine.

        Creates a SQLAlchemy engine with connection pooling and returns
        a sessionmaker bound to that engine. The sessionmaker is cached
        to avoid recreating it on each use.

        The engine automatically creates all tables defined in Base.metadata
        if they don't exist.

        Returns:
            Configured sessionmaker instance

        Note:
            This property is cached, so the engine and sessionmaker are only
            created once per AQIDatabase instance.
        """
        engine = create_engine(
            f'postgresql+psycopg2://{self.username}:{self.password}@{self.host}:{self.port}/{self.db}',
            pool_pre_ping=True,  # Verify connections before using
            pool_size=10,  # Connection pool size
            max_overflow=20,  # Extra connections beyond pool_size
        )
        Base.metadata.create_all(engine)
        return sessionmaker(autoflush=False, bind=engine)

    def __init__(
        self,
        username: str,
        password: str,
        host: str,
        port: int,
        db: str,
    ):
        """Initialize database connection parameters.

        Args:
            username: PostgreSQL username
            password: PostgreSQL password
            host: Database host address
            port: Database port
            db: Database name

        Example:
            >>> db = AQIDatabase(
            ...     username='postgres',
            ...     password='secret',
            ...     host='localhost',
            ...     port=5432,
            ...     db='aqi_db'
            ... )
        """
        self.username = username
        self.password = password
        self.host = host
        self.port = port
        self.db = db

    @contextmanager
    def get_session(self):
        """Get database session with automatic cleanup and transaction management.

        Provides a context manager that:
        1. Creates a new session
        2. Yields the session for use
        3. Commits the transaction on success
        4. Rolls back on exception
        5. Always closes the session

        Yields:
            Session: Active database session

        Example:
            >>> with db.get_session() as session:
            ...     district = db.get_district_by_id(session, '001')
            ...     if district:
            ...         district.name = 'Updated Name'
            ...         db.update_district(session, district)
            ...     # Auto-commit and close on exit

        Note:
            Any exception raised within the context will trigger a rollback.
            The session is always closed, even if an exception occurs.
        """
        session = None
        try:
            session: Session = self.sessionmaker()
            yield session
            session.commit()
        except Exception:
            if session:
                session.rollback()
            raise
        finally:
            if session:
                session.close()

    async def check_health(self) -> bool:
        """Check if database connection is healthy.

        Attempts to execute a simple query to verify the database
        connection is working properly.

        Returns:
            True if database is healthy and responsive, False otherwise

        Example:
            >>> is_healthy = await db.check_health()
            >>> if is_healthy:
            ...     print("Database connection OK")
            ... else:
            ...     print("Database connection failed")
        """
        try:
            with self.get_session() as session:
                session.execute('SELECT 1')
                return True
        except Exception:
            return False

    def close(self):
        """Close all database connections and dispose of the engine.

        Should be called when shutting down the application to ensure
        all connections are properly closed.

        Example:
            >>> db = AQIDatabase(...)
            >>> # ... use database ...
            >>> db.close()  # Clean shutdown
        """
        if hasattr(self, '_sessionmaker'):
            self.sessionmaker.close_all()
            if self.sessionmaker.kw.get('bind'):
                self.sessionmaker.kw['bind'].dispose()
