-- ============================================
-- Add Hasura Data Source via SQL
-- ============================================

-- Connect to Hasura metadata database
-- Run this with: psql -U hanoiair_user -d hanoiair_db -f add_hasura_datasource.sql

-- Track all tables
SELECT hdb_catalog.hdb_track_table('{"schema": "public", "name": "provinces"}');
SELECT hdb_catalog.hdb_track_table('{"schema": "public", "name": "districts"}');
SELECT hdb_catalog.hdb_track_table('{"schema": "public", "name": "air_component"}');
SELECT hdb_catalog.hdb_track_table('{"schema": "public", "name": "distric_stats"}');

-- Track relationships
-- districts -> province
SELECT hdb_catalog.hdb_create_object_relationship('{"table": {"schema": "public", "name": "districts"}, "name": "province", "using": {"foreign_key_constraint_on": "province_id"}}');

-- districts -> stats (array relationship)
SELECT hdb_catalog.hdb_create_array_relationship('{"table": {"schema": "public", "name": "districts"}, "name": "stats", "using": {"foreign_key_constraint_on": {"table": {"schema": "public", "name": "distric_stats"}, "column": "district_id"}}}');

-- distric_stats -> district
SELECT hdb_catalog.hdb_create_object_relationship('{"table": {"schema": "public", "name": "distric_stats"}, "name": "district", "using": {"foreign_key_constraint_on": "district_id"}}');

-- provinces -> districts (array relationship)
SELECT hdb_catalog.hdb_create_array_relationship('{"table": {"schema": "public", "name": "provinces"}, "name": "districts", "using": {"foreign_key_constraint_on": {"table": {"schema": "public", "name": "districts"}, "column": "province_id"}}}');

-- Enable aggregation queries
SELECT hdb_catalog.hdb_set_table_is_enum('{"table": {"schema": "public", "name": "air_component"}, "is_enum": true}');
