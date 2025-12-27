# MongoDB Setup Guide

Complete guide for importing pairing data into MongoDB for analytics.

## Prerequisites

### 1. Install MongoDB

**macOS (using Homebrew):**
```bash
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community
```

**Or use MongoDB Atlas (cloud):**
- Sign up at https://www.mongodb.com/cloud/atlas
- Create a free cluster
- Get your connection string

### 2. Install Python MongoDB Driver

```bash
pip3 install pymongo
```

---

## Quick Start

### Import Single File
```bash
python3 mongodb_import.py --file output/ORD.json
```

### Import All Files
```bash
python3 mongodb_import.py --dir output/
```

### Clear and Re-import
```bash
python3 mongodb_import.py --dir output/ --clear
```

---

## Database Schema

The import script creates 3 collections optimized for different query patterns:

### Collection 1: `bid_periods`
Top-level summary of each bid period (fleet/base combination).

**Document structure:**
```javascript
{
  _id: ObjectId("..."),
  bid_month_year: "JAN 2026",
  fleet: "787",
  base: "CHICAGO",
  effective_date: "12/30/25",
  effective_date_iso: "2025-12-30",
  through_date: "01/29/26",
  through_date_iso: "2026-01-29",
  ftm: "13,578:02",
  ftm_minutes: 814682,
  ttl: "14,387:35",
  ttl_minutes: 863255,
  imported_at: ISODate("2025-12-25T..."),
  source_file: "ORD.json"
}
```

**Indexes:**
- Unique compound: `(bid_month_year, fleet, base)`
- `effective_date_iso`

---

### Collection 2: `pairings`
Individual pairings with embedded duty periods.

**Document structure:**
```javascript
{
  _id: ObjectId("..."),
  id: "O8001",
  pairing_category: "BASIC (HNL)",
  is_first_officer: false,

  // Dates
  effective_date: "12/30/25",
  effective_date_iso: "2025-12-30",
  through_date: "01/04/26",
  through_date_iso: "2026-01-04",
  date_instances: ["30", "31", "1", "2", "3"],

  // Summary metrics
  days: "3",
  credit: "17.23",
  credit_minutes: 1043,
  flight_time: "17.23",
  flight_time_minutes: 1043,
  time_away_from_base: "45.09",
  time_away_from_base_minutes: 2709,

  // Embedded duty periods
  duty_periods: [
    {
      report_time: "0820",
      report_time_formatted: "08:20",
      report_time_minutes: 500,
      release_time: "1459",
      release_time_formatted: "14:59",
      release_time_minutes: 899,
      hotel: "MAUI COAST HOTEL",
      hotel_phone: "808-874-6284",
      legs: [
        {
          equipment: "78J",
          deadhead: false,
          flight_number: "202",
          departure_station: "ORD",
          arrival_station: "OGG",
          departure_time: "0920",
          departure_time_formatted: "09:20",
          departure_time_minutes: 560,
          arrival_time: "1444",
          arrival_time_formatted: "14:44",
          arrival_time_minutes: 884,
          ground_time: "26:31",
          ground_time_minutes: 1591,
          meal_code: "B",
          flight_time: "9:24",
          flight_time_minutes: 564,
          duty_time: "10:39",
          duty_time_minutes: 639
        }
      ]
    }
  ],

  // References
  bid_period_id: ObjectId("..."),
  fleet: "787",
  base: "CHICAGO",
  duty_period_count: 2,
  leg_count: 3,
  imported_at: ISODate("2025-12-25T...")
}
```

**Indexes:**
- `id` (pairing ID)
- `pairing_category`
- `effective_date_iso`
- `bid_period_id`
- `credit_minutes` (descending)
- `flight_time_minutes` (descending)

---

### Collection 3: `legs`
Flattened leg data for route/equipment analysis.

**Document structure:**
```javascript
{
  _id: ObjectId("..."),
  pairing_id: "O8001",
  bid_period_id: ObjectId("..."),
  duty_period_index: 0,
  leg_index: 0,

  equipment: "78J",
  deadhead: false,
  flight_number: "202",
  departure_station: "ORD",
  arrival_station: "OGG",

  // Times - original and standardized
  departure_time: "0920",
  departure_time_formatted: "09:20",
  departure_time_minutes: 560,
  arrival_time: "1444",
  arrival_time_formatted: "14:44",
  arrival_time_minutes: 884,

  // Durations
  ground_time: "26:31",
  ground_time_minutes: 1591,
  flight_time: "9:24",
  flight_time_minutes: 564,
  duty_time: "10:39",
  duty_time_minutes: 639,

  meal_code: "B",
  fleet: "787",
  base: "CHICAGO",
  imported_at: ISODate("2025-12-25T...")
}
```

**Indexes:**
- `pairing_id`
- `equipment`
- `departure_station`
- `arrival_station`
- `departure_time_minutes`
- `deadhead`

---

## MongoDB Compass (GUI)

Download MongoDB Compass for visual exploration:
https://www.mongodb.com/products/compass

Connect to: `mongodb://localhost:27017`

Database: `airline_pairings`

---

## Example Analytics Queries

### 1. Find High-Value Pairings
```javascript
db.pairings.find({
  credit_minutes: { $gt: 1200 }  // > 20 hours
}).sort({ credit_minutes: -1 }).limit(10)
```

### 2. Morning Departures from ORD
```javascript
db.legs.find({
  departure_station: "ORD",
  departure_time_minutes: { $gte: 360, $lt: 720 }  // 6am-12pm
})
```

### 3. Average Flight Time by Equipment
```javascript
db.legs.aggregate([
  {
    $group: {
      _id: "$equipment",
      avg_flight_minutes: { $avg: "$flight_time_minutes" },
      total_legs: { $sum: 1 }
    }
  },
  { $sort: { total_legs: -1 } }
])
```

### 4. Popular Routes
```javascript
db.legs.aggregate([
  {
    $group: {
      _id: {
        from: "$departure_station",
        to: "$arrival_station"
      },
      count: { $sum: 1 },
      avg_flight_time: { $avg: "$flight_time_minutes" }
    }
  },
  { $sort: { count: -1 } },
  { $limit: 20 }
])
```

### 5. Pairings by Date Range
```javascript
db.pairings.find({
  effective_date_iso: {
    $gte: "2025-12-30",
    $lte: "2026-01-15"
  }
})
```

### 6. International vs Domestic
```javascript
db.pairings.aggregate([
  {
    $group: {
      _id: {
        $cond: [
          { $gt: ["$international_flight_time_minutes", 0] },
          "International",
          "Domestic"
        ]
      },
      count: { $sum: 1 },
      avg_credit: { $avg: "$credit_minutes" }
    }
  }
])
```

### 7. Deadhead Analysis
```javascript
db.legs.aggregate([
  {
    $group: {
      _id: "$deadhead",
      count: { $sum: 1 },
      avg_duration: { $avg: "$flight_time_minutes" }
    }
  }
])
```

### 8. Hotels by Frequency
```javascript
db.pairings.aggregate([
  { $unwind: "$duty_periods" },
  { $match: { "duty_periods.hotel": { $ne: null } } },
  {
    $group: {
      _id: "$duty_periods.hotel",
      count: { $sum: 1 }
    }
  },
  { $sort: { count: -1 } },
  { $limit: 10 }
])
```

---

## Python Analytics Examples

### Connect and Query
```python
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['airline_pairings']

# Find all 787 pairings
for pairing in db.pairings.find({'fleet': '787'}).limit(5):
    print(f"{pairing['id']}: {pairing['credit']} credit hours")

# Aggregate statistics
pipeline = [
    {'$group': {
        '_id': '$base',
        'total_pairings': {'$sum': 1},
        'avg_credit': {'$avg': '$credit_minutes'}
    }}
]
for result in db.pairings.aggregate(pipeline):
    print(f"{result['_id']}: {result['total_pairings']} pairings")
```

### Export to Pandas
```python
import pandas as pd
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['airline_pairings']

# Load pairings into DataFrame
pairings = list(db.pairings.find({}, {
    'id': 1,
    'credit_minutes': 1,
    'flight_time_minutes': 1,
    'effective_date_iso': 1,
    'pairing_category': 1
}))

df = pd.DataFrame(pairings)
print(df.describe())
```

---

## Backup and Restore

### Backup
```bash
mongodump --db airline_pairings --out backup/
```

### Restore
```bash
mongorestore --db airline_pairings backup/airline_pairings/
```

---

## MongoDB Atlas (Cloud) Setup

1. Create account at https://www.mongodb.com/cloud/atlas
2. Create a free cluster (M0)
3. Add your IP to whitelist
4. Create database user
5. Get connection string:
   ```
   mongodb+srv://username:password@cluster.mongodb.net/
   ```

6. Import to Atlas:
   ```bash
   python3 mongodb_import.py \
     --connection "mongodb+srv://user:pass@cluster.mongodb.net/" \
     --dir output/
   ```

---

## Troubleshooting

### Connection Failed
- Check MongoDB is running: `brew services list`
- Start MongoDB: `brew services start mongodb-community`

### Import Errors
- Check JSON files are valid
- Use `--clear` flag to reset data

### Slow Queries
- Ensure indexes are created
- Use `explain()` to analyze queries:
  ```javascript
  db.pairings.find({...}).explain("executionStats")
  ```

---

## Next Steps

1. Import your data: `python3 mongodb_import.py --dir output/`
2. Open MongoDB Compass to explore visually
3. Run sample queries from [MONGODB_FIELDS.md](MONGODB_FIELDS.md)
4. Build dashboards using Tableau, Power BI, or custom web apps
5. Create scheduled reports and analytics

All computed fields (`*_minutes`, `*_iso`, `*_formatted`) are automatically available for querying!
