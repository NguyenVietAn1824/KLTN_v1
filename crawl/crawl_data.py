#!/usr/bin/env python3
"""
Script crawl dữ liệu từ HanoiAir API
Lấy 100 mẫu dữ liệu về AQI của các quận/huyện Hà Nội và forecast data
"""

import requests
import csv
import json
from datetime import datetime, timedelta
from typing import List, Dict
import time

BASE_URL = "https://geoi.com.vn"

def get_districts() -> List[Dict]:
    """Lấy danh sách các quận/huyện Hà Nội"""
    url = f"{BASE_URL}/api/administrative/administrative_province_district"
    params = {
        "province_id": "12",  # Hà Nội với internal_id
        "lang_id": "vi"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Lọc chỉ lấy districts (không lấy province)
        districts = [d for d in data if d.get('type') == 'district']
        print(f"✅ Lấy được {len(districts)} quận/huyện")
        return districts
    except Exception as e:
        print(f"❌ Lỗi khi lấy danh sách quận/huyện: {e}")
        return []

def get_district_statistics(date_str: str) -> List[Dict]:
    """Lấy thống kê AQI của các quận/huyện theo ngày"""
    url = f"{BASE_URL}/api/analysis/district_avg_statistic"
    
    payload = {
        "id": "12",  # Hà Nội
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
            print(f"✅ Lấy được {len(stats)} thống kê AQI cho ngày {date_str}")
            return stats
        return []
    except Exception as e:
        print(f"❌ Lỗi khi lấy thống kê ngày {date_str}: {e}")
        return []

def get_forecast_data(district_id: str, date_request: str, predays: int = 3, nextdays: int = 7) -> Dict:
    """Lấy dữ liệu forecast và historical cho một quận/huyện"""
    url = f"{BASE_URL}/api/componentgeotiffdaily/identify_district_id_list_geotiff"
    
    payload = {
        "district_id": district_id,
        "groupcomponent_id": "63",  # PM2.5
        "date_request": date_request,
        "predays": predays,
        "nextdays": nextdays,
        "lang_id": "vi"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('Code') == 200 and data.get('Data'):
            return data['Data']
        return {}
    except Exception as e:
        print(f"❌ Lỗi khi lấy forecast cho district {district_id}: {e}")
        return {}

def crawl_data(num_samples: int = 100) -> List[Dict]:
    """Crawl dữ liệu và trả về danh sách các mẫu"""
    all_data = []
    
    # 1. Lấy danh sách quận/huyện
    print("\n📍 Bước 1: Lấy danh sách quận/huyện...")
    districts = get_districts()
    if not districts:
        print("❌ Không lấy được danh sách quận/huyện")
        return []
    
    # 2. Lấy thống kê AQI cho ngày hiện tại (dùng ngày hôm qua để chắc chắn có data)
    print("\n📊 Bước 2: Lấy thống kê AQI...")
    today = datetime.now()
    yesterday = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    
    stats = get_district_statistics(yesterday)
    
    # Sắp xếp theo AQI từ cao xuống thấp để có ranking
    stats_sorted = sorted(stats, key=lambda x: x.get('val', 0), reverse=True)
    
    for idx, stat_data in enumerate(stats_sorted, 1):
        all_data.append({
            'data_type': 'current_aqi',
            'date': yesterday,
            'district_id': stat_data.get('id', ''),
            'district_name': stat_data.get('name', ''),
            'rank': idx,
            'aqi_avg': stat_data.get('val', 0),
            'aqi_prev': None,
            'forecast_date': None,
            'forecast_aqi': None
        })
    
    time.sleep(0.5)  # Tránh spam API
    
    # 3. Lấy forecast data cho một số quận/huyện
    print("\n🔮 Bước 3: Lấy dữ liệu forecast...")
    
    # Nếu chưa đủ 100 mẫu, lấy thêm forecast data
    if len(all_data) < num_samples:
        # Chọn 3 quận/huyện để lấy forecast (mỗi quận có ~10-20 mẫu)
        for district in districts[:3]:
            district_id = district.get('id')
            district_name = district.get('name')
            
            print(f"  Đang lấy forecast cho {district_name}...")
            forecast_data = get_forecast_data(district_id, yesterday, predays=3, nextdays=7)
            
            if forecast_data and 'comps' in forecast_data:
                for item in forecast_data['comps']:
                    req_date = item.get('requestdate', '')
                    all_data.append({
                        'data_type': 'forecast' if req_date > yesterday else 'historical',
                        'date': yesterday,
                        'district_id': district_id,
                        'district_name': district_name,
                        'rank': None,
                        'aqi_avg': item.get('val', 0),
                        'aqi_prev': None,
                        'forecast_date': req_date,
                        'forecast_aqi': item.get('val_aqi', 0)
                    })
            
            time.sleep(0.5)
            
            # Kiểm tra nếu đã đủ 100 mẫu
            if len(all_data) >= num_samples:
                break
    
    # Giới hạn số lượng mẫu
    return all_data[:num_samples]

def save_to_csv(data: List[Dict], filename: str = "hanoiair_data.csv"):
    """Lưu dữ liệu vào file CSV"""
    if not data:
        print("❌ Không có dữ liệu để lưu")
        return
    
    fieldnames = [
        'data_type', 'date', 'district_id', 'district_name', 
        'rank', 'aqi_avg', 'aqi_prev', 'forecast_date', 'forecast_aqi'
    ]
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        
        print(f"\n✅ Đã lưu {len(data)} mẫu vào file {filename}")
    except Exception as e:
        print(f"❌ Lỗi khi lưu file CSV: {e}")

def main():
    print("=" * 60)
    print("🚀 BẮT ĐẦU CRAWL DỮ LIỆU HANOIAIR")
    print("=" * 60)
    
    # Crawl 100 mẫu
    data = crawl_data(num_samples=100)
    
    if data:
        # Lưu vào CSV
        save_to_csv(data, "hanoiair_data.csv")
        
        print("\n" + "=" * 60)
        print("✅ HOÀN THÀNH!")
        print(f"📊 Tổng số mẫu: {len(data)}")
        print(f"📁 File: hanoiair_data.csv")
        print("=" * 60)
    else:
        print("\n❌ Không crawl được dữ liệu")

if __name__ == "__main__":
    main()
