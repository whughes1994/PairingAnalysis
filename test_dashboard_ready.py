#!/usr/bin/env python3
"""
Test if dashboard is ready to launch.
Checks MongoDB connection and data availability.
"""

import sys
from pathlib import Path

def test_dashboard_ready():
    """Run all checks."""
    print("="*60)
    print("DASHBOARD READINESS CHECK")
    print("="*60)

    checks_passed = 0
    checks_total = 0

    # Check 1: Python packages
    print("\n1. Checking Python packages...")
    checks_total += 1
    try:
        import streamlit
        import plotly
        import pandas
        import pymongo
        print("   ✅ All required packages installed")
        checks_passed += 1
    except ImportError as e:
        print(f"   ❌ Missing package: {e}")
        print("   Run: pip3 install streamlit plotly pandas pymongo")

    # Check 2: Secrets file
    print("\n2. Checking MongoDB configuration...")
    checks_total += 1
    secrets_file = Path(".streamlit/secrets.toml")
    if secrets_file.exists():
        print("   ✅ Secrets file exists")
        checks_passed += 1

        # Check if it's configured
        with open(secrets_file) as f:
            content = f.read()
            if "YOUR_" in content or "username:password" in content:
                print("   ⚠️  WARNING: Secrets file not configured yet")
                print("   Edit .streamlit/secrets.toml with your MongoDB connection string")
    else:
        print("   ❌ Secrets file missing")
        print("   Create: .streamlit/secrets.toml")
        print('   Add: MONGO_URI = "your_connection_string"')

    # Check 3: MongoDB connection
    print("\n3. Testing MongoDB connection...")
    checks_total += 1
    try:
        from pymongo import MongoClient
        import streamlit as st

        # Try to load secrets
        try:
            if secrets_file.exists():
                # Read secrets manually for testing
                import toml
                secrets = toml.load(secrets_file)
                mongo_uri = secrets.get('MONGO_URI', 'mongodb://localhost:27017/')
            else:
                mongo_uri = 'mongodb://localhost:27017/'
        except:
            mongo_uri = 'mongodb://localhost:27017/'

        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=3000)
        client.admin.command('ping')
        print(f"   ✅ Connected to MongoDB")
        checks_passed += 1

        # Check 4: Data availability
        print("\n4. Checking data...")
        checks_total += 1
        db = client['airline_pairings']

        pairing_count = db.pairings.count_documents({})
        leg_count = db.legs.count_documents({})
        fleet_count = len(db.pairings.distinct('fleet'))

        if pairing_count > 0:
            print(f"   ✅ Found {pairing_count} pairings")
            print(f"   ✅ Found {leg_count} legs")
            print(f"   ✅ Found {fleet_count} fleets")
            checks_passed += 1

            # Check layover stations
            legs_with_layover = db.legs.count_documents({'layover_station': {'$ne': None}})
            if legs_with_layover > 0:
                print(f"   ✅ Layover stations populated ({legs_with_layover} legs)")
            else:
                print("   ⚠️  WARNING: Layover stations not populated")
                print("   Run: python3 fix_layover_stations_v2.py")
        else:
            print("   ❌ No data found")
            print("   Run: python3 mongodb_import.py --file output/ORD.json")

        client.close()

    except Exception as e:
        print(f"   ❌ MongoDB connection failed: {e}")
        print("   Check:")
        print("   - Is MongoDB running (local)?")
        print("   - Is connection string correct (Atlas)?")
        print("   - Is IP whitelisted (Atlas)?")

    # Check 5: Dashboard file
    print("\n5. Checking dashboard files...")
    checks_total += 1
    if Path("dashboard.py").exists():
        print("   ✅ dashboard.py exists")
        checks_passed += 1
    else:
        print("   ❌ dashboard.py missing")

    # Summary
    print("\n" + "="*60)
    print(f"SUMMARY: {checks_passed}/{checks_total} checks passed")
    print("="*60)

    if checks_passed == checks_total:
        print("\n🎉 READY TO LAUNCH!")
        print("\nRun: streamlit run dashboard.py")
        print("Opens at: http://localhost:8501")
        return True
    else:
        print("\n⚠️  NOT READY - Fix issues above first")
        print("\nSee DASHBOARD_SETUP.md for help")
        return False

if __name__ == '__main__':
    ready = test_dashboard_ready()
    sys.exit(0 if ready else 1)
