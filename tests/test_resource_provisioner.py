"""
Unit tests for ResourceProvisioner base class
Tests SDK initialization, credential validation, and state management
"""
import os
import json
import pytest
import tempfile
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add src to path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from resource_provisioner import (
    ResourceProvisioner,
    ResourceType,
    ResourceStatus,
    ProvisionedResource,
    ProvisioningState
)


class TestProvisionedResource:
    """Test ProvisionedResource dataclass"""
    
    def test_create_resource(self):
        """Test creating a provisioned resource"""
        resource = ProvisionedResource(
            resource_id="bucket-123",
            resource_type=ResourceType.OBS_BUCKET,
            resource_name="saferoute-ai-data",
            region="af-south-1",
            status=ResourceStatus.ACTIVE,
            console_url="https://console.huaweicloud.com/obs/bucket-123",
            estimated_cost_usd=5.0,
            created_at=datetime.utcnow().isoformat()
        )
        
        assert resource.resource_id == "bucket-123"
        assert resource.resource_type == ResourceType.OBS_BUCKET
        assert resource.status == ResourceStatus.ACTIVE
        assert resource.estimated_cost_usd == 5.0
    
    def test_resource_to_dict(self):
        """Test converting resource to dictionary"""
        resource = ProvisionedResource(
            resource_id="bucket-123",
            resource_type=ResourceType.OBS_BUCKET,
            resource_name="saferoute-ai-data",
            region="af-south-1",
            status=ResourceStatus.ACTIVE,
            console_url="https://console.huaweicloud.com/obs/bucket-123",
            estimated_cost_usd=5.0,
            created_at=datetime.utcnow().isoformat(),
            metadata={"size": "10GB"}
        )
        
        data = resource.to_dict()
        
        assert data['resource_id'] == "bucket-123"
        assert data['resource_type'] == "obs_bucket"
        assert data['status'] == "active"
        assert data['metadata']['size'] == "10GB"


class TestProvisioningState:
    """Test ProvisioningState management"""
    
    def test_create_empty_state(self):
        """Test creating empty provisioning state"""
        state = ProvisioningState()
        
        assert len(state.resources) == 0
        assert state.total_estimated_cost == 0.0
        assert state.last_updated is not None
    
    def test_add_resource_to_state(self):
        """Test adding a resource to state"""
        state = ProvisioningState()
        
        resource = ProvisionedResource(
            resource_id="bucket-123",
            resource_type=ResourceType.OBS_BUCKET,
            resource_name="saferoute-ai-data",
            region="af-south-1",
            status=ResourceStatus.ACTIVE,
            console_url="https://console.huaweicloud.com/obs/bucket-123",
            estimated_cost_usd=5.0,
            created_at=datetime.utcnow().isoformat()
        )
        
        state.add_resource(resource)
        
        assert len(state.resources) == 1
        assert state.total_estimated_cost == 5.0
    
    def test_get_resource_by_id(self):
        """Test retrieving a resource by ID"""
        state = ProvisioningState()
        
        resource = ProvisionedResource(
            resource_id="bucket-123",
            resource_type=ResourceType.OBS_BUCKET,
            resource_name="saferoute-ai-data",
            region="af-south-1",
            status=ResourceStatus.ACTIVE,
            console_url="https://console.huaweicloud.com/obs/bucket-123",
            estimated_cost_usd=5.0,
            created_at=datetime.utcnow().isoformat()
        )
        
        state.add_resource(resource)
        
        retrieved = state.get_resource("bucket-123")
        assert retrieved is not None
        assert retrieved.resource_id == "bucket-123"
        
        not_found = state.get_resource("nonexistent")
        assert not_found is None
    
    def test_update_resource_status(self):
        """Test updating resource status"""
        state = ProvisioningState()
        
        resource = ProvisionedResource(
            resource_id="bucket-123",
            resource_type=ResourceType.OBS_BUCKET,
            resource_name="saferoute-ai-data",
            region="af-south-1",
            status=ResourceStatus.CREATING,
            console_url="https://console.huaweicloud.com/obs/bucket-123",
            estimated_cost_usd=5.0,
            created_at=datetime.utcnow().isoformat()
        )
        
        state.add_resource(resource)
        state.update_resource_status("bucket-123", ResourceStatus.ACTIVE)
        
        updated = state.get_resource("bucket-123")
        assert updated.status == ResourceStatus.ACTIVE
    
    def test_get_resources_by_type(self):
        """Test filtering resources by type"""
        state = ProvisioningState()
        
        # Add OBS bucket
        bucket = ProvisionedResource(
            resource_id="bucket-123",
            resource_type=ResourceType.OBS_BUCKET,
            resource_name="saferoute-ai-data",
            region="af-south-1",
            status=ResourceStatus.ACTIVE,
            console_url="https://console.huaweicloud.com/obs/bucket-123",
            estimated_cost_usd=5.0,
            created_at=datetime.utcnow().isoformat()
        )
        
        # Add VPC
        vpc = ProvisionedResource(
            resource_id="vpc-456",
            resource_type=ResourceType.VPC,
            resource_name="saferoute-vpc",
            region="af-south-1",
            status=ResourceStatus.ACTIVE,
            console_url="https://console.huaweicloud.com/vpc/vpc-456",
            estimated_cost_usd=0.0,
            created_at=datetime.utcnow().isoformat()
        )
        
        state.add_resource(bucket)
        state.add_resource(vpc)
        
        buckets = state.get_resources_by_type(ResourceType.OBS_BUCKET)
        assert len(buckets) == 1
        assert buckets[0].resource_id == "bucket-123"
        
        vpcs = state.get_resources_by_type(ResourceType.VPC)
        assert len(vpcs) == 1
        assert vpcs[0].resource_id == "vpc-456"


class TestResourceProvisionerCredentials:
    """Test credential validation"""
    
    def test_missing_credentials(self):
        """Test that missing credentials raise ValueError"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Missing required credentials"):
                ResourceProvisioner()
    
    def test_invalid_ak_length(self):
        """Test that short AK raises ValueError"""
        with patch.dict(os.environ, {
            'HUAWEI_CLOUD_AK': 'short',
            'HUAWEI_CLOUD_SK': 'a' * 40,
            'HUAWEI_CLOUD_PROJECT_ID': 'b' * 32
        }):
            with pytest.raises(ValueError, match="AK appears to be invalid"):
                ResourceProvisioner()
    
    def test_invalid_sk_length(self):
        """Test that short SK raises ValueError"""
        with patch.dict(os.environ, {
            'HUAWEI_CLOUD_AK': 'a' * 20,
            'HUAWEI_CLOUD_SK': 'short',
            'HUAWEI_CLOUD_PROJECT_ID': 'b' * 32
        }):
            with pytest.raises(ValueError, match="SK appears to be invalid"):
                ResourceProvisioner()
    
    def test_invalid_project_id_length(self):
        """Test that short project ID raises ValueError"""
        with patch.dict(os.environ, {
            'HUAWEI_CLOUD_AK': 'a' * 20,
            'HUAWEI_CLOUD_SK': 'b' * 40,
            'HUAWEI_CLOUD_PROJECT_ID': 'short'
        }):
            with pytest.raises(ValueError, match="PROJECT_ID appears to be invalid"):
                ResourceProvisioner()
    
    def test_valid_credentials(self):
        """Test that valid credentials pass validation"""
        with patch.dict(os.environ, {
            'HUAWEI_CLOUD_AK': 'a' * 20,
            'HUAWEI_CLOUD_SK': 'b' * 40,
            'HUAWEI_CLOUD_PROJECT_ID': 'c' * 32
        }):
            # Mock SDK imports to avoid actual initialization
            with patch('resource_provisioner.ResourceProvisioner._initialize_sdk_clients'):
                provisioner = ResourceProvisioner()
                assert provisioner.ak == 'a' * 20
                assert provisioner.sk == 'b' * 40
                assert provisioner.project_id == 'c' * 32


class TestResourceProvisionerRegion:
    """Test region verification"""
    
    def test_valid_region_af_south_1(self):
        """Test that af-south-1 is a valid region"""
        with patch.dict(os.environ, {
            'HUAWEI_CLOUD_AK': 'a' * 20,
            'HUAWEI_CLOUD_SK': 'b' * 40,
            'HUAWEI_CLOUD_PROJECT_ID': 'c' * 32
        }):
            with patch('resource_provisioner.ResourceProvisioner._initialize_sdk_clients'):
                provisioner = ResourceProvisioner(region="af-south-1")
                assert provisioner._verify_region() is True
    
    def test_invalid_region(self):
        """Test that invalid region raises ValueError"""
        with patch.dict(os.environ, {
            'HUAWEI_CLOUD_AK': 'a' * 20,
            'HUAWEI_CLOUD_SK': 'b' * 40,
            'HUAWEI_CLOUD_PROJECT_ID': 'c' * 32
        }):
            with patch('resource_provisioner.ResourceProvisioner._initialize_sdk_clients'):
                provisioner = ResourceProvisioner(region="invalid-region")
                with pytest.raises(ValueError, match="Invalid region"):
                    provisioner._verify_region()
    
    def test_warning_for_non_af_south_1(self, caplog):
        """Test that warning is logged for non-af-south-1 regions"""
        with patch.dict(os.environ, {
            'HUAWEI_CLOUD_AK': 'a' * 20,
            'HUAWEI_CLOUD_SK': 'b' * 40,
            'HUAWEI_CLOUD_PROJECT_ID': 'c' * 32
        }):
            with patch('resource_provisioner.ResourceProvisioner._initialize_sdk_clients'):
                provisioner = ResourceProvisioner(region="cn-north-1")
                provisioner._verify_region()
                
                # Check that warning was logged
                assert any("af-south-1" in record.message for record in caplog.records)


class TestResourceProvisionerState:
    """Test state management"""
    
    def test_load_empty_state(self):
        """Test loading state when no file exists"""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = os.path.join(tmpdir, "test_state.json")
            
            with patch.dict(os.environ, {
                'HUAWEI_CLOUD_AK': 'a' * 20,
                'HUAWEI_CLOUD_SK': 'b' * 40,
                'HUAWEI_CLOUD_PROJECT_ID': 'c' * 32
            }):
                with patch('resource_provisioner.ResourceProvisioner._initialize_sdk_clients'):
                    provisioner = ResourceProvisioner(state_file=state_file)
                    
                    assert len(provisioner.state.resources) == 0
                    assert provisioner.state.total_estimated_cost == 0.0
    
    def test_save_and_load_state(self):
        """Test saving and loading state"""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = os.path.join(tmpdir, "test_state.json")
            
            with patch.dict(os.environ, {
                'HUAWEI_CLOUD_AK': 'a' * 20,
                'HUAWEI_CLOUD_SK': 'b' * 40,
                'HUAWEI_CLOUD_PROJECT_ID': 'c' * 32
            }):
                with patch('resource_provisioner.ResourceProvisioner._initialize_sdk_clients'):
                    # Create provisioner and add resource
                    provisioner1 = ResourceProvisioner(state_file=state_file)
                    
                    resource = ProvisionedResource(
                        resource_id="bucket-123",
                        resource_type=ResourceType.OBS_BUCKET,
                        resource_name="saferoute-ai-data",
                        region="af-south-1",
                        status=ResourceStatus.ACTIVE,
                        console_url="https://console.huaweicloud.com/obs/bucket-123",
                        estimated_cost_usd=5.0,
                        created_at=datetime.utcnow().isoformat()
                    )
                    
                    provisioner1.state.add_resource(resource)
                    provisioner1._save_state()
                    
                    # Create new provisioner and load state
                    provisioner2 = ResourceProvisioner(state_file=state_file)
                    
                    assert len(provisioner2.state.resources) == 1
                    assert provisioner2.state.total_estimated_cost == 5.0
                    assert provisioner2.state.resources[0].resource_id == "bucket-123"


class TestResourceProvisionerStatus:
    """Test status and summary methods"""
    
    def test_get_client_status(self):
        """Test getting client initialization status"""
        with patch.dict(os.environ, {
            'HUAWEI_CLOUD_AK': 'a' * 20,
            'HUAWEI_CLOUD_SK': 'b' * 40,
            'HUAWEI_CLOUD_PROJECT_ID': 'c' * 32
        }):
            with patch('resource_provisioner.ResourceProvisioner._initialize_sdk_clients'):
                provisioner = ResourceProvisioner()
                
                # Mock some clients as initialized
                provisioner.obs_client = Mock()
                provisioner.modelarts_client = Mock()
                provisioner.vpc_client = None
                provisioner.iam_client = None
                provisioner.bss_client = None
                
                status = provisioner.get_client_status()
                
                assert status['obs'] is True
                assert status['modelarts'] is True
                assert status['vpc'] is False
                assert status['iam'] is False
                assert status['bss'] is False
    
    def test_get_state_summary(self):
        """Test getting state summary"""
        with patch.dict(os.environ, {
            'HUAWEI_CLOUD_AK': 'a' * 20,
            'HUAWEI_CLOUD_SK': 'b' * 40,
            'HUAWEI_CLOUD_PROJECT_ID': 'c' * 32
        }):
            with patch('resource_provisioner.ResourceProvisioner._initialize_sdk_clients'):
                provisioner = ResourceProvisioner()
                
                # Add some resources
                bucket = ProvisionedResource(
                    resource_id="bucket-123",
                    resource_type=ResourceType.OBS_BUCKET,
                    resource_name="saferoute-ai-data",
                    region="af-south-1",
                    status=ResourceStatus.ACTIVE,
                    console_url="https://console.huaweicloud.com/obs/bucket-123",
                    estimated_cost_usd=5.0,
                    created_at=datetime.utcnow().isoformat()
                )
                
                vpc = ProvisionedResource(
                    resource_id="vpc-456",
                    resource_type=ResourceType.VPC,
                    resource_name="saferoute-vpc",
                    region="af-south-1",
                    status=ResourceStatus.CREATING,
                    console_url="https://console.huaweicloud.com/vpc/vpc-456",
                    estimated_cost_usd=0.0,
                    created_at=datetime.utcnow().isoformat()
                )
                
                provisioner.state.add_resource(bucket)
                provisioner.state.add_resource(vpc)
                
                summary = provisioner.get_state_summary()
                
                assert summary['total_resources'] == 2
                assert summary['total_estimated_cost_usd'] == 5.0
                assert summary['region'] == "af-south-1"
                assert summary['resources_by_type']['obs_bucket'] == 1
                assert summary['resources_by_type']['vpc'] == 1
                assert summary['resources_by_status']['active'] == 1
                assert summary['resources_by_status']['creating'] == 1
    
    def test_validate_setup_success(self):
        """Test setup validation when everything is correct"""
        with patch.dict(os.environ, {
            'HUAWEI_CLOUD_AK': 'a' * 20,
            'HUAWEI_CLOUD_SK': 'b' * 40,
            'HUAWEI_CLOUD_PROJECT_ID': 'c' * 32
        }):
            with patch('resource_provisioner.ResourceProvisioner._initialize_sdk_clients'):
                provisioner = ResourceProvisioner(region="af-south-1")
                
                # Mock at least one client as initialized
                provisioner.obs_client = Mock()
                
                validation = provisioner.validate_setup()
                
                assert validation['credentials_valid'] is True
                assert validation['region_valid'] is True
                assert validation['ready_to_provision'] is True
                assert len(validation['issues']) == 0
    
    def test_validate_setup_failure(self):
        """Test setup validation when credentials are invalid"""
        with patch.dict(os.environ, {
            'HUAWEI_CLOUD_AK': 'short',
            'HUAWEI_CLOUD_SK': 'b' * 40,
            'HUAWEI_CLOUD_PROJECT_ID': 'c' * 32
        }):
            # This should raise during initialization, so we can't test validate_setup
            # Instead, test that initialization fails
            with pytest.raises(ValueError):
                ResourceProvisioner()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
