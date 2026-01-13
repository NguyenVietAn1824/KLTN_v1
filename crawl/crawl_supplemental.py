#!/usr/bin/env python3
"""
Script bổ sung crawl dữ liệu còn thiếu:
- Rankings (thử nhiều ngày)
- Historical data (thử nhiều payload)
- Grid AQI data (từ WMTS tiles)
"""

import requests
import csv
from datetime import datetime, timedelta
import time

BASE_URL = "https://geoi.com.vn"

def try_rankings_multiple_days(days_back=30):
    """Thử lấy rankings cho nhiều ngày"""
    print("\n" + "="*70)
    print("🏆 THỬ LẤY RANKINGS CHO NHIỀU NGÀY")
    print("="*70)
    
    url = f"{BASE_URL}/api/componentgeotiffdaily/rankingprovince"
    rankings_found = []
    
    for i in range(days_back):
        date_obj = datetime.now() - timedelta(days=i)
        date_str = date_obj.strftime("%Y-%m-%d")
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
            data = response.json()
            
            if data.get('Code') == 200 and data.get('Data'):
                comps = data['Data'].get('comps', [])
                if comps:
                    print(f"  ✓ {date_str}: {len(comps)} rankings")
                    for rank_data in comps:
                        rankings_found.append({
                            'administrative_id': rank_data.get('administrative_id'),
                            'district_name': rank_data.get('administrative_name'),
                            'rank': rank_data.get('no'),
                            'aqi_avg': rank_data.get('avg'),
                            'aqi_prev': rank_data.get('avg_pre'),
                            'date': date_str
                        })
                    break  # Tìm được rồi thì dừng
        except:
            pass
        
        if i % 5 == 0 and i > 0:
            print(f"  • Đã thử {i} ngày...")
        time.sleep(0.2)
    
    if not rankings_found:
        print(f"  ⚠️  Không tìm thấy rankings trong {days_back} ngày gần đây")
    
    return rankings_found

def try_historical_multiple_methods():
    """Thử nhiều cách lấy historical data"""
    print("\n" + "="*70)
    print("📈 THỬ LẤY HISTORICAL DATA")
    print("="*70)
    
    url = f"{BASE_URL}/api/componentgeotiffdaily/identify_province_id_list_geotiff"
    historical_found = []
    
    # Method 1: Province-wide với nhiều ngày
    for days_back in [3, 7, 14, 30]:
        date_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        payload = {
            "province_id": "VNM.27_1",
            "groupcomponent_id": "63",
            "date_request": date_str,
            "predays": days_back,
            "nextdays": 0,
            "lang_id": "vi"
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            data = response.json()
            
            if data.get('Code') == 200 and data.get('Data'):
                comps = data['Data'].get('comps', [])
                if comps:
                    print(f"  ✓ Method 1 (predays={days_back}): {len(comps)} records")
                    for comp in comps:
                        historical_found.append({
                            'province_id': 'VNM.27_1',
                            'province_name': 'Hà Nội',
                            'date': comp.get('requestdate'),
                            'pm25_value': comp.get('val'),
                            'aqi_value': comp.get('val_aqi'),
                            'component': comp.get('titlecomponent', 'PM2.5')
                        })
                    break
        except:
            pass
        
        time.sleep(0.3)
    
    # Method 2: Thử với date_request cũ hơn
    if not historical_found:
        for days_back in [30, 60, 90]:
            date_str = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
            
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
                data = response.json()
                
                if data.get('Code') == 200 and data.get('Data'):
                    comps = data['Data'].get('comps', [])
                    if comps:
                        print(f"  ✓ Method 2 (date={date_str}): {len(comps)} records")
                        for comp in comps:
                            historical_found.append({
                                'province_id': 'VNM.27_1',
                                'province_name': 'Hà Nội',
                                'date': comp.get('requestdate'),
                                'pm25_value': comp.get('val'),
                                'aqi_value': comp.get('val_aqi'),
                                'component': comp.get('titlecomponent', 'PM2.5')
                            })
                        break
            except:
                pass
            
            time.sleep(0.3)
    
    if not historical_found:
        print(f"  ⚠️  Không tìm thấy historical data")
    
    return historical_found

def crawl_grid_aqi_sample():
    """Crawl mẫu grid AQI từ WMTS tiles"""
    print("\n" + "="*70)
    print("🗺️  CRAWL GRID AQI (WMTS TILES) - MẪU")
    print("="*70)
    
    try:
        import mapbox_vector_tile
        print("  ✓ mapbox_vector_tile available")
    except ImportError:
        print("  ⚠️  Cần cài: pip install mapbox-vector-tile")
        print("  → Bỏ qua crawl grid AQI")
        return []
    
    grid_data = []
    
    # Tile covering Hà Nội center (zoom 9)
    tiles_to_crawl = [
        (812, 196, 9),  # Cầu Giấy area
        (812, 197, 9),  # Đống Đa area
    ]
    
    for tilecol, tilerow, zoom in tiles_to_crawl:
        url = f"{BASE_URL}/geoserver/gwc/service/wmts"
        params = {
            "REQUEST": "GetTile",
            "SERVICE": "WMTS",
            "VERSION": "1.0.0",
            "LAYER": "hydroalp:gis_a_station_days_aqi_pm25",
            "STYLE": "",
            "TILEMATRIX": f"EPSG:4326:{zoom}",
            "TILEMATRIXSET": "EPSG:4326",
            "FORMAT": "application/vnd.mapbox-vector-tile",
            "TILECOL": str(tilecol),
            "TILEROW": str(tilerow)
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                tile_data = mapbox_vector_tile.decode(response.content)
                
                for layer_name, layer_data in tile_data.items():
                    features = layer_data.get('features', [])
                    print(f"  ✓ Tile ({tilecol},{tilerow}): {len(features)} features")
                    
                    # Lấy 20 features đầu mỗi tile
                    for feature in features[:20]:
                        props = feature.get('properties', {})
                        grid_data.append({
                            'latitude': props.get('coor_y'),
                            'longitude': props.get('coor_x'),
                            'aqi_pm25': props.get('aqi_pm25'),
                            'measurement_time': props.get('datetime_shooting'),
                            'parent_id': props.get('parent_id'),
                            'group_id': props.get('group_id'),
                            'oid': props.get('oid')
                        })
        except Exception as e:
            print(f"  ✗ Tile ({tilecol},{tilerow}): {e}")
        
        time.sleep(0.3)
    
    print(f"  → Tổng: {len(grid_data)} grid points")
    return grid_data

def save_supplemental_data(rankings, historical, grid_data):
    """Lưu dữ liệu bổ sung"""
    files = []
    
    if rankings:
        filename = 'rankings_supplemental.csv'
        fieldnames = ['administrative_id', 'district_name', 'rank', 'aqi_avg', 'aqi_prev', 'date']
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rankings)
        files.append(f"{filename} ({len(rankings)} rows)")
    
    if historical:
        filename = 'historical_supplemental.csv'
        fieldnames = ['province_id', 'province_name', 'date', 'pm25_value', 'aqi_value', 'component']
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(historical)
        files.append(f"{filename} ({len(historical)} rows)")
    
    if grid_data:
        filename = 'grid_aqi_supplemental.csv'
        fieldnames = ['latitude', 'longitude', 'aqi_pm25', 'measurement_time', 'parent_id', 'group_id', 'oid']
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(grid_data)
        files.append(f"{filename} ({len(grid_data)} rows)")
    
    return files

def main():
    print("\n" + "="*70)
    print("🔧 CRAWL DỮ LIỆU BỔ SUNG")
    print("="*70)
    
    # 1. Rankings
    rankings = try_rankings_multiple_days(days_back=30)
    
    # 2. Historical
    historical = try_historical_multiple_methods()
    
    # 3. Grid AQI
    grid_data = crawl_grid_aqi_sample()
    
    # Save
    if rankings or historical or grid_data:
        print("\n" + "="*70)
        print("💾 Lưu dữ liệu...")
        print("="*70)
        files = save_supplemental_data(rankings, historical, grid_data)
        
        print("\n✅ Hoàn thành!")
        print(f"📁 Files:")
        for f in files:
            print(f"   • {f}")
    else:
        print("\n⚠️  Không crawl được dữ liệu bổ sung nào")
    
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
