
import requests
import json
from urllib.parse import quote_plus
import sys
import os

# Add src to path for settings
sys.path.append('src')

try:
    from config import settings
    
    # Use real credentials from .env
    API_KEY = settings.huawei_map_api_key
    LOCATION_KEY = settings.huawei_location_api_key
    
    # Define map_payload early to avoid name error
    map_payload = {
        "origin": {"lat": -26.2041, "lng": 28.0473},
        "destination": {"lat": -25.7479, "lng": 28.2293},
        "lang": "en"
    }

    # Updated Endpoints list
    USER_OAUTH_URL = "https://oauth-login.cloud.huawei.com/oauth2/v3/token"
    API_CLIENT_OAUTH_URL = "https://connect-api.cloud.huawei.com/api/oauth2/v1/token"
    
    # siteapi clusters: dre (Europe/Africa), dra (Asia/Africa), drn (North America), dru (Russia)
    SITE_CLUSTERS = ["dre", "dra", "drn", "dru"]
    SITE_BASE_URLS = [f"https://siteapi-{c}.cloud.huawei.com/mapApi/v1/siteService" for c in SITE_CLUSTERS]
    SITE_BASE_URLS.append("https://siteapi.cloud.huawei.com/mapApi/v1/siteService")

    MAP_CLUSTERS = ["dre", "dra", "drn", "dru"]
    MAP_BASE_URLS = [f"https://mapapi-{c}.cloud.huawei.com/mapApi/v1/routeService" for c in MAP_CLUSTERS]
    MAP_BASE_URLS.append("https://mapapi.cloud.huawei.com/mapApi/v1/routeService")

    REGIONS = ["DE", "SG", "CN", "RU", "US"]

    print("\n🔍 --- Huawei Cloud Services Verification (Exhaustive) ---")
    print(f"Project ID: {settings.huawei_project_id}")
    
    # 1. OAuth
    print("\n🔑 Testing OAuth Tokens...")
    user_token = None
    if settings.huawei_oauth_client_id:
        try:
            resp = requests.post(USER_OAUTH_URL, data={
                "grant_type": "client_credentials",
                "client_id": settings.huawei_oauth_client_id,
                "client_secret": settings.huawei_oauth_client_secret
            }, timeout=10)
            if resp.status_code == 200:
                user_token = resp.json().get("access_token")
                print("   ✅ User OAuth: SUCCESS")
        except Exception as e: print(f"   ❌ User OAuth Error: {e}")

    api_token = None
    if settings.huawei_api_client_id:
        try:
            resp = requests.post(API_CLIENT_OAUTH_URL, json={
                "grant_type": "client_credentials",
                "client_id": settings.huawei_api_client_id,
                "client_secret": settings.huawei_api_client_secret
            }, timeout=10)
            if resp.status_code == 200:
                api_token = resp.json().get("access_token")
                print("   ✅ API Client OAuth: SUCCESS")
        except Exception as e: print(f"   ❌ API Client OAuth Error: {e}")

    effective_token = api_token or user_token

    # 2. Site Kit Exhaustive
    print("\n📍 Testing Huawei Site Kit (Exhaustive)...")
    site_success = False
    for base_url in SITE_BASE_URLS:
        if site_success: break
        for method in ["POST", "GET"]:
            if site_success: break
            endpoint = "/searchByText" if method == "POST" else "/nearbySearch"
            full_url_template = f"{base_url}{endpoint}?key={quote_plus(LOCATION_KEY)}"
            
            # Simple payload for searchByText
            payload = {"query": "Pizza", "location": {"lat": -26.2041, "lng": 28.0473}, "radius": 5000}
            # Simple params for nearbySearch
            params = {"location": "-26.2041,28.0473", "radius": 5000, "query": "Pizza"}
            
            for r_id in REGIONS:
                try:
                    headers = {"Content-Type": "application/json", "x-agccp-region-id": r_id}
                    if effective_token: headers["Authorization"] = f"Bearer {effective_token}"
                    
                    print(f"   Trying: {method} {base_url}{endpoint} [Region: {r_id}]...")
                    if method == "POST":
                        resp = requests.post(full_url_template, json=payload, headers=headers, timeout=5)
                    else:
                        resp = requests.get(full_url_template, params=params, headers=headers, timeout=5)
                    
                    print(f"   Response: {resp.status_code} - {resp.text[:100]}...")
                    if resp.status_code == 200 and ("sites" in resp.text or "site" in resp.text):
                        print("   ✅ SUCCESS!")
                        site_success = True
                        break
                except Exception as e:
                    print(f"   ❌ Error: {e}")

    # 3. Map Kit Exhaustive
    print("\n🚗 Testing Huawei Map Kit (Exhaustive)...")
    map_success = False
    for base_url in MAP_BASE_URLS:
        if map_success: break
        endpoint = "/driving"
        full_url_template = f"{base_url}{endpoint}?key={quote_plus(API_KEY)}"
        
        for r_id in REGIONS:
            try:
                headers = {"Content-Type": "application/json", "x-agccp-region-id": r_id}
                if effective_token: headers["Authorization"] = f"Bearer {effective_token}"
                
                print(f"   Trying: POST {base_url}{endpoint} [Region: {r_id}]...")
                resp = requests.post(full_url_template, json=map_payload, headers=headers, timeout=5)
                print(f"   Response: {resp.status_code} - {resp.text[:100]}...")
                if resp.status_code == 200 and "routes" in resp.text:
                    print("   ✅ SUCCESS!")
                    map_success = True
                    break
            except Exception as e:
                print(f"   ❌ Error: {e}")

    # 4. Test OBS (Object Storage Service) - Proof of AK/SK
    print("\n📦 Testing Huawei Cloud OBS (AK/SK Validity)...")
    try:
        from obs import ObsClient
        
        obs_client = ObsClient(
            access_key_id=settings.huawei_cloud_ak,
            secret_access_key=settings.huawei_cloud_sk,
            server=f"https://obs.af-south-1.myhuaweicloud.com"
        )
        
        print("   📍 Attempting to list buckets in Johannesburg (af-south-1)...")
        resp = obs_client.listBuckets()
        
        if resp.status < 300:
            print("   ✅ OBS Connection: SUCCESS!")
            print(f"   Buckets Found: {len(resp.body.buckets) if resp.body.buckets else 0}")
            print("   --- REAL AK/SK CREDENTIALS VERIFIED ---")
        else:
            print(f"   ❌ OBS Connection: FAILED - {resp.status} {resp.reason}")
            
    except Exception as e:
        print(f"   ❌ OBS Error: {e}")
        print("   💡 Note: This requires the huaweicloud-sdk-python-obs package.")

    # 5. Final Report
    print("\n" + "="*40)
    print("📋 VERIFICATION SUMMARY")
    print("="*40)
    print(f"OAuth Connectivity:  {'✅ VERIFIED' if effective_token else '❌ FAILED'}")
    print(f"Site Kit Results:    {'✅ READY' if site_success else '⚠️ SERVICE NOT ACTIVATED'}")
    print(f"Map Kit Results:     {'✅ READY' if map_success else '⚠️ SERVICE NOT ACTIVATED'}")
    print("="*40)
    if not (site_success or map_success):
        print("\n💡 NEXT STEPS FOR REAL MAPS:")
        print("1. Log in to AppGallery Connect (https://developer.huawei.com/consumer/en/service/josp/agc/index.html)")
        print(f"2. Open Project: {settings.huawei_project_id}")
        print("3. Go to 'Manage APIs' and ensure 'Map Kit' and 'Site Kit' are toggled ON.")
        print("4. Ensure your account has accepted the 'Huawei Map Kit Service Agreement'.")

except Exception as e:
    print(f"Setup Error: {e}")
