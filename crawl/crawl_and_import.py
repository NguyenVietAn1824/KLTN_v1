#!/usr/bin/env python3
"""
Script crawl và import dữ liệu vào schema đơn giản
"""

import requests
from datetime import datetime, timedelta
import time

BASE_URL = "https://geoi.com.vn"

def get_districts():
    """Lấy danh sách districts"""
    url = f"{BASE_URL}/api/administrative/administrative_province_district"
    
    try:
        response = requests.get(url, params={"province_id": "12", "lang_id": "vi"}, timeout=10)
        response.raise_for_status()
        districts = [d for d in response.json() if d.get('type') == 'district']
        print(f"✓ Lấy được {len(districts)} districts")
        return districts
    except Exception as e:
        print(f"✗ Lỗi: {e}")
        return []

def get_current_aqi(date_str):
    """Lấy AQI hiện tại"""
    url = f"{BASE_URL}/api/analysis/district_avg_statistic"
    
    payload = {
        "id": "12",
        "from_date": f"{date_str} 00:00:00",
        "to_date": f"{date_str} 23:59:59",
        "component_id": "aqi",
        "lang_id": "vi"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('Code') == 200 and data.get('Data'):
            stats = data['Data'].get('comps', [])
            print(f"✓ Lấy được {len(stats)} AQI records")
            return stats
        return []
    except Exception as e:
        print(f"✗ Lỗi: {e}")
        return []

def normalize_name(name):
    """Chuẩn hóa tên (bỏ dấu)"""
    import unicodedata
    name = unicodedata.normalize('NFD', name)
    name = ''.join(c for c in name if unicodedata.category(c) != 'Mn')
    return name.lower().replace(' ', '_')

def import_to_db(districts, aqi_stats, date_str):
    """Import vào database"""
    import psycopg2
    
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='hanoiair_db',
        user='hanoiair_user',
        password='hanoiair_pass'
    )
    
    cursor = conn.cursor()
    
    # Import districts
    print("\n→ Import districts...")
    count = 0
    for d in districts:
        try:
            cursor.execute("""
                INSERT INTO districts (id, province_id, name, normalized_name)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    normalized_name = EXCLUDED.normalized_name
            """, (d['id'], '12', d['name'], normalize_name(d['name'])))
            count += 1
        except Exception as e:
            print(f"  ✗ {d['name']}: {e}")
    
    conn.commit()
    print(f"✓ Import {count}/{len(districts)} districts")
    
    # Import AQI stats
    print("\n→ Import AQI stats...")
    count = 0
    for stat in aqi_stats:
        try:
            cursor.execute("""
                INSERT INTO distric_stats (district_id, date, hour, component_id, aqi_value, pm25_value)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (district_id, date, hour, component_id) DO UPDATE SET
                    aqi_value = EXCLUDED.aqi_value,
                    pm25_value = EXCLUDED.pm25_value
            """, (
                stat['id'], 
                date_str, 
                0,  # hour = 0 (daily average)
                'aqi',
                int(stat['val']) if stat.get('val') else None,
                None  # pm25_value chưa có trong API này
            ))
            count += 1
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    conn.commit()
    print(f"✓ Import {count}/{len(aqi_stats)} AQI stats")
    
    conn.close()

def main():
    print("="*70)
    print("🚀 CRAWL & IMPORT DỮ LIỆU")
    print("="*70)
    
    # Ngày hôm qua
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    print(f"\n📅 Ngày: {yesterday}")
    
    # Crawl
    print("\n📍 Bước 1: Crawl districts...")
    districts = get_districts()
    
    print("\n📊 Bước 2: Crawl AQI stats...")
    aqi_stats = get_current_aqi(yesterday)
    
    if not districts or not aqi_stats:
        print("\n❌ Không có dữ liệu để import")
        return
    
    # Import
    print("\n💾 Bước 3: Import vào database...")
    try:
        import_to_db(districts, aqi_stats, yesterday)
        print("\n" + "="*70)
        print("✅ HOÀN THÀNH!")
        print(f"📊 Districts: {len(districts)}")
        print(f"📊 AQI Stats: {len(aqi_stats)}")
        print("="*70)
    except Exception as e:
        print(f"\n❌ Lỗi import: {e}")

if __name__ == "__main__":
    main()
