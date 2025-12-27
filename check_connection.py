#!/usr/bin/env python3
"""Quick script to check MongoDB connection and show current data."""

from pymongo import MongoClient
import sys

def check_connection():
    """Check what MongoDB connections work."""

    connections_to_try = [
        ("Local MongoDB", "mongodb://localhost:27017/"),
        ("Local MongoDB Alt Port", "mongodb://127.0.0.1:27017/"),
    ]

    print("Testing MongoDB connections...\n")

    working_connection = None

    for name, conn_str in connections_to_try:
        try:
            print(f"Trying {name}...")
            client = MongoClient(conn_str, serverSelectionTimeoutMS=2000)
            client.admin.command('ping')

            db = client['airline_pairings']
            count = db.pairings.count_documents({})

            print(f"  ✓ Connected! Found {count} pairings")
            working_connection = conn_str

            # Show sample data
            if count > 0:
                sample = db.pairings.find_one({}, {'id': 1, 'fleet': 1, 'base': 1})
                print(f"  Sample: {sample.get('id')} - {sample.get('fleet')} - {sample.get('base')}")

                # Check layover_station
                leg_sample = db.legs.find_one({}, {'layover_station': 1, 'origin_station': 1})
                print(f"  Layover station: {leg_sample.get('layover_station')}")
                print(f"  Origin station: {leg_sample.get('origin_station')}")

            client.close()
            break

        except Exception as e:
            print(f"  ✗ Failed: {e}")

    if not working_connection:
        print("\n" + "="*60)
        print("No local MongoDB connection found.")
        print("="*60)
        print("\nYou're likely using MongoDB Atlas (cloud).")
        print("\nTo use Atlas:")
        print("1. Get your connection string from MongoDB Compass")
        print("2. Run: python3 check_connection.py 'mongodb+srv://...'")
        print("\nOr install local MongoDB:")
        print("  brew tap mongodb/brew")
        print("  brew install mongodb-community")
        print("  brew services start mongodb-community")
    else:
        print(f"\n✓ Working connection: {working_connection}")
        return working_connection

if __name__ == '__main__':
    if len(sys.argv) > 1:
        # Test provided connection string
        conn_str = sys.argv[1]
        print(f"Testing provided connection: {conn_str[:50]}...\n")
        try:
            client = MongoClient(conn_str, serverSelectionTimeoutMS=5000)
            client.admin.command('ping')
            db = client['airline_pairings']
            count = db.pairings.count_documents({})
            print(f"✓ Connected! Found {count} pairings")

            if count > 0:
                sample = db.pairings.find_one({}, {'id': 1, 'fleet': 1})
                print(f"Sample: {sample}")
        except Exception as e:
            print(f"✗ Connection failed: {e}")
    else:
        check_connection()
