# 🚀 SafeRouteAI - Huawei Cloud Production Setup Guide

**Maximize Your $100 Coupon Value**

## 📋 Quick Start Checklist

- [ ] Create Huawei Cloud account in af-south-1 region
- [ ] Apply $100 coupon and set billing alerts
- [ ] Generate Access Key (AK) and Secret Key (SK)
- [ ] Run setup script: `python setup_huawei_cloud.py`
- [ ] Test connection: `python test_connection.py`
- [ ] Monitor costs: `python monitor_costs.py`

## 🎯 Phase 1: Account Setup (15 minutes)

### Step 1: Create Huawei Cloud Account

1. **Visit Huawei Cloud Console**
   - Go to: https://console.huaweicloud.com
   - Click "Register" if you don't have an account

2. **Select South African Region**
   - **Important**: Choose **Africa-Johannesburg (af-south-1)**
   - This ensures data locality and compliance

3. **Complete Account Verification**
   - Provide South African phone number
   - Verify email address
   - Complete identity verification

### Step 2: Apply Your $100 Coupon

1. **Navigate to Billing**
   - Go to "Billing & Costs" → "Coupons"
   - Click "Apply Coupon"
   - Enter your $100 coupon code

2. **Set Up Cost Alerts**
   - Go to "Billing & Costs" → "Budget Management"
   - Create budget alerts at:
     - $50 (50% threshold)
     - $75 (75% threshold) 
     - $90 (90% threshold)

### Step 3: Generate Access Credentials

1. **Create Access Keys**
   - Go to "My Credentials" → "Access Keys"
   - Click "Create Access Key"
   - **Save both AK and SK securely**

2. **Note Your Project ID**
   - Find Project ID in the project dropdown
   - Usually looks like: `0123456789abcdef0123456789abcdef`

## 🔧 Phase 2: Local Configuration (10 minutes)

### Step 1: Run Setup Script

```bash
# Run the interactive setup script
python setup_huawei_cloud.py
```

This script will:
- Guide you through credential entry
- Create/update your `.env` file
- Provide cost optimization tips
- Show next steps

### Step 2: Verify Configuration

```bash
# Test your Huawei Cloud connection
python test_connection.py

# Monitor your costs
python monitor_costs.py
```

## 💰 Cost Optimization Strategy

### Service Cost Breakdown (AF-Johannesburg Region)

| Service | Cost Range | Optimization Tips |
|---------|------------|-------------------|
| **ECS App Hosting** | $8-15/month | Use s6.large.2, enable auto-scaling |
| **ModelArts Training** | $0.08/hour | Use CPU instances, 2-hour job limits |
| **ModelArts Inference** | $0.08/hour | Auto-scale to zero when idle |
| **OBS Storage (100GB)** | $1-3/month | Use lifecycle policies, free tier |
| **Data Transfer** | $1-3/month | Cache responses, minimize API calls |
| **Monitoring & Misc** | $2-5/month | Essential logging and alerts |

**Total Budget**: $100 = **3-4 months** of production operation

### Budget Maximization Tips

1. **Start Small, Scale Up**
   - Begin with minimal resources
   - Monitor performance and scale as needed
   - Use auto-scaling to handle traffic spikes

2. **Optimize Training Jobs**
   - Use CPU instances for initial training
   - Schedule jobs during off-peak hours (if available)
   - Implement early stopping to avoid overtraining

3. **Smart Data Management**
   - Use OBS lifecycle policies to archive old data
   - Compress data before uploading
   - Delete temporary files regularly

4. **Monitor Daily**
   - Check spending every day
   - Set up automated alerts
   - Review service usage patterns

## 🏗️ Phase 3: Service Configuration

### Required Services Setup

1. **ECS (Elastic Cloud Server)** - App Hosting
   ```bash
   # Instance: s6.large.2 (2 vCPU, 4GB RAM)
   # Region: af-south-1 (Johannesburg)
   # Estimated cost: $8-15/month
   # Purpose: Host React frontend + FastAPI backend
   ```

2. **ModelArts** (AI/ML Platform)
   ```bash
   # Training: c6.large.2 (CPU-based for cost savings)
   # Inference: Auto-scaling endpoints (scale to zero)
   # Estimated cost: $5-15/month
   ```

3. **OBS** (Object Storage)
   ```bash
   # Bucket: saferoute-ai-data
   # Region: af-south-1
   # Estimated cost: $1-3/month for 100GB
   ```

4. **Optional: GaussDB** (Database)
   ```bash
   # For spatial queries and high-performance data access
   # Estimated cost: $10-30/month (consider carefully)
   ```

### Service Configuration Commands

```bash
# Run all setup tasks (recommended)
# Ask Kiro: "run all tasks for huawei-cloud-production-setup"

# Or run individual phases:
# Ask Kiro: "execute task 1 for huawei-cloud-production-setup"  # Account setup
# Ask Kiro: "execute task 2 for huawei-cloud-production-setup"  # Service config
# Ask Kiro: "execute task 3 for huawei-cloud-production-setup"  # Cost optimization
```

## 🧪 Phase 4: Testing and Validation

### Connection Testing

```bash
# Test all services
python test_connection.py

# Expected output:
# ✅ ModelArts connection: Success
# ✅ OBS connection: Success  
# ✅ Authentication: Valid
# ✅ Region: af-south-1
```

### API Testing

```bash
# Start the production API
python -m src.api

# Test endpoints at:
# http://localhost:8000/docs
```

### Load Testing

```bash
# Run comprehensive tests
python test_end_to_end.py
python test_backend_stress.py
```

## 📊 Phase 5: Monitoring and Maintenance

### Daily Monitoring

```bash
# Check costs daily
python monitor_costs.py

# View detailed spending in console:
# https://console.huaweicloud.com/billing
```

### Weekly Optimization

1. **Review Service Usage**
   - Check which services are consuming most budget
   - Identify unused or underutilized resources
   - Adjust instance sizes based on actual usage

2. **Optimize Data Storage**
   - Archive old training data
   - Clean up temporary files
   - Review OBS storage classes

3. **Performance Tuning**
   - Monitor API response times
   - Optimize model inference performance
   - Adjust auto-scaling policies

## 🚨 Troubleshooting

### Common Issues

1. **Authentication Errors**
   ```bash
   # Check credentials in .env file
   # Verify AK/SK are correct
   # Ensure Project ID matches your region
   ```

2. **Service Unavailable**
   ```bash
   # Verify services are enabled in af-south-1
   # Check service quotas and limits
   # Review billing status
   ```

3. **High Costs**
   ```bash
   # Run cost monitor: python monitor_costs.py
   # Check for idle resources
   # Review auto-scaling settings
   ```

### Getting Help

1. **Huawei Cloud Support**
   - Console: https://console.huaweicloud.com
   - Documentation: https://support.huaweicloud.com

2. **SafeRouteAI Issues**
   - Check logs in the application
   - Run diagnostic scripts
   - Review error messages in console

## 🎯 Success Metrics

Your setup is successful when:

- [ ] All services connect without errors
- [ ] API responds with real cloud data (not mock)
- [ ] Cost monitoring shows reasonable daily spend
- [ ] Training jobs complete successfully
- [ ] Inference endpoints return predictions

## 📈 Next Steps After Setup

1. **Deploy Your First Model**
   - Upload crime data to OBS
   - Run ModelArts training job
   - Deploy inference endpoint

2. **Integrate with Frontend**
   - Update API endpoints
   - Test real-time predictions
   - Monitor performance

3. **Scale for Production**
   - Set up load balancing
   - Implement caching
   - Add monitoring dashboards

---

## 💡 Pro Tips

- **Budget Alerts**: Set up multiple alert thresholds
- **Off-Peak Training**: Schedule expensive operations during low-cost hours
- **Data Lifecycle**: Implement automatic data archiving
- **Resource Tagging**: Tag all resources for better cost tracking
- **Regular Reviews**: Weekly cost and performance reviews

**🎉 You're ready to deploy SafeRouteAI on Huawei Cloud!**

For detailed implementation, ask Kiro to run the complete setup tasks.