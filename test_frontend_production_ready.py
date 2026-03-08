#!/usr/bin/env python3
"""
Frontend Production Readiness Test
Verifies that the React frontend is properly integrated with real backend services
"""
import requests
import json
import time
import sys
from datetime import datetime

def test_frontend_backend_integration():
    """Test that frontend can communicate with backend"""
    print("🔗 Testing Frontend-Backend Integration")
    print("=" * 50)
    
    frontend_url = "http://localhost:3000"
    backend_url = "http://localhost:8004"
    
    # Test if React frontend is accessible
    try:
        response = requests.get(frontend_url, timeout=10)
        if response.status_code == 200:
            print("✅ React Frontend: Accessible")
            frontend_accessible = True
        else:
            print(f"❌ React Frontend: HTTP {response.status_code}")
            frontend_accessible = False
    except Exception as e:
        print(f"❌ React Frontend: Not accessible ({e})")
        frontend_accessible = False
    
    # Test if backend API is accessible
    try:
        response = requests.get(backend_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ Backend API: Accessible")
            print(f"   Version: {data.get('version', 'Unknown')}")
            print(f"   Map Kit: {data.get('services', {}).get('map_kit', 'Unknown')}")
            backend_accessible = True
        else:
            print(f"❌ Backend API: HTTP {response.status_code}")
            backend_accessible = False
    except Exception as e:
        print(f"❌ Backend API: Not accessible ({e})")
        backend_accessible = False
    
    return frontend_accessible and backend_accessible

def test_api_endpoints_used_by_frontend():
    """Test all API endpoints that the frontend uses"""
    print("\n📡 Testing Frontend API Endpoints")
    print("=" * 50)
    
    backend_url = "http://localhost:8004"
    endpoints_to_test = [
        ("/", "Root endpoint (used by App.js)"),
        ("/api/v1/map/config", "Map configuration (used by HuaweiMapComponent)"),
        ("/api/v1/map/markers", "Crime markers (used by HuaweiMapComponent)"),
        ("/api/v1/map/safety-heatmap", "Safety heatmap (used by HuaweiMapComponent)"),
        ("/api/v1/map/hazard-zones", "Hazard zones (used by HuaweiMapComponent)"),
        ("/api/v1/optimize-route", "Route optimization (used by NavigationScreen)")
    ]
    
    results = []
    
    for endpoint, description in endpoints_to_test:
        try:
            if endpoint == "/api/v1/optimize-route":
                # POST endpoint - test with sample data
                test_data = {
                    "start_point": {"lat": -26.2041, "lng": 28.0473},
                    "end_point": {"lat": -26.1941, "lng": 28.0573},
                    "departure_time": datetime.now().isoformat(),
                    "safety_preferences": {"avoid_high_crime": True}
                }
                response = requests.post(f"{backend_url}{endpoint}", json=test_data, timeout=15)
            else:
                # GET endpoint
                response = requests.get(f"{backend_url}{endpoint}", timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if endpoint == "/":
                    print(f"✅ {description}")
                    print(f"   Services: {data.get('services', {})}")
                elif 'success' in data and data['success']:
                    print(f"✅ {description}")
                    if 'total_markers' in data:
                        print(f"   Data: {data['total_markers']} markers")
                    elif 'total_points' in data:
                        print(f"   Data: {data['total_points']} heatmap points")
                    elif 'route_data' in data:
                        print(f"   Route: {data['route_data']['route_id']}")
                else:
                    print(f"✅ {description}")
                results.append(True)
            else:
                print(f"❌ {description}: HTTP {response.status_code}")
                results.append(False)
                
        except Exception as e:
            print(f"❌ {description}: {e}")
            results.append(False)
    
    return all(results)

def test_map_kit_integration():
    """Test Huawei Map Kit specific integration"""
    print("\n🗺️  Testing Huawei Map Kit Integration")
    print("=" * 50)
    
    backend_url = "http://localhost:8004"
    
    try:
        # Test map configuration
        response = requests.get(f"{backend_url}/api/v1/map/config", timeout=10)
        if response.status_code == 200:
            config = response.json()
            if config.get('success'):
                map_config = config['map_config']
                print("✅ Map Kit Configuration:")
                print(f"   API Key: {'Configured' if map_config.get('api_key') else 'Missing'}")
                print(f"   Production Mode: {map_config.get('production_mode', False)}")
                print(f"   Region: {map_config.get('region', 'Unknown')}")
                print(f"   JS API URL: {map_config.get('js_api_url', 'Unknown')}")
                
                # Check if API key is properly URL encoded
                api_key = map_config.get('api_key', '')
                if '%2B' in api_key or '%2F' in api_key or '%3D' in api_key:
                    print("✅ API Key: Properly URL encoded")
                    url_encoded = True
                else:
                    print("⚠️  API Key: May not be URL encoded")
                    url_encoded = False
                
                return True and url_encoded
            else:
                print("❌ Map Kit Configuration: Failed to retrieve")
                return False
        else:
            print(f"❌ Map Kit Configuration: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Map Kit Configuration: {e}")
        return False

def test_real_data_integration():
    """Test that frontend is getting real data, not mock data"""
    print("\n📊 Testing Real Data Integration")
    print("=" * 50)
    
    backend_url = "http://localhost:8004"
    
    try:
        # Test crime markers - should have real SAPS data
        response = requests.get(f"{backend_url}/api/v1/map/markers", timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                markers = data.get('markers', [])
                total_markers = data.get('total_markers', 0)
                data_source = data.get('data_source', 'Unknown')
                
                print(f"✅ Crime Markers: {total_markers} markers loaded")
                print(f"   Data Source: {data_source}")
                
                # Check if we have real SAPS data
                if 'SAPS' in data_source and total_markers > 0:
                    print("✅ Real SAPS crime data detected")
                    real_crime_data = True
                else:
                    print("⚠️  Using mock crime data")
                    real_crime_data = False
                
                # Check marker structure for real data indicators
                if markers and len(markers) > 0:
                    sample_marker = markers[0]
                    if 'Hillbrow' in sample_marker.get('title', '') or 'Carjacking' in sample_marker.get('title', ''):
                        print("✅ Real South African crime hotspots detected")
                        real_locations = True
                    else:
                        print("⚠️  Generic marker data")
                        real_locations = False
                else:
                    real_locations = False
                
                return real_crime_data and real_locations
            else:
                print("❌ Crime Markers: Failed to retrieve")
                return False
        else:
            print(f"❌ Crime Markers: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Crime Markers: {e}")
        return False

def test_frontend_components():
    """Test that frontend components are production-ready"""
    print("\n⚛️  Testing Frontend Components")
    print("=" * 50)
    
    # Check if React app is using the correct API endpoints
    frontend_files_to_check = [
        ("frontend/src/services/apiService.js", "API Service"),
        ("frontend/src/components/HuaweiMapComponent.js", "Huawei Map Component"),
        ("frontend/src/components/Dashboard.js", "Dashboard Component"),
        ("frontend/src/components/NavigationScreen.js", "Navigation Screen")
    ]
    
    results = []
    
    for file_path, component_name in frontend_files_to_check:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for production-ready indicators
            checks = [
                ("Real API calls", "this.get" in content or "this.post" in content or "fetch('/api/v1/" in content or "apiService.get" in content),
                ("No hardcoded localhost", "localhost:8003" not in content),
                ("Error handling", "catch" in content and "error" in content.lower()),
                ("Backend integration", "apiService" in content or "/api/v1/" in content or "this.baseURL" in content)
            ]
            
            print(f"\n{component_name}:")
            component_ready = True
            
            for check_name, check_result in checks:
                if check_result:
                    print(f"   ✅ {check_name}")
                else:
                    print(f"   ❌ {check_name}")
                    component_ready = False
            
            results.append(component_ready)
            
        except Exception as e:
            print(f"   ❌ Could not analyze {component_name}: {e}")
            results.append(False)
    
    return all(results)

def main():
    """Run complete frontend production readiness test"""
    print("🇿🇦 SafeRouteAI - Frontend Production Readiness Test")
    print("⚛️  React Frontend + Huawei Map Kit Integration")
    print("=" * 70)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Run all tests
    tests = [
        ("Frontend-Backend Integration", test_frontend_backend_integration),
        ("API Endpoints", test_api_endpoints_used_by_frontend),
        ("Huawei Map Kit Integration", test_map_kit_integration),
        ("Real Data Integration", test_real_data_integration),
        ("Frontend Components", test_frontend_components)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}: Test failed with error: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 FRONTEND PRODUCTION READINESS SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 FRONTEND IS PRODUCTION READY!")
        print("✅ All components properly integrated with real backend")
        print("✅ Huawei Map Kit integration working")
        print("✅ Real SAPS crime data being used")
        print("✅ No mock dependencies remaining")
        print()
        print("🚀 Ready for production deployment!")
        return True
    else:
        print(f"\n❌ {total - passed} issues found")
        print("Frontend needs additional work before production deployment")
        print()
        print("Common issues to check:")
        print("- Ensure React server is running on http://localhost:3000")
        print("- Ensure backend API is running on http://localhost:8004")
        print("- Check that all API endpoints are accessible")
        print("- Verify Huawei Map Kit API key is configured")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)