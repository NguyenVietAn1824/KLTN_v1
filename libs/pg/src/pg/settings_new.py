from __future__ import annotations

"""PostgreSQL database settings.

Configuration for database connection following sun_assistant pattern.
"""

from base import CustomBaseModel as BaseModel
from pydantic import Field


class PostgresSettings(BaseModel):
    """PostgreSQL database connection settings.

    Attributes:
        username (str): Database username
        password (str): Database password
        host (str): Database host address
        port (int): Database port (default: 5432)
        db (str): Database name
    """

    username: str = Field(
        description='PostgreSQL username',
    )
    password: str = Field(
        description='PostgreSQL password',
    )
    host: str = Field(
        default='localhost',
        description='Database host address',
    )
    port: int = Field(
        default=5432,
        description='Database port',
    )
    db: str = Field(
        description='Database name',
    )
