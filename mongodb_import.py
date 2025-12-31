#!/usr/bin/env python3
"""
Import parsed pairing JSON files into MongoDB.

Usage:
    python3 mongodb_import.py --file output/ORD.json
    python3 mongodb_import.py --dir output/

Requirements:
    pip install pymongo
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

try:
    from pymongo import MongoClient, ASCENDING, DESCENDING
    from pymongo.errors import ConnectionFailure, BulkWriteError
except ImportError:
    print("Error: pymongo not installed. Run: pip install pymongo")
    sys.exit(1)

try:
    import toml
except ImportError:
    toml = None  # Optional dependency


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

        # If not found, return None
        return None

    except Exception as e:
        print(f"Warning: Could not read .streamlit/secrets.toml: {e}")
        return None


class MongoDBImporter:
    """Import pairing data into MongoDB."""

    def __init__(self, connection_string: str = "mongodb://localhost:27017/"):
        """Initialize MongoDB connection."""
        self.client = MongoClient(connection_string)
        self.db = self.client['airline_pairings']

        # Collections
        self.bid_periods = self.db['bid_periods']
        self.pairings = self.db['pairings']
        self.legs = self.db['legs']

    def test_connection(self) -> bool:
        """Test MongoDB connection."""
        try:
            self.client.admin.command('ping')
            print("✓ MongoDB connection successful")
            return True
        except ConnectionFailure:
            print("✗ MongoDB connection failed")
            return False

    def create_indexes(self):
        """Create indexes for efficient querying."""
        print("\nCreating indexes...")

        # Bid Period indexes
        self.bid_periods.create_index([
            ("bid_month_year", ASCENDING),
            ("fleet", ASCENDING),
            ("base", ASCENDING)
        ], unique=True, name="bid_period_unique")

        self.bid_periods.create_index([("effective_date_iso", ASCENDING)])

        # Pairing indexes
        self.pairings.create_index([("id", ASCENDING)], name="pairing_id")
        self.pairings.create_index([("pairing_category", ASCENDING)])
        self.pairings.create_index([("effective_date_iso", ASCENDING)])
        self.pairings.create_index([("bid_period_id", ASCENDING)])
        self.pairings.create_index([("credit_minutes", DESCENDING)])
        self.pairings.create_index([("flight_time_minutes", DESCENDING)])

        # Leg indexes
        self.legs.create_index([("pairing_id", ASCENDING)])
        self.legs.create_index([("equipment", ASCENDING)])
        self.legs.create_index([("departure_station", ASCENDING)])
        self.legs.create_index([("arrival_station", ASCENDING)])
        self.legs.create_index([("departure_time_minutes", ASCENDING)])
        self.legs.create_index([("deadhead", ASCENDING)])
        self.legs.create_index([("layover_station", ASCENDING)])  # For overnight queries
        self.legs.create_index([("origin_station", ASCENDING)])   # For duty period origin

        print("✓ Indexes created")

    def import_file(self, json_file: Path, clear_existing: bool = False) -> Dict[str, int]:
        """
        Import a single JSON file.

        Returns:
            Dictionary with counts of imported records
        """
        print(f"\nImporting: {json_file.name}")

        with open(json_file) as f:
            data = json.load(f)

        stats = {
            'bid_periods': 0,
            'pairings': 0,
            'legs': 0,
            'duty_periods': 0
        }

        # Process each bid period
        for bid_period_data in data['data']:
            # Extract pairings before inserting bid period
            pairings_data = bid_period_data.pop('pairings', [])

            # Insert or update bid period
            bid_period_key = {
                'bid_month_year': bid_period_data['bid_month_year'],
                'fleet': bid_period_data['fleet'],
                'base': bid_period_data['base']
            }

            # Add metadata
            bid_period_data['imported_at'] = datetime.utcnow()
            bid_period_data['source_file'] = json_file.name

            result = self.bid_periods.update_one(
                bid_period_key,
                {'$set': bid_period_data},
                upsert=True
            )

            if result.upserted_id or result.modified_count:
                stats['bid_periods'] += 1

            # Get bid period ID for reference
            bid_period_record = self.bid_periods.find_one(bid_period_key)
            bid_period_id = bid_period_record['_id']

            # Process pairings
            pairing_docs = []
            leg_docs = []

            for pairing_data in pairings_data:
                # Extract duty periods
                duty_periods = pairing_data.pop('duty_periods', [])

                # Add references
                pairing_data['bid_period_id'] = bid_period_id
                pairing_data['fleet'] = bid_period_data['fleet']
                pairing_data['base'] = bid_period_data['base']
                pairing_data['imported_at'] = datetime.utcnow()

                # Count duty periods
                pairing_data['duty_period_count'] = len(duty_periods)
                stats['duty_periods'] += len(duty_periods)

                # Extract all legs from duty periods
                all_legs = []
                for dp_idx, duty_period in enumerate(duty_periods):
                    legs = duty_period.get('legs', [])

                    # Get duty period layover and origin stations
                    dp_layover = duty_period.get('layover_station')
                    dp_origin = duty_period.get('origin_station')

                    for leg_idx, leg in enumerate(legs):
                        leg['pairing_id'] = pairing_data['id']
                        leg['bid_period_id'] = bid_period_id
                        leg['duty_period_index'] = dp_idx
                        leg['leg_index'] = leg_idx
                        leg['fleet'] = bid_period_data['fleet']
                        leg['base'] = bid_period_data['base']
                        leg['layover_station'] = dp_layover  # Overnight destination
                        leg['origin_station'] = dp_origin    # Duty period start
                        leg['imported_at'] = datetime.utcnow()
                        all_legs.append(leg)

                # Store duty periods as embedded documents
                pairing_data['duty_periods'] = duty_periods
                pairing_data['leg_count'] = len(all_legs)

                pairing_docs.append(pairing_data)
                leg_docs.extend(all_legs)

            # Bulk insert pairings
            if pairing_docs:
                if clear_existing:
                    self.pairings.delete_many({'bid_period_id': bid_period_id})

                try:
                    self.pairings.insert_many(pairing_docs, ordered=False)
                    stats['pairings'] += len(pairing_docs)
                except BulkWriteError as e:
                    # Count successful inserts
                    stats['pairings'] += e.details['nInserted']
                    print(f"  Warning: {len(e.details['writeErrors'])} duplicate pairings skipped")

            # Bulk insert legs
            if leg_docs:
                if clear_existing:
                    self.legs.delete_many({'bid_period_id': bid_period_id})

                try:
                    self.legs.insert_many(leg_docs, ordered=False)
                    stats['legs'] += len(leg_docs)
                except BulkWriteError as e:
                    stats['legs'] += e.details['nInserted']
                    print(f"  Warning: {len(e.details['writeErrors'])} duplicate legs skipped")

        return stats

    def import_directory(self, directory: Path, clear_existing: bool = False) -> Dict[str, int]:
        """Import all JSON files from a directory."""
        json_files = list(directory.glob("*.json"))

        if not json_files:
            print(f"No JSON files found in {directory}")
            return {}

        print(f"Found {len(json_files)} JSON files")

        total_stats = {
            'bid_periods': 0,
            'pairings': 0,
            'legs': 0,
            'duty_periods': 0
        }

        for json_file in json_files:
            stats = self.import_file(json_file, clear_existing)
            for key in total_stats:
                total_stats[key] += stats[key]

        return total_stats

    def print_stats(self):
        """Print database statistics."""
        print("\n" + "=" * 60)
        print("DATABASE STATISTICS")
        print("=" * 60)

        print(f"Bid Periods: {self.bid_periods.count_documents({})}")
        print(f"Pairings: {self.pairings.count_documents({})}")
        print(f"Legs: {self.legs.count_documents({})}")

        print("\nBy Fleet:")
        pipeline = [
            {'$group': {
                '_id': '$fleet',
                'pairings': {'$sum': 1},
                'avg_credit': {'$avg': '$credit_minutes'}
            }},
            {'$sort': {'pairings': -1}}
        ]
        for result in self.pairings.aggregate(pipeline):
            print(f"  {result['_id']}: {result['pairings']} pairings "
                  f"(avg credit: {result['avg_credit']:.0f} min)")

        print("\nBy Base:")
        pipeline[0]['$group']['_id'] = '$base'
        for result in self.pairings.aggregate(pipeline):
            print(f"  {result['_id']}: {result['pairings']} pairings")

    def close(self):
        """Close MongoDB connection."""
        self.client.close()


def main():
    parser = argparse.ArgumentParser(
        description="Import pairing data to MongoDB",
        epilog="If --connection is not provided, will try to read from .streamlit/secrets.toml"
    )
    parser.add_argument('--file', type=str, help="JSON file to import")
    parser.add_argument('--dir', type=str, help="Directory of JSON files to import")
    parser.add_argument('--connection', type=str,
                       help="MongoDB connection string (or use .streamlit/secrets.toml)")
    parser.add_argument('--clear', action='store_true',
                       help="Clear existing data before import")
    parser.add_argument('--skip-indexes', action='store_true',
                       help="Skip index creation")

    args = parser.parse_args()

    if not args.file and not args.dir:
        parser.print_help()
        print("\nError: Must specify --file or --dir")
        sys.exit(1)

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

    # Initialize importer
    print("Connecting to MongoDB...")
    importer = MongoDBImporter(connection_string)

    if not importer.test_connection():
        sys.exit(1)

    # Create indexes
    if not args.skip_indexes:
        importer.create_indexes()

    # Import data
    if args.file:
        stats = importer.import_file(Path(args.file), args.clear)
    else:
        stats = importer.import_directory(Path(args.dir), args.clear)

    # Print results
    print("\n" + "=" * 60)
    print("IMPORT COMPLETE")
    print("=" * 60)
    print(f"Bid Periods: {stats['bid_periods']}")
    print(f"Pairings: {stats['pairings']}")
    print(f"Duty Periods: {stats['duty_periods']}")
    print(f"Legs: {stats['legs']}")

    # Show database stats
    importer.print_stats()

    importer.close()


if __name__ == '__main__':
    main()
