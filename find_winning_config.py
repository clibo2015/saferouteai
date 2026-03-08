
import os
import requests
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("HUAWEI_MAP_API_KEY")
LOCATION_KEY = os.getenv("HUAWEI_LOCATION_API_KEY")

REGIONS = ["DE", "SG", "CN", "RU", "US"]

def test():
    print("🔍 Hunting for the winning Map Kit token combination...")
    
    # User OAuth Token
    user_token = None
    try:
        resp = requests.post("https://oauth-login.cloud.huawei.com/oauth2/v3/token", data={
            "grant_type": "client_credentials",
            "client_id": os.getenv("HUAWEI_OAUTH_CLIENT_ID"),
            "client_secret": os.getenv("HUAWEI_OAUTH_CLIENT_SECRET")
        }, timeout=5)
        user_token = resp.json().get("access_token")
    except: pass

    # API Client OAuth Token
    api_token = None
    try:
        resp = requests.post("https://connect-api.cloud.huawei.com/api/oauth2/v1/token", json={
            "grant_type": "client_credentials",
            "client_id": os.getenv("HUAWEI_API_CLIENT_ID"),
            "client_secret": os.getenv("HUAWEI_API_CLIENT_SECRET")
        }, timeout=5)
        api_token = resp.json().get("access_token")
    except: pass

    found_map = None
    tokens = [("USER_OAUTH", user_token), ("API_CLIENT", api_token)]
    
    for t_name, token in tokens:
        if not token:
            print(f"⚠️ {t_name} token retrieval failed.")
            continue
        print(f"Testing {t_name} token...")
        for r_id in REGIONS:
            url = "https://mapapi.cloud.huawei.com/mapApi/v1/routeService/driving"
            payload = {"origin": {"lat": -26.2041, "lng": 28.0473}, "destination": {"lat": -26.2141, "lng": 28.0573}}
            headers = {
                "Content-Type": "application/json",
                "x-agccp-region-id": r_id,
                "Authorization": f"Bearer {token}"
            }
            try:
                resp = requests.post(url, json=payload, headers=headers, timeout=3)
                print(f"   Region {r_id}: {resp.status_code}")
                if resp.status_code == 200:
                    found_map = (t_name, r_id)
                    print(f"\n✅ SUCCESS! Token: {t_name}, Region: {r_id}")
                    break
            except: pass
        if found_map: break

    print(f"\n\nFINAL MAP WINNER: {found_map}")

if __name__ == "__main__":
    test()
