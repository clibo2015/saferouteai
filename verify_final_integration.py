
import sys
import os
import asyncio
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from huawei_map_kit import map_kit_service
from routing_engine import routing_engine

async def verify():
    print("\n🚀 Final System Verification (Using Production Classes) 🚀")
    
    # 1. Test Geocoding via HuaweiMapKitService
    print("\n📍 Testing Geocoding (Site Kit)...")
    address = "Rosebank Mall, Johannesburg"
    coords = map_kit_service.get_real_gps_coordinates(address)
    
    if coords:
        print(f"   ✅ SUCCESS: '{address}' -> {coords}")
    else:
        print(f"   ❌ FAILED: Could not geocode '{address}'")

    # 2. Test Routing via SafetyOptimizedRouter
    print("\n🚗 Testing Routing (Map Kit)...")
    start = (-26.1467, 28.0439) # Rosebank
    end = (-26.2041, 28.0473)   # JHB CBD
    
    try:
        route = routing_engine.calculate_safe_route(
            start[0], start[1], end[0], end[1]
        )
        print(f"   ✅ SUCCESS: Created Route '{route.route_id}'")
        print(f"   Distance: {route.total_distance_km:.2f} km")
        print(f"   Time:     {route.total_time_minutes:.2f} mins")
        print(f"   Safety:   {route.overall_safety_score:.2f}")
    except Exception as e:
        print(f"   ❌ FAILED: Routing Error: {e}")

if __name__ == "__main__":
    asyncio.run(verify())
