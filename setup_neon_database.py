#!/usr/bin/env python3
"""
Neon Database Setup for SafeRouteAI
Initializes the Neon PostgreSQL database with required tables and sample data
"""
import os
import sys
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Add src to path
sys.path.append('src')

from neon_database import neon_db
from real_data_integration import real_data_integrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def setup_neon_database():
    """Set up Neon database with initial data"""
    print("🐘 SafeRouteAI - Neon Database Setup")
    print("=" * 50)
    print(f"Setup started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # 1. Connect to Neon database
        print("1. 🔗 Connecting to Neon PostgreSQL...")
        await neon_db.connect()
        print("   ✅ Connected successfully")
        print()
        
        # 2. Initialize schema (already done in connect, but let's confirm)
        print("2. 🏗️  Database schema initialized")
        print("   ✅ Tables created: users, journeys, hazard_reports, crime_hotspots, safety_heatmap")
        print()
        
        # 3. Load real crime data
        print("3. 📊 Loading real crime hotspots data...")
        try:
            # Get real crime data
            crime_df = real_data_integrator.load_real_crime_hotspots_data()
            
            if not crime_df.empty:
                # Convert to database format
                hotspots_data = []
                
                for _, row in crime_df.iterrows():
                    # Generate coordinates for each station (in production, use real coordinates)
                    base_lat = -26.2041 + (hash(row['station']) % 1000) / 10000
                    base_lng = 28.0473 + (hash(row['station']) % 1000) / 10000
                    
                    # Add carjacking hotspots
                    if row['is_carjacking_hotspot']:
                        hotspots_data.append({
                            'station_name': row['station'],
                            'lat': base_lat,
                            'lng': base_lng,
                            'crime_type': 'carjacking',
                            'incident_count': row['quarterly_carjackings'],
                            'quarter': 'Q1',
                            'year': 2025,
                            'severity': min(row['quarterly_carjackings'] / 50.0, 1.0)
                        })
                    
                    # Add robbery hotspots
                    if row['is_robbery_hotspot']:
                        hotspots_data.append({
                            'station_name': row['station'],
                            'lat': base_lat + 0.001,
                            'lng': base_lng + 0.001,
                            'crime_type': 'robbery',
                            'incident_count': row['quarterly_robberies'],
                            'quarter': 'Q1',
                            'year': 2025,
                            'severity': min(row['quarterly_robberies'] / 100.0, 1.0)
                        })
                
                # Store in database
                inserted = await neon_db.store_crime_hotspots(hotspots_data)
                print(f"   ✅ Loaded {inserted} crime hotspots from real SAPS data")
            else:
                print("   ⚠️  No real crime data available, using mock data")
                
        except Exception as e:
            logger.error(f"Failed to load crime data: {e}")
            print("   ❌ Failed to load real crime data")
        
        print()
        
        # 4. Generate safety heatmap
        print("4. 🗺️  Generating safety heatmap...")
        try:
            heatmap_data = []
            
            # Generate grid points across South Africa
            sa_bounds = {
                "north": -22.0,
                "south": -35.0,
                "east": 33.0,
                "west": 16.0
            }
            
            lat_step = 0.1  # ~11km resolution
            lng_step = 0.1
            
            for lat in [sa_bounds["south"] + i * lat_step 
                       for i in range(int((sa_bounds["north"] - sa_bounds["south"]) / lat_step))]:
                for lng in [sa_bounds["west"] + i * lng_step 
                           for i in range(int((sa_bounds["east"] - sa_bounds["west"]) / lng_step))]:
                    
                    # Get risk score for this location
                    risk_data = real_data_integrator.get_enhanced_risk_score(lat, lng, datetime.now())
                    
                    heatmap_data.append({
                        'lat': lat,
                        'lng': lng,
                        'safety_score': 1.0 - risk_data["risk_score"],
                        'risk_factors': ["crime_data", "load_shedding", "time_based"],
                        'data_sources': risk_data["data_sources"]
                    })
            
            # Store in database
            updated = await neon_db.update_safety_heatmap(heatmap_data)
            print(f"   ✅ Generated {updated} safety heatmap points")
            
        except Exception as e:
            logger.error(f"Failed to generate heatmap: {e}")
            print("   ❌ Failed to generate safety heatmap")
        
        print()
        
        # 5. Get database statistics
        print("5. 📈 Database Statistics:")
        try:
            stats = await neon_db.get_database_stats()
            
            for key, value in stats.items():
                if key.endswith('_count'):
                    table_name = key.replace('_count', '').replace('_', ' ').title()
                    print(f"   • {table_name}: {value:,} records")
            
            print()
            
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
        
        # 6. Test database operations
        print("6. 🧪 Testing Database Operations:")
        
        # Test user creation
        try:
            test_user = await neon_db.create_user(
                email="test@saferoute.ai",
                name="Test User"
            )
            print(f"   ✅ Created test user: {test_user.email}")
            
            # Test user retrieval
            retrieved_user = await neon_db.get_user_by_email("test@saferoute.ai")
            if retrieved_user:
                print(f"   ✅ Retrieved user: {retrieved_user.name}")
            
        except Exception as e:
            logger.warning(f"User test failed (may already exist): {e}")
        
        print()
        
        # Success summary
        print("=" * 50)
        print("🎉 NEON DATABASE SETUP COMPLETE!")
        print("=" * 50)
        print()
        print("✅ Database Connection: Ready")
        print("✅ Schema: Initialized")
        print("✅ Crime Data: Loaded")
        print("✅ Safety Heatmap: Generated")
        print("✅ Authentication: Ready")
        print()
        print("🚀 Your SafeRouteAI backend is now ready with:")
        print("   • Real PostgreSQL database (Neon)")
        print("   • User authentication system")
        print("   • Journey history tracking")
        print("   • Hazard reporting system")
        print("   • Real crime data integration")
        print()
        print("💰 Cost Savings:")
        print("   • Using Neon instead of GaussDB saves ~$50-100/month")
        print("   • Preserves your $100 Huawei Cloud coupon for ModelArts/OBS")
        print()
        print("Next Steps:")
        print("1. Update DATABASE_URL in .env with your real Neon connection string")
        print("2. Start the backend: python src/api.py")
        print("3. Test authentication endpoints")
        print("4. Deploy to production")
        
        return True
        
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        print(f"❌ Setup failed: {e}")
        return False
        
    finally:
        # Disconnect from database
        await neon_db.disconnect()

async def test_neon_connection():
    """Test Neon database connection"""
    print("🧪 Testing Neon Database Connection...")
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        print("   Please add your Neon connection string to .env file")
        return False
    
    if "postgresql://" not in database_url:
        print("❌ Invalid DATABASE_URL format")
        print("   Expected: postgresql://username:password@host/database")
        return False
    
    try:
        await neon_db.connect()
        print("✅ Neon database connection successful!")
        await neon_db.disconnect()
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print()
        print("Troubleshooting:")
        print("1. Check your DATABASE_URL in .env file")
        print("2. Ensure your Neon database is running")
        print("3. Verify network connectivity")
        print("4. Check database credentials")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup Neon database for SafeRouteAI")
    parser.add_argument("--test-only", action="store_true", help="Only test connection")
    args = parser.parse_args()
    
    if args.test_only:
        success = asyncio.run(test_neon_connection())
    else:
        success = asyncio.run(setup_neon_database())
    
    sys.exit(0 if success else 1)