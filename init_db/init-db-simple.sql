-- ============================================
-- HanoiAir Database Schema - Simple Version
-- Theo thiết kế của người dùng
-- ============================================

-- ============================================
-- 1. PROVINCES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS provinces (
    id TEXT PRIMARY KEY,
    name TEXT
);

-- Insert Hà Nội
INSERT INTO provinces (id, name) VALUES ('12', 'Hà Nội');

-- ============================================
-- 2. DISTRICTS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS districts (
    id TEXT PRIMARY KEY,
    province_id TEXT REFERENCES provinces(id),
    name TEXT NOT NULL,
    normalized_name TEXT,
    administrative_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_districts_province ON districts(province_id);
CREATE INDEX idx_districts_name ON districts(name);
CREATE INDEX idx_districts_admin_id ON districts(administrative_id);

-- ============================================
-- 3. AIR_COMPONENT TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS air_component (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert components
INSERT INTO air_component (name, description) VALUES
('aqi', 'Air Quality Index'),
('pm25', 'PM2.5 - Bụi mịn'),
('pm10', 'PM10 - Bụi thô'),
('o3', 'Ozone'),
('no2', 'Nitrogen Dioxide'),
('so2', 'Sulfur Dioxide'),
('co', 'Carbon Monoxide');

-- ============================================
-- 4. DISTRIC_STATS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS distric_stats (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    hour INTEGER,
    component_id TEXT NOT NULL,
    aqi_value INTEGER,
    pm25_value INTEGER,
    create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    district_id TEXT REFERENCES districts(id),
    UNIQUE(district_id, date, hour, component_id)
);

CREATE INDEX idx_stats_date ON distric_stats(date);
CREATE INDEX idx_stats_district ON distric_stats(district_id);
CREATE INDEX idx_stats_component ON distric_stats(component_id);
CREATE INDEX idx_stats_date_district ON distric_stats(date, district_id);

-- ============================================
-- DONE
-- ============================================
DO $$
BEGIN
    RAISE NOTICE '✅ Database schema initialized!';
    RAISE NOTICE '📊 Tables: provinces, districts, air_component, distric_stats';
END $$;
