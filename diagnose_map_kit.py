"""
Diagnostic script to check Huawei Map Kit API key configuration
"""
import requests
import json
from urllib.parse import quote_plus
import os
from dotenv import load_dotenv

load_dotenv()

# Get API key
api_key = os.getenv('HUAWEI_MAP_API_KEY')
if not api_key:
    print("❌ HUAWEI_MAP_API_KEY not found in environment")
    exit(1)

print(f"🔑 API Key: {api_key[:30]}...")

# URL encode
encoded_key = quote_plus(api_key)
print(f"🔒 Encoded Key: {encoded_key[:50]}...")

# Test different Map Kit endpoints
endpoints = [
    {
        "name": "Map JS API",
        "url": f"https://mapapi.cloud.huawei.com/mapjs/v1/api/js?callback=test&key={encoded_key}",
        "method": "GET"
    },
    {
        "name": "Map Config API",
        "url": f"https://mapapi.cloud.huawei.com/mapjs/v1/api/config?key={encoded_key}",
        "method": "GET"
    }
]

print("\n🔍 Testing Map Kit Endpoints:")
print("=" * 50)

for endpoint in endpoints:
    print(f"\nTesting {endpoint['name']}:")
    print(f"URL: {endpoint['url']}")
    
    try:
        if endpoint['method'] == 'GET':
            response = requests.get(endpoint['url'], timeout=10)
        else:
            response = requests.post(endpoint['url'], timeout=10)
            
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ SUCCESS - Endpoint accessible")
            if 'js' in endpoint['url']:
                print("   This means the JavaScript API should work")
            elif 'config' in endpoint['url']:
                try:
                    data = response.json()
                    print(f"   Config: {json.dumps(data, indent=2)[:200]}...")
                except:
                    print("   Response:", response.text[:200])
        elif response.status_code == 401:
            print("❌ UNAUTHORIZED - API key not valid for this service")
        elif response.status_code == 403:
            print("❌ FORBIDDEN - API key not authorized for this endpoint")
        elif response.status_code == 404:
            print("❌ NOT FOUND - Endpoint may not exist or API key not configured")
        else:
            print(f"❌ ERROR - HTTP {response.status_code}")
            print("   Response:", response.text[:200])
            
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")

print("\n" + "=" * 50)
print("📋 Troubleshooting Steps:")
print("1. Verify API key is enabled for Map Kit in AppGallery Connect")
print("2. Ensure 'JavaScript API' is enabled for the API key")
print("3. Check that authorized domains include localhost for development")
print("4. Confirm the API key has Map Kit permissions")
