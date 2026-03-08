"""
Resource Provisioner for Huawei Cloud Infrastructure
Provisions actual, tangible Huawei Cloud resources visible in the console
"""
import os
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass, field, asdict
from enum import Enum
from dotenv import load_dotenv

# Import error recovery components
from error_recovery import (
    ErrorRecoveryManager,
    CircuitBreaker,
    ErrorCategory,
    RecoveryAction,
    HuaweiCloudError,
    AuthenticationError,
    AuthorizationError,
    ResourceCreationError,
    NetworkError,
    ValidationError
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ResourceType(Enum):
    """Types of resources that can be provisioned"""
    OBS_BUCKET = "obs_bucket"
    TRAINING_JOB = "training_job"
    INFERENCE_ENDPOINT = "inference_endpoint"
    VPC = "vpc"
    SUBNET = "subnet"
    SECURITY_GROUP = "security_group"
    IAM_ROLE = "iam_role"
    BUDGET_ALERT = "budget_alert"


class ResourceStatus(Enum):
    """Status of provisioned resources"""
    CREATING = "creating"
    ACTIVE = "active"
    FAILED = "failed"
    DELETING = "deleting"
    DELETED = "deleted"


@dataclass
class ProvisionedResource:
    """Represents a provisioned cloud resource"""
    resource_id: str
    resource_type: ResourceType
    resource_name: str
    region: str
    status: ResourceStatus
    console_url: str
    estimated_cost_usd: float
    created_at: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['resource_type'] = self.resource_type.value
        data['status'] = self.status.value
        return data


@dataclass
class ProvisioningState:
    """Tracks the state of all provisioned resources"""
    resources: List[ProvisionedResource] = field(default_factory=list)
    total_estimated_cost: float = 0.0
    last_updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def add_resource(self, resource: ProvisionedResource):
        """Add a resource to the state"""
        self.resources.append(resource)
        self.total_estimated_cost += resource.estimated_cost_usd
        self.last_updated = datetime.utcnow().isoformat()
    
    def get_resource(self, resource_id: str) -> Optional[ProvisionedResource]:
        """Get a resource by ID"""
        for resource in self.resources:
            if resource.resource_id == resource_id:
                return resource
        return None
    
    def update_resource_status(self, resource_id: str, status: ResourceStatus, error_message: Optional[str] = None):
        """Update the status of a resource"""
        resource = self.get_resource(resource_id)
        if resource:
            resource.status = status
            if error_message:
                resource.error_message = error_message
            self.last_updated = datetime.utcnow().isoformat()
    
    def get_resources_by_type(self, resource_type: ResourceType) -> List[ProvisionedResource]:
        """Get all resources of a specific type"""
        return [r for r in self.resources if r.resource_type == resource_type]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'resources': [r.to_dict() for r in self.resources],
            'total_estimated_cost': self.total_estimated_cost,
            'last_updated': self.last_updated
        }


class ResourceProvisioner:
    """
    Core provisioner for Huawei Cloud resources
    Creates actual infrastructure visible in the Huawei Cloud console
    """
    
    def __init__(self, region: str = "af-south-1", state_file: str = "provisioning_state.json"):
        """
        Initialize the Resource Provisioner
        
        Args:
            region: Huawei Cloud region (default: af-south-1 for Johannesburg)
            state_file: Path to state file for tracking provisioned resources
        """
        self.region = region
        self.state_file = state_file
        
        # Load credentials from environment
        self.ak = os.getenv('HUAWEI_CLOUD_AK')
        self.sk = os.getenv('HUAWEI_CLOUD_SK')
        self.project_id = os.getenv('HUAWEI_CLOUD_PROJECT_ID')
        
        # Initialize state
        self.state = self._load_state()
        
        # Initialize error recovery manager
        self.error_manager = ErrorRecoveryManager(state_file="error_recovery_state.json")
        
        # SDK clients (will be initialized)
        self.obs_client = None
        self.modelarts_client = None
        self.vpc_client = None
        self.iam_client = None
        self.bss_client = None  # Billing Support System client
        
        # Validate credentials and initialize clients
        self._validate_credentials()
        self._initialize_sdk_clients()
        
        logger.info(f"ResourceProvisioner initialized for region: {self.region}")
    
    def _validate_credentials(self) -> bool:
        """
        Validate that all required credentials are present
        
        Returns:
            True if credentials are valid, raises exception otherwise
        
        Raises:
            AuthenticationError: If credentials are missing or invalid
        """
        missing_credentials = []
        
        if not self.ak:
            missing_credentials.append("HUAWEI_CLOUD_AK")
        if not self.sk:
            missing_credentials.append("HUAWEI_CLOUD_SK")
        if not self.project_id:
            missing_credentials.append("HUAWEI_CLOUD_PROJECT_ID")
        
        if missing_credentials:
            error_msg = f"Missing required credentials: {', '.join(missing_credentials)}"
            logger.error(error_msg)
            raise AuthenticationError(error_msg)
        
        # Validate credential format (basic checks)
        if len(self.ak) < 16:
            raise AuthenticationError("HUAWEI_CLOUD_AK appears to be invalid (too short)")
        
        if len(self.sk) < 32:
            raise AuthenticationError("HUAWEI_CLOUD_SK appears to be invalid (too short)")
        
        if len(self.project_id) < 32:
            raise AuthenticationError("HUAWEI_CLOUD_PROJECT_ID appears to be invalid (too short)")
        
        logger.info("✅ Credentials validated successfully")
        return True
    
    def _verify_region(self) -> bool:
        """
        Verify that the specified region is valid and accessible
        
        Returns:
            True if region is valid and accessible
        
        Raises:
            ValueError: If region is invalid or not accessible
        """
        # List of valid Huawei Cloud regions
        valid_regions = [
            "af-south-1",  # Johannesburg (primary for SafeRouteAI)
            "ap-southeast-1",  # Singapore
            "ap-southeast-2",  # Bangkok
            "ap-southeast-3",  # Manila
            "cn-north-1",  # Beijing
            "cn-north-4",  # Beijing
            "cn-east-2",  # Shanghai
            "cn-east-3",  # Shanghai
            "cn-south-1",  # Guangzhou
            "eu-west-0",  # Paris
        ]
        
        if self.region not in valid_regions:
            raise ValueError(f"Invalid region: {self.region}. Valid regions: {valid_regions}")
        
        # Warn if not using af-south-1 for SafeRouteAI
        if self.region != "af-south-1":
            logger.warning(f"⚠️  Using region {self.region} instead of af-south-1 (Johannesburg)")
            logger.warning("   SafeRouteAI is optimized for af-south-1 region")
        
        logger.info(f"✅ Region verified: {self.region}")
        return True
    
    def _initialize_sdk_clients(self):
        """
        Initialize all Huawei Cloud SDK clients
        
        Initializes:
            - OBS client for object storage
            - ModelArts client for AI training and inference
            - VPC client for network infrastructure
            - IAM client for identity and access management
            - BSS client for billing and cost monitoring
        """
        try:
            # Import Huawei Cloud SDKs
            from huaweicloudsdkcore.auth.credentials import BasicCredentials
            from huaweicloudsdkcore.http.http_config import HttpConfig
            from huaweicloudsdkcore.exceptions import exceptions
            
            # Create credentials
            credentials = BasicCredentials(
                ak=self.ak,
                sk=self.sk,
                project_id=self.project_id
            )
            
            # Configure HTTP settings
            http_config = HttpConfig.get_default_config()
            http_config.ignore_ssl_verification = False
            http_config.timeout = (60, 120)  # (connect timeout, read timeout)
            
            # Initialize OBS client
            self._initialize_obs_client(credentials, http_config)
            
            # Initialize ModelArts client
            self._initialize_modelarts_client(credentials, http_config)
            
            # Initialize VPC client
            self._initialize_vpc_client(credentials, http_config)
            
            # Initialize IAM client
            self._initialize_iam_client(credentials, http_config)
            
            # Initialize BSS (Billing) client
            self._initialize_bss_client(credentials, http_config)
            
            # Verify region after client initialization
            self._verify_region()
            
            logger.info("✅ All SDK clients initialized successfully")
            
        except ImportError as e:
            error_msg = f"Failed to import Huawei Cloud SDK: {e}"
            logger.error(error_msg)
            logger.error("Please install required SDKs: pip install huaweicloudsdkcore huaweicloud-sdk-python-v3")
            raise ImportError(error_msg)
        
        except Exception as e:
            error_msg = f"Failed to initialize SDK clients: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def _initialize_obs_client(self, credentials, http_config):
        """Initialize OBS (Object Storage Service) client"""
        try:
            from obs import ObsClient
            
            # OBS client uses different initialization
            self.obs_client = ObsClient(
                access_key_id=self.ak,
                secret_access_key=self.sk,
                server=f'https://obs.{self.region}.myhuaweicloud.com'
            )
            
            logger.info("  📦 OBS client initialized")
            
        except ImportError:
            logger.warning("  ⚠️  OBS SDK not available - install: pip install esdk-obs-python")
            self.obs_client = None
        except Exception as e:
            logger.error(f"  ❌ Failed to initialize OBS client: {e}")
            self.obs_client = None
    
    def _initialize_modelarts_client(self, credentials, http_config):
        """Initialize ModelArts client for AI training and inference"""
        try:
            from huaweicloudsdkmodelarts.v1 import ModelArtsClient
            from huaweicloudsdkmodelarts.v1.region.modelarts_region import ModelArtsRegion
            
            region_obj = ModelArtsRegion.value_of(self.region)
            
            self.modelarts_client = ModelArtsClient.new_builder() \
                .with_credentials(credentials) \
                .with_region(region_obj) \
                .with_http_config(http_config) \
                .build()
            
            logger.info("  🧠 ModelArts client initialized")
            
        except ImportError:
            logger.warning("  ⚠️  ModelArts SDK not available")
            self.modelarts_client = None
        except Exception as e:
            logger.error(f"  ❌ Failed to initialize ModelArts client: {e}")
            self.modelarts_client = None
    
    def _initialize_vpc_client(self, credentials, http_config):
        """Initialize VPC (Virtual Private Cloud) client"""
        try:
            from huaweicloudsdkvpc.v2 import VpcClient
            from huaweicloudsdkvpc.v2.region.vpc_region import VpcRegion
            
            region_obj = VpcRegion.value_of(self.region)
            
            self.vpc_client = VpcClient.new_builder() \
                .with_credentials(credentials) \
                .with_region(region_obj) \
                .with_http_config(http_config) \
                .build()
            
            logger.info("  🌐 VPC client initialized")
            
        except ImportError:
            logger.warning("  ⚠️  VPC SDK not available")
            self.vpc_client = None
        except Exception as e:
            logger.error(f"  ❌ Failed to initialize VPC client: {e}")
            self.vpc_client = None
    
    def _initialize_iam_client(self, credentials, http_config):
        """Initialize IAM (Identity and Access Management) client"""
        try:
            from huaweicloudsdkiam.v3 import IamClient
            from huaweicloudsdkiam.v3.region.iam_region import IamRegion
            
            # IAM is a global service, but we still use region for endpoint
            region_obj = IamRegion.value_of(self.region)
            
            self.iam_client = IamClient.new_builder() \
                .with_credentials(credentials) \
                .with_region(region_obj) \
                .with_http_config(http_config) \
                .build()
            
            logger.info("  🔐 IAM client initialized")
            
        except ImportError:
            logger.warning("  ⚠️  IAM SDK not available")
            self.iam_client = None
        except Exception as e:
            logger.error(f"  ❌ Failed to initialize IAM client: {e}")
            self.iam_client = None
    
    def _initialize_bss_client(self, credentials, http_config):
        """Initialize BSS (Billing Support System) client for cost monitoring"""
        try:
            from huaweicloudsdkbss.v2 import BssClient
            from huaweicloudsdkbss.v2.region.bss_region import BssRegion
            
            # BSS is a global service
            region_obj = BssRegion.value_of(self.region)
            
            self.bss_client = BssClient.new_builder() \
                .with_credentials(credentials) \
                .with_region(region_obj) \
                .with_http_config(http_config) \
                .build()
            
            logger.info("  💰 BSS (Billing) client initialized")
            
        except ImportError:
            logger.warning("  ⚠️  BSS SDK not available")
            self.bss_client = None
        except Exception as e:
            logger.error(f"  ❌ Failed to initialize BSS client: {e}")
            self.bss_client = None
    
    def _load_state(self) -> ProvisioningState:
        """
        Load provisioning state from file
        
        Returns:
            ProvisioningState object with loaded or empty state
        """
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                
                # Reconstruct ProvisionedResource objects
                resources = []
                for r_data in data.get('resources', []):
                    resource = ProvisionedResource(
                        resource_id=r_data['resource_id'],
                        resource_type=ResourceType(r_data['resource_type']),
                        resource_name=r_data['resource_name'],
                        region=r_data['region'],
                        status=ResourceStatus(r_data['status']),
                        console_url=r_data['console_url'],
                        estimated_cost_usd=r_data['estimated_cost_usd'],
                        created_at=r_data['created_at'],
                        metadata=r_data.get('metadata', {}),
                        error_message=r_data.get('error_message')
                    )
                    resources.append(resource)
                
                state = ProvisioningState(
                    resources=resources,
                    total_estimated_cost=data.get('total_estimated_cost', 0.0),
                    last_updated=data.get('last_updated', datetime.utcnow().isoformat())
                )
                
                logger.info(f"📂 Loaded state: {len(resources)} resources, ${state.total_estimated_cost:.2f} total cost")
                return state
                
            except Exception as e:
                logger.error(f"Failed to load state file: {e}")
                logger.info("Starting with empty state")
                return ProvisioningState()
        else:
            logger.info("No existing state file found, starting fresh")
            return ProvisioningState()
    
    def _save_state(self):
        """Save current provisioning state to file"""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state.to_dict(), f, indent=2)
            
            logger.debug(f"💾 State saved to {self.state_file}")
            
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    def get_state_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current provisioning state
        
        Returns:
            Dictionary with state summary
        """
        summary = {
            'total_resources': len(self.state.resources),
            'total_estimated_cost_usd': self.state.total_estimated_cost,
            'last_updated': self.state.last_updated,
            'resources_by_type': {},
            'resources_by_status': {},
            'region': self.region
        }
        
        # Count by type
        for resource_type in ResourceType:
            count = len(self.state.get_resources_by_type(resource_type))
            if count > 0:
                summary['resources_by_type'][resource_type.value] = count
        
        # Count by status
        for status in ResourceStatus:
            count = len([r for r in self.state.resources if r.status == status])
            if count > 0:
                summary['resources_by_status'][status.value] = count
        
        return summary
    
    def get_client_status(self) -> Dict[str, bool]:
        """
        Get the initialization status of all SDK clients
        
        Returns:
            Dictionary mapping client names to their initialization status
        """
        return {
            'obs': self.obs_client is not None,
            'modelarts': self.modelarts_client is not None,
            'vpc': self.vpc_client is not None,
            'iam': self.iam_client is not None,
            'bss': self.bss_client is not None
        }
    
    def validate_setup(self) -> Dict[str, Any]:
        """
        Validate that the provisioner is properly set up
        
        Returns:
            Dictionary with validation results
        """
        validation = {
            'credentials_valid': False,
            'region_valid': False,
            'clients_initialized': {},
            'ready_to_provision': False,
            'issues': []
        }
        
        # Check credentials
        try:
            self._validate_credentials()
            validation['credentials_valid'] = True
        except Exception as e:
            validation['issues'].append(f"Credentials invalid: {e}")
        
        # Check region
        try:
            self._verify_region()
            validation['region_valid'] = True
        except Exception as e:
            validation['issues'].append(f"Region invalid: {e}")
        
        # Check clients
        validation['clients_initialized'] = self.get_client_status()
        
        # Determine if ready to provision
        validation['ready_to_provision'] = (
            validation['credentials_valid'] and
            validation['region_valid'] and
            any(validation['clients_initialized'].values())
        )
        
        return validation
    
    def handle_provisioning_error(self, error: Exception, resource_type: str = None, 
                                  resource_id: str = None) -> Dict[str, Any]:
        """
        Handle provisioning errors with appropriate recovery strategy
        
        Args:
            error: Exception that occurred
            resource_type: Type of resource being provisioned
            resource_id: ID of resource being provisioned
        
        Returns:
            Dictionary with error handling results and recovery strategy
        """
        # Create error context
        error_context = self.error_manager.create_error_context(
            error,
            resource_type=resource_type,
            resource_id=resource_id
        )
        
        # Get recovery strategy
        strategy = self.error_manager.get_recovery_strategy(error_context)
        
        # Log error details
        logger.error(f"❌ Error in {resource_type or 'unknown'}: {error}")
        logger.info(f"📋 Recovery Action: {strategy.action.value}")
        logger.info(f"💬 Message: {strategy.message}")
        
        # Save error state
        self.error_manager.save_error_state({
            'resource_type': resource_type,
            'resource_id': resource_id,
            'recovery_action': strategy.action.value
        })
        
        return {
            'error_context': error_context,
            'recovery_strategy': strategy,
            'should_retry': strategy.retry_allowed,
            'should_rollback': strategy.rollback_required,
            'user_action_required': strategy.action == RecoveryAction.PROMPT_USER
        }
    
    def rollback_resource(self, resource: ProvisionedResource) -> bool:
        """
        Rollback (delete) a single provisioned resource
        
        Args:
            resource: ProvisionedResource to rollback
        
        Returns:
            True if rollback successful, False otherwise
        """
        try:
            logger.info(f"🔄 Rolling back {resource.resource_type.value}: {resource.resource_id}")
            
            # Implement resource-specific deletion logic
            if resource.resource_type == ResourceType.OBS_BUCKET:
                return self._rollback_obs_bucket(resource)
            elif resource.resource_type == ResourceType.TRAINING_JOB:
                return self._rollback_training_job(resource)
            elif resource.resource_type == ResourceType.INFERENCE_ENDPOINT:
                return self._rollback_inference_endpoint(resource)
            elif resource.resource_type == ResourceType.VPC:
                return self._rollback_vpc(resource)
            elif resource.resource_type == ResourceType.SECURITY_GROUP:
                return self._rollback_security_group(resource)
            elif resource.resource_type == ResourceType.IAM_ROLE:
                return self._rollback_iam_role(resource)
            else:
                logger.warning(f"⚠️  No rollback handler for {resource.resource_type.value}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Rollback failed for {resource.resource_id}: {e}")
            return False
    
    def rollback_partial_provisioning(self, start_from_resource: str = None) -> Dict[str, Any]:
        """
        Rollback partially provisioned resources in reverse order
        
        Args:
            start_from_resource: Resource ID to start rollback from (inclusive)
                                If None, rollback all resources
        
        Returns:
            Dictionary with rollback results
        """
        logger.info("🔄 Starting partial provisioning rollback...")
        
        # Get resources to rollback (in reverse order)
        resources_to_rollback = list(reversed(self.state.resources))
        
        # If start_from_resource specified, only rollback from that point
        if start_from_resource:
            start_index = next(
                (i for i, r in enumerate(resources_to_rollback) 
                 if r.resource_id == start_from_resource),
                None
            )
            if start_index is not None:
                resources_to_rollback = resources_to_rollback[start_index:]
        
        rollback_results = {
            'total_resources': len(resources_to_rollback),
            'successful': 0,
            'failed': 0,
            'results': []
        }
        
        # Rollback each resource
        for resource in resources_to_rollback:
            success = self.rollback_resource(resource)
            
            result = {
                'resource_id': resource.resource_id,
                'resource_type': resource.resource_type.value,
                'status': 'deleted' if success else 'failed'
            }
            
            rollback_results['results'].append(result)
            
            if success:
                rollback_results['successful'] += 1
                # Update resource status in state
                self.state.update_resource_status(
                    resource.resource_id,
                    ResourceStatus.DELETED
                )
            else:
                rollback_results['failed'] += 1
        
        # Save updated state
        self._save_state()
        
        logger.info(
            f"✅ Rollback complete: {rollback_results['successful']} successful, "
            f"{rollback_results['failed']} failed"
        )
        
        return rollback_results
    
    def _rollback_obs_bucket(self, resource: ProvisionedResource) -> bool:
        """Rollback OBS bucket (placeholder - will be implemented in task 2.1)"""
        logger.info(f"  Rollback OBS bucket: {resource.resource_id}")
        # TODO: Implement in task 2.1
        return True
    
    def _rollback_training_job(self, resource: ProvisionedResource) -> bool:
        """Rollback training job (placeholder - will be implemented in task 3.2)"""
        logger.info(f"  Rollback training job: {resource.resource_id}")
        # TODO: Implement in task 3.2
        return True
    
    def _rollback_inference_endpoint(self, resource: ProvisionedResource) -> bool:
        """Rollback inference endpoint (placeholder - will be implemented in task 5.2)"""
        logger.info(f"  Rollback inference endpoint: {resource.resource_id}")
        # TODO: Implement in task 5.2
        return True
    
    def _rollback_vpc(self, resource: ProvisionedResource) -> bool:
        """Rollback VPC (placeholder - will be implemented in task 6.1)"""
        logger.info(f"  Rollback VPC: {resource.resource_id}")
        # TODO: Implement in task 6.1
        return True
    
    def _rollback_security_group(self, resource: ProvisionedResource) -> bool:
        """Rollback security group (placeholder - will be implemented in task 6.2)"""
        logger.info(f"  Rollback security group: {resource.resource_id}")
        # TODO: Implement in task 6.2
        return True
    
    def _rollback_iam_role(self, resource: ProvisionedResource) -> bool:
        """Rollback IAM role (placeholder - will be implemented in task 7.1)"""
        logger.info(f"  Rollback IAM role: {resource.resource_id}")
        # TODO: Implement in task 7.1
        return True
    
    def get_error_summary(self) -> Dict[str, Any]:
        """
        Get summary of errors encountered during provisioning
        
        Returns:
            Dictionary with error statistics
        """
        return self.error_manager.get_error_summary()
    
    def get_circuit_breaker_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status of all circuit breakers
        
        Returns:
            Dictionary mapping service names to circuit breaker states
        """
        return {
            name: cb.get_state()
            for name, cb in self.error_manager.circuit_breakers.items()
        }


if __name__ == "__main__":
    # Test initialization
    try:
        provisioner = ResourceProvisioner()
        
        print("\n" + "="*60)
        print("Resource Provisioner Initialization Test")
        print("="*60)
        
        # Print client status
        print("\n📊 SDK Client Status:")
        client_status = provisioner.get_client_status()
        for client_name, is_initialized in client_status.items():
            status_icon = "✅" if is_initialized else "❌"
            print(f"  {status_icon} {client_name.upper()}: {'Initialized' if is_initialized else 'Not Available'}")
        
        # Print state summary
        print("\n📈 Provisioning State Summary:")
        summary = provisioner.get_state_summary()
        print(f"  Total Resources: {summary['total_resources']}")
        print(f"  Total Estimated Cost: ${summary['total_estimated_cost_usd']:.2f}")
        print(f"  Region: {summary['region']}")
        
        if summary['resources_by_type']:
            print("\n  Resources by Type:")
            for resource_type, count in summary['resources_by_type'].items():
                print(f"    - {resource_type}: {count}")
        
        # Validate setup
        print("\n🔍 Setup Validation:")
        validation = provisioner.validate_setup()
        print(f"  Credentials Valid: {'✅' if validation['credentials_valid'] else '❌'}")
        print(f"  Region Valid: {'✅' if validation['region_valid'] else '❌'}")
        print(f"  Ready to Provision: {'✅' if validation['ready_to_provision'] else '❌'}")
        
        if validation['issues']:
            print("\n  ⚠️  Issues Found:")
            for issue in validation['issues']:
                print(f"    - {issue}")
        
        print("\n" + "="*60)
        
    except Exception as e:
        print(f"\n❌ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
