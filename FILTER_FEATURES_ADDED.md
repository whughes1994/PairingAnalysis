# Layover & Overnight Filters - Implementation Summary

**Date:** 2025-12-27
**File Modified:** `unified_dashboard.py`

## Overview

Added advanced filtering capabilities to the Pairing Explorer dashboard for layover stations and overnight duration, enabling users to find pairings based on where they stay overnight and how long those overnights are.

## Features Added

### 1. Layover Station Filter

**UI Component:**
- Location: Sidebar → "🏨 Layover Filters" section
- Type: Dropdown/selectbox
- Options: "All" + all unique layover stations from database
- Default: "All"

**Functionality:**
- Filters pairings that have layovers in the selected station
- Uses MongoDB query: `duty_periods.layover_station = selected_station`
- Efficient database-level filtering

**Code Location:**
- Lines 315-323 (UI component)
- Line 153-154 (query logic in `get_pairings_data()`)

### 2. Overnight Duration Filter

**UI Component:**
- Location: Sidebar → "🏨 Layover Filters" section
- Type: Checkbox + slider
- Range: 0-48 hours
- Default: 8-24 hours (when enabled)
- Default state: Disabled

**Functionality:**
- Calculates overnight duration for each duty period (release to next report)
- Filters pairings based on maximum overnight hours
- Handles day transitions (overnight -> next day)

**Code Location:**
- Lines 326-341 (UI component)
- Lines 171-191 (overnight calculation in `get_pairings_data()`)
- Lines 196-200 (filtering logic in `get_pairings_data()`)

## Implementation Details

### Modified Functions

#### `get_pairings_data()` (Lines 138-202)

**New Parameters:**
```python
layover_station=None,           # Filter by layover city
min_overnight_hours=None,       # Minimum overnight duration
max_overnight_hours=None        # Maximum overnight duration
```

**New Logic:**

1. **Layover Station Filtering:**
```python
if layover_station and layover_station != 'All':
    query['duty_periods.layover_station'] = layover_station
```

2. **Overnight Calculation:**
```python
overnight_hours = []
for i in range(len(duty_periods) - 1):
    release_mins = duty_periods[i]['release_time_minutes']
    next_report_mins = duty_periods[i+1]['report_time_minutes']

    # Handle day transition
    if next_report_mins < release_mins:
        next_report_mins += 1440

    overnight_hours.append((next_report_mins - release_mins) / 60)

# Store max/min overnight hours
p['max_overnight_hours'] = max(overnight_hours) if overnight_hours else 0
p['min_overnight_hours'] = min(overnight_hours) if overnight_hours else 0
```

3. **Overnight Duration Filtering:**
```python
if min_overnight_hours is not None:
    df = df[df['max_overnight_hours'] >= min_overnight_hours]
if max_overnight_hours is not None:
    df = df[df['max_overnight_hours'] <= max_overnight_hours]
```

### Display Enhancements

#### 1. Pairing Table (Lines 454-474)

**Added Column:**
- `max_overnight_h` - Shows longest overnight in pairing (rounded to 1 decimal)

**Before:**
```
id | fleet | category | credit_hours | days | flight_hours | layovers
```

**After:**
```
id | fleet | category | credit_hours | days | flight_hours | layovers | max_overnight_h
```

#### 2. Active Filters Display (Lines 385-388)

**Added to filter summary:**
```python
if selected_layover != 'All':
    active_filters.append(f"Layover: {selected_layover}")
if overnight_enabled:
    active_filters.append(f"Overnight: {min_overnight}-{max_overnight}h")
```

**Example Output:**
```
🔍 Active filters: Fleet: 737 • Days: 3, 4 • Layover: SFO • Overnight: 14-20h
```

#### 3. Duty Period Details (Lines 590-615)

**Added to Expander Title:**
```python
overnight_info = ""
if dp_idx < len(duty_periods) - 1:
    # Calculate overnight hours
    overnight_info = f" - Overnight: {overnight_hrs:.1f}h"
```

**Before:**
```
Day 1 - 3 flights - Layover: SFO
```

**After:**
```
Day 1 - 3 flights - Layover: SFO - Overnight: 14.5h
```

**Enhanced Hotel Display:**
```python
if hotel:
    hotel_str = f"🏨 **Hotel:** {hotel}"
    if hotel_phone:
        hotel_str += f" | ☎️ {hotel_phone}"
    st.info(hotel_str)
```

## Code Changes Summary

### Modified Sections

1. **`get_pairings_data()` function signature** (Line 138)
   - Added: `layover_station`, `min_overnight_hours`, `max_overnight_hours` parameters

2. **MongoDB query building** (Lines 152-154)
   - Added layover station filter to query

3. **Post-query processing** (Lines 165-201)
   - Added overnight hours calculation for each pairing
   - Added overnight duration filtering

4. **Sidebar filters** (Lines 311-341)
   - Added "🏨 Layover Filters" section header
   - Added layover station dropdown
   - Added overnight duration checkbox and slider

5. **Active filters display** (Lines 385-388)
   - Added layover and overnight to active filter list

6. **Function calls** (Lines 440-449)
   - Updated `get_pairings_data()` call with new parameters

7. **Table display** (Lines 454-474)
   - Added max_overnight_h column to pairing table

8. **Duty period details** (Lines 590-615)
   - Added overnight duration to expander title
   - Enhanced hotel information display

## Database Fields Used

**Existing Fields:**
- `duty_periods.layover_station` - Layover city (None for last day)
- `duty_periods.release_time_minutes` - Duty end time
- `duty_periods.report_time_minutes` - Next duty start time
- `duty_periods.hotel` - Hotel name
- `duty_periods.hotel_phone` - Hotel phone

**Calculated Fields (Runtime):**
- `overnight_hours` - Array of overnight durations
- `max_overnight_hours` - Longest overnight
- `min_overnight_hours` - Shortest overnight

## Performance Considerations

1. **Database Query:**
   - Layover station filter applied at database level (efficient)
   - Indexed field (see `mongodb_import.py` line 79)

2. **Calculation:**
   - Overnight hours calculated for up to 1,000 pairings (query limit)
   - Lightweight calculation (simple arithmetic)

3. **Caching:**
   - Results cached for 10 minutes (TTL=600)
   - Cache key includes all filter parameters

## Testing Checklist

- [x] Layover station filter returns correct pairings
- [x] Overnight duration calculation handles day transitions
- [x] Overnight filter correctly limits results
- [x] Active filters display shows layover/overnight info
- [x] Pairing table includes overnight hours column
- [x] Duty period expanders show overnight duration
- [x] Hotel information displays correctly
- [x] Filter combinations work together
- [x] Cache invalidates on filter changes

## Example Use Cases

### Use Case 1: Find Long SFO Layovers on 737
```
Filters:
- Fleet: 737
- Layover Station: SFO
- Overnight Duration: 18-24 hours

Result: All 737 pairings with long SFO overnights
```

### Use Case 2: Short Overnights for Commuters
```
Filters:
- Overnight Duration: 8-12 hours
- Days: 2, 3

Result: Multi-day trips with minimal hotel time
```

### Use Case 3: International Layovers
```
Filters:
- Layover Station: MUC (Munich)
- Credit Hours: 25-35
- Days: 4

Result: Long-haul international trips
```

## Files Modified

1. **unified_dashboard.py** - Main dashboard file
   - Added layover/overnight filter UI
   - Enhanced `get_pairings_data()` function
   - Updated display components

## Documentation Created

1. **LAYOVER_FILTERS_GUIDE.md** - User guide for new filters
2. **FILTER_FEATURES_ADDED.md** - This file (technical implementation)

## Related Changes

These filters work seamlessly with the layover_station fixes implemented earlier:
- 1-day trips: `layover_station = None` ✅
- Last duty period: `layover_station = None` ✅
- Intermediate duty periods: `layover_station = arrival_station` ✅

## Next Steps

Suggested enhancements for future development:

1. **Overnight Quality Metrics:**
   - Add rating system for layover cities
   - Show average overnight duration by station

2. **Multiple Layover Filters:**
   - Allow selecting multiple layover stations
   - "Must include" vs "may include" logic

3. **Overnight Time-of-Day:**
   - Filter by overnight start time (e.g., no late releases)
   - Filter by overnight end time (e.g., no early reports)

4. **Statistical Views:**
   - Chart: Overnight duration distribution
   - Chart: Most common layover cities
   - Chart: Average overnight by fleet

---

**Status:** Implementation complete and ready for use ✅

All filter features have been added to the dashboard and are fully functional with the updated MongoDB data.
