#!/usr/bin/env python3
"""
Quick test for the route optimization endpoint
"""
import requests
import json

def test_route_optimization():
    url = "http://localhost:8003/api/v1/optimize-route"
    
    payload = {
        "start_point": {"lat": -26.2041, "lng": 28.0473},  # Johannesburg CBD
        "end_point": {"lat": -26.2678, "lng": 27.8546},    # Soweto
        "departure_time": "2026-02-03T23:30:00",
        "safety_preferences": {
            "avoid_high_crime": True,
            "avoid_load_shedding": True,
            "priority": "safety"
        }
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Route Optimization Test PASSED")
            print(f"Route ID: {data['route_data']['route_id']}")
            print(f"Total Distance: {data['route_data']['total_distance_km']} km")
            print(f"Total Time: {data['route_data']['total_time_minutes']} minutes")
            print(f"Safety Score: {data['route_data']['overall_safety_score']}")
            print(f"Segments: {len(data['route_data']['segments'])}")
            return True
        else:
            print(f"❌ Route Optimization Test FAILED: HTTP {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"❌ Route Optimization Test FAILED: {e}")
        return False

if __name__ == "__main__":
    print("🚗 Testing Route Optimization Endpoint")
    print("="*50)
    test_route_optimization()