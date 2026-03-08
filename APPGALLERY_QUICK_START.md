# AppGallery Connect - Quick Start Guide

**5-Minute Setup for SafeRouteAI**

---

## ✅ What's Already Done

- ✅ Developer account verified
- ✅ Project created (SafeRouteAI)
- ✅ App registered
- ✅ API keys configured
- ✅ Backend configured
- ✅ Frontend configured
- ✅ Database connected (Neon)

---

## 🎯 What You Need to Do Now

Just **2 simple steps** in AppGallery Connect console:

### Step 1: Add Callback URLs (2 minutes)
### Step 2: Add Authorized Domains (2 minutes)

That's it! Then you can test everything.

---

## 📍 Step 1: Add Callback URLs

### Go to AppGallery Connect
1. Open: https://developer.huawei.com/consumer/en/service/josp/agc/index.html
2. Click on **SafeRouteAI** project
3. Click **Build** → **Auth Service** → **Settings** tab
4. Scroll to **OAuth 2.0 Configuration**

### Add These 4 URLs
Click "Add Callback URL" button and add each one:

```
http://localhost:3000/auth/callback
http://localhost:8004/auth/callback
http://127.0.0.1:3000/auth/callback
http://127.0.0.1:8004/auth/callback
```

### Click Save
Don't forget to click the **Save** button at the bottom!

---

## 🌐 Step 2: Add Authorized Domains

### In the Same Settings Page
Scroll to **Access Restrictions** section

### Add These 4 Domains
Click "Add Domain" button and add each one:

```
http://localhost:3000
http://localhost:8004
http://127.0.0.1:3000
http://127.0.0.1:8004
```

### Enable CORS
Make sure the **Enable CORS** checkbox is checked for each domain

### Click Save
Don't forget to click the **Save** button at the bottom!

---

## 🗺️ Optional: Enable Map Kit

If Map Kit is not already enabled:

1. Click **Build** → **Map Kit**
2. Click **Enable Now**
3. Use default settings
4. Add the same 4 domains as authorized domains
5. Click **Save**

---

## 🚀 Test Your Setup

### 1. Start Backend
```bash
python src/api.py
```

You should see:
```
✅ Connected to Neon PostgreSQL database
🇿🇦 Starting SafeRouteAI API with Huawei Map Kit Integration
📡 API will be available at: http://localhost:8004
```

### 2. Start Frontend
```bash
cd frontend
npm start
```

Browser should open at: http://localhost:3000

### 3. Test Authentication
1. Click "Get Started" or "Sign Up"
2. Enter email and password
3. Click "Register"
4. You should be logged in and see the dashboard

### 4. Test Map
1. Click "Navigate" or "Start Journey"
2. Map should load with Johannesburg, South Africa
3. You should see crime hotspots and safety heatmap

---

## ✅ Success Indicators

You'll know it's working when:

- ✅ Backend starts without errors
- ✅ Frontend loads without console errors
- ✅ You can register a new user
- ✅ You can log in
- ✅ Map loads and displays correctly
- ✅ You can see crime hotspots on the map
- ✅ Safety heatmap displays

---

## 🔧 Troubleshooting

### "Callback URL not authorized"
→ Make sure you added all 4 callback URLs and clicked Save

### "CORS error in console"
→ Make sure you added all 4 domains to Access Restrictions and enabled CORS

### "Map not loading"
→ Check that Map Kit is enabled and domains are authorized

### "Database connection error"
→ Check that DATABASE_URL in .env is correct

### Still having issues?
→ Run: `python setup_appgallery_connect.py` to validate configuration

---

## 📊 Your Configuration Summary

```
Developer ID:     30027000029470745
Project ID:       101653523863540321
App ID:           101653523124655000
OAuth Client ID:  116823677
Region:           AF-Johannesburg
Database:         Neon PostgreSQL ✅
Authentication:   JWT + Neon Auth ✅
Map Kit:          Enabled ✅
```

---

## 📝 Important Files

- **Backend Config**: `.env`
- **Frontend Config**: `frontend/.env.local`
- **API Code**: `src/api.py`
- **Database**: `src/neon_database.py`
- **Auth Service**: `src/neon_auth.py`
- **Map Component**: `frontend/src/components/HuaweiMapComponent.js`

---

## 🎯 Next Steps After Testing

Once everything works locally:

1. **Deploy Backend** → Railway, Render, or Vercel
2. **Deploy Frontend** → Netlify or Vercel
3. **Update Callback URLs** → Add production URLs
4. **Update Domains** → Add production domains
5. **Configure SSL** → Enable HTTPS
6. **Set up Monitoring** → Sentry, LogRocket, etc.

---

## 📞 Need Help?

- **Detailed Guide**: See `APPGALLERY_CONNECT_CONFIG.md`
- **Callback Setup**: See `CALLBACK_URL_SETUP_GUIDE.md`
- **Validation Script**: Run `python setup_appgallery_connect.py`
- **Huawei Forum**: https://forums.developer.huawei.com/

---

## 🎉 You're Almost There!

Just add those callback URLs and domains in AppGallery Connect, then you're ready to test!

**Time Required**: 5 minutes  
**Difficulty**: Easy  
**Result**: Fully functional SafeRouteAI app! 🚀

---

*Last Updated: February 5, 2026*  
*SafeRouteAI Quick Start Guide*
