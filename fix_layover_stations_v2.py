#!/usr/bin/env python3
"""
Fix layover_station and origin_station fields - EFFICIENT VERSION.

This version uses batch operations and progress tracking.
"""

from pymongo import MongoClient, UpdateOne
from datetime import datetime
import sys

def fix_layover_stations(connection_string="mongodb://localhost:27017/"):
    """Update all legs with layover_station and origin_station - efficiently."""

    print("Connecting to MongoDB...")
    client = MongoClient(connection_string, serverSelectionTimeoutMS=10000)

    # Test connection
    try:
        client.admin.command('ping')
        print("✓ Connected to MongoDB")
    except Exception as e:
        print(f"✗ MongoDB connection failed: {e}")
        print("\nMake sure:")
        print("  - MongoDB is running (local), OR")
        print("  - You provided the correct Atlas connection string")
        return

    db = client['airline_pairings']

    # Check data exists
    pairing_count = db.pairings.count_documents({})
    leg_count = db.legs.count_documents({})

    print(f"\nFound {pairing_count} pairings and {leg_count} legs")

    if pairing_count == 0:
        print("No data found. Import data first with mongodb_import.py")
        return

    print("\n" + "="*60)
    print("UPDATING LAYOVER STATIONS")
    print("="*60)

    # Method 1: Update legs collection (FASTER - batch updates)
    print("\n[1/2] Updating legs collection...")

    batch_operations = []
    processed = 0

    # Process in batches to avoid memory issues
    batch_size = 100
    cursor = db.pairings.find({}, {'id': 1, 'duty_periods': 1}).batch_size(batch_size)

    for pairing in cursor:
        pairing_id = pairing['id']

        # Process each duty period
        for dp_idx, duty_period in enumerate(pairing.get('duty_periods', [])):
            legs = duty_period.get('legs', [])

            if not legs:
                continue

            # Calculate layover and origin stations
            layover_station = legs[-1].get('arrival_station') if legs else None
            origin_station = legs[0].get('departure_station') if legs else None

            # Prepare batch update for all legs in this duty period
            batch_operations.append(
                UpdateOne(
                    {
                        'pairing_id': pairing_id,
                        'duty_period_index': dp_idx
                    },
                    {
                        '$set': {
                            'layover_station': layover_station,
                            'origin_station': origin_station
                        }
                    }
                )
            )

        processed += 1

        # Execute batch every 500 operations
        if len(batch_operations) >= 500:
            result = db.legs.bulk_write(batch_operations, ordered=False)
            print(f"  Progress: {processed}/{pairing_count} pairings, {result.modified_count} legs updated")
            batch_operations = []

    # Execute remaining operations
    if batch_operations:
        result = db.legs.bulk_write(batch_operations, ordered=False)
        print(f"  Progress: {processed}/{pairing_count} pairings, {result.modified_count} legs updated")

    print(f"✓ Completed updating legs collection")

    # Method 2: Update pairings collection (duty_periods embedded)
    print("\n[2/2] Updating pairings collection (duty_periods)...")

    updated_count = 0
    cursor = db.pairings.find({})

    for pairing in cursor:
        updates = {}

        # Process each duty period
        for dp_idx, duty_period in enumerate(pairing.get('duty_periods', [])):
            legs = duty_period.get('legs', [])

            if not legs:
                continue

            # Calculate layover and origin stations
            layover_station = legs[-1].get('arrival_station') if legs else None
            origin_station = legs[0].get('departure_station') if legs else None

            # Prepare updates
            updates[f'duty_periods.{dp_idx}.layover_station'] = layover_station
            updates[f'duty_periods.{dp_idx}.origin_station'] = origin_station

        # Update if there are changes
        if updates:
            db.pairings.update_one(
                {'_id': pairing['_id']},
                {'$set': updates}
            )
            updated_count += 1

            if updated_count % 100 == 0:
                print(f"  Progress: {updated_count}/{pairing_count} pairings updated")

    print(f"✓ Completed updating {updated_count} pairings")

    # Verification
    print("\n" + "="*60)
    print("VERIFICATION")
    print("="*60)

    legs_with_layover = db.legs.count_documents({'layover_station': {'$ne': None}})
    print(f"\nLegs with layover_station: {legs_with_layover} / {leg_count}")

    # Show top layover cities
    print("\nTop 10 layover cities:")
    pipeline = [
        {'$match': {'layover_station': {'$ne': None}}},
        {'$group': {
            '_id': '$layover_station',
            'count': {'$sum': 1}
        }},
        {'$sort': {'count': -1}},
        {'$limit': 10}
    ]

    for idx, result in enumerate(db.legs.aggregate(pipeline), 1):
        print(f"  {idx:2d}. {result['_id']}: {result['count']} layovers")

    client.close()

    print("\n" + "="*60)
    print("✅ DONE!")
    print("="*60)
    print("\nYou can now query layover stations:")
    print("  - In playground: db.legs.find({ layover_station: 'LAX' })")
    print("  - In Python: python3 analytics_examples.py --query layovers")


if __name__ == '__main__':
    connection = sys.argv[1] if len(sys.argv) > 1 else "mongodb://localhost:27017/"

    print("="*60)
    print("FIX LAYOVER STATIONS - EFFICIENT VERSION")
    print("="*60)
    print(f"Connection: {connection[:50]}...")
    print()

    try:
        fix_layover_stations(connection)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user (Ctrl+C)")
        print("Partial updates may have been applied.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
