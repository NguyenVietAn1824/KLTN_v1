#!/usr/bin/env python3
"""
Script crawl dữ liệu HOÀN CHỈNH từ HanoiAir API
- Districts với cả 2 format ID + bounding box
- Current AQI cho TẤT CẢ quận/huyện
- Rankings (nếu có)
- Forecast data
- Historical data
"""

import requests
import csv
import json
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import time

BASE_URL = "https://geoi.com.vn"

def get_districts_both_formats() -> Tuple[List[Dict], List[Dict]]:
    """Lấy districts với cả 2 format ID"""
    print("  → Lấy districts với internal_id (ID_XXXXX)...")
    url = f"{BASE_URL}/api/administrative/administrative_province_district"
    
    # Format 1: internal_id (ID_XXXXX)
    try:
        response = requests.get(url, params={"province_id": "12", "lang_id": "vi"}, timeout=10)
        response.raise_for_status()
        internal_list = [d for d in response.json() if d.get('type') == 'district']
        print(f"  ✓ {len(internal_list)} districts (internal_id)")
    except Exception as e:
        print(f"  ✗ Lỗi: {e}")
        internal_list = []
    
    # Format 2: administrative_id (VNM.27.X_1)
    print("  → Lấy districts với administrative_id (VNM.27.X_1)...")
    try:
        response = requests.get(url, params={"province_id": "VNM.27_1", "lang_id": "vi"}, timeout=10)
        response.raise_for_status()
        admin_list = [d for d in response.json() if d.get('type') == 'district']
        print(f"  ✓ {len(admin_list)} districts (administrative_id)")
    except Exception as e:
        print(f"  ✗ Lỗi: {e}")
        admin_list = []
    
    return internal_list, admin_list

def get_district_bbox(district_id: str, district_name: str) -> Dict:
    """Lấy bounding box cho một district"""
    url = f"{BASE_URL}/api/componentgeotiffdaily/identify_district_id_list_geotiff"
    
    payload = {
        "district_id": district_id,
        "lang_id": "vi"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Response có thể là object trực tiếp hoặc trong Data.comps
        if isinstance(data, dict) and 'id' in data:
            return {
                'id': data.get('id'),
                'name': data.get('name'),
                'minx': data.get('minx'),
                'miny': data.get('miny'),
                'maxx': data.get('maxx'),
                'maxy': data.get('maxy')
            }
        return {}
    except Exception as e:
        return {}

def get_current_aqi_all_districts(date_str: str) -> List[Dict]:
    """Lấy AQI hiện tại cho TẤT CẢ quận/huyện"""
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
            print(f"  ✓ {len(stats)} districts")
            return stats
        return []
    except Exception as e:
        print(f"  ✗ Lỗi: {e}")
        return []

def get_rankings(date_str: str) -> List[Dict]:
    """Lấy rankings"""
    url = f"{BASE_URL}/api/componentgeotiffdaily/rankingprovince"
    
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    date_pre = (date_obj - timedelta(days=1)).strftime("%Y-%m-%d")
    
    payload = {
        "group_id": "satellite_aqi_pm25",
        "component_id": "pm25",
        "date_shooting": date_str,
        "date_shooting_pre": date_pre,
        "lang_id": "vi",
        "province_id": "VNM.27_1"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('Code') == 200 and data.get('Data'):
            return data['Data'].get('comps', [])
        return []
    except Exception as e:
        return []

def get_forecast(district_id: str, date_str: str) -> List[Dict]:
    """Lấy forecast + historical"""
    url = f"{BASE_URL}/api/componentgeotiffdaily/identify_district_id_list_geotiff"
    
    payload = {
        "district_id": district_id,
        "groupcomponent_id": "63",
        "date_request": date_str,
        "predays": 3,
        "nextdays": 7,
        "lang_id": "vi"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('Code') == 200 and data.get('Data'):
            return data['Data'].get('comps', [])
        return []
    except Exception as e:
        return []

def get_province_historical(date_str: str) -> List[Dict]:
    """Lấy historical data province-wide"""
    url = f"{BASE_URL}/api/componentgeotiffdaily/identify_province_id_list_geotiff"
    
    payload = {
        "province_id": "VNM.27_1",
        "groupcomponent_id": "63",
        "date_request": date_str,
        "predays": 7,
        "nextdays": 0,
        "lang_id": "vi"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('Code') == 200 and data.get('Data'):
            return data['Data'].get('comps', [])
        return []
    except Exception as e:
        return []

def crawl_all_data():
    """Crawl TẤT CẢ dữ liệu cần thiết"""
    
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    all_data = {
        'districts_full': [],  # Districts với đầy đủ thông tin
        'current_aqi': [],
        'rankings': [],
        'forecast': [],
        'historical': []
    }
    
    # 1. Lấy districts với cả 2 format
    print("\n" + "="*70)
    print("📍 BƯỚC 1: Lấy danh sách Districts (cả 2 format ID)")
    print("="*70)
    internal_list, admin_list = get_districts_both_formats()
    
    # Tạo mapping giữa 2 formats (dựa trên tên)
    name_to_admin = {d['name']: d['id'] for d in admin_list}
    
    # Lấy bounding box cho 10 districts đầu (test)
    print("\n  → Lấy bounding box cho districts (10 mẫu)...")
    for i, district in enumerate(internal_list[:10]):
        internal_id = district['id']
        name = district['name']
        
        bbox = get_district_bbox(internal_id, name)
        
        all_data['districts_full'].append({
            'internal_id': internal_id,
            'administrative_id': name_to_admin.get(name, ''),
            'name': name,
            'type': district.get('type', 'district'),
            'minx': bbox.get('minx'),
            'miny': bbox.get('miny'),
            'maxx': bbox.get('maxx'),
            'maxy': bbox.get('maxy')
        })
        
        if (i + 1) % 5 == 0:
            print(f"    • {i+1}/10...")
        time.sleep(0.2)
    
    # Thêm các districts còn lại (không có bbox)
    for district in internal_list[10:]:
        internal_id = district['id']
        name = district['name']
        all_data['districts_full'].append({
            'internal_id': internal_id,
            'administrative_id': name_to_admin.get(name, ''),
            'name': name,
            'type': district.get('type', 'district'),
            'minx': None,
            'miny': None,
            'maxx': None,
            'maxy': None
        })
    
    print(f"  ✓ Tổng: {len(all_data['districts_full'])} districts")
    
    # 2. Lấy Current AQI cho TẤT CẢ quận/huyện
    print("\n" + "="*70)
    print(f"📊 BƯỚC 2: Lấy AQI hiện tại ngày {yesterday}")
    print("="*70)
    current_stats = get_current_aqi_all_districts(yesterday)
    
    for stat in current_stats:
        all_data['current_aqi'].append({
            'district_id': stat.get('id'),
            'district_name': stat.get('name'),
            'aqi_value': stat.get('val'),
            'date': yesterday,
            'component': 'aqi'
        })
    
    # 3. Lấy Rankings
    print("\n" + "="*70)
    print(f"🏆 BƯỚC 3: Lấy Rankings ngày {yesterday}")
    print("="*70)
    rankings = get_rankings(yesterday)
    
    if rankings:
        print(f"  ✓ {len(rankings)} rankings")
        for rank_data in rankings:
            all_data['rankings'].append({
                'administrative_id': rank_data.get('administrative_id'),
                'district_name': rank_data.get('administrative_name'),
                'rank': rank_data.get('no'),
                'aqi_avg': rank_data.get('avg'),
                'aqi_prev': rank_data.get('avg_pre'),
                'date': yesterday
            })
    else:
        print(f"  ⚠️  Không có rankings cho ngày {yesterday}")
    
    # 4. Lấy Forecast cho 5 districts
    print("\n" + "="*70)
    print("🔮 BƯỚC 4: Lấy Forecast (5 districts)")
    print("="*70)
    for district in internal_list[:5]:
        district_id = district['id']
        district_name = district['name']
        
        print(f"  → {district_name}...", end=" ")
        forecast_comps = get_forecast(district_id, yesterday)
        
        if forecast_comps:
            print(f"✓ {len(forecast_comps)} records")
            for comp in forecast_comps:
                all_data['forecast'].append({
                    'district_id': district_id,
                    'district_name': district_name,
                    'date': comp.get('requestdate'),
                    'pm25_value': comp.get('val'),
                    'aqi_value': comp.get('val_aqi'),
                    'component': comp.get('titlecomponent', 'PM2.5')
                })
        else:
            print("✗ Không có data")
        
        time.sleep(0.3)
    
    # 5. Lấy Historical
    print("\n" + "="*70)
    print("📈 BƯỚC 5: Lấy Historical (Province-wide)")
    print("="*70)
    historical_comps = get_province_historical(yesterday)
    
    if historical_comps:
        print(f"  ✓ {len(historical_comps)} records")
        for comp in historical_comps:
            all_data['historical'].append({
                'province_id': 'VNM.27_1',
                'province_name': 'Hà Nội',
                'date': comp.get('requestdate'),
                'pm25_value': comp.get('val'),
                'aqi_value': comp.get('val_aqi'),
                'component': comp.get('titlecomponent', 'PM2.5')
            })
    else:
        print(f"  ⚠️  Không có historical data")
    
    return all_data

def save_to_csv(data: Dict[str, List[Dict]]):
    """Lưu vào CSV files"""
    files = []
    
    # 1. Districts Full
    if data['districts_full']:
        filename = 'districts_full.csv'
        fieldnames = ['internal_id', 'administrative_id', 'name', 'type', 'minx', 'miny', 'maxx', 'maxy']
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data['districts_full'])
        files.append(f"{filename} ({len(data['districts_full'])} rows)")
    
    # 2. Current AQI
    if data['current_aqi']:
        filename = 'current_aqi.csv'
        fieldnames = ['district_id', 'district_name', 'aqi_value', 'date', 'component']
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data['current_aqi'])
        files.append(f"{filename} ({len(data['current_aqi'])} rows)")
    
    # 3. Rankings
    if data['rankings']:
        filename = 'rankings.csv'
        fieldnames = ['administrative_id', 'district_name', 'rank', 'aqi_avg', 'aqi_prev', 'date']
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data['rankings'])
        files.append(f"{filename} ({len(data['rankings'])} rows)")
    
    # 4. Forecast
    if data['forecast']:
        filename = 'forecast.csv'
        fieldnames = ['district_id', 'district_name', 'date', 'pm25_value', 'aqi_value', 'component']
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data['forecast'])
        files.append(f"{filename} ({len(data['forecast'])} rows)")
    
    # 5. Historical
    if data['historical']:
        filename = 'historical.csv'
        fieldnames = ['province_id', 'province_name', 'date', 'pm25_value', 'aqi_value', 'component']
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data['historical'])
        files.append(f"{filename} ({len(data['historical'])} rows)")
    
    return files

def main():
    print("\n" + "="*70)
    print("🚀 CRAWL DỮ LIỆU HANOIAIR - PHIÊN BẢN HOÀN CHỈNH")
    print("="*70)
    
    # Crawl
    data = crawl_all_data()
    
    # Count
    total = sum(len(v) for v in data.values())
    
    # Save
    print("\n" + "="*70)
    print("💾 Đang lưu vào CSV...")
    print("="*70)
    files = save_to_csv(data)
    
    # Summary
    print("\n" + "="*70)
    print("✅ HOÀN THÀNH!")
    print("="*70)
    print(f"📊 Tổng records: {total}")
    print(f"\n📁 Files:")
    for f in files:
        print(f"   • {f}")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
