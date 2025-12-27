#!/usr/bin/env python3
"""
Example analytics queries for pairing data in MongoDB.

Run after importing data with mongodb_import.py
"""

from pymongo import MongoClient
from datetime import datetime
import json


class PairingAnalytics:
    """Analytics queries for pairing data."""

    def __init__(self, connection_string: str = "mongodb://localhost:27017/"):
        self.client = MongoClient(connection_string)
        self.db = self.client['airline_pairings']

    def fleet_summary(self):
        """Summary statistics by fleet."""
        print("\n" + "=" * 80)
        print("FLEET SUMMARY")
        print("=" * 80)

        pipeline = [
            {
                '$group': {
                    '_id': '$fleet',
                    'total_pairings': {'$sum': 1},
                    'avg_credit_hours': {'$avg': {'$divide': ['$credit_minutes', 60]}},
                    'max_credit_hours': {'$max': {'$divide': ['$credit_minutes', 60]}},
                    'avg_days': {'$avg': {'$toInt': '$days'}},
                    'total_legs': {'$sum': '$leg_count'}
                }
            },
            {'$sort': {'total_pairings': -1}}
        ]

        for result in self.db.pairings.aggregate(pipeline):
            print(f"\n{result['_id']}:")
            print(f"  Pairings: {result['total_pairings']}")
            print(f"  Avg Credit: {result['avg_credit_hours']:.2f} hours")
            print(f"  Max Credit: {result['max_credit_hours']:.2f} hours")
            print(f"  Avg Days: {result['avg_days']:.1f}")
            print(f"  Total Legs: {result['total_legs']}")

    def route_analysis(self, limit: int = 20):
        """Most common routes."""
        print("\n" + "=" * 80)
        print(f"TOP {limit} ROUTES")
        print("=" * 80)

        pipeline = [
            {
                '$group': {
                    '_id': {
                        'from': '$departure_station',
                        'to': '$arrival_station'
                    },
                    'count': {'$sum': 1},
                    'avg_flight_time_hours': {
                        '$avg': {'$divide': ['$flight_time_minutes', 60]}
                    },
                    'deadhead_count': {
                        '$sum': {'$cond': ['$deadhead', 1, 0]}
                    }
                }
            },
            {'$sort': {'count': -1}},
            {'$limit': limit}
        ]

        for idx, result in enumerate(self.db.legs.aggregate(pipeline), 1):
            route = result['_id']
            print(f"{idx:2d}. {route['from']} → {route['to']}: "
                  f"{result['count']} legs "
                  f"({result['avg_flight_time_hours']:.1f}h avg, "
                  f"{result['deadhead_count']} DH)")

    def time_of_day_analysis(self):
        """Departure time distribution."""
        print("\n" + "=" * 80)
        print("DEPARTURE TIME DISTRIBUTION")
        print("=" * 80)

        time_periods = [
            ("Early Morning (00-06)", 0, 360),
            ("Morning (06-12)", 360, 720),
            ("Afternoon (12-18)", 720, 1080),
            ("Evening (18-24)", 1080, 1440)
        ]

        for period_name, start, end in time_periods:
            count = self.db.legs.count_documents({
                'departure_time_minutes': {'$gte': start, '$lt': end}
            })
            print(f"{period_name:25s}: {count:5d} departures")

    def high_value_pairings(self, min_credit_hours: float = 20, limit: int = 10):
        """Find high-credit pairings."""
        print("\n" + "=" * 80)
        print(f"HIGH-VALUE PAIRINGS (>{min_credit_hours}h credit)")
        print("=" * 80)

        pairings = self.db.pairings.find({
            'credit_minutes': {'$gt': min_credit_hours * 60}
        }).sort('credit_minutes', -1).limit(limit)

        for idx, p in enumerate(pairings, 1):
            credit_hours = p['credit_minutes'] / 60
            print(f"{idx:2d}. {p['id']:8s} {p['fleet']:3s} {p['base']:10s} "
                  f"{credit_hours:5.2f}h  {p['pairing_category']}")

    def international_vs_domestic(self):
        """Compare international vs domestic pairings."""
        print("\n" + "=" * 80)
        print("INTERNATIONAL vs DOMESTIC")
        print("=" * 80)

        pipeline = [
            {
                '$group': {
                    '_id': {
                        '$cond': [
                            {'$gt': ['$international_flight_time_minutes', 0]},
                            'International',
                            'Domestic'
                        ]
                    },
                    'count': {'$sum': 1},
                    'avg_credit_hours': {
                        '$avg': {'$divide': ['$credit_minutes', 60]}
                    },
                    'avg_days': {
                        '$avg': {'$toInt': '$days'}
                    }
                }
            }
        ]

        for result in self.db.pairings.aggregate(pipeline):
            print(f"\n{result['_id']}:")
            print(f"  Count: {result['count']}")
            print(f"  Avg Credit: {result['avg_credit_hours']:.2f} hours")
            print(f"  Avg Days: {result['avg_days']:.1f}")

    def equipment_usage(self):
        """Equipment type usage."""
        print("\n" + "=" * 80)
        print("EQUIPMENT USAGE")
        print("=" * 80)

        pipeline = [
            {
                '$group': {
                    '_id': '$equipment',
                    'total_legs': {'$sum': 1},
                    'avg_flight_time_hours': {
                        '$avg': {'$divide': ['$flight_time_minutes', 60]}
                    },
                    'unique_routes': {
                        '$addToSet': {
                            '$concat': ['$departure_station', '-', '$arrival_station']
                        }
                    }
                }
            },
            {
                '$project': {
                    'total_legs': 1,
                    'avg_flight_time_hours': 1,
                    'route_count': {'$size': '$unique_routes'}
                }
            },
            {'$sort': {'total_legs': -1}}
        ]

        for result in self.db.legs.aggregate(pipeline):
            print(f"{result['_id']:5s}: {result['total_legs']:5d} legs, "
                  f"{result['avg_flight_time_hours']:5.2f}h avg, "
                  f"{result['route_count']:3d} routes")

    def hotel_frequency(self, limit: int = 15):
        """Most common hotels."""
        print("\n" + "=" * 80)
        print(f"TOP {limit} HOTELS")
        print("=" * 80)

        pipeline = [
            {'$unwind': '$duty_periods'},
            {'$match': {'duty_periods.hotel': {'$ne': None}}},
            {
                '$group': {
                    '_id': '$duty_periods.hotel',
                    'count': {'$sum': 1}
                }
            },
            {'$sort': {'count': -1}},
            {'$limit': limit}
        ]

        for idx, result in enumerate(self.db.pairings.aggregate(pipeline), 1):
            print(f"{idx:2d}. {result['_id']:40s}: {result['count']:3d} layovers")

    def pairing_category_breakdown(self):
        """Breakdown by pairing category."""
        print("\n" + "=" * 80)
        print("PAIRING CATEGORIES")
        print("=" * 80)

        pipeline = [
            {
                '$group': {
                    '_id': '$pairing_category',
                    'count': {'$sum': 1},
                    'avg_credit_hours': {
                        '$avg': {'$divide': ['$credit_minutes', 60]}
                    }
                }
            },
            {'$sort': {'count': -1}},
            {'$limit': 20}
        ]

        for result in self.db.pairings.aggregate(pipeline):
            category = result['_id'] or 'Unknown'
            print(f"{category:30s}: {result['count']:4d} pairings "
                  f"({result['avg_credit_hours']:.2f}h avg)")

    def monthly_distribution(self):
        """Distribution across effective dates."""
        print("\n" + "=" * 80)
        print("MONTHLY DISTRIBUTION")
        print("=" * 80)

        pipeline = [
            {
                '$group': {
                    '_id': {
                        '$substr': ['$effective_date_iso', 0, 7]  # YYYY-MM
                    },
                    'count': {'$sum': 1}
                }
            },
            {'$sort': {'_id': 1}}
        ]

        for result in self.db.pairings.aggregate(pipeline):
            print(f"{result['_id']}: {result['count']:4d} pairings")

    def layover_analysis(self, limit: int = 15):
        """Analyze overnight layover destinations."""
        print("\n" + "=" * 80)
        print(f"TOP {limit} LAYOVER CITIES (Overnight Destinations)")
        print("=" * 80)

        pipeline = [
            {
                '$match': {'layover_station': {'$ne': None}}
            },
            {
                '$group': {
                    '_id': '$layover_station',
                    'count': {'$sum': 1},
                    'avg_ground_time_hours': {
                        '$avg': {'$divide': ['$ground_time_minutes', 60]}
                    }
                }
            },
            {'$sort': {'count': -1}},
            {'$limit': limit}
        ]

        for idx, result in enumerate(self.db.legs.aggregate(pipeline), 1):
            station = result['_id']
            count = result['count']
            avg_ground = result.get('avg_ground_time_hours', 0)
            print(f"{idx:2d}. {station}: {count:5d} layovers "
                  f"(avg ground time: {avg_ground:.1f}h)")

    def layover_hotels(self, station: str = None):
        """Show hotels used for layovers at specific stations."""
        print("\n" + "=" * 80)
        if station:
            print(f"LAYOVER HOTELS IN {station}")
        else:
            print("LAYOVER HOTELS BY CITY")
        print("=" * 80)

        pipeline = [
            {'$unwind': '$duty_periods'},
            {
                '$match': {
                    'duty_periods.hotel': {'$ne': None},
                    'duty_periods.layover_station': {'$ne': None}
                }
            }
        ]

        if station:
            pipeline[1]['$match']['duty_periods.layover_station'] = station

        pipeline.extend([
            {
                '$group': {
                    '_id': {
                        'station': '$duty_periods.layover_station',
                        'hotel': '$duty_periods.hotel'
                    },
                    'count': {'$sum': 1}
                }
            },
            {'$sort': {'_id.station': 1, 'count': -1}}
        ])

        current_station = None
        for result in self.db.pairings.aggregate(pipeline):
            station = result['_id']['station']
            hotel = result['_id']['hotel']
            count = result['count']

            if current_station != station:
                current_station = station
                print(f"\n{station}:")

            print(f"  • {hotel}: {count} layovers")

    def run_all(self):
        """Run all analytics."""
        self.fleet_summary()
        self.route_analysis()
        self.time_of_day_analysis()
        self.high_value_pairings()
        self.international_vs_domestic()
        self.equipment_usage()
        self.layover_analysis()
        self.hotel_frequency()
        self.layover_hotels()
        self.pairing_category_breakdown()
        self.monthly_distribution()

        print("\n" + "=" * 80)
        print("ANALYTICS COMPLETE")
        print("=" * 80)

    def close(self):
        """Close connection."""
        self.client.close()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description="Run pairing analytics")
    parser.add_argument('--connection', type=str,
                       default="mongodb://localhost:27017/",
                       help="MongoDB connection string")
    parser.add_argument('--query', type=str,
                       choices=['fleet', 'routes', 'time', 'value', 'intl',
                               'equipment', 'layovers', 'hotels', 'categories', 'monthly', 'all'],
                       default='all',
                       help="Which analytics to run")
    parser.add_argument('--station', type=str,
                       help="Filter by station code (for layover hotels query)")

    args = parser.parse_args()

    analytics = PairingAnalytics(args.connection)

    query_map = {
        'fleet': analytics.fleet_summary,
        'routes': analytics.route_analysis,
        'time': analytics.time_of_day_analysis,
        'value': analytics.high_value_pairings,
        'intl': analytics.international_vs_domestic,
        'equipment': analytics.equipment_usage,
        'layovers': analytics.layover_analysis,
        'hotels': lambda: analytics.layover_hotels(args.station) if args.station else analytics.hotel_frequency(),
        'categories': analytics.pairing_category_breakdown,
        'monthly': analytics.monthly_distribution,
        'all': analytics.run_all
    }

    query_map[args.query]()
    analytics.close()
