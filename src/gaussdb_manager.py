"""
GaussDB Manager for SafeRouteAI (Optional)
Cost-optimized database management with local fallback
"""

import logging
import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from config import settings

logger = logging.getLogger(__name__)

# Import GaussDB SDK (optional)
try:
    from huaweicloudsdkcore.auth.credentials import BasicCredentials
    from huaweicloudsdkgaussdb.v3 import GaussDBClient
    from huaweicloudsdkgaussdb.v3.region.gaussdb_region import GaussDBRegion
    from huaweicloudsdkgaussdb.v3.model import *
    GAUSSDB_SDK_AVAILABLE = True
    logger.info("GaussDB SDK loaded successfully")
except ImportError as e:
    GAUSSDB_SDK_AVAILABLE = False
    logger.info(f"GaussDB SDK not available - using local SQLite: {e}")

@dataclass
class DatabaseConfig:
    """Database configuration for cost optimization"""
    use_cloud_db: bool = False  # Default to local for cost savings
    instance_type: str = "gaussdb.mysql.c6.large.2"
    storage_type: str = "ULTRAHIGH"
    storage_size_gb: int = 40  # Minimum size
    backup_retention_days: int = 7  # Minimum for cost
    auto_scaling: bool = True
    multi_az: bool = False  # Single AZ for cost savings

class GaussDBManager:
    """Manages database operations with cost optimization"""
    
    def __init__(self):
        self.region = settings.huawei_cloud_region or "af-south-1"
        self.project_id = settings.huawei_cloud_project_id
        self.client = None
        self.local_db_path = "data/saferoute_local.db"
        self.demo_mode = settings.demo_mode or not GAUSSDB_SDK_AVAILABLE
        
        # For cost optimization, default to local SQLite
        self.use_local_db = True
        
        # Initialize local database
        self._initialize_local_database()
        
        # Only initialize cloud DB if explicitly requested and credentials available
        if not self.demo_mode and settings.huawei_cloud_ak and not self.use_local_db:
            self._initialize_cloud_client()
    
    def _initialize_cloud_client(self):
        """Initialize GaussDB cloud client (optional)"""
        try:
            credentials = BasicCredentials(
                ak=settings.huawei_cloud_ak,
                sk=settings.huawei_cloud_sk,
                project_id=self.project_id
            )
            
            region = GaussDBRegion.value_of(self.region)
            self.client = GaussDBClient.new_builder() \
                .with_credentials(credentials) \
                .with_region(region) \
                .build()
            
            logger.info("GaussDB client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize GaussDB client: {e}")
            logger.info("Falling back to local SQLite database")
            self.use_local_db = True
    
    def _initialize_local_database(self):
        """Initialize local SQLite database for cost optimization"""
        try:
            # Create data directory if it doesn't exist
            os.makedirs(os.path.dirname(self.local_db_path), exist_ok=True)
            
            # Connect to SQLite database
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            # Create tables for SafeRouteAI data
            self._create_local_tables(cursor)
            
            conn.commit()
            conn.close()
            
            logger.info(f"Local SQLite database initialized at {self.local_db_path}")
            
        except Exception as e:
            logger.error(f"Failed to initialize local database: {e}")
            raise
    
    def _create_local_tables(self, cursor):
        """Create local database tables"""
        
        # Crime incidents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crime_incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                incident_type TEXT NOT NULL,
                severity INTEGER NOT NULL,
                timestamp DATETIME NOT NULL,
                description TEXT,
                source TEXT DEFAULT 'SAPS',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Safety zones table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS safety_zones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                center_lat REAL NOT NULL,
                center_lng REAL NOT NULL,
                radius_meters INTEGER NOT NULL,
                safety_score REAL NOT NULL,
                zone_type TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Route history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS route_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                start_lat REAL NOT NULL,
                start_lng REAL NOT NULL,
                end_lat REAL NOT NULL,
                end_lng REAL NOT NULL,
                route_data TEXT NOT NULL,
                safety_score REAL,
                duration_minutes INTEGER,
                distance_km REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Model predictions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS model_predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                risk_score REAL NOT NULL,
                confidence REAL NOT NULL,
                model_version TEXT NOT NULL,
                prediction_time DATETIME NOT NULL,
                features_used TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Cost tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cost_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_name TEXT NOT NULL,
                cost_amount REAL NOT NULL,
                currency TEXT DEFAULT 'USD',
                billing_period TEXT NOT NULL,
                usage_details TEXT,
                recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create spatial indexes (SQLite doesn't have native spatial indexing)
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_crime_location 
            ON crime_incidents(latitude, longitude)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_safety_zones_location 
            ON safety_zones(center_lat, center_lng)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_route_start 
            ON route_history(start_lat, start_lng)
        ''')
        
        logger.info("Local database tables created successfully")
    
    def configure_database(self, config: DatabaseConfig = None) -> Dict[str, Any]:
        """Configure database with cost optimization"""
        logger.info("Configuring database with cost optimization...")
        
        if config is None:
            config = DatabaseConfig()
        
        # For cost optimization, recommend local SQLite
        if config.use_cloud_db and not self.demo_mode:
            return self._configure_cloud_database(config)
        else:
            return self._configure_local_database(config)
    
    def _configure_cloud_database(self, config: DatabaseConfig) -> Dict[str, Any]:
        """Configure GaussDB cloud database (expensive option)"""
        logger.info("Configuring GaussDB cloud database...")
        
        if self.demo_mode:
            return {
                "status": "demo_mode",
                "message": "GaussDB configuration simulated",
                "estimated_monthly_cost": "$15-30",
                "recommendation": "Use local SQLite for cost optimization"
            }
        
        try:
            # This would be expensive - estimated $15-30/month minimum
            estimated_cost = {
                "instance_cost": "$15-25/month",
                "storage_cost": "$2-5/month", 
                "backup_cost": "$1-2/month",
                "total_estimated": "$18-32/month"
            }
            
            return {
                "status": "not_recommended",
                "message": "GaussDB would consume 18-32% of $100 budget monthly",
                "estimated_cost": estimated_cost,
                "recommendation": "Use local SQLite database for cost optimization",
                "cost_savings": "$18-32/month saved by using local database",
                "alternative_configured": True
            }
            
        except Exception as e:
            logger.error(f"GaussDB configuration failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "fallback": "Using local SQLite database"
            }
    
    def _configure_local_database(self, config: DatabaseConfig) -> Dict[str, Any]:
        """Configure local SQLite database (cost-optimized option)"""
        logger.info("Configuring local SQLite database for cost optimization...")
        
        try:
            # Verify local database is working
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            # Test query
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                "status": "success",
                "message": "Local SQLite database configured successfully",
                "database_type": "SQLite",
                "database_path": self.local_db_path,
                "tables_created": table_count,
                "cost_optimization": {
                    "monthly_cost": "$0 (local storage)",
                    "cost_savings": "$18-32/month vs GaussDB",
                    "storage_location": "Local file system",
                    "backup_strategy": "File-based backups"
                },
                "capabilities": [
                    "Spatial queries (basic)",
                    "Crime data storage",
                    "Route history tracking",
                    "Model prediction logging",
                    "Cost tracking"
                ],
                "limitations": [
                    "No cloud-native scaling",
                    "Limited concurrent connections",
                    "Basic spatial indexing"
                ],
                "configuration_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Local database configuration failed: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def store_crime_data(self, crime_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Store crime data in database"""
        logger.info(f"Storing {len(crime_data)} crime incidents...")
        
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            stored_count = 0
            for incident in crime_data:
                cursor.execute('''
                    INSERT INTO crime_incidents 
                    (latitude, longitude, incident_type, severity, timestamp, description, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    incident.get('latitude', 0.0),
                    incident.get('longitude', 0.0),
                    incident.get('type', 'unknown'),
                    incident.get('severity', 1),
                    incident.get('timestamp', datetime.now().isoformat()),
                    incident.get('description', ''),
                    incident.get('source', 'SAPS')
                ))
                stored_count += 1
            
            conn.commit()
            conn.close()
            
            return {
                "status": "success",
                "message": f"Stored {stored_count} crime incidents",
                "stored_count": stored_count,
                "database": "Local SQLite"
            }
            
        except Exception as e:
            logger.error(f"Failed to store crime data: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def query_nearby_incidents(self, lat: float, lng: float, radius_km: float = 1.0) -> List[Dict[str, Any]]:
        """Query nearby crime incidents (basic spatial query)"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            # Simple bounding box query (not true spatial distance)
            lat_delta = radius_km / 111.0  # Rough conversion
            lng_delta = radius_km / (111.0 * abs(lat))
            
            cursor.execute('''
                SELECT id, latitude, longitude, incident_type, severity, timestamp, description
                FROM crime_incidents
                WHERE latitude BETWEEN ? AND ?
                AND longitude BETWEEN ? AND ?
                ORDER BY timestamp DESC
                LIMIT 50
            ''', (
                lat - lat_delta, lat + lat_delta,
                lng - lng_delta, lng + lng_delta
            ))
            
            incidents = []
            for row in cursor.fetchall():
                incidents.append({
                    'id': row[0],
                    'latitude': row[1],
                    'longitude': row[2],
                    'incident_type': row[3],
                    'severity': row[4],
                    'timestamp': row[5],
                    'description': row[6]
                })
            
            conn.close()
            
            return incidents
            
        except Exception as e:
            logger.error(f"Failed to query nearby incidents: {e}")
            return []
    
    def store_route_history(self, route_data: Dict[str, Any]) -> Dict[str, Any]:
        """Store route history for analysis"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO route_history 
                (user_id, start_lat, start_lng, end_lat, end_lng, route_data, 
                 safety_score, duration_minutes, distance_km)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                route_data.get('user_id', 'anonymous'),
                route_data.get('start_lat', 0.0),
                route_data.get('start_lng', 0.0),
                route_data.get('end_lat', 0.0),
                route_data.get('end_lng', 0.0),
                json.dumps(route_data.get('waypoints', [])),
                route_data.get('safety_score', 0.0),
                route_data.get('duration_minutes', 0),
                route_data.get('distance_km', 0.0)
            ))
            
            conn.commit()
            route_id = cursor.lastrowid
            conn.close()
            
            return {
                "status": "success",
                "route_id": route_id,
                "message": "Route history stored successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to store route history: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            stats = {}
            
            # Count records in each table
            tables = ['crime_incidents', 'safety_zones', 'route_history', 'model_predictions', 'cost_tracking']
            
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[f"{table}_count"] = cursor.fetchone()[0]
            
            # Database file size
            db_size_bytes = os.path.getsize(self.local_db_path) if os.path.exists(self.local_db_path) else 0
            stats['database_size_mb'] = round(db_size_bytes / (1024 * 1024), 2)
            
            conn.close()
            
            return {
                "status": "success",
                "database_type": "SQLite (Local)",
                "database_path": self.local_db_path,
                "statistics": stats,
                "cost_optimization": {
                    "monthly_cost": "$0",
                    "storage_cost": "Local disk space only",
                    "cost_savings_vs_cloud": "$18-32/month"
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def backup_database(self, backup_path: str = None) -> Dict[str, Any]:
        """Create database backup"""
        if backup_path is None:
            backup_path = f"backups/saferoute_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        
        try:
            # Create backup directory
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            # Copy database file
            import shutil
            shutil.copy2(self.local_db_path, backup_path)
            
            backup_size = os.path.getsize(backup_path)
            
            return {
                "status": "success",
                "message": "Database backup created successfully",
                "backup_path": backup_path,
                "backup_size_mb": round(backup_size / (1024 * 1024), 2),
                "backup_time": datetime.now().isoformat(),
                "cost": "$0 (local backup)"
            }
            
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def get_cost_comparison(self) -> Dict[str, Any]:
        """Compare costs between local and cloud database options"""
        return {
            "local_sqlite": {
                "setup_cost": "$0",
                "monthly_cost": "$0",
                "storage_cost": "Local disk space only",
                "backup_cost": "$0 (local backups)",
                "total_annual_cost": "$0"
            },
            "gaussdb_cloud": {
                "setup_cost": "$0",
                "monthly_cost": "$18-32",
                "storage_cost": "$2-5/month",
                "backup_cost": "$1-2/month",
                "total_annual_cost": "$216-384"
            },
            "recommendation": {
                "choice": "Local SQLite",
                "reason": "Cost optimization for $100 budget",
                "savings": "$216-384/year",
                "budget_impact": "0% vs 18-32% monthly for cloud option"
            },
            "trade_offs": {
                "local_pros": [
                    "Zero ongoing costs",
                    "Full data control",
                    "No network dependency",
                    "Sufficient for SafeRouteAI needs"
                ],
                "local_cons": [
                    "No cloud-native scaling",
                    "Limited concurrent users",
                    "Manual backup management"
                ],
                "cloud_pros": [
                    "Automatic scaling",
                    "Built-in backups",
                    "High availability",
                    "Advanced spatial features"
                ],
                "cloud_cons": [
                    "High monthly cost",
                    "Network dependency",
                    "Complex configuration"
                ]
            }
        }

# Global database manager instance
gaussdb_manager = GaussDBManager()