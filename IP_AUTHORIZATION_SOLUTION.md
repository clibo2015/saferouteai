# IP Authorization Issue - Complete Solution

## Problem Summary
Your IP address `192.143.129.78` is not authorized to access Huawei Cloud ModelArts APIs, resulting in error `APIGW.0402`.

## Three Ways to Fix This

### 🚀 Method 1: Whitelist IP in Console (5 minutes)

**Quick Start:**
```bash
python open_console_pages.py
```
This will open all the pages you need in your browser.

**Manual Steps:**
1. Go to: https://console.huaweicloud.com/apigateway
2. Find "Access Control" or "IP Whitelist" section
3. Add IP: `192.143.129.78`
4. Save and wait 5-10 minutes
5. Test: `python create_modelarts_job.py`

**Detailed Guide:** See `FIX_IP_AUTHORIZATION.md`

---

### 📧 Method 2: Support Ticket (24-48 hours)

**If you can't find API Gateway settings:**

1. Go to: https://console.huaweicloud.com/ticket
2. Create ticket with this message:

```
Subject: Whitelist IP for ModelArts API Access

Hello,

I'm getting error APIGW.0402 when accessing ModelArts APIs.

Please whitelist:
- IP: 192.143.129.78
- Project ID: 4b96831b25094c25993949bab01aa216
- Region: af-south-1
- User: clifton15

I need to create training jobs programmatically.

Thank you!
```

3. Wait for support response (usually 24-48 hours)

---

### 🖱️ Method 3: Use Console Manually (Works Now)

**No IP whitelisting needed for console:**

1. Go to: https://console.huaweicloud.com/modelarts/?region=af-south-1#/trainingJobs
2. Click "Create Training Job"
3. Use these settings:
   - Algorithm: TensorFlow 2.1.0
   - Code: /saferoute-ai-data/training-data/
   - Boot: /saferoute-ai-data/training-data/train.py
   - Input: /saferoute-ai-data/crime-data/
   - Output: /saferoute-ai-data/models/
   - **Instance: CPU (2 cores)** ← Saves $4/hour!
   - **Region: cn-north-4** ← Better availability
   - Auto-stop: 30 minutes

**Cost**: ~$0.50/hour (vs $4.72/hour for GPU)

---

## What to Do Right Now

### Option A: Fix IP Issue (Recommended)
```bash
# Open console pages
python open_console_pages.py

# After whitelisting, test it
python create_modelarts_job.py
```

### Option B: Use Mock Services (Works Immediately)
```bash
# Your app is fully functional with mocks
python demo_api_with_mock.py
```

### Option C: Create Job Manually
- Use console (Method 3 above)
- Switch to CPU instances for cost savings
- Try cn-north-4 region (better availability)

---

## Files Created for You

1. **FIX_IP_AUTHORIZATION.md** - Detailed step-by-step guide
2. **QUICK_FIX_GUIDE.md** - Quick 5-minute fix
3. **IP_AUTHORIZATION_SOLUTION.md** - This file
4. **open_console_pages.py** - Opens console pages automatically
5. **check_modelarts_access.py** - Diagnostic tool
6. **create_modelarts_job.py** - Multi-region job creator

---

## Testing After Fix

### Step 1: Verify IP
```bash
python -c "import requests; print(requests.get('https://api.ipify.org').text)"
```
Should show: `192.143.129.78`

### Step 2: Run Diagnostic
```bash
python check_modelarts_access.py
```

### Step 3: Create Training Job
```bash
python create_modelarts_job.py
```

### Expected Success Output:
```
✅ Session created successfully!
✅ Estimator configured!
✅ Training Job Submitted Successfully!
Job Name: saferoute-training-cn-north-4
Region: cn-north-4
Status: Submitted
```

---

## Cost Optimization Tips

### GPU vs CPU Comparison
| Instance Type | Cost/Hour | 1 Hour Cost | Recommendation |
|---------------|-----------|-------------|----------------|
| GPU (gp-vnt1) | $4.72 | $4.72 | ❌ Overkill for small dataset |
| CPU (2 cores) | $0.50-1.00 | $0.75 | ✅ Perfect for your use case |

**Your dataset**: 8.23 KiB (very small)
**Recommendation**: Use CPU - saves 80%

### Region Comparison
| Region | GPU Availability | Cost | Recommendation |
|--------|------------------|------|----------------|
| af-south-1 | ❌ None (7+ hour queue) | High | ❌ Avoid |
| cn-north-4 | ✅ Good | Moderate | ✅ Best choice |
| ap-southeast-3 | ✅ Good | Moderate | ✅ Good alternative |

---

## Troubleshooting

### Issue: Still getting APIGW.0402 after whitelisting
**Solution:**
- Wait 10-15 minutes for propagation
- Check if your IP changed: `python check_modelarts_access.py`
- Try different region: cn-north-4 instead of af-south-1
- Contact support

### Issue: Can't find API Gateway in console
**Solution:**
- Search for "APIG" instead
- Try: https://console.huaweicloud.com/apig
- Submit support ticket (Method 2)

### Issue: Job queues for hours
**Solution:**
- Switch to CPU instances (no queue)
- Try different region (cn-north-4)
- Use mock services for development

### Issue: Your IP keeps changing
**Solution:**
- Whitelist IP range: `192.143.129.0/24`
- Use VPN with static IP
- Run script from cloud VM

---

## Summary

**Your IP**: `192.143.129.78`
**Error**: APIGW.0402 (IP not authorized)

**Quick Fix**: 
1. Run `python open_console_pages.py`
2. Whitelist IP in API Gateway
3. Test with `python create_modelarts_job.py`

**Alternative**: Use mock services (works now!)
```bash
python demo_api_with_mock.py
```

**Cost Tip**: Use CPU instances instead of GPU - saves $4/hour

Your application is fully functional with mock data. You can continue development while waiting for IP whitelisting!
