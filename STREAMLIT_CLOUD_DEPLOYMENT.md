# Streamlit Cloud Deployment Guide

**Date:** 2025-12-30
**App:** Airline Pairing Dashboard

## Pre-Deployment Checklist

### 1. MongoDB Atlas Network Access

**CRITICAL:** Streamlit Cloud uses dynamic IPs, so you must allow all IPs.

1. Go to [MongoDB Atlas](https://cloud.mongodb.com)
2. Select your cluster → Network Access
3. Click "Add IP Address"
4. Select "Allow Access from Anywhere" (0.0.0.0/0)
5. Click "Confirm"

> ⚠️ **Security Note:** For production, consider using MongoDB's VPC peering or PrivateLink for better security.

### 2. Verify MongoDB Connection String

Your connection string should NOT include the `tlsAllowInvalidCertificates` parameter for Streamlit Cloud:

**Correct format:**
```
mongodb+srv://username:password@cluster0.odztddj.mongodb.net/?retryWrites=true&w=majority
```

**Incorrect format (don't use this in cloud):**
```
mongodb+srv://.../?tlsAllowInvalidCertificates=true
```

### 3. Create requirements.txt

Create a `requirements.txt` file with all dependencies:

```bash
streamlit>=1.28.0
pymongo>=4.5.0
pandas>=2.0.0
plotly>=5.18.0
pydantic>=2.0.0
airportsdata>=20231201
certifi>=2023.11.17
toml>=0.10.2
tqdm>=4.66.0
```

Save this to your project root.

---

## Step-by-Step Deployment

### Step 1: Prepare Git Repository

```bash
# Initialize git (if not already done)
git init

# Create .gitignore
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.so
*.egg
*.egg-info/
dist/
build/

# Virtual Environment
venv/
env/
ENV/

# Streamlit
.streamlit/secrets.toml

# Data files
output/
*.json
*.pdf
*.DAT
Pairing Source Docs/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# macOS
.DS_Store

# Logs
*.log
EOF

# Add all files
git add .
git commit -m "Initial commit for Streamlit Cloud deployment"
```

### Step 2: Push to GitHub

```bash
# Create a new repository on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/pairing-dashboard.git
git branch -M main
git push -u origin main
```

### Step 3: Deploy to Streamlit Cloud

1. **Go to Streamlit Cloud:**
   - Visit [share.streamlit.io](https://share.streamlit.io)
   - Sign in with your GitHub account

2. **Create New App:**
   - Click "New app"
   - Select your repository
   - Branch: `main`
   - Main file: `unified_dashboard.py`
   - App URL: Choose a custom name (e.g., `pairing-dashboard`)

3. **Configure Secrets (CRITICAL):**
   - Before clicking "Deploy", click "Advanced settings"
   - Go to the "Secrets" section
   - Add your MongoDB connection string in TOML format:

   ```toml
   MONGO_URI = "mongodb+srv://whughes:whughes@cluster0.odztddj.mongodb.net/?retryWrites=true&w=majority"
   ```

   > ⚠️ **Important:** Use your actual username and password, not "whughes"

4. **Deploy:**
   - Click "Deploy!"
   - Wait 2-5 minutes for deployment to complete

---

## Troubleshooting Common Issues

### Issue 1: "MONGO_URI not found in secrets"

**Solution:**
1. Go to your app dashboard: `https://share.streamlit.io`
2. Click on your app
3. Click the hamburger menu (⋮) → Settings
4. Go to "Secrets"
5. Add the MONGO_URI in TOML format
6. Click "Save"
7. App will automatically restart

### Issue 2: "SSL handshake failed" or "Connection timeout"

**Possible causes:**
1. **MongoDB Network Access not configured**
   - Solution: Add 0.0.0.0/0 to Network Access in MongoDB Atlas

2. **Incorrect connection string**
   - Solution: Remove `tlsAllowInvalidCertificates` parameter
   - Use: `mongodb+srv://user:pass@cluster.mongodb.net/?retryWrites=true&w=majority`

3. **Database user doesn't exist or has wrong permissions**
   - Solution: In MongoDB Atlas, go to Database Access
   - Ensure user exists with "Read and write to any database" permission

### Issue 3: "Module not found" errors

**Solution:**
1. Ensure `requirements.txt` is in the root of your repository
2. Check that all dependencies are listed
3. Redeploy the app

### Issue 4: App is slow or times out

**Causes:**
- Caching not working properly
- Too many pairings being loaded at once

**Solutions:**
1. The app already uses `@st.cache_resource` for MongoDB connection
2. The app already uses `@st.cache_data(ttl=600)` for data queries
3. Consider limiting the initial query to 500 pairings (already implemented)

---

## Updating Your Deployed App

### Method 1: Git Push (Automatic)

```bash
# Make your changes locally
git add .
git commit -m "Update dashboard features"
git push origin main

# Streamlit Cloud will automatically redeploy
```

### Method 2: Manual Redeploy

1. Go to your app on Streamlit Cloud
2. Click hamburger menu (⋮) → Reboot app

---

## Security Best Practices

### 1. Use Environment-Specific Credentials

For production:
- Create a separate MongoDB database user for production
- Use a strong, unique password
- Grant only necessary permissions

### 2. Enable IP Whitelisting (Advanced)

If you need better security than 0.0.0.0/0:
- Use MongoDB Atlas VPC Peering
- Or use MongoDB Atlas PrivateLink
- Contact Streamlit support for their IP ranges

### 3. Protect Sensitive Data

Never commit these files:
- `.streamlit/secrets.toml`
- Any files with credentials
- Large data files (JSON, PDF, DAT)

### 4. Monitor Usage

- Set up MongoDB Atlas alerts for unusual activity
- Monitor Streamlit Cloud usage dashboard
- Set up database user audit logs

---

## App Settings in Streamlit Cloud

### Recommended Settings:

**Python version:** 3.9+ (matches your local environment)

**Resources:**
- Free tier: 1 GB RAM (sufficient for this app)
- Paid tier: Consider upgrading if >1000 concurrent users

**App Settings (.streamlit/config.toml):**

```toml
[theme]
primaryColor = "#FF4B4B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"

[server]
headless = true
enableCORS = false
port = 8501

[browser]
gatherUsageStats = false
```

---

## Cost Considerations

### Streamlit Cloud (Free Tier)
- ✅ Free for public apps
- ✅ 1 GB RAM
- ✅ Shared CPU
- ⚠️ App sleeps after inactivity
- ⚠️ Limited to 3 apps
- ⚠️ Public by default

### Streamlit Cloud (Paid - $20/month per user)
- ✅ Private apps with password protection
- ✅ More resources
- ✅ No sleep mode
- ✅ Unlimited apps
- ✅ Custom domains

### MongoDB Atlas (Free Tier - M0)
- ✅ 512 MB storage
- ✅ Shared cluster
- ✅ Sufficient for ~10,000 pairings
- ⚠️ Limited connections (100 max)

---

## Monitoring & Maintenance

### Check App Health

1. **Streamlit Cloud Logs:**
   - App dashboard → "Manage app" → "Logs"
   - Check for errors or warnings

2. **MongoDB Atlas Metrics:**
   - Cluster → Metrics tab
   - Monitor connection count
   - Monitor data size
   - Set up alerts for storage/connection limits

### Regular Maintenance

**Weekly:**
- Check app logs for errors
- Verify MongoDB connection is stable

**Monthly:**
- Review MongoDB storage usage
- Check Streamlit Cloud usage stats
- Update dependencies if needed

---

## Adding New Data

### To add new bid months:

1. **Parse the .DAT file locally:**
   ```bash
   python3 -m src.main \
     -i "Pairing Source Docs/MONTH_YEAR/ORDDSL.DAT" \
     -o "output/ORDDSL_MONTH_YEAR.json"
   ```

2. **Import to MongoDB:**
   ```bash
   python3 mongodb_import.py --file output/ORDDSL_MONTH_YEAR.json
   ```

3. **Verify in dashboard:**
   - The new bid month will automatically appear in the dropdown
   - No code changes needed!

---

## Sharing Your App

### Public App URL:
```
https://YOUR_APP_NAME.streamlit.app
```

### Share with others:
- Anyone with the URL can access (free tier)
- For password protection, upgrade to paid tier

---

## Getting Help

### Streamlit Resources:
- Docs: https://docs.streamlit.io
- Community: https://discuss.streamlit.io
- GitHub: https://github.com/streamlit/streamlit

### MongoDB Resources:
- Atlas Docs: https://www.mongodb.com/docs/atlas/
- Connection Troubleshooting: https://www.mongodb.com/docs/atlas/troubleshoot-connection/

---

## Summary Checklist

Before deploying, ensure:

- [ ] MongoDB Atlas allows 0.0.0.0/0 access
- [ ] Connection string is correct (no `tlsAllowInvalidCertificates`)
- [ ] `requirements.txt` exists with all dependencies
- [ ] `.gitignore` excludes `.streamlit/secrets.toml`
- [ ] Code is pushed to GitHub
- [ ] Secrets are added in Streamlit Cloud settings
- [ ] App is deployed and showing green status

**Your app should now be live! 🎉**

---

**Last Updated:** 2025-12-30
