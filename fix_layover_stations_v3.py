#!/usr/bin/env python3
"""
Fix layover_station fields - CORRECTED VERSION.

Rules:
- 1-day trips: layover_station should be null (no overnight)
- Multi-day trips: layover_station should be null for the LAST duty period (going home)
- Multi-day trips: layover_station for intermediate duty periods = arrival_station of last leg
"""

from pymongo import MongoClient, UpdateOne
from datetime import datetime
import sys

def fix_layover_stations(connection_string="mongodb://localhost:27017/"):
    """Update all legs with correct layover_station values."""

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
    print("UPDATING LAYOVER STATIONS (CORRECTED LOGIC)")
    print("="*60)
    print("\nRules:")
    print("  - 1-day trips: layover_station = null (no overnight)")
    print("  - Last duty period: layover_station = null (going home)")
    print("  - Intermediate duty periods: layover_station = arrival station")
    print()

    # Update legs collection
    print("[1/2] Updating legs collection...")

    batch_operations = []
    processed = 0
    stats = {'null_count': 0, 'layover_count': 0}

    # Process in batches
    batch_size = 100
    cursor = db.pairings.find({}, {'id': 1, 'days': 1, 'base': 1, 'duty_periods': 1}).batch_size(batch_size)

    for pairing in cursor:
        pairing_id = pairing['id']
        days = int(pairing.get('days', '1'))
        base = pairing.get('base', '')
        duty_periods = pairing.get('duty_periods', [])
        total_duty_periods = len(duty_periods)

        # Process each duty period
        for dp_idx, duty_period in enumerate(duty_periods):
            legs = duty_period.get('legs', [])

            if not legs:
                continue

            # Calculate layover station
            is_last_duty_period = (dp_idx == total_duty_periods - 1)

            # Layover station logic:
            # - If it's a 1-day trip OR the last duty period: layover_station = null
            # - Otherwise: layover_station = arrival station of last leg
            if days == 1 or is_last_duty_period:
                layover_station = None
                stats['null_count'] += 1
            else:
                layover_station = legs[-1].get('arrival_station')
                stats['layover_count'] += 1

            # Origin station is always the departure of the first leg
            origin_station = legs[0].get('departure_station') if legs else None

            # Batch update for all legs in this duty period
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
                    },
                    upsert=False
                )
            )

        processed += 1

        # Execute batch every 500 operations
        if len(batch_operations) >= 500:
            result = db.legs.bulk_write(batch_operations, ordered=False)
            print(f"  Progress: {processed}/{pairing_count} pairings")
            batch_operations = []

    # Execute remaining operations
    if batch_operations:
        result = db.legs.bulk_write(batch_operations, ordered=False)
        print(f"  Progress: {processed}/{pairing_count} pairings")

    print(f"✓ Completed updating legs collection")
    print(f"  - Duty periods with layovers: {stats['layover_count']}")
    print(f"  - Duty periods without layovers (null): {stats['null_count']}")

    # Update pairings collection (duty_periods embedded)
    print("\n[2/2] Updating pairings collection...")

    updated_pairings = 0
    cursor = db.pairings.find({}, {'_id': 1, 'days': 1, 'duty_periods': 1}).batch_size(batch_size)

    for pairing in cursor:
        days = int(pairing.get('days', '1'))
        duty_periods = pairing.get('duty_periods', [])
        total_duty_periods = len(duty_periods)
        modified = False

        for dp_idx, duty_period in enumerate(duty_periods):
            legs = duty_period.get('legs', [])

            if not legs:
                continue

            # Same logic as above
            is_last_duty_period = (dp_idx == total_duty_periods - 1)

            if days == 1 or is_last_duty_period:
                new_layover = None
            else:
                new_layover = legs[-1].get('arrival_station')

            new_origin = legs[0].get('departure_station')

            # Update if changed
            if duty_period.get('layover_station') != new_layover or \
               duty_period.get('origin_station') != new_origin:
                duty_period['layover_station'] = new_layover
                duty_period['origin_station'] = new_origin
                modified = True

                # Also update all legs in this duty period
                for leg in legs:
                    leg['layover_station'] = new_layover
                    leg['origin_station'] = new_origin

        # Save if modified
        if modified:
            db.pairings.update_one(
                {'_id': pairing['_id']},
                {'$set': {'duty_periods': duty_periods}}
            )
            updated_pairings += 1

            if updated_pairings % 100 == 0:
                print(f"  Progress: {updated_pairings} pairings updated")

    print(f"✓ Completed updating {updated_pairings} pairings")

    # Verification
    print("\n" + "="*60)
    print("VERIFICATION")
    print("="*60)

    # Check 1-day trips
    one_day_with_layover = db.legs.count_documents({
        'layover_station': {'$ne': None},
        'pairing_id': {'$regex': '^O3'}  # 1-day trips start with O3
    })

    # Check last duty periods
    last_dp_with_layover = 0
    for pairing in db.pairings.find({}, {'duty_periods': 1}):
        duty_periods = pairing.get('duty_periods', [])
        if duty_periods and duty_periods[-1].get('layover_station'):
            last_dp_with_layover += 1

    print(f"\n1-day trips with layovers: {one_day_with_layover} (should be 0)")
    print(f"Last duty periods with layovers: {last_dp_with_layover} (should be 0)")

    if one_day_with_layover == 0 and last_dp_with_layover == 0:
        print("\n✓ All checks passed!")
    else:
        print("\n⚠ Warning: Some issues detected")

    # Sample data
    print("\n" + "="*60)
    print("SAMPLE DATA")
    print("="*60)

    # 1-day sample
    one_day = db.pairings.find_one({'days': '1'}, {'id': 1, 'days': 1, 'duty_periods.layover_station': 1})
    print(f"\n1-day pairing {one_day.get('id')}:")
    for idx, dp in enumerate(one_day.get('duty_periods', [])):
        print(f"  Duty period {idx}: layover_station = {dp.get('layover_station')}")

    # 3-day sample
    three_day = db.pairings.find_one({'days': '3'}, {'id': 1, 'days': 1, 'duty_periods.layover_station': 1})
    print(f"\n3-day pairing {three_day.get('id')}:")
    for idx, dp in enumerate(three_day.get('duty_periods', [])):
        print(f"  Duty period {idx}: layover_station = {dp.get('layover_station')}")

    client.close()
    print("\n✓ Done!")

if __name__ == '__main__':
    # Get connection string from command line or use default
    if len(sys.argv) > 1:
        connection_string = sys.argv[1]
    else:
        connection_string = "mongodb://localhost:27017/"

    fix_layover_stations(connection_string)
