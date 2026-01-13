#!/usr/bin/env python3
"""
Script crawl dữ liệu từ HanoiAir API - Version 2
Lấy tất cả các loại dữ liệu: Districts, Rankings, Forecast, Historical, Current AQI
"""

import requests
import csv
import json
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import time

BASE_URL = "https://geoi.com.vn"

def get_districts_with_both_ids() -> Tuple[List[Dict], List[Dict]]:
    """Lấy danh sách quận/huyện với cả 2 format ID"""
    print("  → Lấy districts với internal_id (ID_XXXXX)...")
    url = f"{BASE_URL}/api/administrative/administrative_province_district"
    
    # Lấy districts với internal_id
    try:
        response = requests.get(url, params={"province_id": "12", "lang_id": "vi"}, timeout=10)
        response.raise_for_status()
        internal_districts = [d for d in response.json() if d.get('type') == 'district']
        print(f"  ✓ Lấy được {len(internal_districts)} districts (internal_id)")
    except Exception as e:
        print(f"  ✗ Lỗi: {e}")
        internal_districts = []
    
    # Lấy districts với administrative_id
    print("  → Lấy districts với administrative_id (VNM.XX.X_X)...")
    try:
        response = requests.get(url, params={"province_id": "VNM.27_1", "lang_id": "vi"}, timeout=10)
        response.raise_for_status()
        admin_districts = [d for d in response.json() if d.get('type') == 'district']
        print(f"  ✓ Lấy được {len(admin_districts)} districts (administrative_id)")
    except Exception as e:
        print(f"  ✗ Lỗi: {e}")
        admin_districts = []
    
    return internal_districts, admin_districts

def get_district_statistics(date_str: str) -> List[Dict]:
    """Lấy thống kê AQI hiện tại cho tất cả quận/huyện"""
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
            print(f"  ✓ Lấy được {len(stats)} districts với AQI")
            return stats
        return []
    except Exception as e:
        print(f"  ✗ Lỗi: {e}")
        return []

def get_district_rankings(date_str: str) -> List[Dict]:
    """Lấy xếp hạng các quận/huyện theo AQI"""
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
            rankings = data['Data'].get('comps', [])
            print(f"  ✓ Lấy được {len(rankings)} rankings")
            return rankings
        return []
    except Exception as e:
        print(f"  ✗ Lỗi: {e}")
        return []

def get_forecast_data(district_id: str, district_name: str, date_str: str) -> List[Dict]:
    """Lấy dữ liệu forecast và historical cho một quận/huyện"""
    url = f"{BASE_URL}/api/componentgeotiffdaily/identify_district_id_list_geotiff"
    
    payload = {
        "district_id": district_id,
        "groupcomponent_id": "63",  # PM2.5
        "date_request": date_str,
        "predays": 3,  # 3 ngày lịch sử
        "nextdays": 7,  # 7 ngày dự báo
        "lang_id": "vi"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('Code') == 200 and data.get('Data'):
            comps = data['Data'].get('comps', [])
            if comps:
                print(f"  ✓ {district_name}: {len(comps)} records")
                return comps
        return []
    except Exception as e:
        print(f"  ✗ {district_name}: {e}")
        return []

def get_province_historical(date_str: str) -> List[Dict]:
    """Lấy dữ liệu lịch sử PM2.5 cho toàn tỉnh"""
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
            comps = data['Data'].get('comps', [])
            print(f"  ✓ Lấy được {len(comps)} records historical")
            return comps
        return []
    except Exception as e:
        print(f"  ✗ Lỗi: {e}")
        return []

def crawl_data(num_samples: int = 100) -> Dict[str, List[Dict]]:
    """Crawl tất cả các loại dữ liệu"""
    
    today = datetime.now()
    yesterday = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    today_str = today.strftime("%Y-%m-%d")
    
    all_data = {
        'districts': [],
        'current_aqi': [],
        'rankings': [],
        'forecast': [],
        'historical': []
    }
    
    # 1. Lấy danh sách quận/huyện
    print("\n📍 BƯỚC 1: Lấy danh sách quận/huyện")
    internal_districts, admin_districts = get_districts_with_both_ids()
    
    # Lưu districts vào data
    for d in internal_districts:
        all_data['districts'].append({
            'internal_id': d.get('id'),
            'name': d.get('name'),
            'type': d.get('type')
        })
    
    # 2. Lấy AQI hiện tại
    print("\n📊 BƯỚC 2: Lấy AQI hiện tại (Current Statistics)")
    current_stats = get_district_statistics(yesterday)
    for stat in current_stats:
        all_data['current_aqi'].append({
            'district_id': stat.get('id'),
            'district_name': stat.get('name'),
            'aqi_value': stat.get('val'),
            'date': yesterday,
            'component': 'aqi'
        })
    
    # 3. Lấy rankings
    print("\n🏆 BƯỚC 3: Lấy xếp hạng (Rankings)")
    rankings = get_district_rankings(yesterday)
    for rank_data in rankings:
        all_data['rankings'].append({
            'administrative_id': rank_data.get('administrative_id'),
            'district_name': rank_data.get('administrative_name'),
            'rank': rank_data.get('no'),
            'aqi_avg': rank_data.get('avg'),
            'aqi_prev': rank_data.get('avg_pre'),
            'date': yesterday
        })
    
    # 4. Lấy forecast cho 5 quận/huyện đầu
    print("\n🔮 BƯỚC 4: Lấy dữ liệu Forecast (5 districts)")
    for district in internal_districts[:5]:
        district_id = district.get('id')
        district_name = district.get('name')
        
        forecast_comps = get_forecast_data(district_id, district_name, yesterday)
        for comp in forecast_comps:
            all_data['forecast'].append({
                'district_id': district_id,
                'district_name': district_name,
                'date': comp.get('requestdate'),
                'pm25_value': comp.get('val'),
                'aqi_value': comp.get('val_aqi'),
                'component': comp.get('titlecomponent', 'PM2.5')
            })
        
        time.sleep(0.3)
    
    # 5. Lấy historical data cho toàn tỉnh
    print("\n📈 BƯỚC 5: Lấy dữ liệu Historical (Province-wide)")
    historical_comps = get_province_historical(yesterday)
    for comp in historical_comps:
        all_data['historical'].append({
            'province_id': 'VNM.27_1',
            'province_name': 'Hà Nội',
            'date': comp.get('requestdate'),
            'pm25_value': comp.get('val'),
            'aqi_value': comp.get('val_aqi'),
            'component': comp.get('titlecomponent', 'PM2.5')
        })
    
    return all_data

def save_to_multiple_csv(data: Dict[str, List[Dict]]):
    """Lưu dữ liệu vào nhiều file CSV"""
    
    files_created = []
    
    # 1. Districts
    if data['districts']:
        filename = 'districts.csv'
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['internal_id', 'name', 'type'])
            writer.writeheader()
            writer.writerows(data['districts'])
        files_created.append(f"{filename} ({len(data['districts'])} rows)")
    
    # 2. Current AQI
    if data['current_aqi']:
        filename = 'current_aqi.csv'
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['district_id', 'district_name', 'aqi_value', 'date', 'component'])
            writer.writeheader()
            writer.writerows(data['current_aqi'])
        files_created.append(f"{filename} ({len(data['current_aqi'])} rows)")
    
    # 3. Rankings
    if data['rankings']:
        filename = 'rankings.csv'
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['administrative_id', 'district_name', 'rank', 'aqi_avg', 'aqi_prev', 'date'])
            writer.writeheader()
            writer.writerows(data['rankings'])
        files_created.append(f"{filename} ({len(data['rankings'])} rows)")
    
    # 4. Forecast
    if data['forecast']:
        filename = 'forecast.csv'
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['district_id', 'district_name', 'date', 'pm25_value', 'aqi_value', 'component'])
            writer.writeheader()
            writer.writerows(data['forecast'])
        files_created.append(f"{filename} ({len(data['forecast'])} rows)")
    
    # 5. Historical
    if data['historical']:
        filename = 'historical.csv'
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['province_id', 'province_name', 'date', 'pm25_value', 'aqi_value', 'component'])
            writer.writeheader()
            writer.writerows(data['historical'])
        files_created.append(f"{filename} ({len(data['historical'])} rows)")
    
    return files_created

def main():
    print("=" * 70)
    print("🚀 BẮT ĐẦU CRAWL DỮ LIỆU HANOIAIR")
    print("=" * 70)
    
    # Crawl all data
    data = crawl_data(num_samples=100)
    
    # Đếm tổng records
    total = sum(len(v) for v in data.values())
    
    if total > 0:
        print("\n" + "=" * 70)
        print("💾 Đang lưu dữ liệu vào CSV files...")
        print("=" * 70)
        
        files = save_to_multiple_csv(data)
        
        print("\n✅ HOÀN THÀNH!")
        print(f"📊 Tổng số records: {total}")
        print("\n📁 Files đã tạo:")
        for f in files:
            print(f"   • {f}")
        print("=" * 70)
    else:
        print("\n❌ Không crawl được dữ liệu")

if __name__ == "__main__":
    main()
