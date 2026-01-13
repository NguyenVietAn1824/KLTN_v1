#!/bin/bash
# Script import dữ liệu vào PostgreSQL sử dụng COPY command

echo "========================================================================"
echo "📥 BẮT ĐẦU IMPORT DỮ LIỆU VÀO POSTGRESQL"
echo "========================================================================"

# Wait for PostgreSQL to be ready
echo "⏳ Đợi PostgreSQL khởi động..."
sleep 5

# Import districts
echo ""
echo "📍 Bước 1: Import districts..."
if [ -f "districts.csv" ]; then
    docker exec -i hanoiair_postgres psql -U hanoiair_user -d hanoiair_db << EOF
CREATE TEMP TABLE temp_districts (
    internal_id VARCHAR(50),
    name VARCHAR(255),
    type VARCHAR(50)
);

\COPY temp_districts FROM '/tmp/districts.csv' WITH (FORMAT CSV, HEADER true, ENCODING 'UTF8');

INSERT INTO districts (internal_id, name, type, province_id)
SELECT internal_id, name, type, '12'
FROM temp_districts
ON CONFLICT (internal_id) DO UPDATE SET
    name = EXCLUDED.name,
    type = EXCLUDED.type;

SELECT COUNT(*) || ' districts imported' AS result;
DROP TABLE temp_districts;
EOF
else
    echo "⚠️  File districts.csv không tồn tại"
fi

# Copy CSV files vào container
echo ""
echo "📦 Copy CSV files vào container..."
docker cp districts.csv hanoiair_postgres:/tmp/ 2>/dev/null
docker cp current_aqi.csv hanoiair_postgres:/tmp/ 2>/dev/null
docker cp rankings.csv hanoiair_postgres:/tmp/ 2>/dev/null
docker cp forecast.csv hanoiair_postgres:/tmp/ 2>/dev/null
docker cp historical.csv hanoiair_postgres:/tmp/ 2>/dev/null

# Import current_aqi
echo ""
echo "📊 Bước 2: Import current AQI..."
docker exec -i hanoiair_postgres psql -U hanoiair_user -d hanoiair_db << 'EOF'
CREATE TEMP TABLE temp_current_aqi (
    district_id VARCHAR(50),
    district_name VARCHAR(255),
    aqi_value DECIMAL(10,2),
    date DATE,
    component VARCHAR(50)
);

\COPY temp_current_aqi FROM '/tmp/current_aqi.csv' WITH (FORMAT CSV, HEADER true, ENCODING 'UTF8');

INSERT INTO current_aqi (district_internal_id, measurement_date, measurement_time, aqi_value, component_id)
SELECT 
    district_id, 
    date,
    date::timestamp,
    aqi_value,
    component
FROM temp_current_aqi
ON CONFLICT (district_internal_id, measurement_time, component_id) DO UPDATE SET
    aqi_value = EXCLUDED.aqi_value;

SELECT COUNT(*) || ' current AQI records imported' AS result;
DROP TABLE temp_current_aqi;
EOF

# Import forecast
echo ""
echo "🔮 Bước 3: Import forecast..."
docker exec -i hanoiair_postgres psql -U hanoiair_user -d hanoiair_db << 'EOF'
CREATE TEMP TABLE temp_forecast (
    district_id VARCHAR(50),
    district_name VARCHAR(255),
    date DATE,
    pm25_value DECIMAL(10,2),
    aqi_value DECIMAL(10,2),
    component VARCHAR(50)
);

\COPY temp_forecast FROM '/tmp/forecast.csv' WITH (FORMAT CSV, HEADER true, ENCODING 'UTF8');

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
    aqi_value = EXCLUDED.aqi_value;

SELECT COUNT(*) || ' forecast records imported' AS result;
DROP TABLE temp_forecast;
EOF

echo ""
echo "========================================================================"
echo "✅ HOÀN THÀNH IMPORT DỮ LIỆU"
echo "========================================================================"

# Show statistics
docker exec -i hanoiair_postgres psql -U hanoiair_user -d hanoiair_db << 'EOF'
SELECT 'districts' AS table_name, COUNT(*) AS records FROM districts
UNION ALL
SELECT 'current_aqi', COUNT(*) FROM current_aqi
UNION ALL
SELECT 'forecast_data', COUNT(*) FROM forecast_data
ORDER BY table_name;
EOF
