# Layover & Overnight Filters Guide

**Added:** 2025-12-27

## New Dashboard Features

The Pairing Explorer now includes advanced filters for layover stations and overnight duration, making it easy to find pairings that match your specific overnight preferences.

## 🏨 Layover Filters

### 1. Layover Station Filter

**Location:** Sidebar → Layover Filters section

**Purpose:** Filter pairings based on where you have layovers (overnight stays)

**How to Use:**
1. Open the Pairing Explorer (Tab 1)
2. Scroll down in the sidebar to "🏨 Layover Filters"
3. Select a station from the "Layover Station" dropdown
4. The pairing list will update to show only pairings with layovers in that city

**Example Use Cases:**
- Find all pairings with SFO layovers
- See which pairings overnight in your favorite cities
- Avoid or prefer specific layover cities

### 2. Overnight Duration Filter

**Location:** Sidebar → Layover Filters section

**Purpose:** Filter pairings by the length of overnight rest periods

**How to Use:**
1. Check the box "Filter by Overnight Duration"
2. Adjust the slider to set minimum and maximum overnight hours
3. Default range: 8-24 hours
4. Pairings will be filtered based on their longest overnight period

**Example Use Cases:**
- **Short overnights (8-12h):** Quick turnarounds, less time in hotel
- **Standard overnights (12-18h):** Normal rest periods
- **Long overnights (18-24h+):** Extra time to explore the city, better rest

**How Overnight Duration is Calculated:**
- Time between release (duty period end) and next report (next duty period start)
- Automatically handles overnight transitions (next day)
- Example: Release at 20:00, next report at 10:00 = 14 hours overnight

## Display Enhancements

### Pairing Search Table

The pairing search results now include:
- **max_overnight_h** column: Shows the longest overnight in the pairing

**Example:**
```
id      fleet  category  credit_hours  days  max_overnight_h  layovers
O8014   787    BASIC     28.5          4     15.2            IAD, MUC, BOS
O3001   737    BASIC     12.3          1     0.0             None
```

### Pairing Detail View

Duty period expanders now show:
- **Layover station:** Where you overnight
- **Overnight duration:** How long the overnight is
- **Hotel information:** Hotel name and phone number (when available)

**Example Expander Title:**
```
Day 1 - 3 flights - Layover: SFO - Overnight: 14.5h
```

**Inside Expander:**
```
Report: 08:00 | Release: 18:30

🏨 Hotel: Hilton San Francisco Airport | ☎️ (650) 589-0770

[Flight legs table]
```

## Filter Combinations

You can combine the layover filters with existing filters for powerful searches:

### Example 1: Long SFO Overnights on 737
- **Fleet:** 737
- **Layover Station:** SFO
- **Overnight Duration:** 18-24 hours
- **Result:** All 737 pairings with long SFO layovers

### Example 2: Multi-Day Trips with Specific Layovers
- **Number of Days:** 3, 4
- **Layover Station:** LAX
- **Credit Hours:** 20-30
- **Result:** Longer trips with LAX layovers in a specific credit range

### Example 3: Quick Turnarounds
- **Overnight Duration:** 8-12 hours
- **Days:** 2, 3
- **Result:** Multi-day trips with short overnights (less hotel time)

## Active Filters Display

When layover filters are active, they appear in the filter summary banner:

```
🔍 Active filters: Fleet: 737 • Days: 3, 4 • Layover: SFO • Overnight: 14-20h
```

## Data Fields Used

### From MongoDB Schema

**DutyPeriod fields:**
- `layover_station` - IATA code of layover city (None for last duty period)
- `release_time_minutes` - Minutes since midnight for duty end
- `report_time_minutes` - Minutes since midnight for next duty start
- `hotel` - Hotel name
- `hotel_phone` - Hotel phone number

**Calculated fields:**
- `overnight_hours` - Array of overnight durations for each layover
- `max_overnight_hours` - Longest overnight in the pairing
- `min_overnight_hours` - Shortest overnight in the pairing

## Technical Notes

### Overnight Calculation Logic

```python
# For each consecutive duty period pair
current_release = duty_period[i].release_time_minutes
next_report = duty_period[i+1].report_time_minutes

# Handle day transition
if next_report < current_release:
    next_report += 1440  # Add 24 hours (next day)

overnight_minutes = next_report - current_release
overnight_hours = overnight_minutes / 60
```

### Filtering Behavior

1. **Layover Station Filter:**
   - Uses MongoDB query: `duty_periods.layover_station = selected_station`
   - Matches any pairing where ANY duty period has that layover
   - Efficient database-level filtering

2. **Overnight Duration Filter:**
   - Calculated client-side after initial query
   - Filters based on `max_overnight_hours` (longest overnight)
   - Allows finding pairings with at least one long overnight

### Performance Considerations

- Layover station filter is efficient (database index)
- Overnight calculation done for up to 1,000 pairings (limit)
- Results cached for 10 minutes (TTL=600)

## Tips & Best Practices

### Finding Good Layovers

1. **Start with location:** Select your preferred layover city
2. **Then refine duration:** Adjust overnight hours to your preference
3. **Add other filters:** Fleet, days, credit hours for complete customization

### Typical Overnight Ranges

- **Minimum legal rest:** Usually 9-10 hours
- **Short overnight:** 10-12 hours
- **Standard overnight:** 12-18 hours
- **Long overnight:** 18-24 hours
- **Extra-long overnight:** 24+ hours (often international)

### Use Cases

**Commuters:**
- Filter for short overnights to minimize time away from home
- Prefer familiar layover cities

**Trip Optimization:**
- Find pairings with long layovers in desirable cities
- Combine with credit hours to maximize value

**Lifestyle Preferences:**
- Avoid red-eye patterns (short overnights)
- Find trips with specific city combinations

## Troubleshooting

### "No pairings found"

**Possible causes:**
1. Filter combination too restrictive
2. Selected layover station not in dataset
3. Overnight range outside actual values

**Solutions:**
1. Remove some filters one at a time
2. Check "Layover Cities" metric for available stations
3. Adjust overnight range to include more values

### Overnight hours showing 0.0

**Meaning:** Pairing has no layovers (1-day trip or data issue)

**Check:**
1. Verify it's not a 1-day trip (Days column)
2. Check if duty_periods have layover_station set

## Related Documentation

- [FIELD_DEFINITIONS.md](FIELD_DEFINITIONS.md) - Layover station business rules
- [PARSER_FIXES_2025-12-27.md](PARSER_FIXES_2025-12-27.md) - Parser fixes for layover logic
- [DASHBOARD_GUIDE.md](DASHBOARD_GUIDE.md) - General dashboard usage
- [MONGODB_UPSERT_COMPLETE.md](MONGODB_UPSERT_COMPLETE.md) - Database import verification

---

**Last Updated:** 2025-12-27

These filters enable precise pairing selection based on layover preferences, making it easier to find trips that match your lifestyle and rest requirements.
