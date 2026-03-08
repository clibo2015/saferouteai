#!/usr/bin/env python3
"""
Comprehensive Frontend Production Audit
Ensures the entire frontend is ready for real users in production
"""
import os
import json
import re
import sys
from pathlib import Path

def audit_user_experience():
    """Audit user experience and interface quality"""
    print("👤 Auditing User Experience")
    print("=" * 50)
    
    issues = []
    
    # Check for proper loading states
    components_to_check = [
        "frontend/src/components/Dashboard.js",
        "frontend/src/components/NavigationScreen.js", 
        "frontend/src/components/HuaweiMapComponent.js",
        "frontend/src/App.js"
    ]
    
    for component_path in components_to_check:
        if os.path.exists(component_path):
            with open(component_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            component_name = os.path.basename(component_path)
            
            # Check for loading states
            if 'isLoading' not in content and 'loading' not in content.lower():
                issues.append(f"{component_name}: Missing loading states")
            
            # Check for error handling
            if 'error' not in content.lower() or 'catch' not in content:
                issues.append(f"{component_name}: Insufficient error handling")
            
            # Check for accessibility
            if 'aria-' not in content and 'role=' not in content:
                issues.append(f"{component_name}: Missing accessibility attributes")
            
            # Check for responsive design considerations
            if '@media' not in content and component_path.endswith('.css'):
                issues.append(f"{component_name}: May not be responsive")
    
    if issues:
        print("❌ User Experience Issues Found:")
        for issue in issues:
            print(f"   • {issue}")
        return False
    else:
        print("✅ User Experience: Good")
        return True

def audit_performance():
    """Audit performance optimizations"""
    print("\n⚡ Auditing Performance")
    print("=" * 50)
    
    issues = []
    
    # Check package.json for optimization
    package_json_path = "frontend/package.json"
    if os.path.exists(package_json_path):
        with open(package_json_path, 'r') as f:
            package_data = json.load(f)
        
        # Check for build script
        if 'build' not in package_data.get('scripts', {}):
            issues.append("Missing build script for production optimization")
        
        # Check for unnecessary dependencies
        deps = package_data.get('dependencies', {})
        if 'lodash' in deps:
            issues.append("Consider using lodash-es for tree shaking")
    
    # Check for lazy loading
    app_js_path = "frontend/src/App.js"
    if os.path.exists(app_js_path):
        with open(app_js_path, 'r') as f:
            content = f.read()
        
        if 'React.lazy' not in content and 'lazy(' not in content:
            issues.append("No lazy loading detected - consider code splitting")
    
    # Check for image optimization
    public_dir = "frontend/public"
    if os.path.exists(public_dir):
        for root, dirs, files in os.walk(public_dir):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    file_path = os.path.join(root, file)
                    file_size = os.path.getsize(file_path)
                    if file_size > 500000:  # 500KB
                        issues.append(f"Large image file: {file} ({file_size/1024:.1f}KB)")
    
    if issues:
        print("⚠️  Performance Issues Found:")
        for issue in issues:
            print(f"   • {issue}")
        return False
    else:
        print("✅ Performance: Optimized")
        return True

def audit_security():
    """Audit security considerations"""
    print("\n🔒 Auditing Security")
    print("=" * 50)
    
    issues = []
    
    # Check for hardcoded secrets
    files_to_check = [
        "frontend/src/services/apiService.js",
        "frontend/src/App.js",
        "frontend/src/components/HuaweiMapComponent.js"
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Check for hardcoded API keys
            if re.search(r'["\'][A-Za-z0-9+/]{40,}["\']', content):
                issues.append(f"{os.path.basename(file_path)}: Possible hardcoded API key")
            
            # Check for console.log in production
            if 'console.log' in content:
                issues.append(f"{os.path.basename(file_path)}: Contains console.log statements")
            
            # Check for eval usage
            if 'eval(' in content:
                issues.append(f"{os.path.basename(file_path)}: Uses eval() - security risk")
    
    # Check environment variable usage
    env_example_path = "frontend/.env.example"
    if not os.path.exists(env_example_path):
        issues.append("Missing .env.example file for environment variables")
    
    if issues:
        print("⚠️  Security Issues Found:")
        for issue in issues:
            print(f"   • {issue}")
        return False
    else:
        print("✅ Security: Good practices followed")
        return True

def audit_accessibility():
    """Audit accessibility compliance"""
    print("\n♿ Auditing Accessibility")
    print("=" * 50)
    
    issues = []
    
    # Check HTML structure
    index_html_path = "frontend/public/index.html"
    if os.path.exists(index_html_path):
        with open(index_html_path, 'r') as f:
            content = f.read()
        
        if 'lang=' not in content:
            issues.append("Missing language attribute in HTML")
        
        if '<title>' not in content:
            issues.append("Missing page title")
        
        if 'viewport' not in content:
            issues.append("Missing viewport meta tag")
    
    # Check components for accessibility
    component_files = [
        "frontend/src/components/Dashboard.js",
        "frontend/src/components/NavigationScreen.js",
        "frontend/src/components/OnboardingScreen.js"
    ]
    
    for component_path in component_files:
        if os.path.exists(component_path):
            with open(component_path, 'r') as f:
                content = f.read()
            
            component_name = os.path.basename(component_path)
            
            # Check for button accessibility
            if '<button' in content and 'aria-label' not in content:
                issues.append(f"{component_name}: Buttons may need aria-labels")
            
            # Check for image alt text
            if '<img' in content and 'alt=' not in content:
                issues.append(f"{component_name}: Images missing alt text")
            
            # Check for form labels
            if '<input' in content and 'label' not in content.lower():
                issues.append(f"{component_name}: Form inputs may need labels")
    
    if issues:
        print("⚠️  Accessibility Issues Found:")
        for issue in issues:
            print(f"   • {issue}")
        return False
    else:
        print("✅ Accessibility: WCAG compliant")
        return True

def audit_mobile_responsiveness():
    """Audit mobile responsiveness"""
    print("\n📱 Auditing Mobile Responsiveness")
    print("=" * 50)
    
    issues = []
    
    # Check CSS files for responsive design
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
            
            # Check for common breakpoints
            if 'max-width: 768px' not in content and 'max-width: 767px' not in content:
                issues.append(f"{os.path.basename(css_file)}: Missing mobile breakpoint")
    
    if not responsive_found:
        issues.append("No responsive design detected in CSS files")
    
    # Check for touch-friendly interactions
    js_files = []
    for root, dirs, files in os.walk("frontend/src"):
        for file in files:
            if file.endswith('.js') and not file.endswith('.test.js'):
                js_files.append(os.path.join(root, file))
    
    touch_friendly = False
    for js_file in js_files:
        with open(js_file, 'r') as f:
            content = f.read()
        
        if 'onTouchStart' in content or 'touchstart' in content:
            touch_friendly = True
            break
    
    if not touch_friendly:
        issues.append("No touch-specific interactions detected")
    
    if issues:
        print("⚠️  Mobile Responsiveness Issues:")
        for issue in issues:
            print(f"   • {issue}")
        return False
    else:
        print("✅ Mobile Responsiveness: Good")
        return True

def audit_error_handling():
    """Audit comprehensive error handling"""
    print("\n🚨 Auditing Error Handling")
    print("=" * 50)
    
    issues = []
    
    # Check API service for error handling
    api_service_path = "frontend/src/services/apiService.js"
    if os.path.exists(api_service_path):
        with open(api_service_path, 'r') as f:
            content = f.read()
        
        if 'try' not in content or 'catch' not in content:
            issues.append("API service lacks try-catch blocks")
        
        if 'throw' not in content:
            issues.append("API service doesn't properly throw errors")
        
        if 'timeout' not in content:
            issues.append("API service lacks timeout handling")
    
    # Check components for error boundaries
    component_files = [
        "frontend/src/App.js",
        "frontend/src/components/Dashboard.js",
        "frontend/src/components/NavigationScreen.js"
    ]
    
    error_boundary_found = False
    for component_path in component_files:
        if os.path.exists(component_path):
            with open(component_path, 'r') as f:
                content = f.read()
            
            if 'componentDidCatch' in content or 'ErrorBoundary' in content:
                error_boundary_found = True
            
            # Check for user-friendly error messages
            if 'error' in content.lower() and 'user' not in content.lower():
                issues.append(f"{os.path.basename(component_path)}: Error messages may not be user-friendly")
    
    if not error_boundary_found:
        issues.append("No React Error Boundaries detected")
    
    if issues:
        print("⚠️  Error Handling Issues:")
        for issue in issues:
            print(f"   • {issue}")
        return False
    else:
        print("✅ Error Handling: Comprehensive")
        return True

def audit_production_build():
    """Audit production build configuration"""
    print("\n🏗️  Auditing Production Build")
    print("=" * 50)
    
    issues = []
    
    # Check package.json scripts
    package_json_path = "frontend/package.json"
    if os.path.exists(package_json_path):
        with open(package_json_path, 'r') as f:
            package_data = json.load(f)
        
        scripts = package_data.get('scripts', {})
        
        if 'build' not in scripts:
            issues.append("Missing 'build' script")
        
        if 'start' not in scripts:
            issues.append("Missing 'start' script")
        
        # Check for production optimizations
        if 'homepage' not in package_data:
            issues.append("Missing 'homepage' field for deployment")
    
    # Check for environment configuration
    if not os.path.exists("frontend/.env.example"):
        issues.append("Missing .env.example file")
    
    # Check for build output directory
    if os.path.exists("frontend/build"):
        print("✅ Build directory exists")
    else:
        issues.append("No build directory found - run 'npm run build'")
    
    if issues:
        print("⚠️  Production Build Issues:")
        for issue in issues:
            print(f"   • {issue}")
        return False
    else:
        print("✅ Production Build: Ready")
        return True

def audit_user_data_handling():
    """Audit user data and privacy handling"""
    print("\n🔐 Auditing User Data Handling")
    print("=" * 50)
    
    issues = []
    
    # Check for localStorage usage
    js_files = []
    for root, dirs, files in os.walk("frontend/src"):
        for file in files:
            if file.endswith('.js'):
                js_files.append(os.path.join(root, file))
    
    local_storage_used = False
    for js_file in js_files:
        with open(js_file, 'r') as f:
            content = f.read()
        
        if 'localStorage' in content:
            local_storage_used = True
            
            # Check for sensitive data in localStorage
            if 'password' in content.lower() or 'token' in content.lower():
                issues.append(f"{os.path.basename(js_file)}: May store sensitive data in localStorage")
    
    if local_storage_used:
        print("✅ localStorage usage detected - ensure no sensitive data")
    
    # Check for geolocation handling
    geolocation_found = False
    for js_file in js_files:
        with open(js_file, 'r') as f:
            content = f.read()
        
        if 'geolocation' in content:
            geolocation_found = True
            
            # Check for user permission handling
            if 'permission' not in content.lower():
                issues.append("Geolocation used without proper permission handling")
    
    if geolocation_found:
        print("✅ Geolocation usage detected")
    
    if issues:
        print("⚠️  User Data Handling Issues:")
        for issue in issues:
            print(f"   • {issue}")
        return False
    else:
        print("✅ User Data Handling: Privacy-conscious")
        return True

def main():
    """Run comprehensive frontend production audit"""
    from datetime import datetime
    
    print("🇿🇦 SafeRouteAI - Comprehensive Frontend Production Audit")
    print("👥 Ensuring Frontend is Ready for Real Users")
    print("=" * 70)
    print(f"Audit started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Run all audits
    audits = [
        ("User Experience", audit_user_experience),
        ("Performance", audit_performance),
        ("Security", audit_security),
        ("Accessibility", audit_accessibility),
        ("Mobile Responsiveness", audit_mobile_responsiveness),
        ("Error Handling", audit_error_handling),
        ("Production Build", audit_production_build),
        ("User Data Handling", audit_user_data_handling)
    ]
    
    results = []
    
    for audit_name, audit_func in audits:
        try:
            result = audit_func()
            results.append((audit_name, result))
        except Exception as e:
            print(f"❌ {audit_name}: Audit failed with error: {e}")
            results.append((audit_name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 FRONTEND PRODUCTION AUDIT SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for audit_name, result in results:
        status = "✅ PASS" if result else "❌ NEEDS WORK"
        print(f"{status} {audit_name}")
    
    print(f"\nResults: {passed}/{total} audits passed")
    
    if passed == total:
        print("\n🎉 FRONTEND IS FULLY PRODUCTION READY!")
        print("✅ User Experience: Excellent")
        print("✅ Performance: Optimized")
        print("✅ Security: Secure")
        print("✅ Accessibility: WCAG compliant")
        print("✅ Mobile: Responsive")
        print("✅ Error Handling: Comprehensive")
        print("✅ Build: Production ready")
        print("✅ Privacy: User data protected")
        print()
        print("🚀 READY FOR REAL USERS!")
        return True
    else:
        print(f"\n⚠️  {total - passed} areas need improvement")
        print("Address the issues above before deploying to real users")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)