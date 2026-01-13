#!/usr/bin/env python3
"""
Script crawl và export CSV
"""

import requests
import csv
from datetime import datetime, timedelta
import unicodedata

BASE_URL = "https://geoi.com.vn"

def normalize_name(name):
    """Chuẩn hóa tên (bỏ dấu)"""
    name = unicodedata.normalize('NFD', name)
    name = ''.join(c for c in name if unicodedata.category(c) != 'Mn')
    return name.lower().replace(' ', '_')

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

def save_districts_csv(districts):
    """Lưu districts vào CSV"""
    with open('districts.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'province_id', 'name', 'normalized_name'])
        
        for d in districts:
            writer.writerow([
                d['id'],
                '12',
                d['name'],
                normalize_name(d['name'])
            ])
    
    print(f"✓ Đã lưu districts.csv ({len(districts)} rows)")

def save_stats_csv(aqi_stats, date_str):
    """Lưu AQI stats vào CSV"""
    with open('distric_stats.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['district_id', 'date', 'hour', 'component_id', 'aqi_value', 'pm25_value'])
        
        for stat in aqi_stats:
            writer.writerow([
                stat['id'],
                date_str,
                0,  # hour = 0 (daily average)
                'aqi',
                int(stat['val']) if stat.get('val') else '',
                ''  # pm25_value chưa có
            ])
    
    print(f"✓ Đã lưu distric_stats.csv ({len(aqi_stats)} rows)")

def main():
    print("="*70)
    print("🚀 CRAWL DỮ LIỆU & EXPORT CSV")
    print("="*70)
    
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    print(f"\n📅 Ngày: {yesterday}")
    
    print("\n📍 Bước 1: Crawl districts...")
    districts = get_districts()
    
    print("\n📊 Bước 2: Crawl AQI stats...")
    aqi_stats = get_current_aqi(yesterday)
    
    if not districts or not aqi_stats:
        print("\n❌ Không có dữ liệu")
        return
    
    print("\n💾 Bước 3: Export CSV...")
    save_districts_csv(districts)
    save_stats_csv(aqi_stats, yesterday)
    
    print("\n" + "="*70)
    print("✅ HOÀN THÀNH!")
    print(f"📊 Districts: {len(districts)}")
    print(f"📊 AQI Stats: {len(aqi_stats)}")
    print("\n📁 Files:")
    print("   • districts.csv")
    print("   • distric_stats.csv")
    print("="*70)

if __name__ == "__main__":
    main()
