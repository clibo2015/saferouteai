#!/usr/bin/env python3
"""
Test script to check Map Kit imports
"""
import sys
import os

# Add src to path
sys.path.append('src')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("Testing Map Kit imports...")
print(f"Python path: {sys.path}")

try:
    print("1. Testing huawei_map_kit import...")
    from huawei_map_kit import map_kit_service
    print("✅ huawei_map_kit imported successfully")
    
    print("2. Testing edge_ai_simulation import...")
    from edge_ai_simulation import edge_ai_processor
    print("✅ edge_ai_simulation imported successfully")
    
    print("3. Testing config import...")
    from config import settings
    print("✅ config imported successfully")
    
    print("4. Testing real_data_integration import...")
    from real_data_integration import real_data_integrator
    print("✅ real_data_integration imported successfully")
    
    print("\n🎉 ALL IMPORTS SUCCESSFUL - Map Kit should be available!")
    
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print(f"Error type: {type(e)}")
    import traceback
    traceback.print_exc()