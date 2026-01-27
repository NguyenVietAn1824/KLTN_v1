from __future__ import annotations

"""District statistics controller for database operations.

This module provides CRUD operations for the distric_stats table with
specialized queries for AQI data retrieval, historical analysis, and comparisons.
"""

from collections.abc import Sequence
from datetime import date, datetime
from functools import partial
from typing import cast

from sqlalchemy import select, and_, func, desc
from sqlalchemy.orm import Session, joinedload

from ..model import DistricStats as DistricStatsModel, District as DistrictModel
from .repository import Repository
from .schemas import DistricStats, District
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
_insert_method = partial(_insert, logger, DistricStatsModel, DistricStats)
_update_method = partial(_update, logger, DistricStatsModel, DistricStats)
_delete_method = partial(_delete, logger, DistricStatsModel, DistricStats)
_get_method = partial(_get_data, logger, DistricStatsModel, DistricStats)
_get_by_id_method = partial(_get_data_by_id, logger, DistricStatsModel, DistricStats)


class DistricStatsController(Repository):
    """Controller for district statistics database operations.

    Provides CRUD operations plus specialized queries for:
    - Latest AQI data retrieval
    - Historical data analysis
    - District comparisons
    - Aggregated statistics
    """

    def insert_distric_stats(self, session: Session, model: DistricStats) -> DistricStats:
        """Insert a new district statistics record."""
        return cast(DistricStats, _insert_method(session, model))

    def update_distric_stats(self, session: Session, model: DistricStats) -> DistricStats | None:
        """Update an existing district statistics record."""
        result = _update_method(session, model)
        return cast(DistricStats, result) if result else None

    def delete_distric_stats(self, session: Session, id: int) -> DistricStats | None:
        """Delete district statistics by ID."""
        result = _delete_method(session, id)
        return cast(DistricStats, result) if result else None

    def get_distric_stats(
        self,
        session: Session,
        filter: dict[str, object] | None = None,
        order_by: Sequence | None = None,
        limit: int | None = None,
    ) -> list[DistricStats] | None:
        """Get district statistics with optional filtering and ordering."""
        result = _get_method(session, filter, order_by, limit)
        return cast(list[DistricStats], result) if result else None

    def get_distric_stats_by_id(self, session: Session, id: int) -> DistricStats | None:
        """Get district statistics by ID."""
        result = _get_by_id_method(session, id)
        return cast(DistricStats, result) if result else None

    # SPECIALIZED QUERIES FOR AQI ANALYSIS

    def get_latest_stats_by_district(
        self,
        session: Session,
        district_id: str,
    ) -> DistricStats | None:
        """Get latest statistics for a specific district.

        Args:
            session: Active database session
            district_id: District ID to query

        Returns:
            Latest statistics record, or None if not found

        Example:
            >>> latest = controller.get_latest_stats_by_district(session, '001')
            >>> print(f"Current AQI: {latest.aqi_value}")
        """
        try:
            stmt = (
                select(DistricStatsModel)
                .where(DistricStatsModel.district_id == district_id)
                .order_by(
                    desc(DistricStatsModel.date),
                    desc(DistricStatsModel.hour),
                )
                .limit(1)
            )
            obj = session.scalars(stmt).first()
            return DistricStats.model_validate(obj) if obj else None
        except Exception as e:
            logger.exception('Failed to get latest stats', 
                           extra={'district_id': district_id, 'error': str(e)})
            raise

    def get_stats_by_district_and_date(
        self,
        session: Session,
        district_id: str,
        target_date: date,
    ) -> list[DistricStats] | None:
        """Get all statistics for a district on a specific date.

        Args:
            session: Active database session
            district_id: District ID to query
            target_date: Date to filter by

        Returns:
            List of statistics for that day (hourly data), or None if not found

        Example:
            >>> from datetime import date
            >>> stats = controller.get_stats_by_district_and_date(
            ...     session, '001', date(2026, 1, 15)
            ... )
        """
        try:
            stmt = (
                select(DistricStatsModel)
                .where(
                    and_(
                        DistricStatsModel.district_id == district_id,
                        DistricStatsModel.date == target_date,
                    )
                )
                .order_by(DistricStatsModel.hour)
            )
            objs = session.scalars(stmt).all()
            if len(objs) == 0:
                return None
            return [DistricStats.model_validate(obj) for obj in objs]
        except Exception as e:
            logger.exception('Failed to get stats by date', 
                           extra={'district_id': district_id, 'date': target_date, 'error': str(e)})
            raise

    def get_stats_by_district_date_range(
        self,
        session: Session,
        district_id: str,
        start_date: date,
        end_date: date,
    ) -> list[DistricStats] | None:
        """Get statistics for a district within a date range.

        Args:
            session: Active database session
            district_id: District ID to query
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            List of statistics within the date range, or None if not found

        Example:
            >>> from datetime import date, timedelta
            >>> today = date.today()
            >>> week_ago = today - timedelta(days=7)
            >>> stats = controller.get_stats_by_district_date_range(
            ...     session, '001', week_ago, today
            ... )
        """
        try:
            stmt = (
                select(DistricStatsModel)
                .where(
                    and_(
                        DistricStatsModel.district_id == district_id,
                        DistricStatsModel.date >= start_date,
                        DistricStatsModel.date <= end_date,
                    )
                )
                .order_by(
                    DistricStatsModel.date,
                    DistricStatsModel.hour,
                )
            )
            objs = session.scalars(stmt).all()
            if len(objs) == 0:
                return None
            return [DistricStats.model_validate(obj) for obj in objs]
        except Exception as e:
            logger.exception('Failed to get stats by date range', 
                           extra={'district_id': district_id, 'start': start_date, 
                                 'end': end_date, 'error': str(e)})
            raise

    def get_avg_aqi_by_district_date(
        self,
        session: Session,
        district_id: str,
        target_date: date,
    ) -> float | None:
        """Calculate average AQI for a district on a specific date.

        Args:
            session: Active database session
            district_id: District ID to query
            target_date: Date to calculate average for

        Returns:
            Average AQI value, or None if no data found

        Example:
            >>> from datetime import date
            >>> avg_aqi = controller.get_avg_aqi_by_district_date(
            ...     session, '001', date.today()
            ... )
            >>> print(f"Average AQI: {avg_aqi:.1f}")
        """
        try:
            stmt = (
                select(func.avg(DistricStatsModel.aqi_value))
                .where(
                    and_(
                        DistricStatsModel.district_id == district_id,
                        DistricStatsModel.date == target_date,
                        DistricStatsModel.aqi_value.isnot(None),
                    )
                )
            )
            result = session.scalars(stmt).first()
            return float(result) if result else None
        except Exception as e:
            logger.exception('Failed to calculate average AQI', 
                           extra={'district_id': district_id, 'date': target_date, 'error': str(e)})
            raise

    def get_current_aqi_all_districts(
        self,
        session: Session,
    ) -> list[tuple[District, DistricStats]] | None:
        """Get current AQI for all districts (latest record for each).

        Returns a list of tuples containing (District, DistricStats) for
        the most recent measurement of each district.

        Args:
            session: Active database session

        Returns:
            List of (District, DistricStats) tuples, or None if no data

        Example:
            >>> results = controller.get_current_aqi_all_districts(session)
            >>> for district, stats in results:
            ...     print(f"{district.name}: AQI {stats.aqi_value}")
        """
        try:
            # Subquery to get latest date+hour per district
            latest_subq = (
                select(
                    DistricStatsModel.district_id,
                    func.max(DistricStatsModel.date).label('max_date'),
                )
                .group_by(DistricStatsModel.district_id)
                .subquery()
            )

            # Join to get full records
            stmt = (
                select(DistrictModel, DistricStatsModel)
                .join(
                    DistricStatsModel,
                    DistrictModel.id == DistricStatsModel.district_id,
                )
                .join(
                    latest_subq,
                    and_(
                        DistricStatsModel.district_id == latest_subq.c.district_id,
                        DistricStatsModel.date == latest_subq.c.max_date,
                    ),
                )
                .order_by(DistrictModel.name)
            )

            results = session.execute(stmt).all()
            if len(results) == 0:
                return None

            return [
                (District.model_validate(district), DistricStats.model_validate(stats))
                for district, stats in results
            ]
        except Exception as e:
            logger.exception('Failed to get current AQI for all districts', extra={'error': str(e)})
            raise

    def compare_districts_aqi(
        self,
        session: Session,
        district_ids: list[str],
        target_date: date | None = None,
    ) -> list[tuple[District, DistricStats]] | None:
        """Compare AQI values across multiple districts.

        Args:
            session: Active database session
            district_ids: List of district IDs to compare
            target_date: Date to compare (defaults to latest available)

        Returns:
            List of (District, DistricStats) tuples ordered by AQI (worst first),
            or None if no data found

        Example:
            >>> district_ids = ['001', '002', '003']
            >>> results = controller.compare_districts_aqi(session, district_ids)
            >>> print(f"Worst AQI: {results[0][0].name} - {results[0][1].aqi_value}")
        """
        try:
            if target_date is None:
                # Get latest date with data
                stmt = select(func.max(DistricStatsModel.date))
                target_date = session.scalars(stmt).first()

            if not target_date:
                return None

            stmt = (
                select(DistrictModel, DistricStatsModel)
                .join(
                    DistricStatsModel,
                    DistrictModel.id == DistricStatsModel.district_id,
                )
                .where(
                    and_(
                        DistricStatsModel.district_id.in_(district_ids),
                        DistricStatsModel.date == target_date,
                    )
                )
                .order_by(desc(DistricStatsModel.aqi_value))
            )

            results = session.execute(stmt).all()
            if len(results) == 0:
                return None

            return [
                (District.model_validate(district), DistricStats.model_validate(stats))
                for district, stats in results
            ]
        except Exception as e:
            logger.exception('Failed to compare districts', 
                           extra={'district_ids': district_ids, 'date': target_date, 'error': str(e)})
            raise
