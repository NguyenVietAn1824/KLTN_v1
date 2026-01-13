from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy import func
from sqlalchemy import Index
from sqlalchemy import Text
from sqlalchemy import Integer
from sqlalchemy import Date
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship


class Base(DeclarativeBase):
    pass


class Dated(Base):
    __abstract__ = True

    created_at: Mapped[datetime] = mapped_column(insert_default=func.now())


class Province(Base):
    __tablename__ = 'provinces'

    id: Mapped[str] = mapped_column(Text, primary_key=True, index=True)
    name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    districts: Mapped[list[District]] = relationship(
        back_populates='province',
        cascade='all, delete-orphan',
    )


class District(Dated):
    __tablename__ = 'districts'

    id: Mapped[str] = mapped_column(Text, primary_key=True, index=True)
    province_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey('provinces.id', ondelete='CASCADE'),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    administrative_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    province: Mapped[Province] = relationship(back_populates='districts')
    stats: Mapped[list[DistricStats]] = relationship(
        back_populates='district',
        cascade='all, delete-orphan',
    )

    # Indexes
    __table_args__ = (
        Index('idx_districts_province', 'province_id'),
        Index('idx_districts_name', 'name'),
        Index('idx_districts_admin_id', 'administrative_id'),
    )


class AirComponent(Dated):
    __tablename__ = 'air_component'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class DistricStats(Dated):
    __tablename__ = 'distric_stats'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[datetime] = mapped_column(Date, nullable=False)
    hour: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    component_id: Mapped[str] = mapped_column(Text, nullable=False)
    aqi_value: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pm25_value: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    district_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey('districts.id', ondelete='CASCADE'),
        nullable=False,
    )

    # Relationships
    district: Mapped[District] = relationship(back_populates='stats')

    # Indexes
    __table_args__ = (
        Index('idx_stats_date', 'date'),
        Index('idx_stats_district', 'district_id'),
        Index('idx_stats_component', 'component_id'),
        Index('idx_stats_date_district', 'date', 'district_id'),
    )
