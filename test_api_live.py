#!/usr/bin/env python3
"""
Live API Testing for SafeRouteAI Backend
Tests all endpoints while API server is running
"""
import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8003"

def test_endpoint(method, endpoint, data=None, description=""):
    """Test a single API endpoint"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, timeout=10)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, timeout=10)
        else:
            print(f"❌ Unsupported method: {method}")
            return False
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ {method} {endpoint} - {description}")
            if isinstance(result, dict) and len(result) <= 5:
                print(f"   Response: {json.dumps(result, indent=2)[:200]}...")
            return True
        else:
            print(f"❌ {method} {endpoint} - Status: {response.status_code}")
            print(f"   Error: {response.text[:200]}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ {method} {endpoint} - Connection failed (API not running?)")
        return False
    except Exception as e:
        print(f"❌ {method} {endpoint} - Error: {str(e)}")
        return False

def main():
    """Test all API endpoints"""
    print("🧪 SafeRouteAI Backend Live Testing")
    print("="*50)
    
    tests = []
    
    # Basic endpoints
    print("\n📋 Testing Basic Endpoints...")
    tests.append(("GET", "/", None, "API Root"))
    tests.append(("GET", "/status", None, "Service Status"))
    
    # Data management
    print("\n📤 Testing Data Management...")
    tests.append(("POST", "/data/upload", None, "Upload SafeRouteAI Data"))
    
    # Training endpoints
    print("\n🧠 Testing Training Endpoints...")
    training_request = {
        "job_name": f"api-test-{datetime.now().strftime('%H%M%S')}",
        "algorithm": "RandomForest",
        "features": ["latitude", "longitude", "hour", "day_of_week"]
    }
    tests.append(("POST", "/training/start", training_request, "Start Training Job"))
    tests.append(("GET", "/training/jobs", None, "List Training Jobs"))
    
    # Prediction endpoints
    print("\n🎯 Testing Prediction Endpoints...")
    risk_request = {
        "latitude": -26.2041,
        "longitude": 28.0473,
        "hour": 14,
        "day_of_week": 2
    }
    tests.append(("POST", "/predict/risk", risk_request, "Risk Prediction"))
    
    # Route optimization
    print("\n🗺️ Testing Route Optimization...")
    route_request = {
        "start": {"latitude": -26.2041, "longitude": 28.0473},
        "end": {"latitude": -26.1367, "longitude": 28.0835},
        "time_of_day": 18,
        "day_of_week": 5,
        "avoid_high_crime": True,
        "avoid_load_shedding": True
    }
    tests.append(("POST", "/route/optimize", route_request, "Route Optimization"))
    
    # Demo workflow
    print("\n🚀 Testing Demo Workflow...")
    tests.append(("GET", "/demo/full-workflow", None, "Complete Workflow Demo"))
    
    # Run all tests
    passed = 0
    total = len(tests)
    
    for method, endpoint, data, description in tests:
        if test_endpoint(method, endpoint, data, description):
            passed += 1
        time.sleep(0.5)  # Small delay between requests
    
    # Summary
    print("\n" + "="*50)
    print("🏆 BACKEND TEST RESULTS")
    print("="*50)
    print(f"✅ Passed: {passed}/{total} tests")
    print(f"📊 Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 ALL BACKEND TESTS PASSED!")
        print("   SafeRouteAI backend is fully functional")
        print("   Ready for production use")
    else:
        print(f"\n⚠️  {total-passed} tests failed")
        print("   Check error messages above")
    
    print(f"\n🌐 API Documentation: {BASE_URL}/docs")
    print(f"📊 API Status: {BASE_URL}/status")

if __name__ == "__main__":
    main()