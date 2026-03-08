#!/usr/bin/env python3
"""
Simple Frontend Production Audit
"""
import os
import json
from datetime import datetime

print("🇿🇦 SafeRouteAI - Frontend Production Audit")
print("=" * 50)
print(f"Started: {datetime.now().strftime('%H:%M:%S')}")
print()

# Check if frontend directory exists
if not os.path.exists("frontend"):
    print("❌ Frontend directory not found")
    exit(1)

print("📁 Frontend directory: ✅ Found")

# Check package.json
if os.path.exists("frontend/package.json"):
    with open("frontend/package.json", 'r') as f:
        package_data = json.load(f)
    print(f"📦 Package: {package_data.get('name', 'Unknown')} v{package_data.get('version', '0.0.0')}")
    print("✅ Package.json: Valid")
else:
    print("❌ Package.json: Missing")

# Check key components
components = [
    "frontend/src/App.js",
    "frontend/src/components/Dashboard.js", 
    "frontend/src/components/NavigationScreen.js",
    "frontend/src/components/HuaweiMapComponent.js",
    "frontend/src/services/apiService.js"
]

print("\n🔍 Checking Components:")
for component in components:
    if os.path.exists(component):
        print(f"✅ {os.path.basename(component)}")
    else:
        print(f"❌ {os.path.basename(component)}")

print("\n✅ Basic audit complete!")