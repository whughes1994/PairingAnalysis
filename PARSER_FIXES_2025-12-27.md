# Parser Fixes - 2025-12-27

## Summary

This document describes the critical parsing fixes implemented to ensure correct field extraction and layover station logic.

## 1. Leg (Flight) Parsing Fix

### Problem
The original leg parser used format detection and guessing, which led to incorrect field extraction, especially for:
- Deadhead (DH) marker
- Optional ground time field
- Variable number of meal codes (0-3)
- Incorrect time field assignments

### Solution
Completely rewrote `_parse_leg()` method in [src/parsers/pairing_parser.py](src/parsers/pairing_parser.py) (lines 210-314) using **sequential index-based extraction**.

### Field Order (Authoritative)
```
Equipment [DH] FlightNumber Departure Arrival DepTime ArrTime [GroundTime] [MealCode(s)] FlightTime AccumFlightTime AccumDutyTime
```

### Key Changes
1. **Sequential extraction**: Index tracker (`idx`) moves through fields in order
2. **DH detection**: Check for "DH" immediately after equipment code
3. **Smart ground time**: Detect by presence of ":" or numeric format
4. **Meal code loop**: Collect 0-3 single uppercase letters (B, L, D, S)
5. **Proper time fields**: Flight time, accumulated flight time, accumulated duty time

### Examples Handled
```
# Regular flight with meals and ground time
73G 123 ORD LAX 0800 1030 2:15 B L 4:30 4:30 6:45

# Deadhead flight
78J DH 456 LAX SFO 1245 1415 0 7:45 12:15 14:30

# No ground time, multiple meals
37K 789 SFO ORD 1415 2030 B D 4:15 16:30 18:45
```

### Reference
See [FIELD_DEFINITIONS.md](FIELD_DEFINITIONS.md) for complete field specifications.

---

## 2. Layover Station Logic Fix

### Problem
The `layover_station` field was a computed property that always returned the arrival station of the last leg, which was incorrect for:
- 1-day trips (no layovers - crew returns to base same day)
- Last duty period of multi-day trips (returning to base)

### Solution
1. **Changed `layover_station` from computed property to regular field** in [src/models/schemas.py](src/models/schemas.py):129
2. **Added `model_post_init()` method** to `Pairing` class (lines 266-296) that sets layover values based on business rules

### Business Rules

#### 1-Day Trips
- All duty periods: `layover_station = None`
- Crew returns to base same day

#### Multi-Day Trips
- Days 1 through N-1: `layover_station = arrival_station` of last leg
- Day N (last day): `layover_station = None` (returning to base)

### Examples

**1-Day Trip:**
```
Day 1: ORD → LAX → SFO → ORD
  layover_station: None
```

**2-Day Trip:**
```
Day 1: ORD → LAX
  layover_station: LAX
Day 2: LAX → ORD
  layover_station: None (returning to base)
```

**4-Day Trip:**
```
Day 1: ORD → LAX → SFO
  layover_station: SFO
Day 2: SFO → SEA → PDX
  layover_station: PDX
Day 3: PDX → DEN → PHX
  layover_station: PHX
Day 4: PHX → DFW → ORD
  layover_station: None (returning to base)
```

### Validation
Created [test_layover_logic.py](test_layover_logic.py) to verify correct behavior:
- 1-day trip: No layover stations ✅
- 2-day trip: Day 1 has layover, Day 2 is None ✅
- 4-day trip: Days 1-3 have layovers, Day 4 is None ✅

---

## 3. Additional Fixes

### Import Fix
Fixed relative import in [src/models/__init__.py](src/models/__init__.py):2
```python
# Before
from models.schemas import ...

# After
from .schemas import ...
```

---

## Testing

### Run Layover Logic Tests
```bash
python3 test_layover_logic.py
```

### Re-parse with Fixed Parser
```bash
python3 -m src.main "Pairing Source Docs/YOUR_FILE.pdf" --output output/YOUR_FILE.json
```

### Validate Results
```bash
python3 -m streamlit run unified_dashboard.py
# Navigate to Tab 2: QA Workbench
# Select Overview mode and Fleet Totals mode to verify
```

---

## Files Modified

1. **src/parsers/pairing_parser.py** (lines 210-314)
   - Complete rewrite of `_parse_leg()` method

2. **src/models/schemas.py**
   - Line 129: Changed `layover_station` to regular field
   - Lines 266-296: Added `model_post_init()` method

3. **src/models/__init__.py** (line 2)
   - Fixed relative import

4. **FIELD_DEFINITIONS.md**
   - Added layover station logic documentation

---

## Next Steps

1. **Re-parse all PDFs** with the fixed parser
2. **Validate results** using QA Workbench (Fleet Totals mode)
3. **Re-import to MongoDB** if validation passes
4. **Spot-check** specific pairings for correctness

---

## Impact

### Critical Fixes
- ✅ Deadhead flights now correctly identified
- ✅ Meal codes properly extracted (0-3 codes)
- ✅ Time fields (flight, accumulated flight, duty) correctly assigned
- ✅ Layover stations only set for intermediate days
- ✅ 1-day trips have no layover stations
- ✅ Last day of multi-day trips has no layover station

### Data Quality
These fixes ensure:
- Accurate flight time tracking
- Correct duty time calculations
- Proper layover city identification for crew rest requirements
- Correct meal allowance tracking

---

**Last Updated:** 2025-12-27
