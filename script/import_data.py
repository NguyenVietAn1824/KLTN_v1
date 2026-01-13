#!/usr/bin/env python3
"""
Script import dữ liệu từ CSV vào PostgreSQL
"""

import psycopg2
from psycopg2.extras import execute_batch
import csv
from datetime import datetime
import os

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'hanoiair_db',
    'user': 'hanoiair_user',
    'password': 'hanoiair_pass'
}

def connect_db():
    """Kết nối đến PostgreSQL"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Kết nối database thành công")
        return conn
    except Exception as e:
        print(f"❌ Lỗi kết nối: {e}")
        return None

def import_districts(conn, filename='districts.csv'):
    """Import dữ liệu districts"""
    if not os.path.exists(filename):
        print(f"⚠️  File {filename} không tồn tại")
        return 0
    
    cursor = conn.cursor()
    count = 0
    
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
        for row in rows:
            try:
                cursor.execute("""
                    INSERT INTO districts (internal_id, name, type, province_id)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (internal_id) DO UPDATE SET
                        name = EXCLUDED.name,
                        type = EXCLUDED.type
                """, (row['internal_id'], row['name'], row['type'], '12'))
                count += 1
            except Exception as e:
                print(f"  ⚠️  Lỗi insert {row['name']}: {e}")
    
    conn.commit()
    print(f"✅ Import {count}/{len(rows)} districts")
    return count

def import_current_aqi(conn, filename='current_aqi.csv'):
    """Import dữ liệu current AQI"""
    if not os.path.exists(filename):
        print(f"⚠️  File {filename} không tồn tại")
        return 0
    
    cursor = conn.cursor()
    count = 0
    
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
        for row in rows:
            try:
                measurement_time = f"{row['date']} 00:00:00"
                cursor.execute("""
                    INSERT INTO current_aqi 
                    (district_internal_id, measurement_date, measurement_time, aqi_value, component_id)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (district_internal_id, measurement_time, component_id) DO UPDATE SET
                        aqi_value = EXCLUDED.aqi_value
                """, (
                    row['district_id'], 
                    row['date'], 
                    measurement_time,
                    float(row['aqi_value']) if row['aqi_value'] else None,
                    row['component']
                ))
                count += 1
            except Exception as e:
                print(f"  ⚠️  Lỗi insert AQI: {e}")
    
    conn.commit()
    print(f"✅ Import {count}/{len(rows)} current AQI records")
    return count

def import_rankings(conn, filename='rankings.csv'):
    """Import dữ liệu rankings"""
    if not os.path.exists(filename):
        print(f"⚠️  File {filename} không tồn tại")
        return 0
    
    cursor = conn.cursor()
    count = 0
    
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
        for row in rows:
            try:
                cursor.execute("""
                    INSERT INTO aqi_rankings 
                    (district_admin_id, ranking_date, rank, aqi_avg, aqi_prev)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (district_admin_id, ranking_date, component_id) DO UPDATE SET
                        rank = EXCLUDED.rank,
                        aqi_avg = EXCLUDED.aqi_avg,
                        aqi_prev = EXCLUDED.aqi_prev
                """, (
                    row['administrative_id'],
                    row['date'],
                    int(row['rank']) if row['rank'] else None,
                    float(row['aqi_avg']) if row['aqi_avg'] else None,
                    float(row['aqi_prev']) if row['aqi_prev'] else None
                ))
                count += 1
            except Exception as e:
                print(f"  ⚠️  Lỗi insert ranking: {e}")
    
    conn.commit()
    print(f"✅ Import {count}/{len(rows)} rankings")
    return count

def import_forecast(conn, filename='forecast.csv'):
    """Import dữ liệu forecast"""
    if not os.path.exists(filename):
        print(f"⚠️  File {filename} không tồn tại")
        return 0
    
    cursor = conn.cursor()
    count = 0
    
    # Lấy base_date từ dữ liệu (ngày crawl)
    base_date = datetime.now().strftime('%Y-%m-%d')
    
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
        for row in rows:
            try:
                cursor.execute("""
                    INSERT INTO forecast_data 
                    (district_internal_id, forecast_date, base_date, pm25_value, aqi_value, component)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (district_internal_id, forecast_date, component) DO UPDATE SET
                        pm25_value = EXCLUDED.pm25_value,
                        aqi_value = EXCLUDED.aqi_value,
                        base_date = EXCLUDED.base_date
                """, (
                    row['district_id'],
                    row['date'],
                    base_date,
                    float(row['pm25_value']) if row['pm25_value'] else None,
                    float(row['aqi_value']) if row['aqi_value'] else None,
                    row['component']
                ))
                count += 1
            except Exception as e:
                print(f"  ⚠️  Lỗi insert forecast: {e}")
    
    conn.commit()
    print(f"✅ Import {count}/{len(rows)} forecast records")
    return count

def import_historical(conn, filename='historical.csv'):
    """Import dữ liệu historical"""
    if not os.path.exists(filename):
        print(f"⚠️  File {filename} không tồn tại")
        return 0
    
    cursor = conn.cursor()
    count = 0
    
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
        for row in rows:
            try:
                cursor.execute("""
                    INSERT INTO historical_data 
                    (province_id, measurement_date, pm25_value, aqi_value, component)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (province_id, measurement_date, component) DO UPDATE SET
                        pm25_value = EXCLUDED.pm25_value,
                        aqi_value = EXCLUDED.aqi_value
                """, (
                    row['province_id'],
                    row['date'],
                    float(row['pm25_value']) if row['pm25_value'] else None,
                    float(row['aqi_value']) if row['aqi_value'] else None,
                    row['component']
                ))
                count += 1
            except Exception as e:
                print(f"  ⚠️  Lỗi insert historical: {e}")
    
    conn.commit()
    print(f"✅ Import {count}/{len(rows)} historical records")
    return count

def main():
    print("=" * 70)
    print("📥 BẮT ĐẦU IMPORT DỮ LIỆU VÀO POSTGRESQL")
    print("=" * 70)
    
    conn = connect_db()
    if not conn:
        print("❌ Không thể kết nối database")
        return
    
    try:
        total = 0
        
        print("\n📍 Bước 1: Import districts...")
        total += import_districts(conn)
        
        print("\n📊 Bước 2: Import current AQI...")
        total += import_current_aqi(conn)
        
        print("\n🏆 Bước 3: Import rankings...")
        total += import_rankings(conn)
        
        print("\n🔮 Bước 4: Import forecast data...")
        total += import_forecast(conn)
        
        print("\n📈 Bước 5: Import historical data...")
        total += import_historical(conn)
        
        print("\n" + "=" * 70)
        print(f"✅ HOÀN THÀNH! Đã import tổng cộng {total} records")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        conn.rollback()
    finally:
        conn.close()
        print("🔒 Đã đóng kết nối database")

if __name__ == "__main__":
    main()
