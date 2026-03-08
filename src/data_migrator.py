"""
Data Migrator for SafeRouteAI Production
Handles migration of crime data, models, and other assets to Huawei Cloud OBS
"""

import logging
import os
import json
import hashlib
import shutil
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path
from config import settings
from obs_manager import obs_manager

logger = logging.getLogger(__name__)

@dataclass
class MigrationTask:
    task_id: str
    source_path: str
    target_path: str
    file_size_mb: float
    status: str
    progress_percent: float
    estimated_cost: float
    checksum: str = ""
    error_message: str = ""

@dataclass
class MigrationResult:
    success: bool
    total_files: int
    successful_files: int
    failed_files: int
    total_size_mb: float
    total_cost: float
    migration_time: str
    tasks: List[MigrationTask]

class DataMigrator:
    """Handles data migration from local storage to Huawei Cloud OBS"""
    
    def __init__(self):
        self.region = settings.huawei_cloud_region or "af-south-1"
        self.bucket_name = settings.obs_bucket_name or "saferoute-ai-data"
        self.demo_mode = settings.demo_mode
        self.migration_log_file = "data/migration_log.json"
        
        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)
        
        # Crime data sources
        self.crime_data_sources = [
            "data/crime_data.csv",
            "data/saps_statistics.json",
            "data/hotspot_analysis.csv",
            "data/incident_reports.json",
            "data/safety_zones.geojson"
        ]
        
        # Model data sources
        self.model_data_sources = [
            "models/",
            "data/training_data.csv",
            "data/processed_features.json"
        ]
    
    def migrate_all_data(self) -> Dict[str, Any]:
        """Migrate all data to OBS with cost optimization"""
        logger.info("Starting comprehensive data migration to OBS...")
        
        migration_start = datetime.now()
        
        # Step 1: Set up OBS bucket and structure
        bucket_setup = obs_manager.create_bucket_with_optimization()
        if bucket_setup["status"] != "success" and not self.demo_mode:
            return {
                "status": "error",
                "message": "Failed to set up OBS bucket",
                "error": bucket_setup.get("message", "Unknown error")
            }
        
        structure_setup = obs_manager.setup_data_structure()
        
        # Step 2: Migrate crime data
        crime_migration = self.migrate_crime_data()
        
        # Step 3: Migrate model data
        model_migration = self.migrate_model_data()
        
        # Step 4: Migrate additional assets
        asset_migration = self.migrate_additional_assets()
        
        # Calculate totals
        total_files = (crime_migration.get("total_files", 0) + 
                      model_migration.get("total_files", 0) + 
                      asset_migration.get("total_files", 0))
        
        successful_files = (crime_migration.get("successful_files", 0) + 
                           model_migration.get("successful_files", 0) + 
                           asset_migration.get("successful_files", 0))
        
        total_cost = (crime_migration.get("total_cost", 0.0) + 
                     model_migration.get("total_cost", 0.0) + 
                     asset_migration.get("total_cost", 0.0))
        
        migration_time = (datetime.now() - migration_start).total_seconds()
        
        result = {
            "status": "completed",
            "message": f"Migration completed: {successful_files}/{total_files} files successful",
            "bucket_setup": bucket_setup,
            "structure_setup": structure_setup,
            "crime_data_migration": crime_migration,
            "model_data_migration": model_migration,
            "asset_migration": asset_migration,
            "summary": {
                "total_files": total_files,
                "successful_files": successful_files,
                "failed_files": total_files - successful_files,
                "success_rate": (successful_files / total_files * 100) if total_files > 0 else 0,
                "total_cost": round(total_cost, 4),
                "migration_time_seconds": round(migration_time, 2),
                "obs_bucket": f"obs://{self.bucket_name}/",
                "region": self.region
            },
            "migration_time": datetime.now().isoformat()
        }
        
        # Log migration results
        self._log_migration_results(result)
        
        return result
    
    def migrate_crime_data(self) -> Dict[str, Any]:
        """Migrate crime data files to OBS"""
        logger.info("Migrating crime data to OBS...")
        
        migration_tasks = []
        total_cost = 0.0
        successful_count = 0
        
        # Create sample crime data if it doesn't exist
        self._ensure_sample_crime_data()
        
        for source_file in self.crime_data_sources:
            if os.path.exists(source_file):
                # Determine target path in OBS
                filename = Path(source_file).name
                if "saps" in filename.lower():
                    target_path = f"crime-data/saps-statistics/{filename}"
                elif "hotspot" in filename.lower():
                    target_path = f"crime-data/hotspot-analysis/{filename}"
                else:
                    target_path = f"crime-data/processed/{filename}"
                
                # Create migration task
                task = self._create_migration_task(source_file, target_path)
                
                # Execute migration
                if self.demo_mode:
                    task.status = "completed"
                    task.progress_percent = 100.0
                    successful_count += 1
                else:
                    result = obs_manager._upload_file_with_optimization(source_file, target_path)
                    if result.success:
                        task.status = "completed"
                        task.progress_percent = 100.0
                        task.estimated_cost = result.cost_estimate
                        task.checksum = result.checksum
                        successful_count += 1
                    else:
                        task.status = "failed"
                        task.error_message = result.error_message or "Upload failed"
                
                total_cost += task.estimated_cost
                migration_tasks.append(task)
        
        return {
            "status": "completed",
            "total_files": len(migration_tasks),
            "successful_files": successful_count,
            "failed_files": len(migration_tasks) - successful_count,
            "total_cost": round(total_cost, 4),
            "tasks": [self._task_to_dict(task) for task in migration_tasks],
            "target_location": f"obs://{self.bucket_name}/crime-data/"
        }
    
    def migrate_model_data(self) -> Dict[str, Any]:
        """Migrate ML model data to OBS"""
        logger.info("Migrating model data to OBS...")
        
        migration_tasks = []
        total_cost = 0.0
        successful_count = 0
        
        # Create sample model data if it doesn't exist
        self._ensure_sample_model_data()
        
        for source_path in self.model_data_sources:
            if os.path.exists(source_path):
                if os.path.isfile(source_path):
                    # Single file
                    filename = Path(source_path).name
                    target_path = f"models/training-data/{filename}"
                    
                    task = self._create_migration_task(source_path, target_path)
                    
                    if self.demo_mode:
                        task.status = "completed"
                        task.progress_percent = 100.0
                        successful_count += 1
                    else:
                        result = obs_manager._upload_file_with_optimization(source_path, target_path)
                        if result.success:
                            task.status = "completed"
                            task.progress_percent = 100.0
                            task.estimated_cost = result.cost_estimate
                            task.checksum = result.checksum
                            successful_count += 1
                        else:
                            task.status = "failed"
                            task.error_message = result.error_message or "Upload failed"
                    
                    total_cost += task.estimated_cost
                    migration_tasks.append(task)
                
                elif os.path.isdir(source_path):
                    # Directory - upload all files
                    for root, dirs, files in os.walk(source_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            relative_path = os.path.relpath(file_path, source_path)
                            target_path = f"models/trained-models/{relative_path}".replace("\\", "/")
                            
                            task = self._create_migration_task(file_path, target_path)
                            
                            if self.demo_mode:
                                task.status = "completed"
                                task.progress_percent = 100.0
                                successful_count += 1
                            else:
                                result = obs_manager._upload_file_with_optimization(file_path, target_path)
                                if result.success:
                                    task.status = "completed"
                                    task.progress_percent = 100.0
                                    task.estimated_cost = result.cost_estimate
                                    task.checksum = result.checksum
                                    successful_count += 1
                                else:
                                    task.status = "failed"
                                    task.error_message = result.error_message or "Upload failed"
                            
                            total_cost += task.estimated_cost
                            migration_tasks.append(task)
        
        return {
            "status": "completed",
            "total_files": len(migration_tasks),
            "successful_files": successful_count,
            "failed_files": len(migration_tasks) - successful_count,
            "total_cost": round(total_cost, 4),
            "tasks": [self._task_to_dict(task) for task in migration_tasks],
            "target_location": f"obs://{self.bucket_name}/models/"
        }
    
    def migrate_additional_assets(self) -> Dict[str, Any]:
        """Migrate additional assets like configuration files, documentation"""
        logger.info("Migrating additional assets to OBS...")
        
        migration_tasks = []
        total_cost = 0.0
        successful_count = 0
        
        # Additional files to migrate
        additional_files = [
            ("README.md", "docs/README.md"),
            (".env.example", "config/.env.example"),
            ("requirements.txt", "config/requirements.txt"),
            ("HUAWEI_CLOUD_SETUP_GUIDE.md", "docs/HUAWEI_CLOUD_SETUP_GUIDE.md"),
            ("BUDGET_OPTIMIZATION_STRATEGY.md", "docs/BUDGET_OPTIMIZATION_STRATEGY.md")
        ]
        
        for source_file, target_path in additional_files:
            if os.path.exists(source_file):
                task = self._create_migration_task(source_file, target_path)
                
                if self.demo_mode:
                    task.status = "completed"
                    task.progress_percent = 100.0
                    successful_count += 1
                else:
                    result = obs_manager._upload_file_with_optimization(source_file, target_path)
                    if result.success:
                        task.status = "completed"
                        task.progress_percent = 100.0
                        task.estimated_cost = result.cost_estimate
                        task.checksum = result.checksum
                        successful_count += 1
                    else:
                        task.status = "failed"
                        task.error_message = result.error_message or "Upload failed"
                
                total_cost += task.estimated_cost
                migration_tasks.append(task)
        
        return {
            "status": "completed",
            "total_files": len(migration_tasks),
            "successful_files": successful_count,
            "failed_files": len(migration_tasks) - successful_count,
            "total_cost": round(total_cost, 4),
            "tasks": [self._task_to_dict(task) for task in migration_tasks],
            "target_location": f"obs://{self.bucket_name}/docs/"
        }
    
    def _create_migration_task(self, source_path: str, target_path: str) -> MigrationTask:
        """Create a migration task"""
        task_id = f"migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(source_path) % 10000}"
        
        # Calculate file size
        file_size_bytes = os.path.getsize(source_path) if os.path.exists(source_path) else 0
        file_size_mb = file_size_bytes / (1024 * 1024)
        
        # Estimate cost (rough calculation: $0.023 per GB for storage)
        estimated_cost = (file_size_bytes / (1024 * 1024 * 1024)) * 0.023
        
        return MigrationTask(
            task_id=task_id,
            source_path=source_path,
            target_path=target_path,
            file_size_mb=round(file_size_mb, 3),
            status="pending",
            progress_percent=0.0,
            estimated_cost=estimated_cost
        )
    
    def _task_to_dict(self, task: MigrationTask) -> Dict[str, Any]:
        """Convert migration task to dictionary"""
        return {
            "task_id": task.task_id,
            "source_path": task.source_path,
            "target_path": task.target_path,
            "file_size_mb": task.file_size_mb,
            "status": task.status,
            "progress_percent": task.progress_percent,
            "estimated_cost": task.estimated_cost,
            "checksum": task.checksum,
            "error_message": task.error_message
        }
    
    def _ensure_sample_crime_data(self):
        """Create sample crime data files if they don't exist"""
        os.makedirs("data", exist_ok=True)
        
        # Sample crime data CSV
        if not os.path.exists("data/crime_data.csv"):
            sample_crime_csv = """latitude,longitude,incident_type,severity,timestamp,description
-26.2041,28.0473,theft,3,2025-01-20T14:30:00,Vehicle theft reported
-26.1956,28.0516,assault,4,2025-01-20T16:45:00,Assault incident
-26.2089,28.0445,burglary,3,2025-01-21T02:15:00,House burglary
-26.1978,28.0501,robbery,5,2025-01-21T19:20:00,Armed robbery
-26.2034,28.0489,vandalism,2,2025-01-22T11:10:00,Property vandalism
"""
            with open("data/crime_data.csv", "w") as f:
                f.write(sample_crime_csv)
        
        # Sample SAPS statistics JSON
        if not os.path.exists("data/saps_statistics.json"):
            sample_saps_data = {
                "report_period": "2025-01",
                "region": "Johannesburg",
                "statistics": {
                    "total_incidents": 1247,
                    "theft": 456,
                    "assault": 234,
                    "burglary": 189,
                    "robbery": 156,
                    "vandalism": 212
                },
                "hotspots": [
                    {"area": "Hillbrow", "incident_count": 89, "risk_level": "high"},
                    {"area": "Alexandra", "incident_count": 76, "risk_level": "high"},
                    {"area": "Soweto", "incident_count": 134, "risk_level": "medium"}
                ]
            }
            with open("data/saps_statistics.json", "w") as f:
                json.dump(sample_saps_data, f, indent=2)
        
        # Sample hotspot analysis CSV
        if not os.path.exists("data/hotspot_analysis.csv"):
            sample_hotspot_csv = """area_name,center_lat,center_lng,risk_score,incident_count,population
Hillbrow,-26.1849,28.0488,0.85,89,76000
Alexandra,-26.1009,28.0963,0.82,76,180000
Soweto,-26.2678,27.8546,0.65,134,1300000
Sandton,-26.1076,28.0567,0.25,12,220000
Rosebank,-26.1467,28.0436,0.30,18,35000
"""
            with open("data/hotspot_analysis.csv", "w") as f:
                f.write(sample_hotspot_csv)
    
    def _ensure_sample_model_data(self):
        """Create sample model data files if they don't exist"""
        os.makedirs("models", exist_ok=True)
        os.makedirs("data", exist_ok=True)
        
        # Sample training data CSV
        if not os.path.exists("data/training_data.csv"):
            sample_training_csv = """lat,lng,hour,day_of_week,month,is_weekend,is_night,num_risk_factors,risk_level
-26.2041,28.0473,14,1,1,0,0,2,0.65
-26.1956,28.0516,16,1,1,0,0,3,0.78
-26.2089,28.0445,2,2,1,0,1,4,0.89
-26.1978,28.0501,19,2,1,0,1,5,0.92
-26.2034,28.0489,11,3,1,0,0,1,0.34
"""
            with open("data/training_data.csv", "w") as f:
                f.write(sample_training_csv)
        
        # Sample processed features JSON
        if not os.path.exists("data/processed_features.json"):
            sample_features = {
                "feature_engineering": {
                    "spatial_features": ["lat", "lng", "distance_to_hotspot"],
                    "temporal_features": ["hour", "day_of_week", "month", "is_weekend", "is_night"],
                    "risk_features": ["num_risk_factors", "has_gang_activity", "has_poor_lighting"]
                },
                "preprocessing": {
                    "scaling": "StandardScaler",
                    "encoding": "OneHotEncoder for categorical",
                    "missing_values": "median imputation"
                },
                "model_performance": {
                    "r2_score": 0.847,
                    "mse": 0.023,
                    "feature_importance": {
                        "num_risk_factors": 0.34,
                        "is_night": 0.28,
                        "distance_to_hotspot": 0.19,
                        "hour": 0.12,
                        "day_of_week": 0.07
                    }
                }
            }
            with open("data/processed_features.json", "w") as f:
                json.dump(sample_features, f, indent=2)
        
        # Sample model file (placeholder)
        if not os.path.exists("models/saferoute_model.pkl"):
            with open("models/saferoute_model.pkl", "w") as f:
                f.write("# Placeholder for trained SafeRouteAI model\n")
                f.write("# In production, this would be a serialized ML model\n")
                f.write(f"# Created: {datetime.now().isoformat()}\n")
    
    def validate_migration_integrity(self, migration_result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data integrity after migration"""
        logger.info("Validating migration data integrity...")
        
        validation_results = []
        total_validated = 0
        successful_validations = 0
        
        # Validate crime data migration
        if "crime_data_migration" in migration_result:
            for task_dict in migration_result["crime_data_migration"].get("tasks", []):
                if task_dict["status"] == "completed":
                    validation = self._validate_single_file(task_dict["source_path"], task_dict["target_path"])
                    validation_results.append(validation)
                    total_validated += 1
                    if validation["valid"]:
                        successful_validations += 1
        
        # Validate model data migration
        if "model_data_migration" in migration_result:
            for task_dict in migration_result["model_data_migration"].get("tasks", []):
                if task_dict["status"] == "completed":
                    validation = self._validate_single_file(task_dict["source_path"], task_dict["target_path"])
                    validation_results.append(validation)
                    total_validated += 1
                    if validation["valid"]:
                        successful_validations += 1
        
        return {
            "status": "completed",
            "total_files_validated": total_validated,
            "successful_validations": successful_validations,
            "failed_validations": total_validated - successful_validations,
            "validation_success_rate": (successful_validations / total_validated * 100) if total_validated > 0 else 0,
            "validation_results": validation_results,
            "validation_time": datetime.now().isoformat()
        }
    
    def _validate_single_file(self, source_path: str, target_path: str) -> Dict[str, Any]:
        """Validate a single file migration"""
        if self.demo_mode:
            return {
                "source_path": source_path,
                "target_path": target_path,
                "valid": True,
                "checksum_match": True,
                "file_accessible": True,
                "validation_method": "demo_mode"
            }
        
        try:
            # Use OBS manager to validate
            validation_result = obs_manager.validate_data_integrity(source_path, target_path)
            
            return {
                "source_path": source_path,
                "target_path": target_path,
                "valid": validation_result.get("checksum_match", False),
                "checksum_match": validation_result.get("checksum_match", False),
                "file_accessible": validation_result.get("file_accessible", False),
                "validation_method": "checksum_comparison"
            }
            
        except Exception as e:
            return {
                "source_path": source_path,
                "target_path": target_path,
                "valid": False,
                "error": str(e),
                "validation_method": "error"
            }
    
    def _log_migration_results(self, results: Dict[str, Any]):
        """Log migration results for audit"""
        try:
            # Load existing log
            if os.path.exists(self.migration_log_file):
                with open(self.migration_log_file, 'r') as f:
                    log_data = json.load(f)
            else:
                log_data = []
            
            # Add new entry
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "migration_results": results
            }
            log_data.append(log_entry)
            
            # Keep only last 50 entries
            log_data = log_data[-50:]
            
            # Save updated log
            with open(self.migration_log_file, 'w') as f:
                json.dump(log_data, f, indent=2)
                
            logger.info(f"Migration results logged to {self.migration_log_file}")
            
        except Exception as e:
            logger.error(f"Failed to log migration results: {e}")
    
    def get_migration_status(self) -> Dict[str, Any]:
        """Get current migration status"""
        try:
            if os.path.exists(self.migration_log_file):
                with open(self.migration_log_file, 'r') as f:
                    log_data = json.load(f)
                
                if log_data:
                    latest_migration = log_data[-1]
                    return {
                        "status": "completed",
                        "last_migration": latest_migration["timestamp"],
                        "summary": latest_migration["migration_results"]["summary"],
                        "obs_bucket": f"obs://{self.bucket_name}/",
                        "region": self.region
                    }
            
            return {
                "status": "not_started",
                "message": "No migration has been performed yet",
                "obs_bucket": f"obs://{self.bucket_name}/",
                "region": self.region
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

# Global data migrator instance
data_migrator = DataMigrator()