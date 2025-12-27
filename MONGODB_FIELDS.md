# MongoDB Query Fields Reference

The parser now outputs **both original and standardized fields** for easy querying.

## Field Standardization Summary

### Dates
- **Original**: `"12/30/25"` (MM/DD/YY string)
- **Standardized**: `"2025-12-30"` (ISO 8601 string)
- **Use for**: Date range queries, sorting by date

### Clock Times (Departure, Arrival, Report, Release)
- **Original**: `"0920"` (HHMM string)
- **Formatted**: `"09:20"` (HH:MM string) - human readable
- **Minutes**: `560` (integer) - minutes since midnight
- **Use for**: Time range queries, sorting, arithmetic

### Duration Times (Flight Time, Ground Time, Duty Time, Credit)
- **Original**: `"9:24"` or `"17.23"` (various string formats)
- **Minutes**: `564` or `1043` (integer) - total minutes
- **Use for**: Summing totals, range queries, comparisons

---

## Complete Field Reference

### Leg Fields
| Field | Original Format | Standardized Field | Type | Example |
|-------|----------------|-------------------|------|---------|
| departure_time | HHMM string | departure_time_formatted | string | "09:20" |
| | | departure_time_minutes | int | 560 |
| arrival_time | HHMM string | arrival_time_formatted | string | "14:44" |
| | | arrival_time_minutes | int | 884 |
| ground_time | H:MM string | ground_time_minutes | int | 1591 |
| flight_time | H:MM string | flight_time_minutes | int | 564 |
| duty_time | H:MM string | duty_time_minutes | int | 639 |
| accumulated_flight_time | H:MM string | accumulated_flight_time_minutes | int | 564 |
| d_c | H:MM string | d_c_minutes | int | 0 |

### DutyPeriod Fields
| Field | Original Format | Standardized Field | Type | Example |
|-------|----------------|-------------------|------|---------|
| report_time | HHMM string | report_time_formatted | string | "08:20" |
| | | report_time_minutes | int | 500 |
| release_time | HHMM string | release_time_formatted | string | "17:30" |
| | | release_time_minutes | int | 1050 |

### Pairing Fields
| Field | Original Format | Standardized Field | Type | Example |
|-------|----------------|-------------------|------|---------|
| effective_date | MM/DD/YY string | effective_date_iso | string | "2025-12-30" |
| through_date | MM/DD/YY string | through_date_iso | string | "2026-01-29" |
| credit | H.MM string | credit_minutes | int | 1043 |
| flight_time | H.MM string | flight_time_minutes | int | 1043 |
| time_away_from_base | H.MM string | time_away_from_base_minutes | int | 2709 |
| international_flight_time | H.MM string | international_flight_time_minutes | int | 0 |

### BidPeriod Fields
| Field | Original Format | Standardized Field | Type | Example |
|-------|----------------|-------------------|------|---------|
| effective_date | MM/DD/YY string | effective_date_iso | string | "2025-12-30" |
| through_date | MM/DD/YY string | through_date_iso | string | "2026-01-29" |
| ftm | H,HHH:MM string | ftm_minutes | int | 814682 |
| ttl | H,HHH:MM string | ttl_minutes | int | 863255 |

---

## MongoDB Query Examples

### 1. Find pairings with specific departure times
```javascript
// Morning departures (6am - 9am)
db.pairings.find({
  "duty_periods.legs.departure_time_minutes": {
    $gte: 360,  // 06:00
    $lt: 540    // 09:00
  }
})
```

### 2. Find pairings by date range
```javascript
db.pairings.find({
  "effective_date_iso": {
    $gte: "2025-12-30",
    $lte: "2026-01-15"
  }
})
```

### 3. Calculate total flight time for a pairing
```javascript
db.pairings.aggregate([
  {
    $project: {
      pairing_id: "$id",
      total_flight_minutes: "$flight_time_minutes",
      total_flight_hours: { $divide: ["$flight_time_minutes", 60] }
    }
  }
])
```

### 4. Find long duty days (>12 hours)
```javascript
db.pairings.find({
  "duty_periods.legs.duty_time_minutes": { $gt: 720 }  // 12 hours
})
```

### 5. Find high-credit pairings
```javascript
// Credit > 20 hours
db.pairings.find({
  "credit_minutes": { $gt: 1200 }  // 20 * 60
}).sort({ "credit_minutes": -1 })
```

### 6. Average ground time by equipment type
```javascript
db.pairings.aggregate([
  { $unwind: "$duty_periods" },
  { $unwind: "$duty_periods.legs" },
  {
    $group: {
      _id: "$duty_periods.legs.equipment",
      avg_ground_time_minutes: { $avg: "$duty_periods.legs.ground_time_minutes" },
      avg_ground_time_hours: {
        $divide: [{ $avg: "$duty_periods.legs.ground_time_minutes" }, 60]
      }
    }
  },
  { $sort: { avg_ground_time_minutes: -1 } }
])
```

### 7. Find red-eye flights (depart after 10pm, arrive before 6am)
```javascript
db.pairings.find({
  "duty_periods.legs": {
    $elemMatch: {
      departure_time_minutes: { $gte: 1320 },  // 22:00
      arrival_time_minutes: { $lt: 360 }       // 06:00
    }
  }
})
```

### 8. Sum total flight time across all pairings
```javascript
db.pairings.aggregate([
  {
    $group: {
      _id: null,
      total_minutes: { $sum: "$flight_time_minutes" },
      total_hours: { $sum: { $divide: ["$flight_time_minutes", 60] } }
    }
  }
])
```

---

## Benefits of This Approach

✅ **Keep originals**: Human-readable strings preserved for display
✅ **Easy queries**: Integer fields for fast range/comparison queries
✅ **No data loss**: Both formats available in same document
✅ **Sortable**: Numeric fields sort correctly (no string sorting issues)
✅ **Aggregatable**: Can sum/average duration fields easily
✅ **ISO dates**: Standard format for date comparisons

---

## Field Name Patterns

- `*_formatted` - Human-readable string format (HH:MM)
- `*_minutes` - Integer representing total minutes
- `*_iso` - ISO 8601 date string (YYYY-MM-DD)

All computed fields are automatically generated when parsing - no extra processing needed!
