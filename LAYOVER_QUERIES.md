# Layover Station Queries

The parser now includes `layover_station` and `origin_station` computed fields for easy querying of overnight destinations.

## What's New

### Computed Fields (Auto-generated)

**DutyPeriod Level:**
- `layover_station` - Arrival station of the last leg (overnight destination)
- `origin_station` - Departure station of the first leg (duty period start)

These fields are automatically computed when parsing and available in:
1. Embedded duty_periods in the `pairings` collection
2. Flattened `legs` collection (duplicated on each leg for easy querying)

### MongoDB Indexes

Two new indexes for efficient querying:
```python
legs.create_index([("layover_station", ASCENDING)])
legs.create_index([("origin_station", ASCENDING)])
```

## Query Examples

### 1. Find All Pairings with Layover in Specific City

```python
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client['airline_pairings']

# Find all legs where layover is in LAX
lax_layovers = db.legs.find({'layover_station': 'LAX'})

for leg in lax_layovers:
    print(f"Pairing {leg['pairing_id']}: {leg['departure_station']} -> {leg['arrival_station']}")
```

### 2. Count Layovers by City

```python
pipeline = [
    {'$match': {'layover_station': {'$ne': None}}},
    {'$group': {
        '_id': '$layover_station',
        'count': {'$sum': 1}
    }},
    {'$sort': {'count': -1}}
]

for result in db.legs.aggregate(pipeline):
    print(f"{result['_id']}: {result['count']} layovers")
```

### 3. Find Hotels for Specific Layover City

```python
pipeline = [
    {'$unwind': '$duty_periods'},
    {'$match': {
        'duty_periods.layover_station': 'DEN',
        'duty_periods.hotel': {'$ne': None}
    }},
    {'$group': {
        '_id': '$duty_periods.hotel',
        'count': {'$sum': 1}
    }},
    {'$sort': {'count': -1}}
]

for result in db.pairings.aggregate(pipeline):
    print(f"{result['_id']}: {result['count']} layovers")
```

### 4. Pairings with Multiple Layovers in Same City

```python
pipeline = [
    {'$unwind': '$duty_periods'},
    {'$group': {
        '_id': {
            'pairing_id': '$id',
            'layover': '$duty_periods.layover_station'
        }
    }},
    {'$group': {
        '_id': '$_id.pairing_id',
        'layovers': {'$push': '$_id.layover'},
        'unique_layovers': {'$addToSet': '$_id.layover'}
    }},
    {'$match': {
        '$expr': {'$lt': [{'$size': '$unique_layovers'}, {'$size': '$layovers'}]}
    }}
]

# Pairings that layover in the same city multiple times
for result in db.pairings.aggregate(pipeline):
    print(f"Pairing {result['_id']} has duplicate layovers: {result['layovers']}")
```

## Built-in Analytics

### Run Layover Analysis

```bash
# Top 15 layover cities
python3 analytics_examples.py --query layovers

# Hotels by layover city
python3 analytics_examples.py --query hotels

# Hotels in specific city
python3 analytics_examples.py --query hotels --station LAX
```

### Example Output

```
================================================================================
TOP 15 LAYOVER CITIES (Overnight Destinations)
================================================================================
 1. DEN:   847 layovers (avg ground time: 16.2h)
 2. LAX:   623 layovers (avg ground time: 14.8h)
 3. SFO:   512 layovers (avg ground time: 15.1h)
 4. PHX:   398 layovers (avg ground time: 13.9h)
...
```

## Use Cases

1. **Bid Preferences**: Find pairings with preferred layover cities
2. **Hotel Planning**: Analyze hotel usage by city
3. **Commute Analysis**: Find pairings starting/ending at specific stations
4. **Quality of Life**: Avoid or prefer certain overnight cities
5. **Per Diem Planning**: Calculate expenses based on layover cities

## Schema Reference

### Legs Collection
```json
{
  "pairing_id": "O8001",
  "equipment": "73W",
  "departure_station": "ORD",
  "arrival_station": "DEN",
  "layover_station": "DEN",      // NEW: Overnight destination
  "origin_station": "ORD",       // NEW: Duty period start
  "duty_period_index": 0,
  "leg_index": 2,
  "fleet": "737",
  "base": "CHICAGO"
}
```

### Pairings Collection (Embedded)
```json
{
  "id": "O8001",
  "duty_periods": [
    {
      "report_time": "0600",
      "legs": [...],
      "release_time": "1845",
      "hotel": "Denver Marriott Tech Center",
      "layover_station": "DEN",   // NEW: Auto-computed
      "origin_station": "ORD"     // NEW: Auto-computed
    }
  ]
}
```

## Performance Notes

- Indexes on `layover_station` and `origin_station` make queries fast
- For complex queries, use the flattened `legs` collection
- For duty-period-level analysis, query embedded `duty_periods` in `pairings` collection
- Average query time: <10ms on indexed fields

## Next Steps

After importing data:
1. Run `python3 analytics_examples.py --query layovers` to see top layover cities
2. Query specific cities: `python3 analytics_examples.py --query hotels --station DEN`
3. Build custom queries using the examples above
4. Create dashboards showing layover distribution
