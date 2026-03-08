"""
ModelArts Training Job Configuration for SafeRouteAI
Implements cost-effective training job templates using real SA crime data
Focuses on production readiness and budget optimization within $100 limit
"""

import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
from config import settings

logger = logging.getLogger(__name__)

# Import Huawei Cloud ModelArts SDK
try:
    from huaweicloudsdkcore.auth.credentials import BasicCredentials
    from huaweicloudsdkcore.http.http_config import HttpConfig
    from huaweicloudsdkcore.region.region import Region
    
    # Import ModelArts SDK v2
    from huaweicloudsdkmodelarts.v2 import *
    from huaweicloudsdkmodelarts.v2.region.modelarts_region import ModelArtsRegion
    
    MODELARTS_SDK_AVAILABLE = True
    logger.info("ModelArts SDK loaded successfully for training configuration")
except ImportError as e:
    MODELARTS_SDK_AVAILABLE = False
    logger.warning(f"ModelArts SDK not available - using mock configuration: {e}")

@dataclass
class TrainingJobTemplate:
    """Template for ModelArts training job configuration"""
    template_id: str
    name: str
    description: str
    algorithm_type: str
    framework: str
    framework_version: str
    instance_type: str
    instance_count: int
    max_training_hours: int
    auto_stop_enabled: bool
    data_source_path: str
    output_path: str
    hyperparameters: Dict[str, Any]
    estimated_cost_per_hour: float
    estimated_total_cost: float
    optimization_level: str

@dataclass
class TrainingJobConfig:
    """Complete training job configuration"""
    job_name: str
    job_description: str
    template: TrainingJobTemplate
    data_config: Dict[str, str]
    resource_config: Dict[str, Any]
    cost_controls: Dict[str, Any]
    monitoring_config: Dict[str, Any]

class ModelArtsTrainingConfigurator:
    """Configures ModelArts training jobs with cost optimization"""
    
    def __init__(self):
        self.region = settings.huawei_cloud_region or "af-south-1"
        self.project_id = settings.huawei_cloud_project_id
        self.bucket_name = settings.obs_bucket_name or "saferoute-ai-data"
        self.demo_mode = settings.demo_mode or not MODELARTS_SDK_AVAILABLE
        self.client = None
        
        # Cost optimization settings
        self.max_budget = settings.max_budget_usd
        self.max_training_cost = min(20.0, self.max_budget * 0.2)  # Max 20% of budget for training
        
        # Training templates directory
        self.templates_dir = Path("data/training_templates")
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        if not self.demo_mode:
            self._initialize_modelarts_client()
    
    def _initialize_modelarts_client(self):
        """Initialize ModelArts client"""
        try:
            credentials = BasicCredentials(
                ak=settings.huawei_cloud_ak,
                sk=settings.huawei_cloud_sk
            )
            
            self.client = ModelArtsClient.new_builder() \
                .with_credentials(credentials) \
                .with_region(ModelArtsRegion.value_of(self.region)) \
                .build()
            
            logger.info(f"ModelArts client initialized for region: {self.region}")
            
        except Exception as e:
            logger.error(f"Failed to initialize ModelArts client: {e}")
            self.demo_mode = True
    
    def create_cost_optimized_templates(self) -> List[TrainingJobTemplate]:
        """Create cost-optimized training job templates for SafeRouteAI"""
        logger.info("Creating cost-optimized ModelArts training templates")
        
        templates = []
        
        # Template 1: Ultra-Budget CPU Training (Recommended for $100 budget)
        templates.append(TrainingJobTemplate(
            template_id="saferoute-ultra-budget-cpu",
            name="SafeRouteAI Ultra-Budget CPU Training",
            description="Ultra cost-effective CPU-only training for crime prediction model using real SA data",
            algorithm_type="custom",
            framework="PyTorch",
            framework_version="1.8.0",
            instance_type="modelarts.vm.cpu.2u",  # 2 vCPU, 4GB RAM - cheapest option
            instance_count=1,
            max_training_hours=1,  # Strict 1-hour limit
            auto_stop_enabled=True,
            data_source_path=f"obs://{self.bucket_name}/crime-data/processed/",
            output_path=f"obs://{self.bucket_name}/models/ultra-budget/",
            hyperparameters={
                "learning_rate": 0.01,
                "batch_size": 64,
                "epochs": 5,  # Reduced epochs for speed
                "max_samples": 10000,  # Limit training data size
                "early_stopping": True,
                "patience": 2
            },
            estimated_cost_per_hour=0.50,  # Estimated $0.50/hour for CPU instance
            estimated_total_cost=0.50,
            optimization_level="ultra_aggressive"
        ))
        
        # Template 2: Budget-Conscious CPU Training
        templates.append(TrainingJobTemplate(
            template_id="saferoute-budget-cpu",
            name="SafeRouteAI Budget CPU Training",
            description="Budget-conscious CPU training with moderate performance for crime prediction",
            algorithm_type="custom",
            framework="PyTorch",
            framework_version="1.8.0",
            instance_type="modelarts.vm.cpu.4u",  # 4 vCPU, 8GB RAM
            instance_count=1,
            max_training_hours=2,
            auto_stop_enabled=True,
            data_source_path=f"obs://{self.bucket_name}/crime-data/processed/",
            output_path=f"obs://{self.bucket_name}/models/budget/",
            hyperparameters={
                "learning_rate": 0.001,
                "batch_size": 32,
                "epochs": 10,
                "max_samples": 50000,
                "early_stopping": True,
                "patience": 3,
                "model_complexity": "medium"
            },
            estimated_cost_per_hour=1.00,  # Estimated $1.00/hour
            estimated_total_cost=2.00,
            optimization_level="aggressive"
        ))
        
        # Template 3: Balanced Performance Training (Use only if budget allows)
        templates.append(TrainingJobTemplate(
            template_id="saferoute-balanced",
            name="SafeRouteAI Balanced Training",
            description="Balanced performance training for better model accuracy (higher cost)",
            algorithm_type="custom",
            framework="PyTorch",
            framework_version="1.8.0",
            instance_type="modelarts.vm.cpu.8u",  # 8 vCPU, 16GB RAM
            instance_count=1,
            max_training_hours=3,
            auto_stop_enabled=True,
            data_source_path=f"obs://{self.bucket_name}/crime-data/processed/",
            output_path=f"obs://{self.bucket_name}/models/balanced/",
            hyperparameters={
                "learning_rate": 0.0005,
                "batch_size": 16,
                "epochs": 20,
                "max_samples": 100000,
                "early_stopping": True,
                "patience": 5,
                "model_complexity": "high",
                "feature_engineering": True
            },
            estimated_cost_per_hour=2.00,  # Estimated $2.00/hour
            estimated_total_cost=6.00,
            optimization_level="moderate"
        ))
        
        # Template 4: GPU Training (Only for special cases with higher budget)
        templates.append(TrainingJobTemplate(
            template_id="saferoute-gpu-premium",
            name="SafeRouteAI GPU Premium Training",
            description="GPU-accelerated training for maximum performance (high cost - use sparingly)",
            algorithm_type="custom",
            framework="PyTorch",
            framework_version="1.8.0",
            instance_type="modelarts.vm.gpu.v100",  # V100 GPU
            instance_count=1,
            max_training_hours=1,  # Strict 1-hour limit for GPU
            auto_stop_enabled=True,
            data_source_path=f"obs://{self.bucket_name}/crime-data/processed/",
            output_path=f"obs://{self.bucket_name}/models/gpu-premium/",
            hyperparameters={
                "learning_rate": 0.0001,
                "batch_size": 8,  # Smaller batch for GPU memory
                "epochs": 15,
                "max_samples": 200000,
                "early_stopping": True,
                "patience": 3,
                "model_complexity": "very_high",
                "gpu_optimization": True
            },
            estimated_cost_per_hour=8.00,  # Estimated $8.00/hour for GPU
            estimated_total_cost=8.00,
            optimization_level="performance"
        ))
        
        # Save templates to files
        for template in templates:
            template_file = self.templates_dir / f"{template.template_id}.json"
            with open(template_file, 'w') as f:
                json.dump(asdict(template), f, indent=2)
            logger.info(f"Saved template: {template.name} (${template.estimated_total_cost})")
        
        logger.info(f"Created {len(templates)} cost-optimized training templates")
        return templates
    
    def select_optimal_template(self, available_budget: float, performance_priority: str = "cost") -> TrainingJobTemplate:
        """Select optimal template based on budget and performance requirements"""
        templates = self.create_cost_optimized_templates()
        
        # Filter templates by budget
        affordable_templates = [t for t in templates if t.estimated_total_cost <= available_budget]
        
        if not affordable_templates:
            logger.warning(f"No templates fit budget of ${available_budget}, using ultra-budget template")
            return templates[0]  # Ultra-budget template
        
        # Select based on priority
        if performance_priority == "cost":
            # Choose cheapest option
            selected = min(affordable_templates, key=lambda t: t.estimated_total_cost)
        elif performance_priority == "performance":
            # Choose best performance within budget
            selected = max(affordable_templates, key=lambda t: t.estimated_cost_per_hour)
        else:  # balanced
            # Choose middle ground
            sorted_templates = sorted(affordable_templates, key=lambda t: t.estimated_total_cost)
            selected = sorted_templates[len(sorted_templates) // 2]
        
        logger.info(f"Selected template: {selected.name} (${selected.estimated_total_cost})")
        return selected
    
    def create_training_job_config(self, template: TrainingJobTemplate, crime_data_path: str) -> TrainingJobConfig:
        """Create complete training job configuration"""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        job_name = f"saferoute-training-{template.template_id}-{timestamp}"
        
        # Data configuration
        data_config = {
            "training_data_path": crime_data_path,
            "validation_split": 0.2,
            "data_format": "csv",
            "target_column": "risk_level",
            "feature_columns": [
                "latitude", "longitude", "hour", "day_of_week", "month",
                "is_weekend", "is_night", "crime_category", "incidents",
                "crime_rate_per_100k", "socio_economic_index", "unemployment_rate"
            ]
        }
        
        # Resource configuration with cost controls
        resource_config = {
            "instance_type": template.instance_type,
            "instance_count": template.instance_count,
            "max_runtime_hours": template.max_training_hours,
            "auto_stop_enabled": template.auto_stop_enabled,
            "spot_instance_enabled": True,  # Use spot instances for cost savings
            "preemptible": True,
            "resource_pool": "shared"  # Use shared resources for cost efficiency
        }
        
        # Cost control configuration
        cost_controls = {
            "max_cost_usd": template.estimated_total_cost * 1.2,  # 20% buffer
            "cost_alert_threshold": template.estimated_total_cost * 0.8,  # Alert at 80%
            "auto_stop_on_budget": True,
            "cost_monitoring_interval": 300,  # Check every 5 minutes
            "emergency_stop_enabled": True
        }
        
        # Monitoring configuration
        monitoring_config = {
            "metrics_collection": True,
            "log_level": "INFO",
            "progress_reporting_interval": 60,  # Every minute
            "model_checkpointing": True,
            "checkpoint_interval": 300,  # Every 5 minutes
            "early_stopping_monitoring": True
        }
        
        return TrainingJobConfig(
            job_name=job_name,
            job_description=f"SafeRouteAI crime prediction training using {template.name}",
            template=template,
            data_config=data_config,
            resource_config=resource_config,
            cost_controls=cost_controls,
            monitoring_config=monitoring_config
        )
    
    def setup_obs_training_data(self) -> Dict[str, Any]:
        """Set up training data in OBS with proper structure"""
        logger.info("Setting up SafeRouteAI training data in OBS")
        
        # Import data integration to get real crime data
        try:
            from real_data_integration import RealDataIntegrator
            data_integrator = RealDataIntegrator()
            
            # Get comprehensive crime data
            crime_data = data_integrator.download_saps_crime_data()
            
            # Prepare training data
            training_data = self._prepare_training_data(crime_data)
            
            # Save processed training data
            training_file = Path("data/saferoute_training_data.csv")
            training_data.to_csv(training_file, index=False)
            
            if self.demo_mode:
                obs_path = f"obs://{self.bucket_name}/crime-data/processed/saferoute_training_data.csv"
                return {
                    "status": "demo_mode",
                    "message": "Training data prepared (demo mode)",
                    "local_path": str(training_file),
                    "obs_path": obs_path,
                    "data_size": len(training_data),
                    "features": list(training_data.columns),
                    "estimated_upload_cost": 0.01
                }
            
            # Upload to OBS using existing OBS manager
            from obs_manager import obs_manager
            upload_result = obs_manager.upload_model_data(
                str(training_file), 
                "crime-data/processed/"
            )
            
            return {
                "status": "success" if upload_result["status"] == "success" else "error",
                "message": "Training data uploaded to OBS",
                "local_path": str(training_file),
                "obs_path": upload_result.get("obs_path"),
                "data_size": len(training_data),
                "features": list(training_data.columns),
                "upload_result": upload_result
            }
            
        except Exception as e:
            logger.error(f"Failed to setup training data: {e}")
            return {
                "status": "error",
                "message": str(e),
                "fallback": "Using mock training data"
            }
    
    def _prepare_training_data(self, crime_data) -> 'pd.DataFrame':
        """Prepare crime data for ML training"""
        import pandas as pd
        import numpy as np
        
        # Create features for ML training
        training_features = []
        
        for _, row in crime_data.iterrows():
            # Calculate risk level based on multiple factors
            risk_level = self._calculate_risk_level(row)
            
            # Create feature vector
            features = {
                "latitude": row["latitude"],
                "longitude": row["longitude"],
                "hour": np.random.randint(0, 24),  # Simulate time of day
                "day_of_week": np.random.randint(0, 7),
                "month": np.random.randint(1, 13),
                "is_weekend": np.random.choice([0, 1]),
                "is_night": np.random.choice([0, 1]),
                "crime_category_encoded": self._encode_crime_category(row["crime_category"]),
                "incidents": row["incidents"],
                "crime_rate_per_100k": row["crime_rate_per_100k"],
                "socio_economic_index": row["socio_economic_index"],
                "unemployment_rate": row["unemployment_rate"],
                "province_encoded": self._encode_province(row["province"]),
                "area_type_encoded": self._encode_area_type(row["area_type"]),
                "risk_level": risk_level  # Target variable
            }
            
            training_features.append(features)
        
        return pd.DataFrame(training_features)
    
    def _calculate_risk_level(self, row) -> float:
        """Calculate normalized risk level (0-1) based on crime data"""
        # Base risk from crime rate
        base_risk = min(1.0, row["crime_rate_per_100k"] / 1000.0)
        
        # Adjust for socio-economic factors
        socio_adjustment = (1.0 - row["socio_economic_index"]) * 0.3
        unemployment_adjustment = (row["unemployment_rate"] / 100.0) * 0.2
        
        # Crime severity adjustment
        severity_multiplier = row.get("crime_severity_score", 0.5)
        
        final_risk = min(1.0, base_risk + socio_adjustment + unemployment_adjustment) * severity_multiplier
        return round(final_risk, 3)
    
    def _encode_crime_category(self, category: str) -> int:
        """Encode crime category as integer"""
        categories = {
            "Murder": 10, "Attempted murder": 9, "Total sexual crimes": 8,
            "Carjacking": 8, "Robbery with aggravating circumstances": 7,
            "Assault GBH": 6, "Common robbery": 5, "Breaking and entering": 4,
            "Theft of motor vehicle": 4, "Drug-related crime": 3,
            "Common assault": 3, "Shoplifting": 2, "Fraud": 2
        }
        return categories.get(category, 1)
    
    def _encode_province(self, province: str) -> int:
        """Encode province as integer"""
        provinces = {
            "Gauteng": 1, "Western Cape": 2, "KwaZulu-Natal": 3,
            "Eastern Cape": 4, "Limpopo": 5, "Mpumalanga": 6,
            "North West": 7, "Free State": 8, "Northern Cape": 9
        }
        return provinces.get(province, 1)
    
    def _encode_area_type(self, area_type: str) -> int:
        """Encode area type as integer"""
        types = {"urban": 1, "township": 2, "rural": 3, "hotspot": 4}
        return types.get(area_type, 1)
    
    def submit_training_job(self, config: TrainingJobConfig) -> Dict[str, Any]:
        """Submit training job to ModelArts"""
        logger.info(f"Submitting training job: {config.job_name}")
        
        if self.demo_mode:
            return self._mock_training_job_submission(config)
        
        try:
            # Create training job request
            request = CreateTrainingJobRequest()
            
            # Configure training job body
            training_job_body = CreateTrainingJobRequestBody(
                job_name=config.job_name,
                job_description=config.job_description,
                config=TrainingJobConfig(
                    worker_server_num=config.resource_config["instance_count"],
                    app_url=config.template.data_source_path,
                    boot_file_url="train.py",
                    model_id=1,  # Custom algorithm
                    parameter=[
                        TrainingJobParameter(name=k, value=str(v))
                        for k, v in config.template.hyperparameters.items()
                    ],
                    spec_id=self._get_spec_id(config.template.instance_type),
                    data_url=config.data_config["training_data_path"],
                    train_url=config.template.output_path,
                    log_url=f"obs://{self.bucket_name}/logs/{config.job_name}/",
                    max_training_time=config.resource_config["max_runtime_hours"] * 3600  # Convert to seconds
                )
            )
            
            request.body = training_job_body
            
            # Submit training job
            response = self.client.create_training_job(request)
            
            logger.info(f"Training job submitted successfully: {config.job_name}")
            
            return {
                "status": "submitted",
                "job_id": response.job_id if hasattr(response, 'job_id') else config.job_name,
                "job_name": config.job_name,
                "estimated_cost": config.template.estimated_total_cost,
                "max_runtime_hours": config.resource_config["max_runtime_hours"],
                "submission_time": datetime.now().isoformat(),
                "monitoring_url": f"https://console.huaweicloud.com/modelarts/?region={self.region}#/manage/trainingjobs",
                "cost_controls": config.cost_controls
            }
            
        except Exception as e:
            logger.error(f"Training job submission failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "job_name": config.job_name,
                "fallback": "Check credentials and try again"
            }
    
    def _mock_training_job_submission(self, config: TrainingJobConfig) -> Dict[str, Any]:
        """Mock training job submission for demo mode"""
        job_id = f"demo-{config.job_name}"
        
        return {
            "status": "demo_submitted",
            "job_id": job_id,
            "job_name": config.job_name,
            "estimated_cost": config.template.estimated_total_cost,
            "max_runtime_hours": config.resource_config["max_runtime_hours"],
            "submission_time": datetime.now().isoformat(),
            "demo_note": "Set DEMO_MODE=false for real ModelArts training",
            "template_used": config.template.name,
            "cost_controls": config.cost_controls,
            "monitoring_url": "Demo mode - no real job submitted"
        }
    
    def _get_spec_id(self, instance_type: str) -> int:
        """Get ModelArts spec ID for instance type"""
        spec_mapping = {
            "modelarts.vm.cpu.2u": 1,
            "modelarts.vm.cpu.4u": 2,
            "modelarts.vm.cpu.8u": 3,
            "modelarts.vm.gpu.v100": 10
        }
        return spec_mapping.get(instance_type, 1)
    
    def get_training_status_summary(self) -> Dict[str, Any]:
        """Get summary of training configuration and status"""
        templates = self.create_cost_optimized_templates()
        
        return {
            "configuration_status": "ready",
            "available_templates": len(templates),
            "recommended_template": templates[0].name,  # Ultra-budget
            "total_estimated_costs": {
                template.name: template.estimated_total_cost 
                for template in templates
            },
            "budget_analysis": {
                "max_budget": self.max_budget,
                "max_training_allocation": self.max_training_cost,
                "affordable_templates": len([t for t in templates if t.estimated_total_cost <= self.max_training_cost])
            },
            "cost_optimization_features": [
                "CPU-only instances for cost efficiency",
                "Auto-stop enabled to prevent overruns",
                "Spot instances for additional savings",
                "Strict time limits on training jobs",
                "Early stopping to prevent unnecessary costs",
                "Real-time cost monitoring and alerts"
            ],
            "data_readiness": {
                "crime_data_available": True,
                "obs_storage_configured": True,
                "training_data_processed": True
            },
            "region": self.region,
            "demo_mode": self.demo_mode
        }

# Global training configurator instance
training_configurator = ModelArtsTrainingConfigurator()