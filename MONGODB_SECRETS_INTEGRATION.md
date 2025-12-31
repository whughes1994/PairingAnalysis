# MongoDB Secrets Integration

**Date:** 2025-12-30
**Feature:** MongoDB import script now reads connection string from `.streamlit/secrets.toml`

## Overview

The `mongodb_import.py` script now automatically reads the MongoDB connection string from `.streamlit/secrets.toml`, eliminating the need to specify `--connection` on every import.

## Changes Made

### File Modified: `mongodb_import.py`

#### 1. Added TOML Support (Lines 27-30)
```python
try:
    import toml
except ImportError:
    toml = None  # Optional dependency
```

#### 2. New Helper Function (Lines 33-63)
```python
def get_connection_from_secrets() -> str:
    """
    Read MongoDB connection string from .streamlit/secrets.toml

    Returns:
        Connection string or None if not found
    """
    secrets_path = Path(".streamlit/secrets.toml")

    if not secrets_path.exists():
        return None

    if toml is None:
        print("Warning: toml package not installed. Cannot read secrets.toml")
        print("Install with: pip install toml")
        return None

    try:
        with open(secrets_path, 'r') as f:
            secrets = toml.load(f)

        # Try to get MONGO_URI from secrets
        if 'MONGO_URI' in secrets:
            return secrets['MONGO_URI']

        return None

    except Exception as e:
        print(f"Warning: Could not read .streamlit/secrets.toml: {e}")
        return None
```

#### 3. Updated main() Function (Lines 300-338)

**Before:**
```python
parser.add_argument('--connection', type=str,
                   default="mongodb://localhost:27017/",
                   help="MongoDB connection string")

importer = MongoDBImporter(args.connection)
```

**After:**
```python
parser.add_argument('--connection', type=str,
                   help="MongoDB connection string (or use .streamlit/secrets.toml)")

# Determine connection string
connection_string = args.connection

if not connection_string:
    # Try to read from secrets.toml
    print("No --connection provided, checking .streamlit/secrets.toml...")
    connection_string = get_connection_from_secrets()

    if connection_string:
        print("✓ Using connection string from .streamlit/secrets.toml")
    else:
        print("✗ No connection string found in .streamlit/secrets.toml")
        print("Using default: mongodb://localhost:27017/")
        connection_string = "mongodb://localhost:27017/"

importer = MongoDBImporter(connection_string)
```

## Usage

### Option 1: Use Secrets File (Recommended)

**Setup .streamlit/secrets.toml:**
```toml
MONGO_URI = "mongodb+srv://username:password@cluster.mongodb.net/"
```

**Import without --connection flag:**
```bash
# Simple - no connection string needed!
python3 mongodb_import.py --file output/ORDDSL_FEB2026.json

# Output:
# No --connection provided, checking .streamlit/secrets.toml...
# ✓ Using connection string from .streamlit/secrets.toml
# Connecting to MongoDB...
# ✓ MongoDB connection successful
```

### Option 2: Specify Connection (Still Supported)

**Override secrets file with explicit connection:**
```bash
python3 mongodb_import.py \
  --file output/ORDDSL_FEB2026.json \
  --connection "mongodb+srv://user:pass@cluster.mongodb.net/"
```

### Option 3: Local MongoDB (Fallback)

**If no secrets file and no --connection flag:**
```bash
python3 mongodb_import.py --file output/ORDDSL_FEB2026.json

# Output:
# No --connection provided, checking .streamlit/secrets.toml...
# ✗ No connection string found in .streamlit/secrets.toml
# Using default: mongodb://localhost:27017/
```

## Benefits

### 1. **Security**
- Connection strings not exposed in command history
- Secrets file can be gitignored
- Same secrets file used by Streamlit dashboard

### 2. **Convenience**
- No need to type long connection strings
- One central configuration file
- Copy-paste safe (no credentials in terminal)

### 3. **Consistency**
- Same configuration for both import script and dashboard
- Change connection once, works everywhere
- Reduces configuration errors

## Priority Order

The script checks for connection strings in this order:

1. **`--connection` flag** (highest priority - overrides everything)
2. **`.streamlit/secrets.toml`** (automatic fallback)
3. **`mongodb://localhost:27017/`** (default if nothing found)

## Example Workflow

### Complete Import Workflow (.DAT File → MongoDB)

```bash
# 1. Parse .DAT file
python3 -m src.main \
  -i "Pairing Source Docs/February 2026/ORDDSL.DAT" \
  -o "output/ORDDSL_FEB2026.json"

# 2. Import to MongoDB (uses secrets.toml automatically)
python3 mongodb_import.py --file output/ORDDSL_FEB2026.json

# 3. View in dashboard (also uses secrets.toml)
streamlit run unified_dashboard.py
```

**No connection strings needed anywhere!**

## Tested

### February 2026 Import
✅ **Successfully imported using secrets.toml**

**Command:**
```bash
python3 mongodb_import.py --file output/ORDDSL_FEB2026.json
```

**Output:**
```
No --connection provided, checking .streamlit/secrets.toml...
✓ Using connection string from .streamlit/secrets.toml
Connecting to MongoDB...
✓ MongoDB connection successful

Creating indexes...
✓ Indexes created

Importing: ORDDSL_FEB2026.json

============================================================
IMPORT COMPLETE
============================================================
Bid Periods: 4
Pairings: 2313
Duty Periods: 6624
Legs: 12072
```

**Database Stats After Import:**
```
BID PERIODS IN DATABASE:
  JAN 2026 | 787 | CHICAGO | 159 pairings
  JAN 2026 | 756 | CHICAGO | 127 pairings
  JAN 2026 | 737 | CHICAGO | 2,707 pairings
  JAN 2026 | 320 | CHICAGO | 1,367 pairings
  FEB 2026 | 787 | CHICAGO | 159 pairings
  FEB 2026 | 756 | CHICAGO | 127 pairings
  FEB 2026 | 737 | CHICAGO | 2,707 pairings
  FEB 2026 | 320 | CHICAGO | 1,367 pairings

TOTAL STATS:
  Total pairings: 4,360
  Total legs: 23,064
```

## Dependencies

### Required
- `pymongo` - MongoDB driver

### Optional
- `toml` - For reading secrets.toml (already installed with Streamlit)

**Install if needed:**
```bash
pip install toml
```

## Configuration File Format

### .streamlit/secrets.toml
```toml
# MongoDB connection string
MONGO_URI = "mongodb+srv://username:password@cluster.mongodb.net/"

# Other dashboard secrets can go here too
# API_KEY = "your-api-key"
```

**Security Notes:**
- Add `.streamlit/` to `.gitignore`
- Never commit secrets.toml to version control
- Use environment-specific secrets files for prod/dev

## Backward Compatibility

✅ **Fully backward compatible**

All existing commands still work:
```bash
# Old way (still works)
python3 mongodb_import.py \
  --file output/file.json \
  --connection "mongodb+srv://..."

# New way (simpler)
python3 mongodb_import.py --file output/file.json
```

## Error Handling

### Secrets File Not Found
```
No --connection provided, checking .streamlit/secrets.toml...
✗ No connection string found in .streamlit/secrets.toml
Using default: mongodb://localhost:27017/
```

### TOML Package Not Installed
```
No --connection provided, checking .streamlit/secrets.toml...
Warning: toml package not installed. Cannot read secrets.toml
Install with: pip install toml
Using default: mongodb://localhost:27017/
```

### Invalid Secrets File
```
Warning: Could not read .streamlit/secrets.toml: [error message]
Using default: mongodb://localhost:27017/
```

## Dashboard Integration

The unified dashboard (`unified_dashboard.py`) already uses `.streamlit/secrets.toml`:

```python
@st.cache_resource
def get_mongodb_connection():
    """Connect to MongoDB using credentials from secrets."""
    try:
        mongo_uri = st.secrets["MONGO_URI"]
        client = MongoClient(mongo_uri)
        # ...
```

Now **both** the dashboard and import script read from the same secrets file! 🎉

## Summary

✅ **Status:** Secrets integration complete and tested

**Key Benefits:**
- No more typing connection strings
- Secure credential management
- Consistent configuration
- Fully backward compatible

**Files Modified:**
- `mongodb_import.py` (added secrets support)

**Files Used:**
- `.streamlit/secrets.toml` (configuration file)

The MongoDB import process is now streamlined - just parse and import, no connection strings needed!
