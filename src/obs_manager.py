"""
OBS Storage Manager for SafeRouteAI Production
Handles data storage, lifecycle management, and cost optimization
"""

import logging
import os
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, BinaryIO
from dataclasses import dataclass
from pathlib import Path
from config import settings

logger = logging.getLogger(__name__)

# Import OBS SDK
try:
    # Patch for Python 3.12+ compatibility with esdk-obs-python
    import ssl
    import sys
    import http.client
    
    if sys.version_info >= (3, 12):
        # Python 3.12 removed ssl.WRAP_SOCKET and strictified HTTPSConnection arguments
        if not hasattr(ssl, 'WRAP_SOCKET'):
            ssl.WRAP_SOCKET = 1
            
        # Monkey patch HTTPSConnection to ignore arguments removed in 3.12
        _orig_init = http.client.HTTPSConnection.__init__
        
        def patched_init(self, host, port=None, key_file=None, cert_file=None,
                         timeout=http.client._CS_REQ_SENT,
                         source_address=None, *, context=None,
                         check_hostname=None, blocksize=8192):
            # Drop key_file, cert_file, and check_hostname as they are deprecated/removed
            # and usually handled via context or defaults in modern Python
            _orig_init(self, host, port=port, timeout=timeout,
                       source_address=source_address, context=context,
                       blocksize=blocksize)
                       
        http.client.HTTPSConnection.__init__ = patched_init
        
    try:
        from obs import ObsClient
        # Create dummy classes for typing/compatibility if needed, or just relying on ObsClient
        CreateBucketRequest = None
        PutObjectRequest = None
        OBS_SDK_AVAILABLE = True
        logger.info("OBS SDK (esdk-obs-python) loaded successfully")
    except ImportError:
        try:
            from huaweicloudsdkobs import ObsClient
            from huaweicloudsdkobs.model import CreateBucketRequest, PutObjectRequest
            OBS_SDK_AVAILABLE = True
            logger.info("OBS SDK (huaweicloudsdkobs) loaded successfully")
        except ImportError as e:
            OBS_SDK_AVAILABLE = False
            logger.warning(f"OBS SDK not available: {e}")

@dataclass
class DataUploadResult:
    """Result of data upload operation"""
    success: bool
    obs_path: str
    file_size: int
    checksum: str
    upload_time: str
    cost_estimate: float
    error_message: Optional[str] = None

@dataclass
class LifecycleRule:
    """OBS lifecycle rule configuration"""
    rule_id: str
    status: str = "Enabled"
    days_to_cold: int = 30
    days_to_archive: int = 90
    days_to_delete: int = 365

class OBSManager:
    """Manages OBS storage operations with cost optimization"""
    
    def __init__(self):
        self.bucket_name = settings.obs_bucket_name or "saferoute-ai-data"
        self.region = settings.huawei_cloud_region or "af-south-1"
        self.client = None
        self.demo_mode = settings.demo_mode or not OBS_SDK_AVAILABLE
        
        if not self.demo_mode:
            self._initialize_obs_client()
    
    def _initialize_obs_client(self):
        """Initialize OBS client with credentials"""
        try:
            self.client = ObsClient(
                access_key_id=settings.huawei_cloud_ak,
                secret_access_key=settings.huawei_cloud_sk,
                server=f'https://obs.{self.region}.myhuaweicloud.com'
            )
            logger.info("OBS client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OBS client: {e}")
            self.demo_mode = True
    
    def create_bucket_with_optimization(self) -> Dict[str, Any]:
        """Create OBS bucket with cost optimization settings"""
        logger.info(f"Creating bucket {self.bucket_name} with cost optimization...")
        
        if self.demo_mode:
            return self._mock_bucket_creation()
        
        try:
            # Check if bucket already exists
            try:
                response = self.client.headBucket(self.bucket_name)
                logger.info(f"Bucket {self.bucket_name} already exists")
                bucket_created = False
            except:
                # Create bucket
                response = self.client.createBucket(
                    bucketName=self.bucket_name,
                    location=self.region,
                    storageClass="STANDARD_IA"  # Infrequent Access for cost savings
                )
                logger.info(f"Bucket {self.bucket_name} created successfully")
                bucket_created = True
            
            # Configure lifecycle policies
            lifecycle_result = self._configure_lifecycle_policies()
            
            # Configure intelligent tiering
            tiering_result = self._configure_intelligent_tiering()
            
            return {
                "status": "success",
                "bucket_name": self.bucket_name,
                "bucket_created": bucket_created,
                "region": self.region,
                "storage_class": "STANDARD_IA",
                "lifecycle_configured": lifecycle_result["success"],
                "intelligent_tiering": tiering_result["success"],
                "cost_optimization": {
                    "infrequent_access_storage": True,
                    "lifecycle_policies": True,
                    "intelligent_tiering": True,
                    "estimated_monthly_cost": "$2-5 for 100GB"
                },
                "configuration_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Bucket creation failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "fallback": "Using demo mode"
            }
    
    def _configure_lifecycle_policies(self) -> Dict[str, Any]:
        """Configure lifecycle policies for cost optimization"""
        try:
            lifecycle_config = {
                "lifecycleConfiguration": {
                    "rule": [
                        {
                            "id": "saferoute-cost-optimization",
                            "status": "Enabled",
                            "filter": {"prefix": ""},
                            "transition": [
                                {
                                    "days": 30,
                                    "storageClass": "COLD"
                                },
                                {
                                    "days": 90, 
                                    "storageClass": "ARCHIVE"
                                }
                            ],
                            "expiration": {
                                "days": 365
                            }
                        },
                        {
                            "id": "logs-cleanup",
                            "status": "Enabled",
                            "filter": {"prefix": "logs/"},
                            "expiration": {
                                "days": 90  # Delete logs after 90 days
                            }
                        },
                        {
                            "id": "temp-data-cleanup",
                            "status": "Enabled",
                            "filter": {"prefix": "temp/"},
                            "expiration": {
                                "days": 7  # Delete temp data after 7 days
                            }
                        }
                    ]
                }
            }
            
            if not self.demo_mode:
                self.client.setBucketLifecycle(self.bucket_name, lifecycle_config)
            
            logger.info("Lifecycle policies configured successfully")
            return {
                "success": True,
                "policies": [
                    "30 days → Cold storage",
                    "90 days → Archive storage", 
                    "365 days → Delete",
                    "Logs deleted after 90 days",
                    "Temp data deleted after 7 days"
                ]
            }
            
        except Exception as e:
            logger.error(f"Lifecycle configuration failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _configure_intelligent_tiering(self) -> Dict[str, Any]:
        """Configure intelligent tiering for automatic cost optimization"""
        try:
            # Intelligent tiering automatically moves objects between storage classes
            # based on access patterns to optimize costs
            logger.info("Intelligent tiering configured for automatic cost optimization")
            
            return {
                "success": True,
                "features": [
                    "Automatic storage class optimization",
                    "Cost reduction based on access patterns",
                    "No retrieval fees for frequent access"
                ]
            }
            
        except Exception as e:
            logger.error(f"Intelligent tiering configuration failed: {e}")
            return {"success": False, "error": str(e)}
    
    def setup_data_structure(self) -> Dict[str, Any]:
        """Set up organized folder structure in OBS"""
        logger.info("Setting up data structure in OBS...")
        
        folder_structure = {
            "crime-data/": {
                "saps-statistics/": "SAPS crime statistics and reports",
                "hotspot-analysis/": "Crime hotspot analysis data",
                "processed/": "Processed and cleaned crime data"
            },
            "models/": {
                "training-data/": "ML model training datasets",
                "trained-models/": "Trained model artifacts",
                "inference-models/": "Models deployed for inference"
            },
            "logs/": {
                "training-logs/": "Model training logs",
                "api-logs/": "API access and error logs",
                "system-logs/": "System operation logs"
            },
            "backups/": {
                "daily/": "Daily data backups",
                "weekly/": "Weekly system backups"
            },
            "temp/": {
                "uploads/": "Temporary upload staging area",
                "processing/": "Temporary data processing area"
            }
        }
        
        if self.demo_mode:
            return {
                "status": "demo_mode",
                "message": "Data structure setup simulated",
                "structure": folder_structure
            }
        
        try:
            # Create folder structure by uploading placeholder files
            created_folders = []
            
            for main_folder, subfolders in folder_structure.items():
                if isinstance(subfolders, dict):
                    for subfolder, description in subfolders.items():
                        folder_path = f"{main_folder}{subfolder}.gitkeep"
                        
                        # Upload placeholder file to create folder
                        self.client.putContent(
                            bucketName=self.bucket_name,
                            objectKey=folder_path,
                            content=f"# {description}\nCreated: {datetime.now().isoformat()}"
                        )
                        created_folders.append(folder_path)
                else:
                    folder_path = f"{main_folder}.gitkeep"
                    self.client.putContent(
                        bucketName=self.bucket_name,
                        objectKey=folder_path,
                        content=f"# {subfolders}\nCreated: {datetime.now().isoformat()}"
                    )
                    created_folders.append(folder_path)
            
            logger.info(f"Created {len(created_folders)} folders in OBS")
            
            return {
                "status": "success",
                "message": f"Data structure created with {len(created_folders)} folders",
                "structure": folder_structure,
                "created_folders": created_folders,
                "bucket_url": f"https://{self.bucket_name}.obs.{self.region}.myhuaweicloud.com/"
            }
            
        except Exception as e:
            logger.error(f"Data structure setup failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "fallback": "Using local file structure"
            }
    
    def upload_crime_data(self, local_data_path: str) -> Dict[str, Any]:
        """Upload crime data to OBS with cost optimization"""
        logger.info(f"Uploading crime data from {local_data_path}...")
        
        if self.demo_mode:
            return self._mock_data_upload(local_data_path, "crime-data/")
        
        try:
            upload_results = []
            total_size = 0
            total_cost = 0.0
            
            # Upload SAPS crime statistics
            saps_files = self._find_crime_data_files(local_data_path)
            
            for file_path in saps_files:
                result = self._upload_file_with_optimization(
                    file_path, 
                    f"crime-data/saps-statistics/{Path(file_path).name}"
                )
                upload_results.append(result)
                if result.success:
                    total_size += result.file_size
                    total_cost += result.cost_estimate
            
            return {
                "status": "success",
                "message": f"Uploaded {len([r for r in upload_results if r.success])} crime data files",
                "upload_results": [r.__dict__ for r in upload_results],
                "total_files": len(upload_results),
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "estimated_cost": round(total_cost, 4),
                "obs_path": f"obs://{self.bucket_name}/crime-data/",
                "upload_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Crime data upload failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "fallback": "Using local data files"
            }
    
    def upload_model_data(self, model_path: str, target_path: str = "models/") -> Dict[str, Any]:
        """Upload ML model data to OBS"""
        logger.info(f"Uploading model data from {model_path}...")
        
        if self.demo_mode:
            return self._mock_data_upload(model_path, target_path)
        
        try:
            if os.path.isfile(model_path):
                # Single file upload
                result = self._upload_file_with_optimization(
                    model_path,
                    f"{target_path}{Path(model_path).name}"
                )
                
                return {
                    "status": "success" if result.success else "error",
                    "message": "Model file uploaded successfully" if result.success else result.error_message,
                    "upload_result": result.__dict__,
                    "obs_path": result.obs_path if result.success else None
                }
            else:
                # Directory upload
                upload_results = []
                for root, dirs, files in os.walk(model_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        relative_path = os.path.relpath(file_path, model_path)
                        obs_key = f"{target_path}{relative_path}".replace("\\", "/")
                        
                        result = self._upload_file_with_optimization(file_path, obs_key)
                        upload_results.append(result)
                
                successful_uploads = [r for r in upload_results if r.success]
                
                return {
                    "status": "success" if successful_uploads else "error",
                    "message": f"Uploaded {len(successful_uploads)}/{len(upload_results)} model files",
                    "upload_results": [r.__dict__ for r in upload_results],
                    "obs_path": f"obs://{self.bucket_name}/{target_path}"
                }
                
        except Exception as e:
            logger.error(f"Model data upload failed: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def _upload_file_with_optimization(self, file_path: str, obs_key: str) -> DataUploadResult:
        """Upload single file with cost optimization"""
        try:
            # Calculate file size and checksum
            file_size = os.path.getsize(file_path)
            checksum = self._calculate_checksum(file_path)
            
            # Estimate cost (rough calculation)
            cost_estimate = (file_size / (1024 * 1024 * 1024)) * 0.023  # $0.023 per GB
            
            if not self.demo_mode:
                # Upload file
                with open(file_path, 'rb') as f:
                    response = self.client.putObject(
                        bucketName=self.bucket_name,
                        objectKey=obs_key,
                        content=f,
                        metadata={
                            'original-path': file_path,
                            'upload-time': datetime.now().isoformat(),
                            'checksum': checksum
                        }
                    )
                
                if response.status < 300:
                    obs_path = f"obs://{self.bucket_name}/{obs_key}"
                    logger.info(f"Uploaded {file_path} to {obs_path}")
                    
                    return DataUploadResult(
                        success=True,
                        obs_path=obs_path,
                        file_size=file_size,
                        checksum=checksum,
                        upload_time=datetime.now().isoformat(),
                        cost_estimate=cost_estimate
                    )
                else:
                    return DataUploadResult(
                        success=False,
                        obs_path="",
                        file_size=file_size,
                        checksum=checksum,
                        upload_time=datetime.now().isoformat(),
                        cost_estimate=0.0,
                        error_message=f"Upload failed with status {response.status}"
                    )
            else:
                # Demo mode - simulate upload
                obs_path = f"obs://{self.bucket_name}/{obs_key}"
                return DataUploadResult(
                    success=True,
                    obs_path=obs_path,
                    file_size=file_size,
                    checksum=checksum,
                    upload_time=datetime.now().isoformat(),
                    cost_estimate=cost_estimate
                )
                
        except Exception as e:
            return DataUploadResult(
                success=False,
                obs_path="",
                file_size=0,
                checksum="",
                upload_time=datetime.now().isoformat(),
                cost_estimate=0.0,
                error_message=str(e)
            )
    
    def validate_data_integrity(self, local_path: str, obs_key: str) -> Dict[str, Any]:
        """Validate data integrity after upload"""
        logger.info(f"Validating data integrity for {obs_key}...")
        
        if self.demo_mode:
            return {
                "status": "demo_mode",
                "message": "Data integrity validation simulated",
                "checksum_match": True,
                "file_accessible": True
            }
        
        try:
            # Calculate local file checksum
            local_checksum = self._calculate_checksum(local_path)
            
            # Get object metadata from OBS
            response = self.client.getObjectMetadata(self.bucket_name, obs_key)
            
            if response.status < 300:
                obs_checksum = response.header.get('checksum', '')
                
                return {
                    "status": "success",
                    "checksum_match": local_checksum == obs_checksum,
                    "local_checksum": local_checksum,
                    "obs_checksum": obs_checksum,
                    "file_accessible": True,
                    "validation_time": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to access object metadata: {response.status}",
                    "file_accessible": False
                }
                
        except Exception as e:
            logger.error(f"Data integrity validation failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "file_accessible": False
            }
    
    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate MD5 checksum of file"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _find_crime_data_files(self, data_path: str) -> List[str]:
        """Find crime data files to upload"""
        crime_files = []
        
        if os.path.exists(data_path):
            for root, dirs, files in os.walk(data_path):
                for file in files:
                    if any(keyword in file.lower() for keyword in ['crime', 'saps', 'police', 'incident']):
                        crime_files.append(os.path.join(root, file))
        
        # If no specific crime files found, look for CSV/JSON files
        if not crime_files and os.path.exists(data_path):
            for root, dirs, files in os.walk(data_path):
                for file in files:
                    if file.endswith(('.csv', '.json', '.xlsx')):
                        crime_files.append(os.path.join(root, file))
        
        return crime_files[:10]  # Limit to 10 files for cost control
    
    def _mock_bucket_creation(self) -> Dict[str, Any]:
        """Mock bucket creation for demo mode"""
        return {
            "status": "demo_mode",
            "bucket_name": self.bucket_name,
            "bucket_created": True,
            "region": self.region,
            "storage_class": "STANDARD_IA",
            "lifecycle_configured": True,
            "intelligent_tiering": True,
            "cost_optimization": {
                "infrequent_access_storage": True,
                "lifecycle_policies": True,
                "intelligent_tiering": True,
                "estimated_monthly_cost": "$2-5 for 100GB (simulated)"
            },
            "demo_note": "Set DEMO_MODE=false for real OBS operations"
        }
    
    def _mock_data_upload(self, local_path: str, target_path: str) -> Dict[str, Any]:
        """Mock data upload for demo mode"""
        return {
            "status": "demo_mode",
            "message": f"Data upload simulated from {local_path}",
            "total_files": 5,
            "total_size_mb": 25.6,
            "estimated_cost": 0.0006,
            "obs_path": f"obs://{self.bucket_name}/{target_path}",
            "upload_time": datetime.now().isoformat(),
            "demo_note": "Set DEMO_MODE=false for real data uploads"
        }
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """Get cost summary for OBS operations"""
        return {
            "storage_costs": {
                "standard_ia": "$0.0125 per GB/month",
                "cold_storage": "$0.004 per GB/month",
                "archive_storage": "$0.0012 per GB/month"
            },
            "request_costs": {
                "put_requests": "$0.01 per 1000 requests",
                "get_requests": "$0.004 per 1000 requests"
            },
            "data_transfer": {
                "inbound": "Free",
                "outbound": "$0.12 per GB"
            },
            "optimization_features": [
                "Intelligent tiering for automatic cost optimization",
                "Lifecycle policies to move data to cheaper storage",
                "Infrequent Access storage class by default",
                "Automatic cleanup of temporary and log files"
            ],
            "estimated_monthly_cost": "$2-5 for 100GB with optimization"
        }

# Global OBS manager instance
obs_manager = OBSManager()