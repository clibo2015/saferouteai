# Huawei Cloud Resources Provisioned

## ✅ Successfully Created Resources

**Date**: February 7, 2026  
**Region**: af-south-1 (Africa - Johannesburg)  
**Total Cost**: $5.00/month

---

## 📦 Resources Created

### 1. OBS Bucket ✅
- **Name**: saferoute-ai-data
- **Status**: Active
- **Storage Class**: STANDARD
- **Region**: af-south-1
- **Cost**: ~$5/month
- **Console URL**: https://console.huaweicloud.com/obs/?region=af-south-1#/obs/manager/saferoute-ai-data

**Data Uploaded**:
- ✅ Crime data uploaded to `crime-data/` folder
- ✅ Folder structure created (crime-data/, models/, training-data/, inference-models/, logs/)

### 2. VPC (Virtual Private Cloud) ✅
- **Name**: saferoute-vpc
- **Status**: Active
- **CIDR Block**: 192.168.0.0/16
- **Region**: af-south-1
- **Cost**: Free
- **Console URL**: https://console.huaweicloud.com/vpc/?region=af-south-1#/vpcs

### 3. IAM Role ✅
- **Name**: saferoute-modelarts-role
- **Status**: Active
- **Purpose**: ModelArts service role with OBS access
- **Permissions**: OBS read/write
- **Cost**: Free
- **Console URL**: https://console.huaweicloud.com/iam/?region=af-south-1#/iam/roles

### 4. Budget Alert ✅
- **Name**: saferoute-budget
- **Status**: Active
- **Budget Limit**: $100
- **Alert Thresholds**: 50%, 75%, 90%
- **Cost**: Free
- **Console URL**: https://console.huaweicloud.com/billing/?region=af-south-1#/budgets

---

## ⚠️ Resources NOT Created (SDK Compatibility Issues)

### ModelArts Training Job ❌
- **Status**: Not created
- **Reason**: ModelArts SDK version incompatibility
- **Issue**: The `modelarts` package (v1.5.0) uses a different API than the Huawei Cloud SDK v3 pattern
- **Solution Options**:
  1. Use ModelArts REST API directly
  2. Create training job manually via console
  3. Use the older modelarts SDK API (needs code update)

### Inference Endpoint ❌
- **Status**: Not created
- **Reason**: Depends on training job completion
- **Impact**: Cannot deploy AI model for predictions yet

### Pangu Model ❌
- **Status**: Not applicable
- **Note**: Pangu is a pre-trained model service accessed via API, not a provisioned resource
- **Alternative**: Can be used once ModelArts integration is working

---

## 🔍 How to Verify Resources

### Check OBS Bucket
1. Go to: https://console.huaweicloud.com/obs/?region=af-south-1
2. Look for bucket: `saferoute-ai-data`
3. Check folders: crime-data/, models/, training-data/, inference-models/, logs/
4. Verify crime data file is uploaded

### Check VPC
1. Go to: https://console.huaweicloud.com/vpc/?region=af-south-1
2. Look for VPC: `saferoute-vpc`
3. Verify CIDR block: 192.168.0.0/16

### Check IAM Role
1. Go to: https://console.huaweicloud.com/iam/?region=af-south-1
2. Navigate to Roles
3. Look for: `saferoute-modelarts-role`
4. Verify OBS permissions are attached

### Check Budget
1. Go to: https://console.huaweicloud.com/billing/?region=af-south-1
2. Navigate to Budgets
3. Look for: `saferoute-budget`
4. Verify $100 limit and alert thresholds

---

## 📊 Current Status Summary

| Resource Type | Status | Visible in Console | Cost |
|--------------|--------|-------------------|------|
| OBS Bucket | ✅ Created | Yes | $5/month |
| VPC | ✅ Created | Yes | Free |
| IAM Role | ✅ Created | Yes | Free |
| Budget Alert | ✅ Created | Yes | Free |
| Training Job | ❌ Not Created | No | N/A |
| Inference Endpoint | ❌ Not Created | No | N/A |
| **TOTAL** | **4/6 Created** | **4 Visible** | **$5/month** |

---

## 🚀 Next Steps to Create Training Jobs

### Option 1: Manual Creation via Console (Recommended)

1. **Go to ModelArts Console**:
   - URL: https://console.huaweicloud.com/modelarts/?region=af-south-1

2. **Create Training Job**:
   - Click "Training Jobs" → "Create Training Job"
   - Name: `saferoute-training-job`
   - Algorithm Source: Custom
   - Data Source: OBS bucket `saferoute-ai-data/crime-data/`
   - Output Path: `saferoute-ai-data/models/`
   - Resource Type: CPU (modelarts.vm.cpu.2u)
   - Max Training Time: 2 hours
   - Click "Submit"

3. **Monitor Training**:
   - Wait for training to complete (may take 30-120 minutes)
   - Check logs in ModelArts console
   - Verify model output in OBS bucket

4. **Deploy Inference Endpoint**:
   - Once training completes, go to "Model Management"
   - Select your trained model
   - Click "Deploy" → "Real-time Services"
   - Name: `saferoute-endpoint`
   - Instance Type: CPU (modelarts.vm.cpu.1u)
   - Min Instances: 1, Max Instances: 2
   - Click "Deploy"

### Option 2: Use ModelArts REST API

The provisioning script can be updated to use REST API calls instead of SDK:

```python
import requests

# ModelArts API endpoint
api_url = f"https://modelarts.{region}.myhuaweicloud.com/v1/{project_id}/training-jobs"

# Create training job via REST API
headers = {
    "X-Auth-Token": auth_token,
    "Content-Type": "application/json"
}

training_job_data = {
    "job_name": "saferoute-training-job",
    "job_desc": "SafeRoute AI training job",
    "config": {
        "worker_server_num": 1,
        "app_url": f"/saferoute-ai-data/training-data/",
        "boot_file_url": f"/saferoute-ai-data/training-data/train.py",
        "data_url": f"/saferoute-ai-data/crime-data/",
        "train_url": f"/saferoute-ai-data/models/",
        "spec_id": "modelarts.vm.cpu.2u"
    }
}

response = requests.post(api_url, headers=headers, json=training_job_data)
```

### Option 3: Update SDK Code

Update `src/resource_provisioner.py` to use the `modelarts` package API directly instead of the Huawei Cloud SDK v3 pattern.

---

## 💡 Important Notes

1. **OBS Bucket is Live**: Your data is now stored in Huawei Cloud and will incur storage costs (~$5/month)

2. **Budget Alerts Active**: You'll receive email notifications at 50%, 75%, and 90% of $100 budget

3. **VPC and IAM are Free**: These resources don't incur charges

4. **ModelArts Requires Manual Setup**: Due to SDK compatibility issues, training jobs need to be created manually or via REST API

5. **Region Locked**: All resources are in af-south-1 (Africa - Johannesburg) as specified

---

## 📞 Troubleshooting

### If you don't see resources in console:

1. **Check Region**: Make sure you're viewing af-south-1 region in console
2. **Refresh**: Try refreshing the console page
3. **Permissions**: Verify your account has permission to view these resources
4. **Wait**: Some resources may take a few minutes to appear

### To clean up resources:

```bash
python provision_resources.py cleanup
```

This will delete all provisioned resources and stop billing.

---

**Last Updated**: February 7, 2026  
**Provisioning Script**: provision_resources.py  
**Results File**: provisioning_results_20260207_223736.json
