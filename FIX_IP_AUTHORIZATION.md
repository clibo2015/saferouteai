# How to Fix IP Authorization Issue - Step by Step Guide

## Your Information
- **Your Public IP**: `192.143.129.78`
- **Project ID**: `4b96831b25094c25993949bab01aa216`
- **Region**: af-south-1 (Africa - Johannesburg)

## The Problem
Huawei Cloud's API Gateway is blocking your IP address from accessing ModelArts APIs. Error code: `APIGW.0402`

## Solution: Whitelist Your IP Address

### Method 1: Through API Gateway Console (Recommended)

#### Step 1: Access API Gateway
1. Go to Huawei Cloud Console: https://console.huaweicloud.com
2. Login with your account (clifton15)
3. In the top search bar, type "API Gateway" or "APIG"
4. Click on **API Gateway** service

#### Step 2: Navigate to API Groups
1. In the left sidebar, click **API Groups** or **Dedicated Gateways**
2. Look for the region selector at the top
3. Select **af-south-1** (or the region you want to use)

#### Step 3: Find ModelArts API Group
1. Look for an API group related to ModelArts
   - It might be named: "ModelArts", "modelarts-api", or similar
   - If you don't see it, try switching regions (cn-north-4, ap-southeast-3)
2. Click on the API group name to open its details

#### Step 4: Configure IP Whitelist
1. Look for tabs like:
   - **Access Control**
   - **IP Whitelist**
   - **Security Settings**
   - **ACL Policy**
2. Click on the IP whitelist/access control section
3. Click **Add IP** or **Edit Whitelist**
4. Add your IP: `192.143.129.78`
5. You can also add a CIDR range if your IP changes: `192.143.129.0/24`
6. Click **Save** or **Confirm**

#### Step 5: Wait for Propagation
- Wait 5-10 minutes for the changes to take effect
- The API Gateway needs time to update its rules

#### Step 6: Test the Fix
Run the training job script again:
```bash
python create_modelarts_job.py
```

---

### Method 2: Through IAM Policies (Alternative)

If you can't find API Gateway settings, try IAM:

#### Step 1: Access IAM
1. Go to: https://console.huaweicloud.com/iam
2. Click **Policies** in the left sidebar

#### Step 2: Check ModelArts Permissions
1. Look for policies related to ModelArts
2. Ensure your user (clifton15) has these permissions:
   - `ModelArts FullAccess` or `ModelArts Administrator`
   - `OBS OperateAccess`
   - `VPC FullAccess` (if using VPC)

#### Step 3: Create Custom Policy (if needed)
If ModelArts access is restricted by IP:
1. Click **Create Custom Policy**
2. Name: `ModelArts-IP-Access`
3. Add this JSON (replace with your IP):
```json
{
  "Version": "1.1",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "modelarts:*:*"
      ],
      "Condition": {
        "IpAddress": {
          "g:SourceIp": [
            "192.143.129.78"
          ]
        }
      }
    }
  ]
}
```
4. Attach this policy to your user

---

### Method 3: Contact Huawei Cloud Support (If Above Fails)

#### Step 1: Open Support Ticket
1. Go to: https://console.huaweicloud.com/ticket
2. Click **Create Ticket** or **Submit Request**

#### Step 2: Provide Details
**Subject**: Request to whitelist IP for ModelArts API access

**Description**:
```
Hello,

I am unable to access ModelArts APIs programmatically due to IP authorization restrictions (Error: APIGW.0402).

Please whitelist the following IP address for ModelArts API access:
- IP Address: 192.143.129.78
- Project ID: 4b96831b25094c25993949bab01aa216
- Region: af-south-1
- User: clifton15

I need this access to create training jobs programmatically using the ModelArts SDK.

Thank you.
```

#### Step 3: Wait for Response
- Support typically responds within 24-48 hours
- They will whitelist your IP and notify you

---

### Method 4: Use VPN/Proxy (Quick Workaround)

If you have access to a VPN:

1. **Try Different VPN Locations**:
   - Connect to a VPN server in China (for cn-north-4)
   - Connect to a VPN server in Singapore (for ap-southeast-3)
   - Some VPN IPs might already be whitelisted

2. **Test After Connecting**:
   ```bash
   python create_modelarts_job.py
   ```

3. **Popular VPN Services**:
   - ExpressVPN
   - NordVPN
   - Private Internet Access
   - Corporate VPN (if available)

---

## Verification Steps

After whitelisting your IP, verify it works:

### Step 1: Check Your IP (in case it changed)
```bash
python -c "import requests; print(requests.get('https://api.ipify.org').text)"
```

### Step 2: Run Diagnostic
```bash
python check_modelarts_access.py
```

### Step 3: Create Training Job
```bash
python create_modelarts_job.py
```

### Expected Output (Success)
```
✅ Session created successfully!
✅ Estimator configured!
✅ Training Job Submitted Successfully!
Job Name: saferoute-training-cn-north-4
Region: cn-north-4
Status: Submitted
```

---

## Troubleshooting

### Issue: Can't Find API Gateway in Console
**Solution**: 
- Try searching for "APIG" instead of "API Gateway"
- Check if your account has API Gateway permissions
- Try different regions (some regions might not have API Gateway UI)

### Issue: No ModelArts API Group Found
**Solution**:
- ModelArts might not use API Gateway in your region
- The IP restriction might be at the service level
- Contact support (Method 3 above)

### Issue: IP Whitelist Option Not Available
**Solution**:
- Your account might not have permission to modify API Gateway
- Ask your account administrator to whitelist the IP
- Use Method 3 (contact support)

### Issue: Still Getting APIGW.0402 After Whitelisting
**Solution**:
- Wait 10-15 minutes for propagation
- Clear your DNS cache: `ipconfig /flushdns` (Windows)
- Restart your Python script
- Check if your IP changed: `curl https://api.ipify.org`

### Issue: Your IP Keeps Changing
**Solution**:
- Whitelist an IP range instead of single IP
- Example: `192.143.129.0/24` (allows 192.143.129.0 - 192.143.129.255)
- Use a VPN with static IP
- Use a cloud VM with static IP to run the script

---

## Alternative: Use Console Instead of SDK

If whitelisting is too difficult, you can create training jobs manually:

### Step 1: Go to ModelArts Console
https://console.huaweicloud.com/modelarts/?region=af-south-1#/trainingJobs

### Step 2: Click "Create Training Job"
You already know how to do this from your previous attempt!

### Step 3: Use These Settings (Cost-Optimized)
- **Algorithm**: TensorFlow 2.1.0
- **Code Directory**: /saferoute-ai-data/training-data/
- **Boot File**: /saferoute-ai-data/training-data/train.py
- **Input**: crime=/saferoute-ai-data/crime-data/
- **Output**: model=/saferoute-ai-data/models/
- **Instance**: **CPU (2 cores)** instead of GPU - saves $4/hour!
- **Region**: Try **cn-north-4** or **ap-southeast-3** (better availability)
- **Auto-stop**: 30 minutes (not 1 hour)

### Cost Comparison
- GPU (what you tried): $4.72/hour
- CPU (recommended): $0.50-1.00/hour
- **Savings: 80%**

---

## Recommended Path Forward

### For Immediate Development
```bash
# Use mock services - fully functional, no cloud needed
python demo_api_with_mock.py
```

### For Production (After IP Whitelisted)
```bash
# Create training job programmatically
python create_modelarts_job.py
```

### If IP Whitelisting Fails
1. Use console to create jobs manually
2. Switch to CPU instances to save costs
3. Try different regions (cn-north-4 has better availability)
4. Use mock services for development

---

## Summary

**Your IP**: `192.143.129.78`

**Quick Fix**: Whitelist this IP in API Gateway console

**If That Fails**: Contact Huawei Cloud support or use console manually

**Best Option Now**: Use mock services while waiting for IP whitelist

Your application is fully functional with mock data - you don't need to wait for cloud training to continue development!
