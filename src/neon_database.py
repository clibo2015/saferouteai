"""
Neon Database Integration for SafeRouteAI
Replaces GaussDB with cost-effective Neon PostgreSQL
"""
import os
import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import asyncpg
import json
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

@dataclass
class User:
    """User model for SafeRouteAI"""
    id: str
    email: str
    name: str
    created_at: datetime
    is_active: bool = True
    last_login: Optional[datetime] = None
    preferences: Optional[Dict[str, Any]] = None

@dataclass
class Journey:
    """Journey model for route history"""
    id: str
    user_id: str
    start_lat: float
    start_lng: float
    end_lat: float
    end_lng: float
    route_data: Dict[str, Any]
    safety_score: float
    distance_km: float
    duration_minutes: int
    created_at: datetime
    completed_at: Optional[datetime] = None

@dataclass
class HazardReport:
    """User-reported hazard model"""
    id: str
    user_id: str
    lat: float
    lng: float
    hazard_type: str
    description: str
    severity: float
    created_at: datetime
    verified: bool = False
    expires_at: Optional[datetime] = None

class NeonDatabase:
    """
    Neon PostgreSQL database manager for SafeRouteAI
    Handles user data, journey history, and hazard reports
    """
    
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL")
        self.pool = None
        self.connected = False

        if not self.database_url:
            # Do not raise at import time: the API still boots (maps/routing work)
            # and the auth endpoints report 503 until DATABASE_URL is configured.
            logger.warning("DATABASE_URL not set — Neon database is disabled")
    
    async def connect(self):
        """Initialize connection pool to Neon database"""
        if not self.database_url:
            raise RuntimeError("DATABASE_URL is required for Neon connection")
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=1,
                max_size=10,
                command_timeout=60
            )
            self.connected = True
            logger.info("✅ Connected to Neon PostgreSQL database")
            
            # Initialize database schema
            await self._initialize_schema()
            
        except Exception as e:
            logger.error(f"Failed to connect to Neon database: {e}")
            self.connected = False
            raise
    
    async def disconnect(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            self.connected = False
            logger.info("Disconnected from Neon database")
    
    @asynccontextmanager
    async def get_connection(self):
        """Get database connection from pool"""
        if not self.connected:
            await self.connect()
        
        async with self.pool.acquire() as connection:
            yield connection
    
    async def _initialize_schema(self):
        """Create database tables if they don't exist"""
        schema_sql = """
        -- Users table
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            email VARCHAR(255) UNIQUE NOT NULL,
            name VARCHAR(255) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            last_login TIMESTAMP WITH TIME ZONE,
            preferences JSONB DEFAULT '{}',
            is_active BOOLEAN DEFAULT TRUE
        );
        
        -- Journeys table
        CREATE TABLE IF NOT EXISTS journeys (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            start_lat DECIMAL(10, 8) NOT NULL,
            start_lng DECIMAL(11, 8) NOT NULL,
            end_lat DECIMAL(10, 8) NOT NULL,
            end_lng DECIMAL(11, 8) NOT NULL,
            route_data JSONB NOT NULL,
            safety_score DECIMAL(3, 2) NOT NULL,
            distance_km DECIMAL(8, 2) NOT NULL,
            duration_minutes INTEGER NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            completed_at TIMESTAMP WITH TIME ZONE
        );
        
        -- Hazard reports table
        CREATE TABLE IF NOT EXISTS hazard_reports (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            lat DECIMAL(10, 8) NOT NULL,
            lng DECIMAL(11, 8) NOT NULL,
            hazard_type VARCHAR(100) NOT NULL,
            description TEXT,
            severity DECIMAL(3, 2) NOT NULL,
            verified BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            expires_at TIMESTAMP WITH TIME ZONE
        );
        
        -- Crime hotspots table (for real SAPS data)
        CREATE TABLE IF NOT EXISTS crime_hotspots (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            station_name VARCHAR(255) NOT NULL,
            lat DECIMAL(10, 8) NOT NULL,
            lng DECIMAL(11, 8) NOT NULL,
            crime_type VARCHAR(100) NOT NULL,
            incident_count INTEGER NOT NULL,
            quarter VARCHAR(10) NOT NULL,
            year INTEGER NOT NULL,
            severity DECIMAL(3, 2) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            UNIQUE(station_name, crime_type, quarter, year)
        );
        
        -- Safety heatmap data table
        CREATE TABLE IF NOT EXISTS safety_heatmap (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            lat DECIMAL(10, 8) NOT NULL,
            lng DECIMAL(11, 8) NOT NULL,
            safety_score DECIMAL(3, 2) NOT NULL,
            risk_factors JSONB DEFAULT '[]',
            data_sources JSONB DEFAULT '[]',
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            UNIQUE(lat, lng)
        );
        
        -- Create indexes for performance
        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        CREATE INDEX IF NOT EXISTS idx_journeys_user_id ON journeys(user_id);
        CREATE INDEX IF NOT EXISTS idx_journeys_created_at ON journeys(created_at);
        CREATE INDEX IF NOT EXISTS idx_hazard_reports_location ON hazard_reports(lat, lng);
        CREATE INDEX IF NOT EXISTS idx_hazard_reports_created_at ON hazard_reports(created_at);
        CREATE INDEX IF NOT EXISTS idx_crime_hotspots_location ON crime_hotspots(lat, lng);
        CREATE INDEX IF NOT EXISTS idx_safety_heatmap_location ON safety_heatmap(lat, lng);
        """
        
        async with self.get_connection() as conn:
            await conn.execute(schema_sql)
            logger.info("✅ Database schema initialized")
    
    # User Management
    async def create_user(self, email: str, name: str) -> User:
        """Create a new user"""
        async with self.get_connection() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO users (email, name) 
                VALUES ($1, $2) 
                RETURNING id, email, name, created_at, last_login, preferences, is_active
                """,
                email, name
            )
            
            return User(
                id=str(row['id']),
                email=row['email'],
                name=row['name'],
                created_at=row['created_at'],
                last_login=row['last_login'],
                preferences=row['preferences'] or {},
                is_active=row['is_active']
            )
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        async with self.get_connection() as conn:
            row = await conn.fetchrow(
                "SELECT id, email, name, created_at, last_login, preferences, is_active FROM users WHERE email = $1",
                email
            )
            
            if row:
                return User(
                    id=str(row['id']),
                    email=row['email'],
                    name=row['name'],
                    created_at=row['created_at'],
                    last_login=row['last_login'],
                    preferences=row['preferences'] or {},
                    is_active=row['is_active']
                )
            return None
    
    async def update_user_login(self, user_id: str) -> None:
        """Update user's last login timestamp"""
        async with self.get_connection() as conn:
            await conn.execute(
                "UPDATE users SET last_login = NOW() WHERE id = $1",
                user_id
            )
    
    async def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> None:
        """Update user preferences"""
        async with self.get_connection() as conn:
            await conn.execute(
                "UPDATE users SET preferences = $1 WHERE id = $2",
                json.dumps(preferences), user_id
            )
    
    # Journey Management
    async def save_journey(self, journey: Journey) -> str:
        """Save a completed journey"""
        async with self.get_connection() as conn:
            journey_id = await conn.fetchval(
                """
                INSERT INTO journeys (
                    user_id, start_lat, start_lng, end_lat, end_lng,
                    route_data, safety_score, distance_km, duration_minutes,
                    completed_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                RETURNING id
                """,
                journey.user_id, journey.start_lat, journey.start_lng,
                journey.end_lat, journey.end_lng, json.dumps(journey.route_data),
                journey.safety_score, journey.distance_km, journey.duration_minutes,
                journey.completed_at or datetime.now()
            )
            
            return str(journey_id)
    
    async def get_user_journeys(self, user_id: str, limit: int = 10) -> List[Journey]:
        """Get user's recent journeys"""
        async with self.get_connection() as conn:
            rows = await conn.fetch(
                """
                SELECT id, user_id, start_lat, start_lng, end_lat, end_lng,
                       route_data, safety_score, distance_km, duration_minutes,
                       created_at, completed_at
                FROM journeys 
                WHERE user_id = $1 
                ORDER BY created_at DESC 
                LIMIT $2
                """,
                user_id, limit
            )
            
            journeys = []
            for row in rows:
                journeys.append(Journey(
                    id=str(row['id']),
                    user_id=str(row['user_id']),
                    start_lat=float(row['start_lat']),
                    start_lng=float(row['start_lng']),
                    end_lat=float(row['end_lat']),
                    end_lng=float(row['end_lng']),
                    route_data=row['route_data'],
                    safety_score=float(row['safety_score']),
                    distance_km=float(row['distance_km']),
                    duration_minutes=row['duration_minutes'],
                    created_at=row['created_at'],
                    completed_at=row['completed_at']
                ))
            
            return journeys
    
    # Hazard Report Management
    async def create_hazard_report(self, hazard: HazardReport) -> str:
        """Create a new hazard report"""
        async with self.get_connection() as conn:
            hazard_id = await conn.fetchval(
                """
                INSERT INTO hazard_reports (
                    user_id, lat, lng, hazard_type, description, severity, expires_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
                """,
                hazard.user_id, hazard.lat, hazard.lng, hazard.hazard_type,
                hazard.description, hazard.severity, hazard.expires_at
            )
            
            return str(hazard_id)
    
    async def get_active_hazards(self, bounds: Optional[Dict[str, float]] = None) -> List[HazardReport]:
        """Get active hazard reports within bounds"""
        async with self.get_connection() as conn:
            query = """
                SELECT id, user_id, lat, lng, hazard_type, description, severity,
                       verified, created_at, expires_at
                FROM hazard_reports 
                WHERE (expires_at IS NULL OR expires_at > NOW())
            """
            params = []
            
            if bounds:
                query += " AND lat BETWEEN $1 AND $2 AND lng BETWEEN $3 AND $4"
                params = [bounds['south'], bounds['north'], bounds['west'], bounds['east']]
            
            query += " ORDER BY created_at DESC"
            
            rows = await conn.fetch(query, *params)
            
            hazards = []
            for row in rows:
                hazards.append(HazardReport(
                    id=str(row['id']),
                    user_id=str(row['user_id']),
                    lat=float(row['lat']),
                    lng=float(row['lng']),
                    hazard_type=row['hazard_type'],
                    description=row['description'],
                    severity=float(row['severity']),
                    verified=row['verified'],
                    created_at=row['created_at'],
                    expires_at=row['expires_at']
                ))
            
            return hazards
    
    # Crime Data Management
    async def store_crime_hotspots(self, hotspots_data: List[Dict[str, Any]]) -> int:
        """Store crime hotspots data from SAPS"""
        async with self.get_connection() as conn:
            inserted = 0
            
            for hotspot in hotspots_data:
                try:
                    await conn.execute(
                        """
                        INSERT INTO crime_hotspots (
                            station_name, lat, lng, crime_type, incident_count,
                            quarter, year, severity
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                        ON CONFLICT (station_name, crime_type, quarter, year) 
                        DO UPDATE SET 
                            incident_count = EXCLUDED.incident_count,
                            severity = EXCLUDED.severity
                        """,
                        hotspot['station_name'], hotspot['lat'], hotspot['lng'],
                        hotspot['crime_type'], hotspot['incident_count'],
                        hotspot['quarter'], hotspot['year'], hotspot['severity']
                    )
                    inserted += 1
                except Exception as e:
                    logger.warning(f"Failed to insert crime hotspot: {e}")
            
            logger.info(f"Stored {inserted} crime hotspots in Neon database")
            return inserted
    
    async def get_crime_hotspots(self, bounds: Optional[Dict[str, float]] = None) -> List[Dict[str, Any]]:
        """Get crime hotspots within bounds"""
        async with self.get_connection() as conn:
            query = """
                SELECT station_name, lat, lng, crime_type, incident_count,
                       quarter, year, severity, created_at
                FROM crime_hotspots
            """
            params = []
            
            if bounds:
                query += " WHERE lat BETWEEN $1 AND $2 AND lng BETWEEN $3 AND $4"
                params = [bounds['south'], bounds['north'], bounds['west'], bounds['east']]
            
            query += " ORDER BY severity DESC, incident_count DESC"
            
            rows = await conn.fetch(query, *params)
            
            hotspots = []
            for row in rows:
                hotspots.append({
                    'station_name': row['station_name'],
                    'lat': float(row['lat']),
                    'lng': float(row['lng']),
                    'crime_type': row['crime_type'],
                    'incident_count': row['incident_count'],
                    'quarter': row['quarter'],
                    'year': row['year'],
                    'severity': float(row['severity']),
                    'created_at': row['created_at']
                })
            
            return hotspots
    
    # Safety Heatmap Management
    async def update_safety_heatmap(self, heatmap_data: List[Dict[str, Any]]) -> int:
        """Update safety heatmap data"""
        async with self.get_connection() as conn:
            updated = 0
            
            for point in heatmap_data:
                try:
                    await conn.execute(
                        """
                        INSERT INTO safety_heatmap (lat, lng, safety_score, risk_factors, data_sources)
                        VALUES ($1, $2, $3, $4, $5)
                        ON CONFLICT (lat, lng) 
                        DO UPDATE SET 
                            safety_score = EXCLUDED.safety_score,
                            risk_factors = EXCLUDED.risk_factors,
                            data_sources = EXCLUDED.data_sources,
                            updated_at = NOW()
                        """,
                        point['lat'], point['lng'], point['safety_score'],
                        json.dumps(point['risk_factors']), json.dumps(point['data_sources'])
                    )
                    updated += 1
                except Exception as e:
                    logger.warning(f"Failed to update safety heatmap point: {e}")
            
            logger.info(f"Updated {updated} safety heatmap points in Neon database")
            return updated
    
    async def get_safety_heatmap(self, bounds: Optional[Dict[str, float]] = None) -> List[Dict[str, Any]]:
        """Get safety heatmap data within bounds"""
        async with self.get_connection() as conn:
            query = """
                SELECT lat, lng, safety_score, risk_factors, data_sources, updated_at
                FROM safety_heatmap
            """
            params = []
            
            if bounds:
                query += " WHERE lat BETWEEN $1 AND $2 AND lng BETWEEN $3 AND $4"
                params = [bounds['south'], bounds['north'], bounds['west'], bounds['east']]
            
            rows = await conn.fetch(query, *params)
            
            heatmap = []
            for row in rows:
                heatmap.append({
                    'lat': float(row['lat']),
                    'lng': float(row['lng']),
                    'safety_score': float(row['safety_score']),
                    'risk_factors': row['risk_factors'],
                    'data_sources': row['data_sources'],
                    'updated_at': row['updated_at']
                })
            
            return heatmap
    
    # Database Statistics
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        async with self.get_connection() as conn:
            stats = {}
            
            # Count records in each table
            tables = ['users', 'journeys', 'hazard_reports', 'crime_hotspots', 'safety_heatmap']
            
            for table in tables:
                count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                stats[f"{table}_count"] = count
            
            # Get recent activity
            recent_journeys = await conn.fetchval(
                "SELECT COUNT(*) FROM journeys WHERE created_at > NOW() - INTERVAL '24 hours'"
            )
            stats['recent_journeys_24h'] = recent_journeys
            
            recent_hazards = await conn.fetchval(
                "SELECT COUNT(*) FROM hazard_reports WHERE created_at > NOW() - INTERVAL '24 hours'"
            )
            stats['recent_hazards_24h'] = recent_hazards
            
            return stats

# Global database instance
neon_db = NeonDatabase()