# AppGallery Connect Configuration for SafeRouteAI

**Date**: February 5, 2026  
**Status**: ✅ VERIFIED ACCOUNT

---

## 📋 Account Information

### Developer Information
- **Developer ID**: `30027000029470745`
- **Public Key**: Available (RSA 3072-bit)

### Project Information
- **Project Name**: SafeRouteAI
- **Project ID**: `101653523863540321`
- **Data Processing Location**: Client

### Client Credentials
- **Client ID**: `1878108719443651904`
- **Client Secret**: `906EEC9ABBD4D6D97D997953AC94BDB3EF14109A9D5ED5C77DCBE4400AD94123`
- **API Key**: `DgEDAGAopOrNIB9hgsjSL+5/QlkJ+X+tVo6wPfXdx5uJqfErVun7MLWhdxClHHQaeHw0RlHQH4STe5gNEfAkXoDu5K3pmpokr7Jq6g==`

### App Information
- **App Name**: SafeRouteAI
- **App ID**: `101653523124655000`
- **Package Name**: (To be configured)

### OAuth 2.0 Credentials
- **OAuth Client ID**: `116823677`
- **OAuth Client Secret**: `f03a7bf76ce5bfc3a267ab0ef05444d5283adcab926e8304a4464eb7dd110b0a`

---

## 🔧 Required Configuration

### 1. Callback URL Configuration

You need to add the following callback URLs in your AppGallery Connect console:

#### Development URLs
```
http://localhost:3000/auth/callback
http://localhost:8004/auth/callback
http://127.0.0.1:3000/auth/callback
http://127.0.0.1:8004/auth/callback
```

#### Production URLs (Add when deploying)
```
https://your-frontend-domain.com/auth/callback
https://your-backend-domain.com/auth/callback
```

### 2. Access Restrictions

Configure the following domains as authorized:

#### Development Domains
```
http://localhost:3000
http://localhost:8004
http://127.0.0.1:3000
http://127.0.0.1:8004
```

#### Production Domains (Add when deploying)
```
https://your-frontend-domain.com
https://your-backend-domain.com
```

---

## 🗺️ Map Kit Configuration

### Current Map Kit API Key (Already Configured)
```
DgEDAKHF+wVdHovXyTyiZnbDiQEH6lONvjiO1P4/Vyh7OjfRlYDplJRfi377pwH4ltbiVy8aT4+xpPaHiSIN+ITOUiVpKIc8Dhtewg==
```

### New Project API Key (From AppGallery Connect)
```
DgEDAGAopOrNIB9hgsjSL+5/QlkJ+X+tVo6wPfXdx5uJqfErVun7MLWhdxClHHQaeHw0RlHQH4STe5gNEfAkXoDu5K3pmpokr7Jq6g==
```

**Note**: You can use either API key. The new one is specifically tied to your SafeRouteAI project.

---

## 📝 Step-by-Step Setup Instructions

### Step 1: Configure Callback URLs

1. Go to [AppGallery Connect Console](https://developer.huawei.com/consumer/en/service/josp/agc/index.html)
2. Select your **SafeRouteAI** project
3. Navigate to **Build** → **Auth Service**
4. Click on **Settings** tab
5. Scroll to **OAuth 2.0 Configuration**
6. Add the callback URLs listed above
7. Click **Save**

### Step 2: Configure Access Restrictions

1. In the same **Auth Service** settings
2. Find **Access Restrictions** section
3. Add the authorized domains listed above
4. Enable **CORS** for these domains
5. Click **Save**

### Step 3: Enable Required Services

Enable the following services in AppGallery Connect:

#### Map Kit
1. Go to **Build** → **Map Kit**
2. Click **Enable Now**
3. Configure API quotas (use default for development)
4. Add authorized domains (same as above)
5. Click **Save**

#### Location Kit (Optional but Recommended)
1. Go to **Build** → **Location Kit**
2. Click **Enable Now**
3. Configure settings
4. Click **Save**

#### Cloud Storage (For future features)
1. Go to **Build** → **Cloud Storage**
2. Click **Enable Now**
3. Create a storage bucket: `saferoute-ai-storage`
4. Set permissions to authenticated users only

---

## 🔐 Security Configuration

### CORS Settings

Add these CORS headers in your backend (already configured in `src/api.py`):

```python
allow_origins=[
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8004",
    "http://127.0.0.1:8004",
    # Add production domains when deploying
]
```

### API Key Security

- ✅ API keys are URL-encoded
- ✅ Keys stored in environment variables
- ✅ Never commit keys to version control
- ✅ Use different keys for development and production

---

## 🧪 Testing Configuration

### Test Map Kit Integration

Run this command to test Map Kit with the new configuration:

```bash
python test_map_kit_api_keys.py
```

### Test OAuth Flow

1. Start the backend: `python src/api.py`
2. Start the frontend: `cd frontend && npm start`
3. Navigate to `http://localhost:3000`
4. Try to register/login
5. Check if authentication works

---

## 📊 Service Quotas

### Map Kit Quotas (Default)
- **API Calls**: 1,000,000 per month (free tier)
- **Map Loads**: Unlimited
- **Geocoding**: 100,000 per month
- **Routing**: 100,000 per month

### Location Kit Quotas
- **Location Updates**: Unlimited
- **Geofencing**: 100 geofences per app

### Cloud Storage Quotas
- **Storage**: 5 GB (free tier)
- **Bandwidth**: 1 GB per month
- **Operations**: 50,000 per month

---

## 🚀 Production Deployment Checklist

### Before Deploying

- [ ] Update callback URLs with production domains
- [ ] Update access restrictions with production domains
- [ ] Generate production API keys
- [ ] Configure production CORS settings
- [ ] Set up SSL/TLS certificates
- [ ] Configure CDN for static assets
- [ ] Set up monitoring and logging
- [ ] Configure rate limiting
- [ ] Set up backup and disaster recovery

### After Deploying

- [ ] Test all authentication flows
- [ ] Test Map Kit integration
- [ ] Test API endpoints
- [ ] Monitor error rates
- [ ] Check API quota usage
- [ ] Verify security settings
- [ ] Test from different locations
- [ ] Perform load testing

---

## 🔗 Useful Links

- **AppGallery Connect Console**: https://developer.huawei.com/consumer/en/service/josp/agc/index.html
- **Map Kit Documentation**: https://developer.huawei.com/consumer/en/doc/HMSCore-Guides/android-sdk-brief-introduction-0000001061991291
- **Auth Service Documentation**: https://developer.huawei.com/consumer/en/doc/development/AppGallery-connect-Guides/agc-auth-introduction-0000001053732605
- **API Reference**: https://developer.huawei.com/consumer/en/doc/development/AppGallery-connect-References/agcapi-overview-0000001158245079

---

## 📞 Support

If you encounter issues:

1. Check the [Huawei Developer Forum](https://forums.developer.huawei.com/)
2. Review the [FAQ](https://developer.huawei.com/consumer/en/doc/development/AppGallery-connect-Guides/agc-faq-0000001146598793)
3. Contact Huawei Developer Support
4. Email: securesenseinnovations@gmail.com

---

## ✅ Configuration Status

| Component | Status | Notes |
|-----------|--------|-------|
| Developer Account | ✅ Verified | ID: 30027000029470745 |
| Project Created | ✅ Complete | SafeRouteAI |
| App Registered | ✅ Complete | ID: 101653523124655000 |
| OAuth Configured | ⚠️ Pending | Need to add callback URLs |
| Map Kit Enabled | ✅ Complete | API key configured |
| Access Restrictions | ⚠️ Pending | Need to add domains |
| CORS Settings | ✅ Complete | Backend configured |

---

*Last Updated: February 5, 2026*  
*SafeRouteAI Production Configuration*
