-- ============================================
-- HanoiAir Database Schema
-- ============================================

-- Tạo extension nếu cần (cho UUID, PostGIS trong tương lai, v.v.)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- 1. Bảng Districts (Quận/Huyện)
-- ============================================
CREATE TABLE IF NOT EXISTS districts (
    id VARCHAR(50) PRIMARY KEY,
    administrative_id VARCHAR(50) UNIQUE,  -- VNM.27.X_1 format
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) DEFAULT 'district',
    province_id VARCHAR(50) DEFAULT '12',  -- Hà Nội
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_districts_name ON districts(name);
CREATE INDEX idx_districts_admin_id ON districts(administrative_id);

COMMENT ON TABLE districts IS 'Danh sách các quận/huyện tại Hà Nội';
COMMENT ON COLUMN districts.id IS 'Internal ID (ID_XXXXX format)';
COMMENT ON COLUMN districts.administrative_id IS 'Administrative ID (VNM.27.X_1 format)';

-- ============================================
-- 2. Bảng AQI Rankings (Xếp hạng AQI hàng ngày)
-- ============================================
CREATE TABLE IF NOT EXISTS aqi_rankings (
    id SERIAL PRIMARY KEY,
    district_id VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    rank INTEGER NOT NULL,
    aqi_avg DECIMAL(10, 2) NOT NULL,
    aqi_prev DECIMAL(10, 2),  -- AQI ngày trước
    component_id VARCHAR(50) DEFAULT 'pm25',
    group_id VARCHAR(50) DEFAULT 'satellite_aqi_pm25',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (district_id) REFERENCES districts(administrative_id) ON DELETE CASCADE,
    UNIQUE(district_id, date, component_id)
);

CREATE INDEX idx_aqi_rankings_date ON aqi_rankings(date);
CREATE INDEX idx_aqi_rankings_district ON aqi_rankings(district_id);
CREATE INDEX idx_aqi_rankings_rank ON aqi_rankings(rank);
CREATE INDEX idx_aqi_rankings_aqi ON aqi_rankings(aqi_avg);

COMMENT ON TABLE aqi_rankings IS 'Xếp hạng AQI của các quận/huyện theo ngày';
COMMENT ON COLUMN aqi_rankings.rank IS 'Thứ hạng (1 = tệ nhất)';
COMMENT ON COLUMN aqi_rankings.aqi_avg IS 'AQI trung bình trong ngày';
COMMENT ON COLUMN aqi_rankings.aqi_prev IS 'AQI trung bình ngày trước (để so sánh)';

-- ============================================
-- 3. Bảng Forecast Data (Dữ liệu dự báo)
-- ============================================
CREATE TABLE IF NOT EXISTS forecast_data (
    id SERIAL PRIMARY KEY,
    district_id VARCHAR(50) NOT NULL,
    forecast_date DATE NOT NULL,
    forecast_aqi DECIMAL(10, 2) NOT NULL,
    component_id VARCHAR(50) DEFAULT 'pm25',
    group_id VARCHAR(50) DEFAULT 'satellite_aqi_pm25',
    is_historical BOOLEAN DEFAULT FALSE,  -- TRUE nếu là dữ liệu lịch sử, FALSE nếu là dự báo
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (district_id) REFERENCES districts(id) ON DELETE CASCADE,
    UNIQUE(district_id, forecast_date, component_id)
);

CREATE INDEX idx_forecast_date ON forecast_data(forecast_date);
CREATE INDEX idx_forecast_district ON forecast_data(district_id);
CREATE INDEX idx_forecast_is_historical ON forecast_data(is_historical);

COMMENT ON TABLE forecast_data IS 'Dữ liệu dự báo và lịch sử AQI';
COMMENT ON COLUMN forecast_data.is_historical IS 'TRUE = dữ liệu lịch sử, FALSE = dự báo tương lai';

-- ============================================
-- 4. Bảng Grid AQI Data (Dữ liệu theo lưới 1km²)
-- ============================================
CREATE TABLE IF NOT EXISTS grid_aqi_data (
    id SERIAL PRIMARY KEY,
    latitude DECIMAL(10, 7) NOT NULL,
    longitude DECIMAL(10, 7) NOT NULL,
    aqi_pm25 DECIMAL(10, 2) NOT NULL,
    datetime_shooting TIMESTAMP NOT NULL,
    parent_id VARCHAR(50),  -- Nguồn dữ liệu: vea, hnepa
    group_id VARCHAR(50),
    oid INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(latitude, longitude, datetime_shooting)
);

CREATE INDEX idx_grid_coords ON grid_aqi_data(latitude, longitude);
CREATE INDEX idx_grid_datetime ON grid_aqi_data(datetime_shooting);
CREATE INDEX idx_grid_aqi ON grid_aqi_data(aqi_pm25);

COMMENT ON TABLE grid_aqi_data IS 'Dữ liệu AQI theo lưới 1km² (từ WMTS tiles)';
COMMENT ON COLUMN grid_aqi_data.latitude IS 'Vĩ độ (coor_y)';
COMMENT ON COLUMN grid_aqi_data.longitude IS 'Kinh độ (coor_x)';

-- ============================================
-- 5. Bảng Province Info (Thông tin tỉnh/thành phố)
-- ============================================
CREATE TABLE IF NOT EXISTS provinces (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    minx DECIMAL(10, 7),  -- Bounding box
    miny DECIMAL(10, 7),
    maxx DECIMAL(10, 7),
    maxy DECIMAL(10, 7),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE provinces IS 'Thông tin tỉnh/thành phố và bounding box';

-- Insert Hà Nội
INSERT INTO provinces (id, name, minx, miny, maxx, maxy) 
VALUES ('12', 'Hà Nội', 105.285352, 20.564283, 106.020128, 21.385421)
ON CONFLICT (id) DO NOTHING;

-- ============================================
-- 6. View: AQI Summary (Tổng hợp theo quận/huyện)
-- ============================================
CREATE OR REPLACE VIEW aqi_summary AS
SELECT 
    d.id,
    d.name AS district_name,
    r.date,
    r.rank,
    r.aqi_avg,
    r.aqi_prev,
    (r.aqi_avg - r.aqi_prev) AS aqi_change,
    CASE 
        WHEN r.aqi_avg <= 50 THEN 'Tốt'
        WHEN r.aqi_avg <= 100 THEN 'Trung bình'
        WHEN r.aqi_avg <= 150 THEN 'Kém'
        WHEN r.aqi_avg <= 200 THEN 'Xấu'
        WHEN r.aqi_avg <= 300 THEN 'Rất xấu'
        ELSE 'Nguy hại'
    END AS aqi_level
FROM districts d
JOIN aqi_rankings r ON d.administrative_id = r.district_id
ORDER BY r.date DESC, r.rank ASC;

COMMENT ON VIEW aqi_summary IS 'Tổng hợp AQI của các quận/huyện với mức độ đánh giá';

-- ============================================
-- 7. View: Latest Rankings (Xếp hạng mới nhất)
-- ============================================
CREATE OR REPLACE VIEW latest_rankings AS
SELECT 
    d.name AS district_name,
    r.rank,
    r.aqi_avg,
    r.aqi_prev,
    (r.aqi_avg - r.aqi_prev) AS change,
    r.date
FROM districts d
JOIN aqi_rankings r ON d.administrative_id = r.district_id
WHERE r.date = (SELECT MAX(date) FROM aqi_rankings)
ORDER BY r.rank ASC;

COMMENT ON VIEW latest_rankings IS 'Xếp hạng AQI mới nhất của các quận/huyện';

-- ============================================
-- 8. Function: Get District Forecast
-- ============================================
CREATE OR REPLACE FUNCTION get_district_forecast(
    p_district_name VARCHAR,
    p_days_ahead INTEGER DEFAULT 7
)
RETURNS TABLE (
    district_name VARCHAR,
    forecast_date DATE,
    forecast_aqi DECIMAL,
    days_from_now INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        d.name,
        f.forecast_date,
        f.forecast_aqi,
        (f.forecast_date - CURRENT_DATE)::INTEGER AS days_from_now
    FROM districts d
    JOIN forecast_data f ON d.id = f.district_id
    WHERE d.name ILIKE '%' || p_district_name || '%'
      AND f.is_historical = FALSE
      AND f.forecast_date > CURRENT_DATE
      AND f.forecast_date <= CURRENT_DATE + p_days_ahead
    ORDER BY f.forecast_date ASC;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_district_forecast IS 'Lấy dự báo AQI cho quận/huyện trong N ngày tới';

-- ============================================
-- 9. Function: Compare Districts
-- ============================================
CREATE OR REPLACE FUNCTION compare_districts(
    p_date DATE DEFAULT CURRENT_DATE
)
RETURNS TABLE (
    district_name VARCHAR,
    rank INTEGER,
    aqi_avg DECIMAL,
    aqi_level VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        d.name,
        r.rank,
        r.aqi_avg,
        CASE 
            WHEN r.aqi_avg <= 50 THEN 'Tốt'
            WHEN r.aqi_avg <= 100 THEN 'Trung bình'
            WHEN r.aqi_avg <= 150 THEN 'Kém'
            WHEN r.aqi_avg <= 200 THEN 'Xấu'
            WHEN r.aqi_avg <= 300 THEN 'Rất xấu'
            ELSE 'Nguy hại'
        END AS aqi_level
    FROM districts d
    JOIN aqi_rankings r ON d.administrative_id = r.district_id
    WHERE r.date = p_date
    ORDER BY r.rank ASC;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION compare_districts IS 'So sánh AQI giữa các quận/huyện trong một ngày';

-- ============================================
-- 10. Trigger: Update timestamp
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_districts_updated_at
    BEFORE UPDATE ON districts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_provinces_updated_at
    BEFORE UPDATE ON provinces
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- Kết thúc schema initialization
-- ============================================

-- Hiển thị thông tin
DO $$
BEGIN
    RAISE NOTICE '✅ Database schema initialized successfully!';
    RAISE NOTICE '📊 Tables created: districts, aqi_rankings, forecast_data, grid_aqi_data, provinces';
    RAISE NOTICE '📈 Views created: aqi_summary, latest_rankings';
    RAISE NOTICE '🔧 Functions created: get_district_forecast, compare_districts';
END $$;
