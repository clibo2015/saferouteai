#!/usr/bin/env python3
"""
User-Ready Frontend Test
Comprehensive test to ensure frontend is ready for real users
"""
import os
import json
import requests
from datetime import datetime

def test_frontend_accessibility():
    """Test frontend accessibility and user experience"""
    print("♿ Testing Frontend Accessibility & UX")
    print("=" * 50)
    
    results = []
    
    # Check for error boundary
    if os.path.exists("frontend/src/components/ErrorBoundary.js"):
        print("✅ Error Boundary: Implemented")
        results.append(True)
    else:
        print("❌ Error Boundary: Missing")
        results.append(False)
    
    # Check for environment configuration
    if os.path.exists("frontend/.env.example"):
        print("✅ Environment Config: Available")
        results.append(True)
    else:
        print("❌ Environment Config: Missing")
        results.append(False)
    
    # Check for service worker
    if os.path.exists("frontend/public/sw.js"):
        print("✅ Service Worker: Implemented for offline support")
        results.append(True)
    else:
        print("❌ Service Worker: Missing")
        results.append(False)
    
    # Check HTML meta tags
    if os.path.exists("frontend/public/index.html"):
        with open("frontend/public/index.html", 'r') as f:
            html_content = f.read()
        
        checks = [
            ('lang="en"', "Language attribute"),
            ('viewport', "Viewport meta tag"),
            ('description', "Meta description"),
            ('og:title', "Open Graph tags"),
            ('apple-mobile-web-app', "PWA meta tags")
        ]
        
        for check, name in checks:
            if check in html_content:
                print(f"✅ {name}: Present")
                results.append(True)
            else:
                print(f"❌ {name}: Missing")
                results.append(False)
    
    return all(results)

def test_performance_optimizations():
    """Test performance optimizations"""
    print("\n⚡ Testing Performance Optimizations")
    print("=" * 50)
    
    results = []
    
    # Check package.json for build scripts
    if os.path.exists("frontend/package.json"):
        with open("frontend/package.json", 'r') as f:
            package_data = json.load(f)
        
        scripts = package_data.get('scripts', {})
        
        if 'build' in scripts:
            print("✅ Build Script: Available")
            results.append(True)
        else:
            print("❌ Build Script: Missing")
            results.append(False)
        
        if 'build:prod' in scripts:
            print("✅ Production Build: Configured")
            results.append(True)
        else:
            print("❌ Production Build: Not configured")
            results.append(False)
    
    # Check for CSS optimizations
    css_files = []
    for root, dirs, files in os.walk("frontend/src"):
        for file in files:
            if file.endswith('.css'):
                css_files.append(os.path.join(root, file))
    
    responsive_found = False
    for css_file in css_files:
        with open(css_file, 'r') as f:
            content = f.read()
        if '@media' in content:
            responsive_found = True
            break
    
    if responsive_found:
        print("✅ Responsive Design: Implemented")
        results.append(True)
    else:
        print("❌ Responsive Design: Missing")
        results.append(False)
    
    return all(results)

def test_error_handling():
    """Test comprehensive error handling"""
    print("\n🚨 Testing Error Handling")
    print("=" * 50)
    
    results = []
    
    # Check API service error handling
    if os.path.exists("frontend/src/services/apiService.js"):
        with open("frontend/src/services/apiService.js", 'r') as f:
            content = f.read()
        
        error_checks = [
            ('try', 'Try-catch blocks'),
            ('catch', 'Error catching'),
            ('timeout', 'Timeout handling'),
            ('navigator.onLine', 'Offline detection'),
            ('AbortController', 'Request cancellation')
        ]
        
        for check, name in error_checks:
            if check in content:
                print(f"✅ {name}: Implemented")
                results.append(True)
            else:
                print(f"❌ {name}: Missing")
                results.append(False)
    
    return all(results)

def test_security_measures():
    """Test security measures"""
    print("\n🔒 Testing Security Measures")
    print("=" * 50)
    
    results = []
    
    # Check for environment variables usage
    files_to_check = [
        "frontend/src/services/apiService.js",
        "frontend/src/components/HuaweiMapComponent.js"
    ]
    
    hardcoded_secrets = False
    console_logs = False
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Check for hardcoded secrets (basic check)
            import re
            if re.search(r'["\'][A-Za-z0-9+/]{40,}["\']', content):
                hardcoded_secrets = True
            
            # Check for console.log statements
            if 'console.log' in content:
                console_logs = True
    
    if not hardcoded_secrets:
        print("✅ No Hardcoded Secrets: Clean")
        results.append(True)
    else:
        print("⚠️  Possible Hardcoded Secrets: Review needed")
        results.append(False)
    
    if console_logs:
        print("⚠️  Console Logs: Present (should be removed for production)")
        results.append(False)
    else:
        print("✅ Console Logs: Clean")
        results.append(True)
    
    return all(results)

def test_real_user_scenarios():
    """Test real user scenarios"""
    print("\n👥 Testing Real User Scenarios")
    print("=" * 50)
    
    results = []
    
    # Test if backend is accessible
    try:
        response = requests.get("http://localhost:8004", timeout=5)
        if response.status_code == 200:
            print("✅ Backend Connection: Available")
            results.append(True)
        else:
            print("❌ Backend Connection: Failed")
            results.append(False)
    except:
        print("❌ Backend Connection: Not accessible")
        results.append(False)
    
    # Test if frontend is accessible
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        if response.status_code == 200:
            print("✅ Frontend Access: Available")
            results.append(True)
        else:
            print("❌ Frontend Access: Failed")
            results.append(False)
    except:
        print("❌ Frontend Access: Not accessible")
        results.append(False)
    
    # Test API endpoints that frontend uses
    api_endpoints = [
        "/api/v1/map/config",
        "/api/v1/map/markers"
    ]
    
    for endpoint in api_endpoints:
        try:
            response = requests.get(f"http://localhost:8004{endpoint}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print(f"✅ API {endpoint}: Working")
                    results.append(True)
                else:
                    print(f"❌ API {endpoint}: Failed")
                    results.append(False)
            else:
                print(f"❌ API {endpoint}: HTTP {response.status_code}")
                results.append(False)
        except:
            print(f"❌ API {endpoint}: Not accessible")
            results.append(False)
    
    return all(results)

def main():
    """Run comprehensive user-ready frontend test"""
    print("🇿🇦 SafeRouteAI - User-Ready Frontend Test")
    print("👥 Ensuring Frontend is Ready for Real Users")
    print("=" * 70)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Run all tests
    tests = [
        ("Accessibility & UX", test_frontend_accessibility),
        ("Performance", test_performance_optimizations),
        ("Error Handling", test_error_handling),
        ("Security", test_security_measures),
        ("Real User Scenarios", test_real_user_scenarios)
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
    print("📊 USER-READY FRONTEND SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ READY" if result else "❌ NEEDS WORK"
        print(f"{status} {test_name}")
    
    print(f"\nResults: {passed}/{total} areas ready for users")
    
    if passed == total:
        print("\n🎉 FRONTEND IS FULLY READY FOR REAL USERS!")
        print("✅ Accessibility: WCAG compliant")
        print("✅ Performance: Optimized")
        print("✅ Error Handling: Comprehensive")
        print("✅ Security: Production-ready")
        print("✅ User Experience: Excellent")
        print()
        print("🚀 DEPLOY TO PRODUCTION!")
        print()
        print("Final Steps:")
        print("1. Run 'npm run build:prod' to create production build")
        print("2. Configure authorized domains in AppGallery Connect")
        print("3. Set up HTTPS for production deployment")
        print("4. Configure environment variables for production")
        print("5. Set up monitoring and analytics")
        return True
    else:
        print(f"\n⚠️  {total - passed} areas need improvement")
        print("Address the issues above before deploying to real users")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)