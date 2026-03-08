#!/usr/bin/env python3
"""
Backend Stress Testing for SafeRouteAI
Tests performance, error handling, and edge cases
"""
import requests
import json
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

BASE_URL = "http://localhost:8003"

def test_concurrent_predictions(num_requests=10):
    """Test concurrent risk predictions"""
    print(f"\n🔄 Testing {num_requests} concurrent predictions...")
    
    def make_prediction(i):
        try:
            response = requests.post(f"{BASE_URL}/predict/risk", json={
                "latitude": -26.2041 + (i * 0.001),  # Slightly different locations
                "longitude": 28.0473 + (i * 0.001),
                "hour": 12 + (i % 12),
                "day_of_week": 1 + (i % 7)
            }, timeout=5)
            return response.status_code == 200
        except:
            return False
    
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(make_prediction, range(num_requests)))
    
    end_time = time.time()
    
    success_count = sum(results)
    duration = end_time - start_time
    
    print(f"   ✅ {success_count}/{num_requests} predictions successful")
    print(f"   ⏱️ Duration: {duration:.2f} seconds")
    print(f"   📊 Rate: {num_requests/duration:.1f} requests/second")
    
    return success_count == num_requests

def test_multiple_training_jobs():
    """Test creating multiple training jobs"""
    print(f"\n🧠 Testing multiple training jobs...")
    
    jobs_created = []
    
    for i in range(3):
        try:
            response = requests.post(f"{BASE_URL}/training/start", json={
                "job_name": f"stress-test-job-{i}-{datetime.now().strftime('%H%M%S')}",
                "algorithm": "RandomForest" if i % 2 == 0 else "XGBoost",
                "features": ["latitude", "longitude", "hour", "day_of_week"]
            }, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                jobs_created.append(result['job_id'])
                print(f"   ✅ Job {i+1}: {result['job_id']}")
            else:
                print(f"   ❌ Job {i+1}: Failed")
                
        except Exception as e:
            print(f"   ❌ Job {i+1}: Error - {str(e)}")
    
    print(f"   📊 Created {len(jobs_created)}/3 training jobs")
    return len(jobs_created) >= 2  # Allow 1 failure

def test_route_optimization_variations():
    """Test route optimization with different parameters"""
    print(f"\n🗺️ Testing route optimization variations...")
    
    test_routes = [
        # Johannesburg to Pretoria
        {
            "start": {"latitude": -26.2041, "longitude": 28.0473},
            "end": {"latitude": -25.7479, "longitude": 28.2293},
            "time_of_day": 8, "day_of_week": 1
        },
        # Cape Town CBD to Waterfront
        {
            "start": {"latitude": -33.9249, "longitude": 18.4241},
            "end": {"latitude": -33.9030, "longitude": 18.4172},
            "time_of_day": 18, "day_of_week": 5
        },
        # Durban beachfront route
        {
            "start": {"latitude": -29.8587, "longitude": 31.0218},
            "end": {"latitude": -29.8830, "longitude": 31.0493},
            "time_of_day": 22, "day_of_week": 6
        }
    ]
    
    successful_routes = 0
    
    for i, route in enumerate(test_routes):
        try:
            route_data = {
                **route,
                "avoid_high_crime": True,
                "avoid_load_shedding": True
            }
            
            response = requests.post(f"{BASE_URL}/route/optimize", 
                                   json=route_data, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                waypoints = len(result.get('waypoints', []))
                safety_score = result.get('route_metrics', {}).get('average_risk_score', 0)
                print(f"   ✅ Route {i+1}: {waypoints} waypoints, safety: {safety_score:.1f}/10")
                successful_routes += 1
            else:
                print(f"   ❌ Route {i+1}: Status {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Route {i+1}: Error - {str(e)}")
    
    print(f"   📊 Optimized {successful_routes}/{len(test_routes)} routes")
    return successful_routes >= 2

def test_error_handling():
    """Test API error handling"""
    print(f"\n🚨 Testing error handling...")
    
    error_tests = [
        # Invalid coordinates
        ("POST", "/predict/risk", {
            "latitude": 999,  # Invalid latitude
            "longitude": 28.0473,
            "hour": 12,
            "day_of_week": 1
        }),
        # Missing required fields
        ("POST", "/route/optimize", {
            "start": {"latitude": -26.2041, "longitude": 28.0473}
            # Missing end point
        }),
        # Invalid training job
        ("POST", "/training/start", {
            "job_name": "",  # Empty name
            "algorithm": "InvalidAlgorithm"
        }),
        # Non-existent job ID
        ("GET", "/training/jobs/non-existent-job-id", None)
    ]
    
    handled_errors = 0
    
    for method, endpoint, data in error_tests:
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            else:
                response = requests.post(f"{BASE_URL}{endpoint}", json=data, timeout=5)
            
            # We expect these to either fail gracefully (4xx) or handle the error (200 with error message)
            if response.status_code in [200, 400, 404, 422]:
                handled_errors += 1
                print(f"   ✅ {method} {endpoint}: Handled gracefully ({response.status_code})")
            else:
                print(f"   ❌ {method} {endpoint}: Unexpected status {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ {method} {endpoint}: Exception - {str(e)}")
    
    print(f"   📊 Handled {handled_errors}/{len(error_tests)} error cases")
    return handled_errors >= 3

def test_data_persistence():
    """Test that data persists between requests"""
    print(f"\n💾 Testing data persistence...")
    
    try:
        # Get initial job count
        response1 = requests.get(f"{BASE_URL}/training/jobs", timeout=5)
        initial_count = len(response1.json().get('jobs', []))
        
        # Create a new job
        response2 = requests.post(f"{BASE_URL}/training/start", json={
            "job_name": f"persistence-test-{datetime.now().strftime('%H%M%S')}",
            "algorithm": "RandomForest"
        }, timeout=10)
        
        if response2.status_code != 200:
            print("   ❌ Failed to create test job")
            return False
        
        # Check job count increased
        response3 = requests.get(f"{BASE_URL}/training/jobs", timeout=5)
        final_count = len(response3.json().get('jobs', []))
        
        if final_count > initial_count:
            print(f"   ✅ Job count increased: {initial_count} → {final_count}")
            return True
        else:
            print(f"   ❌ Job count unchanged: {initial_count} → {final_count}")
            return False
            
    except Exception as e:
        print(f"   ❌ Persistence test failed: {str(e)}")
        return False

def main():
    """Run comprehensive backend stress tests"""
    print("🔥 SafeRouteAI Backend Stress Testing")
    print("="*50)
    
    # Check if API is running
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code != 200:
            print("❌ API not accessible")
            return
    except:
        print("❌ API not running - start with: python demo_api_with_mock.py")
        return
    
    print("✅ API is running - starting stress tests...")
    
    # Run stress tests
    tests = [
        ("Concurrent Predictions", test_concurrent_predictions),
        ("Multiple Training Jobs", test_multiple_training_jobs),
        ("Route Optimization Variations", test_route_optimization_variations),
        ("Error Handling", test_error_handling),
        ("Data Persistence", test_data_persistence)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}")
        print("-" * 30)
        
        start_time = time.time()
        try:
            result = test_func()
            duration = time.time() - start_time
            
            if result:
                print(f"   ✅ PASSED ({duration:.2f}s)")
                passed += 1
            else:
                print(f"   ❌ FAILED ({duration:.2f}s)")
        except Exception as e:
            duration = time.time() - start_time
            print(f"   ❌ ERROR ({duration:.2f}s): {str(e)}")
    
    # Final summary
    print("\n" + "="*50)
    print("🏆 STRESS TEST RESULTS")
    print("="*50)
    print(f"✅ Passed: {passed}/{total} tests")
    print(f"📊 Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 ALL STRESS TESTS PASSED!")
        print("   Backend is robust and production-ready")
        print("   Handles concurrent requests well")
        print("   Error handling is working properly")
        print("   Data persistence is functioning")
    elif passed >= total * 0.8:
        print("\n✅ MOSTLY SUCCESSFUL!")
        print("   Backend is stable with minor issues")
        print("   Ready for demo and development")
    else:
        print("\n⚠️  SOME ISSUES DETECTED")
        print("   Check failed tests above")
        print("   May need debugging before production")

if __name__ == "__main__":
    main()