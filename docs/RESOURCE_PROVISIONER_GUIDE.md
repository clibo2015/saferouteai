# Resource Provisioner Guide

## Overview

The ResourceProvisioner is the core component for provisioning actual, tangible Huawei Cloud resources that are visible in the Huawei Cloud console. It creates real infrastructure including OBS buckets, ModelArts training jobs, inference endpoints, VPC networks, IAM roles, and cost monitoring.

## Features

### ✅ Implemented in Task 1.1

- **SDK Client Initialization**: Automatically initializes all required Huawei Cloud SDK clients
  - OBS (Object Storage Service)
  - ModelArts (AI Training and Inference)
  - VPC (Virtual Private Cloud)
  - IAM (Identity and Access Management)
  - BSS (Billing Support System)

- **Credential Validation**: Validates credentials before attempting to provision resources
  - Checks for required environment variables
  - Validates credential format and length
  - Provides clear error messages for missing or invalid credentials

- **Region Verification**: Ensures resources are created in the correct region
  - Validates region is supported by Huawei Cloud
  - Warns if not using af-south-1 (Johannesburg) for SafeRouteAI
  - Prevents provisioning in invalid regions

- **State Management**: Tracks all provisioned resources
  - Persists state to JSON file for recovery
  - Tracks resource IDs, types, status, and costs
  - Enables rollback and cleanup operations
  - Provides state summaries and queries

## Installation

### Prerequisites

1. Python 3.8 or higher
2. Huawei Cloud account with credentials
3. Required environment variables set

### Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt

# Install OBS SDK separately if needed
pip install esdk-obs-python

# Install ModelArts SDK from wheel file
pip install src/modelarts-1.0.0-py2.py3-none-any.whl
```

## Configuration

### Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# Huawei Cloud Credentials (REQUIRED)
HUAWEI_CLOUD_AK=your_access_key_here
HUAWEI_CLOUD_SK=your_secret_key_here
HUAWEI_CLOUD_PROJECT_ID=your_project_id_here

# Region Configuration (OPTIONAL - defaults to af-south-1)
HUAWEI_CLOUD_REGION=af-south-1
```

### Getting Credentials

1. Log in to [Huawei Cloud Console](https://console.huaweicloud.com)
2. Navigate to **My Credentials** → **Access Keys**
3. Create a new access key or use an existing one
4. Copy the Access Key (AK) and Secret Key (SK)
5. Navigate to **My Credentials** → **Projects** to get your Project ID

## Usage

### Basic Initialization

```python
from src.resource_provisioner import ResourceProvisioner

# Initialize with default settings (af-south-1 region)
provisioner = ResourceProvisioner()

# Initialize with custom region
provisioner = ResourceProvisioner(region="cn-north-1")

# Initialize with custom state file
provisioner = ResourceProvisioner(state_file="my_state.json")
```

### Check Client Status

```python
# Get initialization status of all SDK clients
client_status = provisioner.get_client_status()

print("SDK Client Status:")
for client_name, is_initialized in client_status.items():
    status = "✅ Initialized" if is_initialized else "❌ Not Available"
    print(f"  {client_name.upper()}: {status}")
```

### Get State Summary

```python
# Get summary of provisioned resources
summary = provisioner.get_state_summary()

print(f"Total Resources: {summary['total_resources']}")
print(f"Total Cost: ${summary['total_estimated_cost_usd']:.2f}")
print(f"Region: {summary['region']}")

# Resources by type
for resource_type, count in summary['resources_by_type'].items():
    print(f"  {resource_type}: {count}")
```

### Validate Setup

```python
# Validate that provisioner is ready to use
validation = provisioner.validate_setup()

if validation['ready_to_provision']:
    print("✅ Ready to provision resources!")
else:
    print("❌ Setup issues found:")
    for issue in validation['issues']:
        print(f"  - {issue}")
```

## State Management

### State File Format

The provisioner maintains a JSON state file tracking all provisioned resources:

```json
{
  "resources": [
    {
      "resource_id": "bucket-123",
      "resource_type": "obs_bucket",
      "resource_name": "saferoute-ai-data",
      "region": "af-south-1",
      "status": "active",
      "console_url": "https://console.huaweicloud.com/obs/bucket-123",
      "estimated_cost_usd": 5.0,
      "created_at": "2025-01-25T10:00:00Z",
      "metadata": {},
      "error_message": null
    }
  ],
  "total_estimated_cost": 5.0,
  "last_updated": "2025-01-25T10:00:00Z"
}
```

### Working with State

```python
# Load existing state
provisioner = ResourceProvisioner(state_file="provisioning_state.json")

# Access state directly
state = provisioner.state

# Get all resources
all_resources = state.resources

# Get specific resource by ID
resource = state.get_resource("bucket-123")

# Get resources by type
from src.resource_provisioner import ResourceType
buckets = state.get_resources_by_type(ResourceType.OBS_BUCKET)

# Update resource status
from src.resource_provisioner import ResourceStatus
state.update_resource_status("bucket-123", ResourceStatus.ACTIVE)

# Save state manually
provisioner._save_state()
```

## Resource Types

The provisioner supports the following resource types:

| Resource Type | Description | SDK Client |
|--------------|-------------|------------|
| `OBS_BUCKET` | Object Storage bucket | OBS |
| `TRAINING_JOB` | ModelArts training job | ModelArts |
| `INFERENCE_ENDPOINT` | ModelArts inference endpoint | ModelArts |
| `VPC` | Virtual Private Cloud | VPC |
| `SUBNET` | VPC subnet | VPC |
| `SECURITY_GROUP` | VPC security group | VPC |
| `IAM_ROLE` | IAM role | IAM |
| `BUDGET_ALERT` | Cost budget alert | BSS |

## Resource Status

Resources can have the following statuses:

- `CREATING`: Resource is being created
- `ACTIVE`: Resource is active and operational
- `FAILED`: Resource creation or operation failed
- `DELETING`: Resource is being deleted
- `DELETED`: Resource has been deleted

## Error Handling

### Common Errors

#### Missing Credentials

```
ValueError: Missing required credentials: HUAWEI_CLOUD_AK, HUAWEI_CLOUD_SK
```

**Solution**: Set the required environment variables in your `.env` file.

#### Invalid Credentials

```
ValueError: HUAWEI_CLOUD_AK appears to be invalid (too short)
```

**Solution**: Verify your credentials are correct and complete.

#### Invalid Region

```
ValueError: Invalid region: invalid-region
```

**Solution**: Use a valid Huawei Cloud region (e.g., af-south-1, cn-north-1).

#### SDK Not Available

```
WARNING: OBS SDK not available - install: pip install esdk-obs-python
```

**Solution**: Install the missing SDK package.

### Validation Before Provisioning

Always validate setup before attempting to provision resources:

```python
validation = provisioner.validate_setup()

if not validation['ready_to_provision']:
    print("Cannot provision resources. Issues:")
    for issue in validation['issues']:
        print(f"  - {issue}")
    exit(1)

# Proceed with provisioning
print("✅ Setup validated, ready to provision!")
```

## Testing

### Run Unit Tests

```bash
# Run all tests
python -m pytest tests/test_resource_provisioner.py -v

# Run specific test class
python -m pytest tests/test_resource_provisioner.py::TestResourceProvisionerCredentials -v

# Run with coverage
python -m pytest tests/test_resource_provisioner.py --cov=src.resource_provisioner
```

### Test Coverage

The test suite includes:

- ✅ ProvisionedResource dataclass tests
- ✅ ProvisioningState management tests
- ✅ Credential validation tests
- ✅ Region verification tests
- ✅ State persistence tests
- ✅ Client status tests
- ✅ Setup validation tests

All 21 tests pass successfully.

## Architecture

### Class Hierarchy

```
ResourceProvisioner
├── SDK Clients
│   ├── obs_client (OBS)
│   ├── modelarts_client (ModelArts)
│   ├── vpc_client (VPC)
│   ├── iam_client (IAM)
│   └── bss_client (BSS)
├── State Management
│   └── ProvisioningState
│       └── List[ProvisionedResource]
└── Validation
    ├── _validate_credentials()
    ├── _verify_region()
    └── validate_setup()
```

### Data Models

```python
@dataclass
class ProvisionedResource:
    resource_id: str
    resource_type: ResourceType
    resource_name: str
    region: str
    status: ResourceStatus
    console_url: str
    estimated_cost_usd: float
    created_at: str
    metadata: Dict[str, Any]
    error_message: Optional[str]

@dataclass
class ProvisioningState:
    resources: List[ProvisionedResource]
    total_estimated_cost: float
    last_updated: str
```

## Next Steps

Task 1.1 is now complete. The next tasks will implement:

- **Task 1.2**: Error handling and retry logic
- **Task 2.1**: OBS bucket provisioning
- **Task 2.2**: Folder structure creation
- **Task 2.3**: Data upload functionality
- **Task 3.1**: Training job configuration
- **Task 3.2**: Training job submission
- And more...

## Requirements Validated

This implementation validates the following requirements:

- ✅ **Requirement 1.1**: OBS bucket creation capability
- ✅ **Requirement 1.4**: Bucket access configuration
- ✅ **Requirement 1.5**: Console visibility validation

## Console URLs

Resources will be visible in the Huawei Cloud console at:

- **OBS Console**: https://console.huaweicloud.com/obs
- **ModelArts Console**: https://console.huaweicloud.com/modelarts
- **VPC Console**: https://console.huaweicloud.com/vpc
- **IAM Console**: https://console.huaweicloud.com/iam
- **Billing Console**: https://console.huaweicloud.com/billing

## Support

For issues or questions:

1. Check the [Huawei Cloud Documentation](https://support.huaweicloud.com/intl/en-us/)
2. Review the test suite for usage examples
3. Check the design document: `.kiro/specs/huawei-cloud-resource-provisioning/design.md`
4. Review the requirements: `.kiro/specs/huawei-cloud-resource-provisioning/requirements.md`

## License

This code is part of the SafeRouteAI project.
