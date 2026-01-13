#!/bin/bash
# Script import dữ liệu vào PostgreSQL sử dụng psql COPY

set -e

DB_CONTAINER="hanoiair_postgres"
DB_USER="hanoiair_user"
DB_NAME="hanoiair_db"

echo "======================================================================"
echo "📥 IMPORT DỮ LIỆU VÀO POSTGRESQL"
echo "======================================================================"

# 1. Copy CSV files vào container
echo ""
echo "📂 Bước 1: Copy CSV files vào container..."
docker cp districts_full.csv ${DB_CONTAINER}:/tmp/
docker cp current_aqi.csv ${DB_CONTAINER}:/tmp/
docker cp forecast.csv ${DB_CONTAINER}:/tmp/
[ -f rankings.csv ] && docker cp rankings.csv ${DB_CONTAINER}:/tmp/ || echo "⚠️  No rankings.csv"
[ -f historical.csv ] && docker cp historical.csv ${DB_CONTAINER}:/tmp/ || echo "⚠️  No historical.csv"
echo "✓ Done"

# 2. Import districts
echo ""
echo "📍 Bước 2: Import districts..."
docker exec -i ${DB_CONTAINER} psql -U ${DB_USER} -d ${DB_NAME} << 'EOF'
-- Import từ CSV (chỉ internal_id và name)
CREATE TEMP TABLE temp_districts (
    internal_id VARCHAR(50),
    administrative_id VARCHAR(50),
    name VARCHAR(255),
    type VARCHAR(50),
    minx DECIMAL(11, 8),
    miny DECIMAL(11, 8),
    maxx DECIMAL(11, 8),
    maxy DECIMAL(11, 8)
);

\COPY temp_districts FROM '/tmp/districts_full.csv' WITH CSV HEADER;

-- Insert vào bảng chính
INSERT INTO districts (internal_id, administrative_id, name, type, province_id, minx, miny, maxx, maxy)
SELECT 
    internal_id,
    NULLIF(administrative_id, ''),
    name,
    type,
    '12',
    minx,
    miny,
    maxx,
    maxy
FROM temp_districts
ON CONFLICT (internal_id) DO UPDATE SET
    name = EXCLUDED.name,
    administrative_id = EXCLUDED.administrative_id,
    type = EXCLUDED.type,
    minx = EXCLUDED.minx,
    miny = EXCLUDED.miny,
    maxx = EXCLUDED.maxx,
    maxy = EXCLUDED.maxy;

SELECT 'Districts imported:', COUNT(*) FROM districts;
DROP TABLE temp_districts;
EOF

# 3. Import current AQI
echo ""
echo "📊 Bước 3: Import current AQI..."
docker exec -i ${DB_CONTAINER} psql -U ${DB_USER} -d ${DB_NAME} << 'EOF'
CREATE TEMP TABLE temp_aqi (
    district_id VARCHAR(50),
    district_name VARCHAR(255),
    aqi_value DECIMAL(10, 2),
    date DATE,
    component VARCHAR(50)
);

\COPY temp_aqi FROM '/tmp/current_aqi.csv' WITH CSV HEADER;

-- Insert
INSERT INTO current_aqi (district_internal_id, measurement_date, measurement_time, aqi_value, component_id)
SELECT 
    district_id,
    date,
    date::timestamp,
    aqi_value,
    component
FROM temp_aqi
ON CONFLICT (district_internal_id, measurement_time, component_id) DO UPDATE SET
    aqi_value = EXCLUDED.aqi_value;

SELECT 'Current AQI imported:', COUNT(*) FROM current_aqi;
DROP TABLE temp_aqi;
EOF

# 4. Import forecast
echo ""
echo "🔮 Bước 4: Import forecast..."
docker exec -i ${DB_CONTAINER} psql -U ${DB_USER} -d ${DB_NAME} << 'EOF'
CREATE TEMP TABLE temp_forecast (
    district_id VARCHAR(50),
    district_name VARCHAR(255),
    date DATE,
    pm25_value DECIMAL(10, 2),
    aqi_value DECIMAL(10, 2),
    component VARCHAR(50)
);

\COPY temp_forecast FROM '/tmp/forecast.csv' WITH CSV HEADER;

-- Insert (base_date = ngày crawl = hôm nay)
INSERT INTO forecast_data (district_internal_id, forecast_date, base_date, pm25_value, aqi_value, component)
SELECT 
    district_id,
    date,
    CURRENT_DATE,
    pm25_value,
    aqi_value,
    component
FROM temp_forecast
ON CONFLICT (district_internal_id, forecast_date, component) DO UPDATE SET
    pm25_value = EXCLUDED.pm25_value,
    aqi_value = EXCLUDED.aqi_value,
    base_date = EXCLUDED.base_date;

SELECT 'Forecast imported:', COUNT(*) FROM forecast_data;
DROP TABLE temp_forecast;
EOF

# 5. Import rankings (nếu có)
if [ -f rankings.csv ]; then
    echo ""
    echo "🏆 Bước 5: Import rankings..."
    docker exec -i ${DB_CONTAINER} psql -U ${DB_USER} -d ${DB_NAME} << 'EOF'
CREATE TEMP TABLE temp_rankings (
    administrative_id VARCHAR(50),
    district_name VARCHAR(255),
    rank INTEGER,
    aqi_avg DECIMAL(10, 2),
    aqi_prev DECIMAL(10, 2),
    date DATE
);

\COPY temp_rankings FROM '/tmp/rankings.csv' WITH CSV HEADER;

INSERT INTO aqi_rankings (district_admin_id, ranking_date, rank, aqi_avg, aqi_prev)
SELECT 
    administrative_id,
    date,
    rank,
    aqi_avg,
    aqi_prev
FROM temp_rankings
WHERE administrative_id IS NOT NULL AND administrative_id != ''
ON CONFLICT (district_admin_id, ranking_date, component_id) DO UPDATE SET
    rank = EXCLUDED.rank,
    aqi_avg = EXCLUDED.aqi_avg,
    aqi_prev = EXCLUDED.aqi_prev;

SELECT 'Rankings imported:', COUNT(*) FROM aqi_rankings;
DROP TABLE temp_rankings;
EOF
else
    echo ""
    echo "⚠️  Bước 5: Skip rankings (no data)"
fi

# 6. Import historical (nếu có)
if [ -f historical.csv ]; then
    echo ""
    echo "📈 Bước 6: Import historical..."
    docker exec -i ${DB_CONTAINER} psql -U ${DB_USER} -d ${DB_NAME} << 'EOF'
CREATE TEMP TABLE temp_historical (
    province_id VARCHAR(50),
    province_name VARCHAR(255),
    date DATE,
    pm25_value DECIMAL(10, 2),
    aqi_value DECIMAL(10, 2),
    component VARCHAR(50)
);

\COPY temp_historical FROM '/tmp/historical.csv' WITH CSV HEADER;

INSERT INTO historical_data (province_id, measurement_date, pm25_value, aqi_value, component)
SELECT 
    province_id,
    date,
    pm25_value,
    aqi_value,
    component
FROM temp_historical
ON CONFLICT (province_id, measurement_date, component) DO UPDATE SET
    pm25_value = EXCLUDED.pm25_value,
    aqi_value = EXCLUDED.aqi_value;

SELECT 'Historical imported:', COUNT(*) FROM historical_data;
DROP TABLE temp_historical;
EOF
else
    echo ""
    echo "⚠️  Bước 6: Skip historical (no data)"
fi

# 7. Show summary
echo ""
echo "======================================================================"
echo "📊 SUMMARY"
echo "======================================================================"
docker exec -i ${DB_CONTAINER} psql -U ${DB_USER} -d ${DB_NAME} << 'EOF'
SELECT 
    'Districts' as table_name, 
    COUNT(*) as total_rows,
    COUNT(*) FILTER (WHERE minx IS NOT NULL) as with_bbox
FROM districts
UNION ALL
SELECT 'Current AQI', COUNT(*), 0 FROM current_aqi
UNION ALL
SELECT 'Forecast', COUNT(*), 0 FROM forecast_data
UNION ALL
SELECT 'Rankings', COUNT(*), 0 FROM aqi_rankings
UNION ALL
SELECT 'Historical', COUNT(*), 0 FROM historical_data;
EOF

echo ""
echo "✅ DONE!"
echo "======================================================================"
