import requests
import json

# Test geocoding endpoint
url = "http://localhost:8004/api/v1/map/geocode"
payload = {
    "address": "Times Square, New York"
}

try:
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            location = data["location"]
            print(f"✅ Found coordinates: {location['lat']}, {location['lng']}")
        else:
            print("❌ Geocoding failed")
    else:
        print(f"❌ HTTP Error: {response.status_code}")
        
except Exception as e:
    print(f"Error: {e}")
