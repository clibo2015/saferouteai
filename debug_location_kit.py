import requests
import json
from urllib.parse import quote_plus
import os

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Get API key from environment
api_key = os.getenv('HUAWEI_LOCATION_API_KEY')
if not api_key:
    print("❌ HUAWEI_LOCATION_API_KEY not found in environment")
    exit(1)

print(f"🔑 Using API Key: {api_key[:20]}...")

# URL encode the key
encoded_key = quote_plus(api_key)
print(f"🔒 Encoded Key: {encoded_key[:30]}...")

# Test Location Kit Geocoding API
url = f"https://siteapi-dre.cloud.huawei.com/mapApi/v1/siteService/geocode?key={encoded_key}"

headers = {
    "Content-Type": "application/json",
    "x-agccp-region-id": "DE"  # Required for Site Kit
}

# Test addresses
test_addresses = [
    "Rosenview, Pretoria, South Africa",
    "Times Square, New York, USA",
    "Cape Town, South Africa"
]

for address in test_addresses:
    print(f"\n📍 Testing: {address}")
    
    payload = {
        "address": address,
        "language": "en"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("returnCode") == "0" and data.get("sites"):
                location = data["sites"][0]["location"]
                print(f"   ✅ Coordinates: {location['lat']}, {location['lng']}")
            else:
                print(f"   ❌ No results: {data.get('returnDesc', 'Unknown error')}")
        else:
            print(f"   ❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
