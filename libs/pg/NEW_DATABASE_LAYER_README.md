from **future** import annotations

"""
Updated PostgreSQL Database Layer for KLTN AQI System

This module provides a restructured database layer following sun_assistant conventions:

## Architecture Pattern (from sun_assistant):

1. **Models** (`model.py`): SQLAlchemy ORM models
2. **Schemas** (`database/schemas.py`): Pydantic schemas for validation
3. **Repository** (`database/repository.py`): Abstract interface
4. **Controllers** (`database/*_controller.py`): Concrete implementations
5. **Main Database** (`database/aqi_database_new.py`): Combined interface
6. **Utils** (`database/utils.py`): Generic CRUD operations

## Key Improvements:

- ✅ Separation of ORM models (SQLAlchemy) and schemas (Pydantic)
- ✅ Repository pattern for consistent interface
- ✅ Controller classes using utility functions to reduce boilerplate
- ✅ Proper session management with context managers
- ✅ Transaction handling (auto-commit/rollback)
- ✅ Type hints and comprehensive docstrings
- ✅ Specialized query methods for AQI-specific operations

## Usage Example:

```python
from pg import AQIDatabase, PostgresSettings

# Create database instance
settings = PostgresSettings(
    username='postgres',
    password='password',
    host='localhost',
    port=5432,
    db='aqi_db'
)

db = AQIDatabase(
    username=settings.username,
    password=settings.password,
    host=settings.host,
    port=settings.port,
    db=settings.db,
)

# Use with context manager
with db.get_session() as session:
    # Search for district
    districts = db.search_districts_by_name(session, "Hoàn Kiếm")

    # Get latest AQI
    if districts:
        stats = db.get_latest_stats_by_district(session, districts[0].id)
        print(f"Current AQI: {stats.aqi_value}")

    # Compare districts
    district_ids = ['001', '002', '003']
    comparison = db.compare_districts_aqi(session, district_ids)
    for district, stats in comparison:
        print(f"{district.name}: AQI {stats.aqi_value}")
```

## Integration with Text2SQL System:

The new database layer provides methods that can be called directly from
SQL execution results or used by the Text2SQL system for data retrieval.

## Migration Notes:

- Old controllers (`district_controller.py`, `distric_stats_controller.py`) can be deprecated
- New controllers add specialized query methods for AQI analysis
- All new files have `_new` suffix to avoid conflicts during migration
- Once tested, rename files to replace old versions

## Files Created:

1. `database/utils.py` - Generic CRUD utilities
2. `database/schemas.py` - Pydantic schemas
3. `database/repository.py` - Abstract repository interface
4. `database/province_controller.py` - Province CRUD + queries
5. `database/district_new_controller.py` - District CRUD + search
6. `database/distric_stats_new_controller.py` - Stats CRUD + AQI analytics
7. `database/air_component_controller.py` - Air component CRUD
8. `database/aqi_database_new.py` - Main database class
9. `settings_new.py` - Database settings

## Next Steps:

1. ✅ Test the new database layer
2. ✅ Integrate with Text2SQL system
3. ✅ Create Hasura GraphQL schema
4. ✅ Implement GraphQL query generation (Apollo-style)
5. ✅ Build complete agentic workflow
   """

# Export classes and types

from .database.aqi_database_new import AQIDatabase
from .database.schemas import (
Province,
District,
DistricStats,
AirComponent,
DatabaseSchema,
)
from .settings_new import PostgresSettings

**all** = [
'AQIDatabase',
'Province',
'District',
'DistricStats',
'AirComponent',
'DatabaseSchema',
'PostgresSettings',
]
