-- ============================================
-- HanoiAir Database Schema - Version 2
-- Comprehensive schema based on all available APIs
-- ============================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search

-- ============================================
-- 1. PROVINCES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS provinces (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    minx DECIMAL(11, 8),  -- Bounding box
    miny DECIMAL(11, 8),
    maxx DECIMAL(11, 8),
    maxy DECIMAL(11, 8),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE provinces IS 'Thông tin các tỉnh/thành phố';
COMMENT ON COLUMN provinces.minx IS 'Kinh độ tây (bounding box)';
COMMENT ON COLUMN provinces.miny IS 'Vĩ độ nam (bounding box)';

-- Insert Hà Nội
INSERT INTO provinces (id, name, minx, miny, maxx, maxy) 
VALUES ('12', 'Hà Nội', 105.285352, 20.564283, 106.020128, 21.385421)
ON CONFLICT (id) DO NOTHING;

-- ============================================
-- 2. DISTRICTS TABLE (Quận/Huyện)
-- ============================================
CREATE TABLE IF NOT EXISTS districts (
    id SERIAL PRIMARY KEY,
    internal_id VARCHAR(50) UNIQUE NOT NULL,  -- ID_XXXXX format
    administrative_id VARCHAR(50) UNIQUE,      -- VNM.27.X_1 format
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) DEFAULT 'district',
    province_id VARCHAR(50) DEFAULT '12' REFERENCES provinces(id),
    minx DECIMAL(11, 8),  -- District bounding box
    miny DECIMAL(11, 8),
    maxx DECIMAL(11, 8),
    maxy DECIMAL(11, 8),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_districts_name ON districts(name);
CREATE INDEX idx_districts_internal_id ON districts(internal_id);
CREATE INDEX idx_districts_admin_id ON districts(administrative_id);
CREATE INDEX idx_districts_name_trgm ON districts USING gin(name gin_trgm_ops);

COMMENT ON TABLE districts IS 'Danh sách quận/huyện tại Hà Nội với cả 2 format ID';
COMMENT ON COLUMN districts.internal_id IS 'Internal ID (ID_XXXXX) - dùng cho Forecast API';
COMMENT ON COLUMN districts.administrative_id IS 'Administrative ID (VNM.27.X_1) - dùng cho Rankings API';

-- ============================================
-- 3. CURRENT AQI DATA (Dữ liệu AQI hiện tại)
-- ============================================
CREATE TABLE IF NOT EXISTS current_aqi (
    id SERIAL PRIMARY KEY,
    district_internal_id VARCHAR(50) NOT NULL REFERENCES districts(internal_id) ON DELETE CASCADE,
    measurement_date DATE NOT NULL,
    measurement_time TIMESTAMP NOT NULL,
    aqi_value DECIMAL(10, 2),
    pm25_value DECIMAL(10, 2),
    pm10_value DECIMAL(10, 2),
    component_id VARCHAR(50) DEFAULT 'aqi',
    data_source VARCHAR(100) DEFAULT 'district_avg_statistic',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(district_internal_id, measurement_time, component_id)
);

CREATE INDEX idx_current_aqi_date ON current_aqi(measurement_date);
CREATE INDEX idx_current_aqi_district ON current_aqi(district_internal_id);
CREATE INDEX idx_current_aqi_value ON current_aqi(aqi_value);
CREATE INDEX idx_current_aqi_component ON current_aqi(component_id);

COMMENT ON TABLE current_aqi IS 'Dữ liệu AQI hiện tại từ District Statistics API';
COMMENT ON COLUMN current_aqi.data_source IS 'Nguồn dữ liệu: district_avg_statistic, wmts_tiles, etc.';

-- ============================================
-- 4. AQI RANKINGS (Xếp hạng theo ngày)
-- ============================================
CREATE TABLE IF NOT EXISTS aqi_rankings (
    id SERIAL PRIMARY KEY,
    district_admin_id VARCHAR(50) NOT NULL REFERENCES districts(administrative_id) ON DELETE CASCADE,
    ranking_date DATE NOT NULL,
    rank INTEGER NOT NULL,
    aqi_avg DECIMAL(10, 2) NOT NULL,
    aqi_prev DECIMAL(10, 2),  -- AQI ngày trước để so sánh
    aqi_change DECIMAL(10, 2),  -- Computed: aqi_avg - aqi_prev
    component_id VARCHAR(50) DEFAULT 'pm25',
    group_id VARCHAR(50) DEFAULT 'satellite_aqi_pm25',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(district_admin_id, ranking_date, component_id)
);

CREATE INDEX idx_rankings_date ON aqi_rankings(ranking_date);
CREATE INDEX idx_rankings_district ON aqi_rankings(district_admin_id);
CREATE INDEX idx_rankings_rank ON aqi_rankings(rank);
CREATE INDEX idx_rankings_aqi ON aqi_rankings(aqi_avg);

COMMENT ON TABLE aqi_rankings IS 'Xếp hạng AQI của các quận/huyện (Rankings API)';
COMMENT ON COLUMN aqi_rankings.rank IS 'Thứ hạng (1 = cao nhất/tệ nhất)';

-- ============================================
-- 5. FORECAST DATA (Dữ liệu dự báo)
-- ============================================
CREATE TABLE IF NOT EXISTS forecast_data (
    id SERIAL PRIMARY KEY,
    district_internal_id VARCHAR(50) NOT NULL REFERENCES districts(internal_id) ON DELETE CASCADE,
    forecast_date DATE NOT NULL,
    base_date DATE NOT NULL,  -- Ngày làm cơ sở dự báo
    days_ahead INTEGER,  -- Số ngày cách base_date (âm = historical, 0 = current, dương = forecast)
    pm25_value DECIMAL(10, 2),
    aqi_value DECIMAL(10, 2),
    component VARCHAR(50) DEFAULT 'PM2.5',
    groupcomponent_id VARCHAR(50) DEFAULT '63',
    is_historical BOOLEAN DEFAULT FALSE,
    is_current BOOLEAN DEFAULT FALSE,
    is_forecast BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(district_internal_id, forecast_date, component)
);

CREATE INDEX idx_forecast_date ON forecast_data(forecast_date);
CREATE INDEX idx_forecast_district ON forecast_data(district_internal_id);
CREATE INDEX idx_forecast_base_date ON forecast_data(base_date);
CREATE INDEX idx_forecast_is_forecast ON forecast_data(is_forecast);
CREATE INDEX idx_forecast_is_historical ON forecast_data(is_historical);

COMMENT ON TABLE forecast_data IS 'Dữ liệu dự báo và lịch sử từ Forecast API';
COMMENT ON COLUMN forecast_data.days_ahead IS 'Số ngày so với base_date: <0=lịch sử, 0=hiện tại, >0=dự báo';

-- ============================================
-- 6. HISTORICAL DATA (Dữ liệu lịch sử cấp tỉnh)
-- ============================================
CREATE TABLE IF NOT EXISTS historical_data (
    id SERIAL PRIMARY KEY,
    province_id VARCHAR(50) NOT NULL REFERENCES provinces(id) ON DELETE CASCADE,
    measurement_date DATE NOT NULL,
    pm25_value DECIMAL(10, 2),
    aqi_value DECIMAL(10, 2),
    component VARCHAR(50) DEFAULT 'PM2.5',
    groupcomponent_id VARCHAR(50) DEFAULT '63',
    title_group VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(province_id, measurement_date, component)
);

CREATE INDEX idx_historical_date ON historical_data(measurement_date);
CREATE INDEX idx_historical_province ON historical_data(province_id);
CREATE INDEX idx_historical_component ON historical_data(component);

COMMENT ON TABLE historical_data IS 'Dữ liệu lịch sử PM2.5/AQI cấp tỉnh (Province Historical API)';

-- ============================================
-- 7. GRID AQI DATA (Dữ liệu lưới 1km²)
-- ============================================
CREATE TABLE IF NOT EXISTS grid_aqi_data (
    id SERIAL PRIMARY KEY,
    latitude DECIMAL(10, 7) NOT NULL,
    longitude DECIMAL(10, 7) NOT NULL,
    aqi_pm25 DECIMAL(10, 2) NOT NULL,
    measurement_time TIMESTAMP NOT NULL,
    parent_id VARCHAR(50),  -- vea, hnepa
    group_id VARCHAR(50),
    oid INTEGER,
    district_internal_id VARCHAR(50) REFERENCES districts(internal_id),  -- Optional: link to district
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(latitude, longitude, measurement_time)
);

CREATE INDEX idx_grid_coords ON grid_aqi_data(latitude, longitude);
CREATE INDEX idx_grid_time ON grid_aqi_data(measurement_time);
CREATE INDEX idx_grid_aqi ON grid_aqi_data(aqi_pm25);
CREATE INDEX idx_grid_district ON grid_aqi_data(district_internal_id);

COMMENT ON TABLE grid_aqi_data IS 'Dữ liệu AQI theo lưới 1km² từ WMTS Tiles';

-- ============================================
-- 8. COMPONENT DEFINITIONS (Định nghĩa các chỉ số)
-- ============================================
CREATE TABLE IF NOT EXISTS component_definitions (
    id SERIAL PRIMARY KEY,
    component_id VARCHAR(50) UNIQUE NOT NULL,
    groupcomponent_id VARCHAR(50),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    unit VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO component_definitions (component_id, groupcomponent_id, name, description, unit) VALUES
('aqi', NULL, 'AQI', 'Air Quality Index', 'index'),
('pm25', '63', 'PM2.5', 'Bụi mịn PM2.5', 'µg/m³'),
('pm10', NULL, 'PM10', 'Bụi PM10', 'µg/m³'),
('o3', NULL, 'O3', 'Ozone', 'ppb'),
('no2', NULL, 'NO2', 'Nitrogen Dioxide', 'ppb'),
('so2', NULL, 'SO2', 'Sulfur Dioxide', 'ppb'),
('co', NULL, 'CO', 'Carbon Monoxide', 'ppm')
ON CONFLICT (component_id) DO NOTHING;

-- ============================================
-- 9. DATA SOURCE LOG (Nhật ký crawl data)
-- ============================================
CREATE TABLE IF NOT EXISTS data_source_log (
    id SERIAL PRIMARY KEY,
    api_endpoint VARCHAR(255) NOT NULL,
    api_method VARCHAR(10) DEFAULT 'GET',
    request_payload JSONB,
    response_code INTEGER,
    records_fetched INTEGER,
    error_message TEXT,
    crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_log_endpoint ON data_source_log(api_endpoint);
CREATE INDEX idx_log_date ON data_source_log(crawled_at);

COMMENT ON TABLE data_source_log IS 'Nhật ký các lần crawl dữ liệu từ API';

-- ============================================
-- VIEWS
-- ============================================

-- View 1: Latest AQI Rankings
CREATE OR REPLACE VIEW v_latest_rankings AS
SELECT 
    d.name AS district_name,
    r.rank,
    r.aqi_avg AS current_aqi,
    r.aqi_prev AS previous_aqi,
    r.aqi_change,
    CASE 
        WHEN r.aqi_avg <= 50 THEN 'Tốt'
        WHEN r.aqi_avg <= 100 THEN 'Trung bình'
        WHEN r.aqi_avg <= 150 THEN 'Kém'
        WHEN r.aqi_avg <= 200 THEN 'Xấu'
        WHEN r.aqi_avg <= 300 THEN 'Rất xấu'
        ELSE 'Nguy hại'
    END AS aqi_level,
    r.ranking_date
FROM aqi_rankings r
JOIN districts d ON r.district_admin_id = d.administrative_id
WHERE r.ranking_date = (SELECT MAX(ranking_date) FROM aqi_rankings)
ORDER BY r.rank ASC;

-- View 2: Current AQI Summary
CREATE OR REPLACE VIEW v_current_aqi_summary AS
SELECT 
    d.name AS district_name,
    c.aqi_value,
    c.pm25_value,
    c.measurement_date,
    CASE 
        WHEN c.aqi_value <= 50 THEN 'Tốt'
        WHEN c.aqi_value <= 100 THEN 'Trung bình'
        WHEN c.aqi_value <= 150 THEN 'Kém'
        WHEN c.aqi_value <= 200 THEN 'Xấu'
        WHEN c.aqi_value <= 300 THEN 'Rất xấu'
        ELSE 'Nguy hại'
    END AS aqi_level
FROM current_aqi c
JOIN districts d ON c.district_internal_id = d.internal_id
WHERE c.measurement_date = (SELECT MAX(measurement_date) FROM current_aqi)
ORDER BY c.aqi_value DESC;

-- View 3: Forecast Summary (7 days ahead)
CREATE OR REPLACE VIEW v_forecast_7days AS
SELECT 
    d.name AS district_name,
    f.forecast_date,
    f.aqi_value,
    f.pm25_value,
    f.days_ahead,
    CASE 
        WHEN f.aqi_value <= 50 THEN 'Tốt'
        WHEN f.aqi_value <= 100 THEN 'Trung bình'
        WHEN f.aqi_value <= 150 THEN 'Kém'
        WHEN f.aqi_value <= 200 THEN 'Xấu'
        WHEN f.aqi_value <= 300 THEN 'Rất xấu'
        ELSE 'Nguy hại'
    END AS forecast_level
FROM forecast_data f
JOIN districts d ON f.district_internal_id = d.internal_id
WHERE f.is_forecast = TRUE 
  AND f.days_ahead > 0 
  AND f.days_ahead <= 7
ORDER BY d.name, f.forecast_date;

-- View 4: Historical Trend (Province)
CREATE OR REPLACE VIEW v_historical_trend AS
SELECT 
    p.name AS province_name,
    h.measurement_date,
    h.pm25_value,
    h.aqi_value,
    LAG(h.aqi_value) OVER (ORDER BY h.measurement_date) AS prev_aqi,
    h.aqi_value - LAG(h.aqi_value) OVER (ORDER BY h.measurement_date) AS aqi_change
FROM historical_data h
JOIN provinces p ON h.province_id = p.id
ORDER BY h.measurement_date DESC;

-- View 5: District Statistics Summary
CREATE OR REPLACE VIEW v_district_statistics AS
SELECT 
    d.name AS district_name,
    d.internal_id,
    d.administrative_id,
    COUNT(DISTINCT c.measurement_date) AS days_with_data,
    AVG(c.aqi_value) AS avg_aqi,
    MIN(c.aqi_value) AS min_aqi,
    MAX(c.aqi_value) AS max_aqi,
    MAX(c.measurement_date) AS latest_date
FROM districts d
LEFT JOIN current_aqi c ON d.internal_id = c.district_internal_id
GROUP BY d.id, d.name, d.internal_id, d.administrative_id
ORDER BY avg_aqi DESC NULLS LAST;

-- ============================================
-- FUNCTIONS
-- ============================================

-- Function 1: Get District Forecast
CREATE OR REPLACE FUNCTION get_district_forecast(
    p_district_name VARCHAR,
    p_days_ahead INTEGER DEFAULT 7
)
RETURNS TABLE (
    district_name VARCHAR,
    forecast_date DATE,
    pm25_value DECIMAL,
    aqi_value DECIMAL,
    days_from_now INTEGER,
    forecast_level TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        d.name,
        f.forecast_date,
        f.pm25_value,
        f.aqi_value,
        f.days_ahead,
        CASE 
            WHEN f.aqi_value <= 50 THEN 'Tốt'
            WHEN f.aqi_value <= 100 THEN 'Trung bình'
            WHEN f.aqi_value <= 150 THEN 'Kém'
            WHEN f.aqi_value <= 200 THEN 'Xấu'
            WHEN f.aqi_value <= 300 THEN 'Rất xấu'
            ELSE 'Nguy hại'
        END AS forecast_level
    FROM districts d
    JOIN forecast_data f ON d.internal_id = f.district_internal_id
    WHERE d.name ILIKE '%' || p_district_name || '%'
      AND f.is_forecast = TRUE
      AND f.days_ahead > 0
      AND f.days_ahead <= p_days_ahead
    ORDER BY f.forecast_date ASC;
END;
$$ LANGUAGE plpgsql;

-- Function 2: Compare Districts by AQI
CREATE OR REPLACE FUNCTION compare_districts_aqi(
    p_date DATE DEFAULT CURRENT_DATE
)
RETURNS TABLE (
    district_name VARCHAR,
    aqi_value DECIMAL,
    pm25_value DECIMAL,
    aqi_level TEXT,
    rank BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        d.name,
        c.aqi_value,
        c.pm25_value,
        CASE 
            WHEN c.aqi_value <= 50 THEN 'Tốt'
            WHEN c.aqi_value <= 100 THEN 'Trung bình'
            WHEN c.aqi_value <= 150 THEN 'Kém'
            WHEN c.aqi_value <= 200 THEN 'Xấu'
            WHEN c.aqi_value <= 300 THEN 'Rất xấu'
            ELSE 'Nguy hại'
        END AS aqi_level,
        ROW_NUMBER() OVER (ORDER BY c.aqi_value DESC) AS rank
    FROM districts d
    JOIN current_aqi c ON d.internal_id = c.district_internal_id
    WHERE c.measurement_date = p_date
    ORDER BY c.aqi_value DESC;
END;
$$ LANGUAGE plpgsql;

-- Function 3: Find Nearest Grid Point
CREATE OR REPLACE FUNCTION find_nearest_grid_aqi(
    p_lat DECIMAL,
    p_lon DECIMAL,
    p_limit INTEGER DEFAULT 5
)
RETURNS TABLE (
    latitude DECIMAL,
    longitude DECIMAL,
    aqi_pm25 DECIMAL,
    distance_km DECIMAL,
    measurement_time TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        g.latitude,
        g.longitude,
        g.aqi_pm25,
        (6371 * acos(cos(radians(p_lat)) * cos(radians(g.latitude)) * 
         cos(radians(g.longitude) - radians(p_lon)) + 
         sin(radians(p_lat)) * sin(radians(g.latitude)))) AS distance_km,
        g.measurement_time
    FROM grid_aqi_data g
    WHERE g.measurement_time = (SELECT MAX(measurement_time) FROM grid_aqi_data)
    ORDER BY distance_km ASC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Function 4: AQI Trend Analysis
CREATE OR REPLACE FUNCTION analyze_aqi_trend(
    p_district_name VARCHAR,
    p_days INTEGER DEFAULT 7
)
RETURNS TABLE (
    measurement_date DATE,
    aqi_value DECIMAL,
    trend TEXT,
    change_from_prev DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    WITH district_aqi AS (
        SELECT 
            c.measurement_date,
            c.aqi_value,
            LAG(c.aqi_value) OVER (ORDER BY c.measurement_date) AS prev_aqi
        FROM current_aqi c
        JOIN districts d ON c.district_internal_id = d.internal_id
        WHERE d.name ILIKE '%' || p_district_name || '%'
          AND c.measurement_date >= CURRENT_DATE - p_days
        ORDER BY c.measurement_date DESC
    )
    SELECT 
        da.measurement_date,
        da.aqi_value,
        CASE 
            WHEN da.aqi_value > da.prev_aqi THEN 'Tăng'
            WHEN da.aqi_value < da.prev_aqi THEN 'Giảm'
            ELSE 'Không đổi'
        END AS trend,
        (da.aqi_value - da.prev_aqi) AS change_from_prev
    FROM district_aqi da;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- TRIGGERS
-- ============================================

-- Trigger 1: Auto-update aqi_change in rankings
CREATE OR REPLACE FUNCTION update_aqi_change()
RETURNS TRIGGER AS $$
BEGIN
    NEW.aqi_change := NEW.aqi_avg - COALESCE(NEW.aqi_prev, NEW.aqi_avg);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_aqi_change
    BEFORE INSERT OR UPDATE ON aqi_rankings
    FOR EACH ROW
    EXECUTE FUNCTION update_aqi_change();

-- Trigger 2: Auto-classify forecast type
CREATE OR REPLACE FUNCTION classify_forecast_type()
RETURNS TRIGGER AS $$
BEGIN
    NEW.days_ahead := NEW.forecast_date - NEW.base_date;
    NEW.is_historical := NEW.days_ahead < 0;
    NEW.is_current := NEW.days_ahead = 0;
    NEW.is_forecast := NEW.days_ahead > 0;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_classify_forecast
    BEFORE INSERT OR UPDATE ON forecast_data
    FOR EACH ROW
    EXECUTE FUNCTION classify_forecast_type();

-- Trigger 3: Update timestamp
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_provinces
    BEFORE UPDATE ON provinces
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_update_districts
    BEFORE UPDATE ON districts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- ============================================
-- INITIALIZATION COMPLETE
-- ============================================

DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE '✅ HanoiAir Database Schema V2 Initialized!';
    RAISE NOTICE '========================================';
    RAISE NOTICE '📊 Tables: 9 (provinces, districts, current_aqi, aqi_rankings, forecast_data, historical_data, grid_aqi_data, component_definitions, data_source_log)';
    RAISE NOTICE '📈 Views: 5 (latest_rankings, current_aqi_summary, forecast_7days, historical_trend, district_statistics)';
    RAISE NOTICE '🔧 Functions: 4 (get_district_forecast, compare_districts_aqi, find_nearest_grid_aqi, analyze_aqi_trend)';
    RAISE NOTICE '⚡ Triggers: 3 (update_aqi_change, classify_forecast, update_timestamp)';
    RAISE NOTICE '========================================';
END $$;
