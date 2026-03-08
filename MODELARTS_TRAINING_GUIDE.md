# ModelArts Training Job Creation Guide

## 🎯 Step-by-Step Instructions

You're now in the ModelArts console. Follow these steps carefully:

---

## Step 1: Navigate to Training Jobs

1. Look for the left sidebar menu
2. Click on **"Training Management"** or **"Training Jobs"**
3. Click the **"Create Training Job"** button (usually blue, top-right)

---

## Step 2: Basic Information

Fill in these fields:

### Job Name
```
saferoute-training-job
```

### Description (optional)
```
SafeRoute AI crime hotspot prediction model training
```

### Algorithm Source
- Select: **"Custom"** or **"My Algorithm"**
- (NOT "Preset Algorithm" or "Marketplace")

---

## Step 3: Algorithm Configuration

### Code Directory
- Click **"Select"** or **"Browse OBS"**
- Navigate to: `saferoute-ai-data/training-data/`
- Select the folder
- Click **"OK"**

### Boot File (Entry Point)
```
train.py
```
(If you don't have train.py in OBS yet, we'll create it - tell me if you see this issue)

### Python Version
- Select: **Python 3.7** or **Python 3.8** (whichever is available)

### Framework
- Select: **TensorFlow** or **PyTorch** (choose what's available)
- Version: Latest stable version

---

## Step 4: Data Configuration

### Training Data Path
- Click **"Select"** or **"Browse OBS"**
- Navigate to: `saferoute-ai-data/crime-data/`
- Select the folder
- Click **"OK"**

### Training Output Path
- Click **"Select"** or **"Browse OBS"**
- Navigate to: `saferoute-ai-data/models/`
- Select the folder
- Click **"OK"**

---

## Step 5: Resource Configuration (IMPORTANT - Cost Control!)

### Resource Pool
- Select: **"Public Resource Pool"**

### Compute Specifications
- **Type**: CPU (NOT GPU - to save costs)
- **Specification**: 
  - Look for: `2 vCPUs | 8 GB` or similar
  - Or: `modelarts.vm.cpu.2u` if you see that option
  - **AVOID GPU options** - they're expensive!

### Compute Nodes
- **Number of Nodes**: `1`

---

## Step 6: Training Parameters (Optional)

You can add hyperparameters if needed:

```
learning_rate = 0.001
batch_size = 32
epochs = 10
```

(Skip this for now if you're not sure)

---

## Step 7: Running Parameters

### Max Running Time
- Set to: **2 hours** (120 minutes)
- This prevents runaway costs

### Auto-Stop
- Enable: **Yes** ✅
- This stops the job automatically if it exceeds time limit

---

## Step 8: Advanced Settings (Optional)

### Log Path
- Use default or set to: `saferoute-ai-data/logs/`

### Environment Variables (if needed)
```
PYTHONUNBUFFERED=1
```

---

## Step 9: Review and Submit

1. Review all settings
2. Check the **estimated cost** (should be low for CPU)
3. Click **"Submit"** or **"Create"**

---

## ✅ After Submission

You should see:
- Job status: **"Creating"** → **"Running"** → **"Completed"**
- Training logs in real-time
- Progress updates

### Monitor Your Job
1. Click on the job name to see details
2. Check the **"Logs"** tab for training output
3. Wait for completion (may take 30-120 minutes)

---

## ⚠️ Troubleshooting

### Issue: "No train.py file found"
**Solution**: We need to upload a training script first. Tell me if you see this error.

### Issue: "Insufficient permissions"
**Solution**: Check that your IAM role has OBS access (we created `saferoute-modelarts-role`)

### Issue: "Resource quota exceeded"
**Solution**: You may need to request quota increase for your region

### Issue: "Data path not found"
**Solution**: Verify the OBS bucket `saferoute-ai-data` exists and has data in `crime-data/` folder

---

## 💰 Cost Estimate

With CPU instances:
- **Training**: ~$0.50 - $2.00 per hour
- **2 hour max**: ~$1.00 - $4.00 total
- **Well within budget!**

---

## 📞 Need Help?

If you get stuck at any step, tell me:
1. Which step you're on
2. What you see on screen
3. Any error messages

I'll help you through it!

---

**Created**: February 7, 2026  
**For**: SafeRoute AI Training Job Setup
