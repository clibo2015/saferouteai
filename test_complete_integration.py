#!/usr/bin/env python3
"""
Complete Integration Test for SafeRouteAI with Huawei Map Kit
Tests the full stack: Backend API + Frontend + Map Kit integration
"""
import requests
import json
import time
import sys
from datetime import datetime

def test_backend_api():
    """Test backend API endpoints"""
    print("🧪 Testing Backend API Integration")
    print("=" * 50)
    
    base_url = "http://localhost:8004"
    
    # Test root endpoint
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend API: {data['message']}")
            print(f"   Version: {data['version']}")
            print(f"   Map Kit: {data['services']['map_kit']}")
        else:
            print(f"❌ Backend API failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend API connection failed: {e}")
        return False
    
    # Test map configuration
    try:
        response = requests.get(f"{base_url}/api/v1/map/config", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                print(f"✅ Map Config: API key configured")
                print(f"   Region: {data['map_config']['region']}")
                print(f"   Production: {data['map_config']['production_mode']}")
            else:
                print("❌ Map config failed")
                return False
        else:
            print(f"❌ Map config failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Map config error: {e}")
        return False
    
    # Test markers endpoint
    try:
        response = requests.get(f"{base_url}/api/v1/map/markers", timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                print(f"✅ Crime Markers: {data['total_markers']} markers loaded")
                print(f"   Data Source: {data['data_source']}")
            else:
                print("❌ Markers failed")
                return False
        else:
            print(f"❌ Markers failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Markers error: {e}")
        return False
    
    # Test heatmap endpoint (this might be slow due to large dataset)
    try:
        print("   Loading safety heatmap (this may take a moment)...")
        response = requests.get(f"{base_url}/api/v1/map/safety-heatmap", timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                print(f"✅ Safety Heatmap: {data['total_points']} data points")
                print(f"   Sources: {', '.join(data['data_sources'])}")
            else:
                print("❌ Heatmap failed")
                return False
        else:
            print(f"❌ Heatmap failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Heatmap error: {e}")
        return False
    
    return True

def test_route_optimization():
    """Test route optimization with safety analysis"""
    print("\n🛣️  Testing Route Optimization")
    print("=" * 50)
    
    base_url = "http://localhost:8004"
    
    # Test route optimization
    route_request = {
        "start_point": {"lat": -26.2041, "lng": 28.0473},  # Johannesburg
        "end_point": {"lat": -33.9249, "lng": 18.4241},    # Cape Town
        "departure_time": datetime.now().isoformat(),
        "safety_preferences": {
            "avoid_high_crime": True,
            "prefer_main_roads": True,
            "safety_weight": 0.8
        }
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/optimize-route", 
            json=route_request, 
            timeout=20
        )
        
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                route = data['route_data']
                print(f"✅ Route Optimization: {route['route_id']}")
                print(f"   Distance: {route['total_distance_km']} km")
                print(f"   Time: {route['total_time_minutes']} minutes")
                print(f"   Safety Score: {route['overall_safety_score']:.2f}")
                print(f"   Segments: {len(route['segments'])}")
                return True
            else:
                print("❌ Route optimization failed")
                return False
        else:
            print(f"❌ Route optimization failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Route optimization error: {e}")
        return False

def test_hazard_reporting():
    """Test user hazard reporting"""
    print("\n🚨 Testing Hazard Reporting")
    print("=" * 50)
    
    base_url = "http://localhost:8004"
    
    hazard_report = {
        "latitude": -26.2041,
        "longitude": 28.0473,
        "hazard_type": "pothole",
        "description": "Large pothole on main road",
        "severity": 0.7
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/map/report-hazard",
            json=hazard_report,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                print(f"✅ Hazard Reported: {data['hazard_id']}")
                print(f"   Impact Radius: {data['estimated_impact']['radius_meters']}m")
                print(f"   Duration: {data['estimated_impact']['duration_minutes']} minutes")
                return True
            else:
                print("❌ Hazard reporting failed")
                return False
        else:
            print(f"❌ Hazard reporting failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Hazard reporting error: {e}")
        return False

def test_edge_ai_integration():
    """Test Edge AI driver behavior analysis"""
    print("\n🤖 Testing Edge AI Integration")
    print("=" * 50)
    
    base_url = "http://localhost:8004"
    
    sensor_data = {
        "sensor_data": {
            "speed": 60,
            "acceleration": 0.5,
            "location": {"lat": -26.2041, "lng": 28.0473},
            "timestamp": datetime.now().isoformat()
        },
        "analysis_type": "behavior"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/edge-ai/driver-behavior",
            json=sensor_data,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                analysis = data['behavior_analysis']
                print(f"✅ Driver Behavior Analysis Complete")
                print(f"   Behavior Score: {analysis['driver_behavior_score']:.2f}")
                print(f"   Speed Assessment: {analysis['speed_assessment']}")
                print(f"   Driving Style: {analysis['driving_style']}")
                return True
            else:
                print("❌ Edge AI analysis failed")
                return False
        else:
            print(f"❌ Edge AI analysis failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Edge AI analysis error: {e}")
        return False

def check_frontend_accessibility():
    """Check if React frontend is accessible"""
    print("\n⚛️  Testing React Frontend")
    print("=" * 50)
    
    try:
        response = requests.get("http://localhost:3000", timeout=10)
        if response.status_code == 200:
            print("✅ React Frontend: Accessible at http://localhost:3000")
            print("   You can now test the Map Kit integration in the browser")
            return True
        else:
            print(f"❌ React Frontend: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"⚠️  React Frontend: Not accessible ({e})")
        print("   This is normal if the React server is still starting")
        return False

def main():
    """Run complete integration test"""
    print("🇿🇦 SafeRouteAI - Complete Integration Test")
    print("🗺️  Huawei Map Kit + Backend API + Frontend")
    print("=" * 70)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test backend API
    backend_ok = test_backend_api()
    
    # Test route optimization
    route_ok = test_route_optimization()
    
    # Test hazard reporting
    hazard_ok = test_hazard_reporting()
    
    # Test Edge AI
    edge_ai_ok = test_edge_ai_integration()
    
    # Check frontend
    frontend_ok = check_frontend_accessibility()
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 INTEGRATION TEST SUMMARY")
    print("=" * 70)
    
    tests = [
        ("Backend API", backend_ok),
        ("Route Optimization", route_ok),
        ("Hazard Reporting", hazard_ok),
        ("Edge AI Integration", edge_ai_ok),
        ("React Frontend", frontend_ok)
    ]
    
    passed = sum(1 for _, ok in tests if ok)
    total = len(tests)
    
    for test_name, ok in tests:
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ SafeRouteAI integration is working correctly")
        print()
        print("Next Steps:")
        print("1. Open http://localhost:3000 in your browser")
        print("2. Navigate to a page with the Huawei Map component")
        print("3. Open test_map_integration.html for detailed Map Kit testing")
        print("4. Configure authorized domains in AppGallery Connect if needed:")
        print("   • http://localhost:3000")
        print("   • http://127.0.0.1:3000")
        print("   • http://localhost:8004")
        return True
    else:
        print(f"\n❌ {total - passed} tests failed")
        print("Check the error messages above for troubleshooting")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)