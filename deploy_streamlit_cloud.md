# Deploy to Streamlit Cloud

## Quick Deployment Guide

### Step 1: Prepare Repository

```bash
# Make sure everything is committed
git add .
git commit -m "Prepare for Streamlit Cloud deployment"
git push
```

### Step 2: Deploy on Streamlit Cloud

1. Go to https://share.streamlit.io
2. Click "Sign in" (use GitHub)
3. Click "New app"
4. Fill in:
   - **Repository:** whughes1994/PairingAnalysis
   - **Branch:** main
   - **Main file path:** unified_dashboard.py
5. Click "Deploy!"

### Step 3: Add Secrets

1. Click "⚙️ Settings" in deployed app
2. Go to "Secrets" section
3. Add your MongoDB URI:

```toml
MONGO_URI = "mongodb+srv://username:password@cluster.mongodb.net/"
```

4. Click "Save"

### Step 4: Access Your App

Your app will be available at:
```
https://[app-name].streamlit.app
```

## Important Notes

### QA Workbench Tab
The QA Workbench requires local PDF/JSON files which won't be available in cloud deployment.

**Options:**
1. **Remove QA tab for cloud version** (create separate public dashboard)
2. **Add file upload widget** to let users upload their own PDFs/JSONs
3. **Keep it** but show message: "QA features require local deployment"

### Making it Public-Safe

Create a public version:

```bash
# Create public version without local file dependencies
cp unified_dashboard.py dashboard_public.py
```

Edit `dashboard_public.py`:
- Remove Tab 2 (QA Workbench) or make it upload-based
- Remove Tab 3 (Annotations)
- Keep Tab 1 (Pairing Explorer) only

Then deploy `dashboard_public.py` instead.

### MongoDB Access

Ensure your MongoDB Atlas:
1. Network Access → Add IP: `0.0.0.0/0` (allow from anywhere)
2. Or add Streamlit Cloud IPs (check their docs)

### Custom Domain (Optional)

Streamlit Cloud supports custom domains on paid plans.

## Troubleshooting

### App won't start
- Check "Manage app" → "Logs"
- Verify secrets are set correctly
- Ensure requirements.txt includes all dependencies

### MongoDB connection fails
- Check MongoDB Network Access settings
- Verify MONGO_URI secret is correct
- Test connection locally first

### Missing dependencies
Add to `requirements.txt`:
```
streamlit>=1.28.0
pymongo>=4.6.0
plotly>=5.18.0
pandas>=2.0.0
airportsdata>=20231215
pdfplumber>=0.10.0
```

## Alternative: Railway.app

If Streamlit Cloud doesn't work:

1. Go to https://railway.app
2. "New Project" → "Deploy from GitHub"
3. Select: whughes1994/PairingAnalysis
4. Add environment variable: `MONGO_URI`
5. Railway auto-detects Streamlit and deploys

## Cost Comparison

| Platform | Free Tier | Paid |
|----------|-----------|------|
| Streamlit Cloud | 1 private app | $20/mo unlimited |
| Railway | $5 credit/mo | Usage-based |
| Heroku | 550 hrs/mo | $7/mo dyno |
| DigitalOcean | None | $5/mo |

**Recommendation:** Start with Streamlit Cloud free tier.
