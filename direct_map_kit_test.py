"""
Direct test of the Map Kit service to isolate the geocoding issue
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.huawei_map_kit import map_kit_service
import requests
import json
from urllib.parse import quote_plus

print("=== Direct Map Kit Service Test ===")
print(f"Production Mode: {map_kit_service.production_mode}")
print(f"API Key Present: {bool(map_kit_service.location_api_key)}")

# Test the service method directly
print("\n--- Testing service method directly ---")
result1 = map_kit_service.get_real_gps_coordinates("Rosenview, Pretoria")
print(f"Service Result: {result1}")

# Test the raw API call manually
print("\n--- Testing raw API call ---")
api_key = map_kit_service.location_api_key
encoded_key = quote_plus(api_key)

url = f"https://siteapi-dre.cloud.huawei.com/mapApi/v1/siteService/geocode?key={encoded_key}"
headers = {
    "Content-Type": "application/json",
    "x-agccp-region-id": "DE"
}
payload = {
    "address": "Rosenview, Pretoria",
    "language": "en"
}

response = requests.post(url, json=payload, headers=headers, timeout=10)
print(f"Raw API Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Raw API Response: {json.dumps(data, indent=2)[:200]}...")
    if data.get("returnCode") == "0" and data.get("sites"):
        location = data["sites"][0]["location"]
        print(f"Raw API Coordinates: {location['lat']}, {location['lng']}")
else:
    print(f"Raw API Error: {response.text}")
