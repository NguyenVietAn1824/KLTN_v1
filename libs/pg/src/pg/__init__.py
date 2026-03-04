from __future__ import annotations

from .aqi_database import AQIDatabase
from .aqi_database import AQIDatabase as SQLDatabase
from .controller.district_controller import DistrictController
from .controller.distric_stats_controller import DistricStatsController
from .controller.user_controller import UserController
from .controller.conversation_controller import ConversationController
from .controller.message_controller import MessageController
from .model import AirComponent
from .model import Base
from .model import Conversation
from .model import District
from .model import DistricStats
from .model import Message
from .model import Province
from .model import User
from .model import UserAuthentication
from .settings import PostgresSettings

# Alias for backward compatibility — aqi_agent imports `pg.models.Message`
from . import model as models  # noqa: F401

__all__ = [
    'Base',
    'Province',
    'District',
    'AirComponent',
    'DistricStats',
    'User',
    'UserAuthentication',
    'Conversation',
    'Message',
    'PostgresSettings',
    'AQIDatabase',
    'SQLDatabase',
    'DistrictController',
    'DistricStatsController',
    'UserController',
    'ConversationController',
    'MessageController',
    'models',
]
