# Collectables Inventory - Deployment Guide

## 🚀 Deploy to Railway

### Step 1: Create Railway Account
1. Go to [Railway.app](https://railway.app)
2. Sign up with GitHub account
3. Connect your GitHub repository

### Step 2: Deploy
1. Click "New Project" → "Deploy from GitHub repo"
2. Select your repository
3. Railway will auto-detect Python and deploy

### Step 3: Configure Environment Variables
In Railway dashboard, go to your project → Variables and add:

```
EBAY_CLIENT_ID=your_ebay_client_id
EBAY_CLIENT_SECRET=your_ebay_client_secret
EBAY_USE_SANDBOX=1
EBAY_MARKETPLACE_INSIGHTS_ENABLED=1
EBAY_MARKETPLACE_ID=EBAY_US
EBAY_NOTIFICATION_VERIFICATION_TOKEN=iCydbjeE9LxeEQ7Suk-uSMpA-mmOLqRejtjr774UBxc
CATALOG_PRICE_REFRESH_ON_START=1
CATALOG_PRICE_REFRESH_LIMIT=25
CATALOG_PRICE_TTL_HOURS=24
FLASK_ENV=production
```

### Step 4: Access Your App
- Railway will provide a URL like: `https://your-app-name.up.railway.app`
- Use this URL from your iPhone!

## 🔧 Production Notes

- SQLite database will be stored in Railway's ephemeral storage
- Data persists between deployments but may be lost if the service is stopped for extended periods
- For production data persistence, consider upgrading to Railway's persistent storage or switching to PostgreSQL

## 📱 iPhone Access

Once deployed, you can:
1. Open Safari on your iPhone
2. Navigate to your Railway URL
3. Bookmark it for easy access
4. The responsive design works great on mobile!