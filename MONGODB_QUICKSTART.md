# MongoDB Quick Start - Upload Your Data

## Option 1: MongoDB Atlas (Cloud) - Fastest Setup ⚡

### Step 1: Create Free Account (5 minutes)
1. Go to https://www.mongodb.com/cloud/atlas/register
2. Sign up (free tier available)
3. Create a free cluster (M0 - no credit card required)
4. Choose region closest to you

### Step 2: Setup Access (2 minutes)
1. **Create Database User**:
   - Security → Database Access → Add New User
   - Username: `parser_user`
   - Password: (generate strong password, save it!)
   - Role: `Read and write to any database`

2. **Add Your IP**:
   - Security → Network Access → Add IP Address
   - Click "Add Current IP Address"
   - Or "Allow Access from Anywhere" (0.0.0.0/0) for testing

### Step 3: Get Connection String (1 minute)
1. Click "Connect" on your cluster
2. Choose "Connect your application"
3. Copy the connection string (looks like):
   ```
   mongodb+srv://parser_user:<password>@cluster0.xxxxx.mongodb.net/
   ```
4. Replace `<password>` with your actual password

### Step 4: Install Python MongoDB Driver
```bash
pip3 install pymongo
```

### Step 5: Import Your Data
```bash
cd "/Users/williamhughes/Library/CloudStorage/GoogleDrive-william.hughes1994@gmail.com/My Drive/Pairing Parser"

# Import single file
python3 mongodb_import.py \
  --connection "mongodb+srv://parser_user:YOUR_PASSWORD@cluster0.xxxxx.mongodb.net/" \
  --file output/ORD.json

# Or import all files
python3 mongodb_import.py \
  --connection "mongodb+srv://parser_user:YOUR_PASSWORD@cluster0.xxxxx.mongodb.net/" \
  --dir output/
```

### Step 6: View Your Data
1. In MongoDB Atlas, click "Browse Collections"
2. Database: `airline_pairings`
3. Collections:
   - `bid_periods` - Top-level summaries
   - `pairings` - Full pairing data
   - `legs` - Individual flight legs

✅ **You're done!** Data is in the cloud and ready to query.

---

## Option 2: Local MongoDB (More Setup)

### Install MongoDB on macOS
```bash
# Install via Homebrew
brew tap mongodb/brew
brew install mongodb-community

# Start MongoDB
brew services start mongodb-community

# Verify it's running
mongosh --eval "db.version()"
```

### Import Data (Local)
```bash
python3 mongodb_import.py --file output/ORD.json
# No --connection needed, defaults to localhost
```

---

## Quick Test After Import

```python
from pymongo import MongoClient

# Atlas connection
client = MongoClient("mongodb+srv://user:pass@cluster.mongodb.net/")
# OR local connection
# client = MongoClient("mongodb://localhost:27017/")

db = client['airline_pairings']

# Count pairings
print(f"Total pairings: {db.pairings.count_documents({})}")

# Sample pairing
pairing = db.pairings.find_one()
print(f"Sample: {pairing['id']} - {pairing['pairing_category']}")

# Pairings by fleet
for fleet in db.pairings.distinct('fleet'):
    count = db.pairings.count_documents({'fleet': fleet})
    print(f"{fleet}: {count} pairings")
```

---

## Next Steps

1. **Import all your PDFs**:
   ```bash
   # Parse all PDFs first
   python3 src/main.py --input-dir "Pairing Source Docs" --output-dir output

   # Import all to MongoDB
   python3 mongodb_import.py --dir output/
   ```

2. **Run analytics**:
   ```bash
   python3 analytics_examples.py
   ```

3. **Query from Python**:
   ```python
   from pymongo import MongoClient

   client = MongoClient("YOUR_CONNECTION_STRING")
   db = client['airline_pairings']

   # High-value pairings
   for p in db.pairings.find({'credit_minutes': {'$gt': 1200}}).sort('credit_minutes', -1).limit(10):
       print(f"{p['id']}: {p['credit_minutes']/60:.1f} hours")
   ```

4. **Build dashboards** using MongoDB Charts, Tableau, or custom web apps

---

## Troubleshooting

### "Authentication failed"
- Check username/password in connection string
- Verify user has correct permissions in Atlas

### "Connection timeout"
- Check your IP is whitelisted in Network Access
- Or allow access from anywhere (0.0.0.0/0)

### "Module not found: pymongo"
```bash
pip3 install pymongo
```

### Import errors
- Make sure JSON files exist in output/ directory
- Check logs for detailed error messages

---

## Storage Estimates

Your data (based on ORD.json - 2,047 pairings):
- Raw JSON: ~10MB per file
- MongoDB storage: ~15MB per file (with indexes)
- All 11 PDFs: ~150-200MB total

MongoDB Atlas Free Tier: **512MB** - plenty of space! ✅

---

## Security Note

For production:
- Use strong passwords
- Restrict IP access (don't use 0.0.0.0/0)
- Enable encryption at rest
- Use read-only users for analytics
- Rotate credentials regularly

For testing/development:
- Atlas free tier with IP whitelist is fine
- Connection string in scripts is okay for personal use
- Can always rotate credentials later
