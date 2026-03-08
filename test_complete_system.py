#!/usr/bin/env python3
"""
Complete System Test for SafeRouteAI
Tests all components: Database, Authentication, Map Kit, API endpoints
"""
import asyncio
import sys
import os
from datetime import datetime
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.append('src')

def print_header(title):
    """Print a formatted header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")

def print_section(title):
    """Print a section title"""
    print(f"\n{'─'*70}")
    print(f"  {title}")
    print(f"{'─'*70}\n")

def print_test(name, passed, details=""):
    """Print test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {name}")
    if details:
        print(f"       {details}")

async def test_database_connection():
    """Test Neon database connection"""
    print_section("Database Connection Test")
    
    try:
        from neon_database import neon_db
        
        # Connect to database
        await neon_db.connect()
        print_test("Database Connection", True, "Connected to Neon PostgreSQL")
        
        # Get database stats
        stats = await neon_db.get_database_stats()
        print_test("Database Statistics", True, 
                  f"Users: {stats['users_count']}, Journeys: {stats['journeys_count']}, "
                  f"Crime Hotspots: {stats['crime_hotspots_count']}")
        
        return True
        
    except Exception as e:
        print_test("Database Connection", False, str(e))
        return False

async def test_authentication():
    """Test authentication system"""
    print_section("Authentication System Test")
    
    try:
        from neon_auth import auth_service
        from neon_database import neon_db
        
        # Test user registration
        test_email = f"test_{datetime.now().timestamp()}@saferoute.ai"
        test_name = "Test User"
        test_password = "TestPassword123!"
        
        user_data = await auth_service.register_user(test_email, test_name, test_password)
        print_test("User Registration", True, f"Created user: {user_data['email']}")
        
        # Test token creation
        token = auth_service.create_access_token(user_data)
        print_test("JWT Token Creation", True, f"Token: {token[:30]}...")
        
        # Test token verification
        payload = auth_service.verify_token(token)
        print_test("JWT Token Verification", True, f"User ID: {payload['user_id']}")
        
        # Test user login
        login_data = await auth_service.authenticate_with_neon(test_email, test_password)
        print_test("User Login", True, f"Logged in: {login_data['email']}")
        
        return True
        
    except Exception as e:
        print_test("Authentication", False, str(e))
        return False

async def test_api_endpoints():
    """Test API endpoints"""
    print_section("API Endpoints Test")
    
    base_url = "http://localhost:8004"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Test root endpoint
            response = await client.get(f"{base_url}/")
            print_test("Root Endpoint", response.status_code == 200, 
                      f"Status: {response.status_code}")
            
            # Test map config endpoint
            response = await client.get(f"{base_url}/api/v1/map/config")
            print_test("Map Config Endpoint", response.status_code == 200,
                      f"Map Kit Available: {response.json().get('map_kit_available')}")
            
            # Test map markers endpoint
            response = await client.get(f"{base_url}/api/v1/map/markers")
            markers_data = response.json()
            print_test("Map Markers Endpoint", response.status_code == 200,
                      f"Markers: {markers_data.get('total_markers', 0)}")
            
            # Test safety heatmap endpoint
            response = await client.get(f"{base_url}/api/v1/map/safety-heatmap")
            heatmap_data = response.json()
            print_test("Safety Heatmap Endpoint", response.status_code == 200,
                      f"Points: {heatmap_data.get('total_points', 0)}")
            
            return True
            
    except httpx.ConnectError:
        print_test("API Connection", False, "Backend not running. Start with: python src/api.py")
        return False
    except Exception as e:
        print_test("API Endpoints", False, str(e))
        return False

async def test_map_kit_integration():
    """Test Map Kit integration"""
    print_section("Map Kit Integration Test")
    
    try:
        from huawei_map_kit import map_kit_service
        
        # Test map config
        config = map_kit_service.get_map_config()
        print_test("Map Kit Configuration", True,
                  f"Region: {config.get('region')}, API Key configured")
        
        # Test markers
        markers = map_kit_service.get_real_time_markers()
        print_test("Crime Hotspot Markers", len(markers) > 0,
                  f"Markers: {len(markers)}")
        
        # Test hazard zones
        zones = map_kit_service.get_hazard_zones()
        print_test("Hazard Zones", len(zones) > 0,
                  f"Zones: {len(zones)}")
        
        # Test safety heatmap
        heatmap = map_kit_service.get_safety_heatmap_data()
        print_test("Safety Heatmap Data", len(heatmap) > 0,
                  f"Points: {len(heatmap)}")
        
        return True
        
    except Exception as e:
        print_test("Map Kit Integration", False, str(e))
        return False

async def test_environment_variables():
    """Test environment variables"""
    print_section("Environment Variables Test")
    
    required_vars = {
        'HUAWEI_CLOUD_AK': 'Huawei Cloud Access Key',
        'HUAWEI_CLOUD_PROJECT_ID': 'Project ID',
        'HUAWEI_MAP_API_KEY': 'Map Kit API Key',
        'HUAWEI_OAUTH_CLIENT_ID': 'OAuth Client ID',
        'HUAWEI_APP_ID': 'App ID',
        'DATABASE_URL': 'Neon Database URL',
        'JWT_SECRET': 'JWT Secret Key'
    }
    
    all_present = True
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            print_test(description, True, "Configured")
        else:
            print_test(description, False, "NOT SET")
            all_present = False
    
    return all_present

async def test_appgallery_connect():
    """Test AppGallery Connect configuration"""
    print_section("AppGallery Connect Configuration Test")
    
    try:
        oauth_client_id = os.getenv('HUAWEI_OAUTH_CLIENT_ID')
        app_id = os.getenv('HUAWEI_APP_ID')
        
        print_test("OAuth Client ID", bool(oauth_client_id), 
                  f"ID: {oauth_client_id}")
        print_test("App ID", bool(app_id),
                  f"ID: {app_id}")
        
        print("\n⚠️  Manual Verification Required:")
        print("   1. Callback URLs added in AppGallery Connect")
        print("   2. Authorized domains added in AppGallery Connect")
        print("   3. CORS enabled for all domains")
        print("   4. Map Kit service enabled")
        
        return True
        
    except Exception as e:
        print_test("AppGallery Connect", False, str(e))
        return False

async def main():
    """Run all tests"""
    print_header("SafeRouteAI - Complete System Test")
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    # Test environment variables
    results['environment'] = await test_environment_variables()
    
    # Test database connection
    results['database'] = await test_database_connection()
    
    # Test authentication
    if results['database']:
        results['authentication'] = await test_authentication()
    else:
        print_section("Authentication System Test")
        print_test("Authentication", False, "Skipped - Database not connected")
        results['authentication'] = False
    
    # Test Map Kit integration
    results['map_kit'] = await test_map_kit_integration()
    
    # Test AppGallery Connect
    results['appgallery'] = await test_appgallery_connect()
    
    # Test API endpoints (requires backend to be running)
    results['api'] = await test_api_endpoints()
    
    # Print summary
    print_header("Test Summary")
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    print("\nTest Results:")
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {test_name.replace('_', ' ').title()}")
    
    if passed_tests == total_tests:
        print_header("🎉 All Tests Passed!")
        print("✅ Your SafeRouteAI system is fully operational!")
        print("\nNext Steps:")
        print("  1. Start backend: python src/api.py")
        print("  2. Start frontend: cd frontend && npm start")
        print("  3. Open browser: http://localhost:3000")
        print("  4. Test user registration and login")
        print("  5. Test map display and route optimization")
    else:
        print_header("⚠️  Some Tests Failed")
        print("Please review the failed tests above and fix any issues.")
        print("\nCommon Issues:")
        print("  • Backend not running: Start with 'python src/api.py'")
        print("  • Database connection: Check DATABASE_URL in .env")
        print("  • Missing env vars: Check .env file")
        print("  • AppGallery Connect: Verify callback URLs and domains")
    
    # Cleanup
    try:
        from neon_database import neon_db
        await neon_db.disconnect()
    except:
        pass

if __name__ == "__main__":
    asyncio.run(main())
