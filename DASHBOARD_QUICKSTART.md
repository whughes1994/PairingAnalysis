# Dashboard Quick Start - 5 Minutes to Demo

## Step 1: Configure MongoDB (1 minute)

```bash
# Create secrets file
cat > .streamlit/secrets.toml << 'EOF'
MONGO_URI = "YOUR_MONGODB_ATLAS_CONNECTION_STRING"
EOF
```

**Replace `YOUR_MONGODB_ATLAS_CONNECTION_STRING` with your actual Atlas connection!**

Example:
```
MONGO_URI = "mongodb+srv://user:pass@cluster0.abc123.mongodb.net/"
```

## Step 2: Test Connection (1 minute)

```bash
python3 test_dashboard_ready.py
```

**Expected output:**
```
DASHBOARD READINESS CHECK
✅ All required packages installed
✅ Secrets file exists
✅ Connected to MongoDB
✅ Found 2,047 pairings
✅ Found 10,741 legs
✅ Found 4 fleets
✅ dashboard.py exists

🎉 READY TO LAUNCH!
```

If you see errors, fix them before proceeding.

## Step 3: Launch Dashboard (1 minute)

```bash
streamlit run dashboard.py
```

**Opens automatically at:** http://localhost:8501

## Step 4: Demo (2 minutes)

### Try These Features:

1. **Fleet Overview**
   - See pie chart with 787, 756, 737, 320 distribution
   - Bar chart shows avg credit by fleet

2. **Search & Filter**
   - Sidebar → Fleet: Select "737"
   - Sidebar → Credit Range: 20-30 hours
   - See filtered results instantly

3. **Layover Analysis**
   - Scroll to "Top Layover Destinations"
   - See bar chart of overnight cities
   - ORD should be #1 with 3,426 layovers

4. **Export Data**
   - Scroll to results table
   - Click "Download Results as CSV"
   - Opens in Excel/Google Sheets

## Common Issues

### "Connection refused"
```bash
# Check if MongoDB is accessible
python3 check_connection.py
```

Fix: Update `.streamlit/secrets.toml` with correct connection string

### "No data found"
```bash
# Re-import data
python3 mongodb_import.py \
  --connection "YOUR_MONGO_URI" \
  --file output/ORD.json \
  --clear
```

### "Module not found"
```bash
# Install missing packages
pip3 install streamlit plotly pandas pymongo
```

### Dashboard looks wrong
```bash
# Clear cache and restart
streamlit cache clear
streamlit run dashboard.py
```

## Share with Others

### Local Network
```bash
# Run with external access
streamlit run dashboard.py --server.address 0.0.0.0
```

Others access at: `http://YOUR_IP:8501`

### Cloud (Free)
1. Push code to GitHub
2. Deploy on https://streamlit.io/cloud
3. Add `MONGO_URI` to Streamlit Cloud secrets
4. Share link with team

## What's Included

- **2,047 pairings** across 4 fleets (787, 756, 737, 320)
- **10,741 flight legs** with layover data
- **32 unique layover cities**
- **Interactive filters** (fleet, category, credit range)
- **Real-time charts** (pie, bar, histogram)
- **CSV export** for offline analysis

## Next Steps

See [PROOF_OF_CONCEPT.md](PROOF_OF_CONCEPT.md) for:
- Deployment options
- Adding more features
- Scaling to production
- Cost estimates

## Files Reference

- `dashboard.py` - Main app
- `DASHBOARD_SETUP.md` - Detailed guide
- `README_DASHBOARD.md` - Feature overview
- `PROOF_OF_CONCEPT.md` - Full POC documentation
- `test_dashboard_ready.py` - Readiness checker

---

**Total time: 5 minutes from zero to demo** ⚡

Questions? Run `python3 test_dashboard_ready.py` to diagnose issues.
