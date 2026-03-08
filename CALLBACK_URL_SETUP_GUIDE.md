# Callback URL Setup Guide for AppGallery Connect

**Quick Reference for SafeRouteAI OAuth Configuration**

---

## 🎯 What You Need to Do

You need to add **Callback URLs** and **Access Restrictions** in your AppGallery Connect console.

---

## 📍 Step 1: Access AppGallery Connect Console

1. Go to: https://developer.huawei.com/consumer/en/service/josp/agc/index.html
2. Log in with your Huawei Developer account
3. Select your **SafeRouteAI** project

---

## 🔐 Step 2: Configure OAuth Callback URLs

### Navigate to Auth Service
1. Click **Build** in the left sidebar
2. Click **Auth Service**
3. Click the **Settings** tab
4. Scroll to **OAuth 2.0 Configuration** section

### Add Callback URLs

Click **Add Callback URL** and add these URLs one by one:

```
http://localhost:3000/auth/callback
http://localhost:8004/auth/callback
http://127.0.0.1:3000/auth/callback
http://127.0.0.1:8004/auth/callback
```

**Important**: 
- Add each URL separately
- Make sure there are no trailing slashes
- Use `http://` for local development (not `https://`)

### Save Configuration
Click **Save** at the bottom of the page

---

## 🌐 Step 3: Configure Access Restrictions

### In the Same Settings Page

Scroll to **Access Restrictions** section

### Add Authorized Domains

Click **Add Domain** and add these domains one by one:

```
http://localhost:3000
http://localhost:8004
http://127.0.0.1:3000
http://127.0.0.1:8004
```

**Important**:
- These are the domains that can make requests to your API
- No trailing slashes
- Include both `localhost` and `127.0.0.1` for compatibility

### Enable CORS

Make sure **Enable CORS** is checked for each domain

### Save Configuration
Click **Save** at the bottom of the page

---

## 🗺️ Step 4: Enable Map Kit (If Not Already Enabled)

### Navigate to Map Kit
1. Click **Build** in the left sidebar
2. Click **Map Kit**
3. If not enabled, click **Enable Now**

### Configure Map Kit Settings

1. **API Quotas**: Use default settings for development
2. **Authorized Domains**: Add the same domains as above:
   ```
   http://localhost:3000
   http://localhost:8004
   http://127.0.0.1:3000
   http://127.0.0.1:8004
   ```
3. Click **Save**

---

## ✅ Step 5: Verify Configuration

### Check Your Settings

Go back to **Auth Service → Settings** and verify:

- ✅ 4 callback URLs are added
- ✅ 4 authorized domains are added
- ✅ CORS is enabled for all domains
- ✅ Map Kit is enabled
- ✅ All changes are saved

---

## 🚀 Step 6: Test Your Configuration

### Start the Backend
```bash
python src/api.py
```

### Start the Frontend
```bash
cd frontend
npm start
```

### Test Authentication
1. Open http://localhost:3000 in your browser
2. Try to register a new user
3. Try to log in
4. Check if the map loads correctly

---

## 🔧 Troubleshooting

### Issue: "Callback URL not authorized"
**Solution**: Make sure you added the exact callback URL including `/auth/callback`

### Issue: "CORS error"
**Solution**: 
1. Check that domains are added to Access Restrictions
2. Make sure CORS is enabled
3. Restart your backend server

### Issue: "Map not loading"
**Solution**:
1. Check that Map Kit is enabled
2. Verify authorized domains are added to Map Kit settings
3. Check browser console for errors

### Issue: "Invalid client ID"
**Solution**: 
1. Verify OAuth Client ID in .env matches AppGallery Connect
2. Check that you're using the correct project

---

## 📝 Production Deployment

When you deploy to production, you'll need to add production URLs:

### Production Callback URLs
```
https://your-frontend-domain.com/auth/callback
https://your-backend-domain.com/auth/callback
```

### Production Authorized Domains
```
https://your-frontend-domain.com
https://your-backend-domain.com
```

**Remember**: Use `https://` for production (not `http://`)

---

## 📊 Current Configuration

### Your AppGallery Connect Details

- **Developer ID**: 30027000029470745
- **Project ID**: 101653523863540321
- **App ID**: 101653523124655000
- **OAuth Client ID**: 116823677

### Your API Keys

- **Map Kit API Key**: DgEDAKHF+wVdHovXyTyiZnbDiQEH6lONvjiO1P4/Vyh7OjfRlYDplJRfi377pwH4ltbiVy8aT4+xpPaHiSIN+ITOUiVpKIc8Dhtewg==
- **Project API Key**: DgEDAGAopOrNIB9hgsjSL+5/QlkJ+X+tVo6wPfXdx5uJqfErVun7MLWhdxClHHQaeHw0RlHQH4STe5gNEfAkXoDu5K3pmpokr7Jq6g==

---

## 🎯 Quick Checklist

Before testing, make sure:

- [ ] Added 4 callback URLs in OAuth 2.0 Configuration
- [ ] Added 4 authorized domains in Access Restrictions
- [ ] Enabled CORS for all domains
- [ ] Enabled Map Kit service
- [ ] Added authorized domains to Map Kit
- [ ] Saved all changes
- [ ] Restarted backend server
- [ ] Cleared browser cache

---

## 📞 Need Help?

- **AppGallery Connect Console**: https://developer.huawei.com/consumer/en/service/josp/agc/index.html
- **Huawei Developer Forum**: https://forums.developer.huawei.com/
- **Documentation**: See APPGALLERY_CONNECT_CONFIG.md

---

*Last Updated: February 5, 2026*  
*SafeRouteAI OAuth Configuration Guide*
