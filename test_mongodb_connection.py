#!/usr/bin/env python3
"""
Test MongoDB connection and show what the import will look like.

Usage:
    # Test with MongoDB Atlas
    python3 test_mongodb_connection.py "mongodb+srv://user:pass@cluster.mongodb.net/"

    # Test with local MongoDB
    python3 test_mongodb_connection.py
"""

import sys
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError


def test_connection(connection_string="mongodb://localhost:27017/"):
    """Test MongoDB connection."""
    print("=" * 80)
    print("MONGODB CONNECTION TEST")
    print("=" * 80)
    print(f"\nConnection string: {connection_string[:50]}...")

    try:
        # Connect with short timeout for quick failure
        print("\n1. Connecting to MongoDB...")
        client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)

        # Test connection
        print("2. Testing connection...")
        client.admin.command('ping')
        print("   ✓ Connection successful!")

        # Get server info
        print("\n3. Server information:")
        server_info = client.server_info()
        print(f"   MongoDB version: {server_info['version']}")

        # Show databases
        print("\n4. Existing databases:")
        dbs = client.list_database_names()
        for db in dbs:
            print(f"   - {db}")

        # Test airline_pairings database
        print("\n5. Checking airline_pairings database:")
        db = client['airline_pairings']

        if 'airline_pairings' in dbs:
            print("   ✓ Database exists")
            collections = db.list_collection_names()
            print(f"   Collections: {collections}")

            # Show counts
            if 'pairings' in collections:
                count = db.pairings.count_documents({})
                print(f"   Pairings: {count}")
            if 'legs' in collections:
                count = db.legs.count_documents({})
                print(f"   Legs: {count}")
        else:
            print("   Database does not exist yet (will be created on first import)")

        print("\n" + "=" * 80)
        print("✅ CONNECTION TEST PASSED")
        print("=" * 80)
        print("\nYou're ready to import data!")
        print("\nNext steps:")
        print("  1. Import your data:")
        print(f'     python3 mongodb_import.py --connection "{connection_string}" --file output/ORD.json')
        print("\n  2. Run analytics:")
        print(f'     python3 analytics_examples.py --connection "{connection_string}"')

        client.close()
        return True

    except ConnectionFailure as e:
        print(f"\n❌ Connection failed: {e}")
        print("\nTroubleshooting:")
        print("  - Is MongoDB running?")
        print("  - Is the connection string correct?")
        print("  - Is your IP whitelisted (for Atlas)?")
        return False

    except ServerSelectionTimeoutError as e:
        print(f"\n❌ Connection timeout: {e}")
        print("\nTroubleshooting:")
        print("  - Check if MongoDB is running")
        print("  - Verify network connectivity")
        print("  - For Atlas: check Network Access settings")
        return False

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False


def show_import_preview():
    """Show what the import will create."""
    print("\n" + "=" * 80)
    print("IMPORT PREVIEW")
    print("=" * 80)
    print("\nWhen you import output/ORD.json, it will create:\n")

    print("📁 Database: airline_pairings")
    print("   ├── 📊 Collection: bid_periods (4 documents)")
    print("   │   - 787 CHICAGO JAN 2026 (70 pairings)")
    print("   │   - 756 CHICAGO JAN 2026 (65 pairings)")
    print("   │   - 737 CHICAGO JAN 2026 (1,262 pairings)")
    print("   │   - 320 CHICAGO JAN 2026 (650 pairings)")
    print("   │")
    print("   ├── 📊 Collection: pairings (2,047 documents)")
    print("   │   Each with: id, category, dates, duty_periods, credit, etc.")
    print("   │   Indexed on: id, fleet, base, dates, credit_minutes")
    print("   │")
    print("   └── 📊 Collection: legs (~10,000+ documents)")
    print("       Each with: equipment, route, times, meal codes")
    print("       Indexed on: pairing_id, equipment, stations")

    print("\n" + "=" * 80)


if __name__ == '__main__':
    connection_string = sys.argv[1] if len(sys.argv) > 1 else "mongodb://localhost:27017/"

    success = test_connection(connection_string)

    if success:
        show_import_preview()
    else:
        print("\n" + "=" * 80)
        print("SETUP OPTIONS")
        print("=" * 80)
        print("\n1. MongoDB Atlas (Cloud - Easiest):")
        print("   - Sign up: https://www.mongodb.com/cloud/atlas/register")
        print("   - Get connection string")
        print("   - Run: python3 test_mongodb_connection.py 'YOUR_CONNECTION_STRING'")
        print("\n2. Local MongoDB:")
        print("   - Install: brew install mongodb-community")
        print("   - Start: brew services start mongodb-community")
        print("   - Run: python3 test_mongodb_connection.py")

    sys.exit(0 if success else 1)
