from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import func
from sqlalchemy import Index
from sqlalchemy import Text
from sqlalchemy import Integer
from sqlalchemy import Date
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship


class Base(DeclarativeBase):
    pass


class Dated(Base):
    __abstract__ = True

    created_at: Mapped[datetime] = mapped_column(insert_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(onupdate=func.now(), nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)


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


# ---------------------------------------------------------------------------
# User / Conversation / Message models
# ---------------------------------------------------------------------------


class User(Dated):
    __tablename__ = 'user'

    id: Mapped[str] = mapped_column(Text, primary_key=True, index=True)
    full_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    email: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    dob: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    avt_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_active: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    role: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    conversations: Mapped[list['Conversation']] = relationship(
        back_populates='user',
        cascade='all, delete-orphan',
    )
    authentications: Mapped[list['UserAuthentication']] = relationship(
        back_populates='user',
        cascade='all, delete-orphan',
    )


class UserAuthentication(Dated):
    __tablename__ = 'user_authentications'

    id: Mapped[str] = mapped_column(Text, primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey('user.id', ondelete='CASCADE'),
        nullable=False,
    )
    username: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    password: Mapped[str] = mapped_column(Text, nullable=False)
    social_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    mfa_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text('false'),
    )

    # Relationships
    user: Mapped['User'] = relationship(back_populates='authentications')


class Conversation(Dated):
    __tablename__ = 'conversation'

    id: Mapped[str] = mapped_column(Text, primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey('user.id', ondelete='CASCADE'),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(Text, nullable=False, default='')
    summary: Mapped[str] = mapped_column(Text, nullable=False, default='')
    is_confirming: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text('false'),
    )

    # Relationships
    user: Mapped['User'] = relationship(back_populates='conversations')
    messages: Mapped[list['Message']] = relationship(
        back_populates='conversation',
        cascade='all, delete-orphan',
    )

    # Indexes
    __table_args__ = (
        Index('idx_conversation_user', 'user_id'),
    )


class Message(Dated):
    __tablename__ = 'message'

    id: Mapped[str] = mapped_column(Text, primary_key=True, index=True)
    conversation_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey('conversation.id', ondelete='CASCADE'),
        nullable=False,
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False, default='')
    additional_info: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Relationships
    conversation: Mapped['Conversation'] = relationship(back_populates='messages')

    # Indexes
    __table_args__ = (
        Index('idx_message_conversation', 'conversation_id'),
    )
