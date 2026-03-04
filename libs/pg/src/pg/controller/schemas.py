from __future__ import annotations

"""Pydantic schemas for database models.

This module defines Pydantic schemas that correspond to SQLAlchemy ORM models.
These schemas are used for:
1. Data validation when inserting/updating records
2. Serialization of database records to JSON
3. Type hints and IDE autocompletion
4. API request/response models

The schemas follow sun_assistant conventions with DatabaseSchema base class.
"""

from datetime import datetime
from datetime import date as date_type
from typing import Optional

from base import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class Identified(BaseModel):
    """Base schema for models with ID field.

    Attributes:
        id: Primary key identifier (string or integer depending on model)
    """

    id: str | int


class Dated(BaseModel):
    """Base schema for models with timestamp fields.

    Attributes:
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
        deleted_at: Timestamp for soft delete
    """

    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None


class DatabaseSchema(Identified, Dated):
    """Base schema for all database models.

    Combines Identified and Dated to provide both ID and timestamp fields.
    Configures Pydantic to work with SQLAlchemy ORM models.
    """

    model_config = ConfigDict(
        from_attributes=True,  # Allow creating from SQLAlchemy models
        arbitrary_types_allowed=True,  # Allow complex types
    )


class Province(DatabaseSchema):
    """Province schema corresponding to provinces table.

    Attributes:
        id (str): Province identifier code
        name (str | None): Province name in Vietnamese
        districts (list[District] | None): Related districts (populated via relationship)
    """

    id: str  # type: ignore  # Override parent's id type
    name: str | None = Field(
        default=None,
        description='Province name in Vietnamese',
    )

    # Relationships
    districts: Optional[list['District']] = Field(
        default=None,
        description='List of districts in this province',
    )


class District(DatabaseSchema):
    """District schema corresponding to districts table.

    Attributes:
        id (str): District identifier code
        province_id (str): Foreign key to provinces table
        name (str): District name in Vietnamese
        normalized_name (str | None): Normalized name for searching (lowercase, no accents)
        administrative_id (str | None): Government administrative code
        province (Province | None): Related province (populated via relationship)
        stats (list[DistricStats] | None): Related statistics (populated via relationship)
    """

    id: str  # type: ignore  # Override parent's id type
    province_id: str = Field(
        description='Foreign key reference to provinces.id',
    )
    name: str = Field(
        description='District name in Vietnamese',
    )
    normalized_name: str | None = Field(
        default=None,
        description='Normalized name for searching (lowercase, no diacritics)',
    )
    administrative_id: str | None = Field(
        default=None,
        description='Government administrative code',
    )

    # Relationships
    province: Optional[Province] = Field(
        default=None,
        description='Related province record',
    )
    stats: Optional[list['DistricStats']] = Field(
        default=None,
        description='List of AQI statistics for this district',
    )


class AirComponent(DatabaseSchema):
    """Air component schema corresponding to air_component table.

    Represents measurable air quality components (e.g., PM2.5, PM10, O3, NO2).

    Attributes:
        id (int): Component identifier (auto-increment)
        name (str): Component name (e.g., 'PM2.5', 'AQI')
        description (str | None): Description of what this component measures
    """

    id: int  # type: ignore  # Override parent's id type
    name: str = Field(
        description='Air component name (e.g., PM2.5, AQI)',
    )
    description: str | None = Field(
        default=None,
        description='Description of the air component',
    )


class DistricStats(DatabaseSchema):
    """District statistics schema corresponding to distric_stats table.

    Contains air quality measurements for a specific district at a specific time.

    Attributes:
        id (int): Statistics record identifier (auto-increment)
        date (date): Date of measurement
        hour (int | None): Hour of measurement (0-23), None for daily average
        component_id (str): Type of air component measured
        aqi_value (int | None): Air Quality Index value
        pm25_value (int | None): PM2.5 concentration value
        district_id (str): Foreign key to districts table
        district (District | None): Related district (populated via relationship)
    """

    id: int  # type: ignore  # Override parent's id type
    date: date_type = Field(
        description='Date of measurement (YYYY-MM-DD)',
    )
    hour: int | None = Field(
        default=None,
        description='Hour of measurement (0-23), None for daily aggregate',
    )
    component_id: str = Field(
        description='Air component identifier (e.g., AQI, PM2.5)',
    )
    aqi_value: int | None = Field(
        default=None,
        description='Air Quality Index value',
    )
    pm25_value: int | None = Field(
        default=None,
        description='PM2.5 particle concentration',
    )
    district_id: str = Field(
        description='Foreign key reference to districts.id',
    )

    # Relationships
    district: Optional[District] = Field(
        default=None,
        description='Related district record',
    )


# Update forward references for relationships
Province.model_rebuild()
District.model_rebuild()
DistricStats.model_rebuild()


# ---------------------------------------------------------------------------
# User / Conversation / Message schemas
# ---------------------------------------------------------------------------


class User(DatabaseSchema):
    """User schema corresponding to user table.

    Attributes:
        id (str): User identifier
        full_name (str | None): Full name of the user
        email (str): Email address
        dob (datetime | None): Date of birth
        phone (str | None): Phone number
        gender (str | None): Gender
        avt_url (str | None): Avatar URL
        last_active (datetime): Last active timestamp
        role (str): User role
        status (str | None): User status
    """

    id: str  # type: ignore
    full_name: str | None = Field(default=None, description='Full name')
    email: str = Field(description='Email address')
    dob: datetime | None = Field(default=None, description='Date of birth')
    phone: str | None = Field(default=None, description='Phone number')
    gender: str | None = Field(default=None, description='Gender')
    avt_url: str | None = Field(default=None, description='Avatar URL')
    last_active: datetime | None = Field(default=None, description='Last active timestamp')
    role: str = Field(default='user', description='User role')
    status: str | None = Field(default=None, description='User status')


class UserAuthentication(DatabaseSchema):
    """User authentication schema corresponding to user_authentications table.

    Attributes:
        id (str): Authentication record identifier
        user_id (str): Foreign key to user table
        username (str): Username for login
        password (str): Hashed password
        social_id (str | None): Social login identifier
        mfa_enabled (bool): Whether MFA is enabled
    """

    id: str  # type: ignore
    user_id: str = Field(description='Foreign key to user table')
    username: str = Field(description='Username for login')
    password: str = Field(description='Hashed password')
    social_id: str | None = Field(default=None, description='Social login identifier')
    mfa_enabled: bool = Field(default=False, description='Whether MFA is enabled')


class Conversation(DatabaseSchema):
    """Conversation schema corresponding to conversation table.

    Attributes:
        id (str): Conversation identifier
        user_id (str): Foreign key to user table
        title (str): Title of the conversation
        summary (str): Summary of the conversation
        is_confirming (bool): Whether the conversation is in confirming state
    """

    id: str  # type: ignore
    user_id: str = Field(description='Foreign key to user table')
    title: str = Field(default='', description='Conversation title')
    summary: str = Field(default='', description='Conversation summary')
    is_confirming: bool = Field(default=False, description='Whether in confirming state')

    # Relationships
    messages: Optional[list['Message']] = Field(
        default=None,
        description='List of messages in this conversation',
    )


class Message(DatabaseSchema):
    """Message schema corresponding to message table.

    Attributes:
        id (str): Message identifier
        conversation_id (str): Foreign key to conversation table
        question (str): User question text
        answer (str): Assistant answer text
        additional_info (dict | None): Additional JSON metadata
    """

    id: str  # type: ignore
    conversation_id: str = Field(description='Foreign key to conversation table')
    question: str = Field(description='User question text')
    answer: str = Field(default='', description='Assistant answer text')
    additional_info: dict | None = Field(default=None, description='Additional JSON metadata')


# Rebuild all models for forward references
User.model_rebuild()
UserAuthentication.model_rebuild()
Conversation.model_rebuild()
Message.model_rebuild()
