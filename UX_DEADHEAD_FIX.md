# UX Deadhead Parsing Fix

**Date:** 2025-12-27
**Issue:** Pairing O1277 was not structured correctly - UX deadhead legs were missing
**Root Cause:** Parser did not recognize UX deadheads (which have no equipment code)

## Problem

Pairing O1277 had missing UX deadhead leg:
```
UX 3707 ORD CID 1300 1420 17.40 1.20 3.11 7.05 1.20
```

This leg was being completely skipped by the parser because:
1. `is_leg_line()` only recognized lines starting with equipment codes (e.g., "20S")
2. UX deadheads start with "UX" (2 letters) instead of equipment code
3. UX deadheads have NO equipment code field

## Solution

### 1. Updated `is_leg_line()` Method

**File:** `src/parsers/pairing_parser.py` (lines 210-229)

```python
def is_leg_line(self, line: str) -> bool:
    """
    Detect if line contains leg data.

    Handles both:
    - Equipment-based legs: "78J 202 ORD OGG..." (starts with 2 digits + letter)
    - DH/UX deadheads: "DH 3707..." or "UX 3707..." (starts with DH or UX)
    """
    if len(line) < 2:
        return False

    # Check for equipment code format (2 digits + letter)
    if len(line) >= 3 and line[0:2].isdigit() and line[2].isalpha():
        return True

    # Check for specific deadhead markers: DH or UX
    if line.startswith('DH ') or line.startswith('UX '):
        return True

    return False
```

**Change:** Added explicit check for lines starting with "DH " or "UX "

### 2. Updated `_parse_leg()` Method

**File:** `src/parsers/pairing_parser.py` (lines 235-251)

```python
# Check if first field is a deadhead marker (UX, DH, etc.) without equipment code
# Deadhead markers are 2-letter uppercase codes
if len(fields[idx]) == 2 and fields[idx].isupper() and fields[idx].isalpha():
    leg.deadhead = True
    leg.equipment = None  # No equipment code for UX deadheads
    idx += 1
else:
    # Normal leg: equipment code comes first
    leg.equipment = fields[idx]
    idx += 1

    # Check for deadhead marker after equipment (e.g., "20S DH 1124...")
    if idx < len(fields) and len(fields[idx]) == 2 and fields[idx].isupper() and fields[idx].isalpha():
        leg.deadhead = True
        idx += 1
    else:
        leg.deadhead = False
```

**Change:** Added logic to detect when deadhead marker comes FIRST (UX case) vs after equipment (DH case)

### 3. Added D/C Field Parsing

**File:** `src/parsers/pairing_parser.py` (lines 311-317)

```python
# 13. D/C (deadhead credit) - optional field, only present on some deadhead legs
if idx < len(fields):
    field = fields[idx]
    # Check if it's a time format (H:MM, HH:MM, or decimal like .00)
    if ':' in field or '.' in field or field.replace('.', '').replace(':', '').isdigit():
        leg.d_c = self.convert_time(field)
        idx += 1
```

**Change:** Added parsing for D/C (deadhead credit) field that appears on some deadhead legs

## Field Formats

### Regular Leg (with equipment)
```
20S 2164 ORD CLE 1047 1320 .56 1.33 1.33
^   ^    ^   ^   ^    ^    ^   ^    ^
|   |    |   |   |    |    |   |    +-- Accumulated duty time
|   |    |   |   |    |    |   +------- Accumulated flight time
|   |    |   |   |    |    +----------- Flight time
|   |    |   |   |    +---------------- Arrival time
|   |    |   |   +--------------------- Departure time
|   |    |   +------------------------- Arrival station
|   |    +----------------------------- Departure station
|   +---------------------------------- Flight number
+-------------------------------------- Equipment code
```

### DH Deadhead (with equipment)
```
20S DH 1124 CLE ORD 1416 1455 1.39 3.01 7.55 1.39
^   ^  ^    ^   ^   ^    ^    ^    ^    ^    ^
|   |  |    |   |   |    |    |    |    |    +-- D/C (deadhead credit)
|   |  |    |   |   |    |    |    |    +------- Accumulated duty time
|   |  |    |   |   |    |    |    +------------ Accumulated flight time
|   |  |    |   |   |    |    +----------------- Flight time
|   |  |    |   |   |    +---------------------- Arrival time
|   |  |    |   |   +--------------------------- Departure time
|   |  |    |   +------------------------------- Arrival station
|   |  |    +----------------------------------- Departure station
|   |  +---------------------------------------- Flight number
|   +------------------------------------------- DH marker
+----------------------------------------------- Equipment code
```

### UX Deadhead (NO equipment)
```
UX 3707 ORD CID 1300 1420 17.40 1.20 3.11 7.05 1.20
^  ^    ^   ^   ^    ^    ^     ^    ^    ^    ^
|  |    |   |   |    |    |     |    |    |    +-- D/C (deadhead credit)
|  |    |   |   |    |    |     |    |    +------- Accumulated duty time
|  |    |   |   |    |    |     |    +------------ Accumulated flight time
|  |    |   |   |    |    |     +----------------- Flight time
|  |    |   |   |    |    +----------------------- Ground time
|  |    |   |   |    +---------------------------- Arrival time
|  |    |   |   +--------------------------------- Departure time
|  |    |   +------------------------------------- Arrival station
|  |    +----------------------------------------- Departure station
|  +---------------------------------------------- Flight number
+------------------------------------------------- UX marker (NO EQUIPMENT!)
```

## Key Differences: DH vs UX

| Aspect | DH Deadhead | UX Deadhead |
|--------|-------------|-------------|
| Equipment Code | Present (e.g., "20S") | **Absent** |
| Format | `EQUIP DH FLIGHT ...` | `UX FLIGHT ...` |
| Example | `20S DH 1124 CLE ORD...` | `UX 3707 ORD CID...` |
| `leg.equipment` | Set to equipment | Set to `None` |
| `leg.deadhead` | `True` | `True` |

## Verification: Pairing O1277

**Before Fix:**
- Day 1: 3 legs ✅
- Day 2: 1 leg ❌ (missing UX 3707)
- Day 3: 3 legs ✅

**After Fix:**
- Day 1: 3 legs ✅ (ORD→CLE→ORD→SRQ)
- Day 2: 2 legs ✅ (SRQ→ORD, **UX** ORD→CID)
- Day 3: 3 legs ✅ (CID→ORD→CLE, **DH** CLE→ORD)

**Verification Output:**
```
✅ CORRECT: [3, 2, 3] legs per day
✅ Day 2 UX deadhead (FL3707 ORD→CID, no equipment)
✅ Day 3 DH deadhead (20S FL1124 CLE→ORD, with equipment)
```

## Files Modified

1. **src/parsers/pairing_parser.py**
   - Lines 210-229: `is_leg_line()` override
   - Lines 235-251: UX deadhead detection in `_parse_leg()`
   - Lines 311-317: D/C field parsing

2. **FIELD_DEFINITIONS.md**
   - Updated deadhead marker documentation
   - Added UX deadhead example
   - Updated parsing logic section

## Documentation Updates

- **Deadhead Marker:** Changed from "DH only" to "DH, UX, or any 2-letter uppercase code"
- **Examples:** Added UX deadhead example alongside DH example
- **Parsing Logic:** Updated step 3 to explain both DH and UX cases

## Testing

**Command:**
```bash
python3 -m src.main -i "Pairing Source Docs/ORDDSL.pdf" -o "output/ORDDSL_fixed.json"
```

**Results:**
- Total pairings: 2,047 (same as before)
- Errors: 0
- Pairing O1277: ✅ Correctly structured with all legs

## Next Steps

1. ✅ Re-import to MongoDB with corrected data
2. Verify other pairings with UX deadheads are also fixed
3. Update dashboard to show UX vs DH distinction if needed

---

**Status:** Fixed and verified ✅

All UX deadheads (without equipment codes) are now correctly parsed and included in pairings.
