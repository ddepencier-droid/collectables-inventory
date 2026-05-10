# Railway Deployment - Quick Start Guide

**Status**: ✅ Ready to Deploy  
**Deployment Time**: 5 minutes  
**Cost**: Free tier available

---

## **Step 1: Go to Railway** (2 minutes)

1. Open [railway.app](https://railway.app) in your browser
2. Click **"Sign In"** → **"GitHub"**
3. Authorize Railway to access your GitHub account

---

## **Step 2: Create New Project** (1 minute)

1. Click **"New Project"** button
2. Select **"Deploy from GitHub repo"**
3. Search for **`collectables-inventory`**
4. Click to select it
5. Railway will automatically start deploying ⏳

**Status**: Watch for green checkmark (deployment complete)

---

## **Step 3: Add Environment Variables** (1 minute)

Once deployed (green checkmark appears):

1. Click the **collectables-inventory** service
2. Go to **"Variables"** tab
3. Add these variables (copy from your `.env` file):

| Variable | Value |
|----------|-------|
| `EBAY_CLIENT_ID` | Your eBay sandbox Client ID |
| `EBAY_CLIENT_SECRET` | Your eBay sandbox Client Secret |
| `EBAY_NOTIFICATION_VERIFICATION_TOKEN` | Your eBay verification token |
| `EBAY_USE_SANDBOX` | `1` |
| `FLASK_ENV` | `production` |

4. Click **"Save"**

Railway will restart the app with these variables.

---

## **Step 4: Get Your Public URL** (30 seconds)

1. After deployment completes, click the **collectables-inventory** service
2. Go to **"Settings"** tab
3. Look for **"Domains"** section
4. Copy your public URL (looks like: `https://collectables-inventory-prod.railway.app`)

**This is your iPhone-accessible URL!** 📱

---

## **Step 5: Test Your App** (1 minute)

1. Open the URL in your browser (or iPhone)
2. You should see your Collectables Inventory app
3. Test the pricing and catalog features

**Congratulations! Your app is now live!** 🎉

---

## **Railway Dashboard Tips**

**Monitor your app**:
- Click service → **"Logs"** tab to see real-time output
- Click **"Metrics"** to see CPU/memory usage
- Free tier includes ~500 hours/month

**Make updates**:
- Push code changes to GitHub (`git push`)
- Railway automatically redeploys within seconds
- No manual steps needed

**Troubleshooting**:
- App won't start? Check **Logs** tab
- Variables not working? Ensure exact spelling and restart service
- Need to restart? Click **"Restart Service"** in Settings

---

## **Using Your App on iPhone**

1. On your iPhone, open Safari (or any browser)
2. Go to: `https://your-railway-url` (from Step 4)
3. Bookmark it for quick access
4. Use it just like on desktop

**Note**: Works on WiFi or cellular data!

---

## **Next: Contact eBay Support**

Now that your app is deployed, contact eBay to re-enable your API:

**Send to eBay Developer Support**:
```
Subject: Request to Re-Enable API Keyset - Marketplace Account Deletion Compliance

Hello,

My application has been deployed and complies with eBay's mandatory 
Marketplace Account Deletion requirements.

Challenge/Response Endpoint:
https://[YOUR-RAILWAY-URL]/api/ebay/marketplace-account-deletion?challenge_code=TEST

Notification Handler:
https://[YOUR-RAILWAY-URL]/api/ebay/marketplace-account-deletion

Both endpoints are fully functional and ready for verification.

Client ID: [your client ID]
```

---

## **You're All Set!** ✅

- ✅ Code on GitHub
- ✅ Production-ready configuration
- ✅ Deployment files verified
- ✅ Environment variables template ready
- ✅ Compliance documentation complete

**Next action**: Deploy to Railway and contact eBay support!
