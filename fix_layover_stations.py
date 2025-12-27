#!/usr/bin/env python3
"""
Fix layover_station and origin_station fields that are currently null.

This script updates existing documents in MongoDB to populate the computed fields.
"""

from pymongo import MongoClient
from datetime import datetime

def fix_layover_stations(connection_string="mongodb://localhost:27017/"):
    """Update all legs with layover_station and origin_station."""

    print("Connecting to MongoDB...")
    client = MongoClient(connection_string)
    db = client['airline_pairings']

    # Test connection
    try:
        client.admin.command('ping')
        print("✓ Connected to MongoDB")
    except:
        print("✗ MongoDB connection failed. Make sure MongoDB is running.")
        return

    print("\nUpdating layover_station and origin_station fields...")

    # Get all pairings
    pairings = db.pairings.find({})

    updated_legs = 0
    updated_pairings = 0

    for pairing in pairings:
        pairing_id = pairing['id']

        # Process each duty period
        for dp_idx, duty_period in enumerate(pairing.get('duty_periods', [])):
            legs = duty_period.get('legs', [])

            if not legs:
                continue

            # Calculate layover and origin stations
            layover_station = legs[-1].get('arrival_station') if legs else None
            origin_station = legs[0].get('departure_station') if legs else None

            # Update the duty period in the pairing document
            update_result = db.pairings.update_one(
                {'_id': pairing['_id']},
                {
                    '$set': {
                        f'duty_periods.{dp_idx}.layover_station': layover_station,
                        f'duty_periods.{dp_idx}.origin_station': origin_station
                    }
                }
            )

            if update_result.modified_count > 0:
                updated_pairings += 1

            # Update all legs in this duty period
            leg_update_result = db.legs.update_many(
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

            updated_legs += leg_update_result.modified_count

    print(f"\n✓ Updated {updated_pairings} duty periods in pairings collection")
    print(f"✓ Updated {updated_legs} legs in legs collection")

    # Verify
    print("\nVerification:")
    legs_with_layover = db.legs.count_documents({'layover_station': {'$ne': None}})
    total_legs = db.legs.count_documents({})
    print(f"  Legs with layover_station: {legs_with_layover} / {total_legs}")

    # Show sample
    print("\nSample layover cities:")
    pipeline = [
        {'$match': {'layover_station': {'$ne': None}}},
        {'$group': {
            '_id': '$layover_station',
            'count': {'$sum': 1}
        }},
        {'$sort': {'count': -1}},
        {'$limit': 5}
    ]

    for result in db.legs.aggregate(pipeline):
        print(f"  {result['_id']}: {result['count']} layovers")

    client.close()
    print("\n✓ Done!")


if __name__ == '__main__':
    import sys

    connection = sys.argv[1] if len(sys.argv) > 1 else "mongodb://localhost:27017/"
    fix_layover_stations(connection)
