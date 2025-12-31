# Pairing PDF Field Definitions

## Leg (Flight) Line Format

### Field Order:

```
Equipment [DH] FlightNumber Departure Arrival DepTime ArrTime [GroundTime] [MealCode(s)] FlightTime AccumFlightTime AccumDutyTime
```

### Field Descriptions:

| Position | Field Name | Required | Format | Examples | Notes |
|----------|------------|----------|--------|----------|-------|
| 1 | Equipment Code | Yes | 3 chars | `73G`, `73Y`, `37K`, `78J` | Aircraft type |
| 2 | Deadhead Marker | No | 2 letters | `DH`, `UX` | Any 2-letter uppercase code |
| 3 | Flight Number | Yes | Alphanumeric | `123`, `456A` | Actual flight number |
| 4 | Departure Airport | Yes | 3 letters | `ORD`, `LAX`, `SFO` | IATA code |
| 5 | Arrival Airport | Yes | 3 letters | `LAX`, `SFO`, `ORD` | IATA code |
| 6 | Departure Time | Yes | `HHMM` | `0800`, `1245` | 24-hour format |
| 7 | Arrival Time | Yes | `HHMM` | `1030`, `2030` | 24-hour format |
| 8 | Ground Time | Optional | `H:MM` or `HH:MM` | `2:15`, `26:31`, `0` | May be omitted |
| 9+ | Meal Code(s) | Optional | 1-3 letters | `B`, `L`, `D`, `S`, `B L` | Space-separated if multiple |
| N-2 | Flight Time | Yes | `H:MM` or `HH:MM` | `4:30`, `9:24` | Duration of flight |
| N-1 | Accumulated Flight Time | Yes | `H:MM` or `HH:MM` | `4:30`, `12:15` | Running total |
| N | Accumulated Duty Time | Yes | `H:MM` or `HH:MM` | `6:45`, `14:30` | Running total |

### Examples:

#### Regular Flight with Meal:
```
73G 123 ORD LAX 0800 1030 2:15 B L 4:30 4:30 6:45
```
- Equipment: 73G
- Flight: 123
- Route: ORD → LAX
- Times: Depart 08:00, Arrive 10:30
- Ground: 2:15
- Meals: B (Breakfast), L (Lunch)
- Flight Time: 4:30
- Accumulated Flight: 4:30
- Accumulated Duty: 6:45

#### Deadhead Flight (DH marker):
```
78J DH 456 LAX SFO 1245 1415 0 7:45 12:15 14:30
```
- Equipment: 78J
- **Deadhead: Yes (DH)**
- Flight: 456

#### Deadhead Flight (UX marker):
```
20S UX 3707 ORD CID 1300 1420 17.40 1.20 3.11 7.05 1.20
```
- Equipment: 20S
- **Deadhead: Yes (UX)**
- Flight: 3707
- Route: LAX → SFO
- Times: Depart 12:45, Arrive 14:15
- Ground: 0
- Meals: None
- Flight Time: 7:45
- Accumulated Flight: 12:15
- Accumulated Duty: 14:30

#### No Ground Time, Multiple Meals:
```
37K 789 SFO ORD 1415 2030 B D 4:15 16:30 18:45
```
- Equipment: 37K
- Flight: 789
- Route: SFO → ORD
- Times: Depart 14:15, Arrive 20:30
- Ground: (omitted - defaults to "0")
- Meals: B (Breakfast), D (Dinner)
- Flight Time: 4:15
- Accumulated Flight: 16:30
- Accumulated Duty: 18:45

## Parsing Logic

### Step-by-Step Field Extraction:

1. **Split line** by whitespace
2. **Extract Equipment** (index 0)
3. **Check for Deadhead Marker** (index 1: 2-letter uppercase code)
   - Valid markers: DH, UX, or any 2-letter uppercase alphabetic code
   - If match: deadhead = true, increment index
   - If no match: deadhead = false
4. **Extract Flight Number** (current index)
5. **Extract Departure** (current index + 1)
6. **Extract Arrival** (current index + 2)
7. **Extract Departure Time** (current index + 3)
8. **Extract Arrival Time** (current index + 4)
9. **Check Ground Time** (current index + 5)
   - If contains `:` or is numeric → Ground Time
   - Otherwise → Skip to meal codes
10. **Collect Meal Codes** (loop while single uppercase letters)
11. **Extract Flight Time** (next field after meals)
12. **Extract Accumulated Flight Time** (next field)
13. **Extract Accumulated Duty Time** (next field)

### Meal Code Detection:

Valid meal codes:
- **B** = Breakfast
- **L** = Lunch
- **D** = Dinner
- **S** = Snack

Rules:
- Single uppercase letter
- Can have 0-3 codes
- Space-separated if multiple
- Stop collecting when encounter non-letter or multi-char field

### Time Format Handling:

Input formats accepted:
- `H:MM` → e.g., `4:30`, `9:24`
- `HH:MM` → e.g., `14:30`, `26:31`
- `H.MM` → e.g., `4.30` (converted to `4:30`)
- `0` → Stored as `"0"`

The `convert_time()` function normalizes all to `HH:MM` format.

## Header Line Format

### Original Format (with "1DSL"):
```
EFF MM/DD/YY THRU MM/DD/YY ... FLEET ... BASE ... MONTH YEAR
```

Column positions:
- Effective Date: 9-17
- Through Date: 23-31
- Fleet: 35-38
- Base: 42-55
- Month/Year: 68-78

### Compact Format (without "1DSL"):
```
EFF MM/DD/YY THRU MM/DD/YY FLEET BASE MONTH YEAR
```

Column positions:
- Effective Date: 4-12
- Through Date: 18-26
- Fleet: 27-30
- Base: 31-38
- Month/Year: 39-47

## Totals Line Format

```
BASE FLEET FTM-HH,HHH:MM TTL-HH,HHH:MM
```

Example:
```
ORD 787 FTM-13,578:02 TTL-14,387:35
```

Regex pattern:
```regex
([A-Z]{3})\s+([0-9]{2,3}[A-Z]?)\s+FTM-\s*([\d:,]+)\s+TTL-\s*([\d:,]+)
```

## Pairing Start Line Format

```
EFF MM/DD/YY THRU MM/DD/YY [F/O] ID PAIRINGID - CATEGORY [(SUBCATEGORY)] date date date...
```

Example:
```
EFF 12/30/25 THRU 01/04/26 ID O8001 - BASIC (HNL) 30 31 1 2| 3
```

Regex pattern:
```regex
EFF (\d{2}/\d{2}/\d{2}) THRU (\d{2}/\d{2}/\d{2}).*?(F/O)?\s*ID (\w+)\s+-\s+(\w+)(?:\s+\((\w+)\))?
```

## Layover Station Logic

### Business Rules:

The `layover_station` field on `DutyPeriod` follows specific business logic:

1. **1-Day Trips**: No layover stations
   - All duty periods have `layover_station = None`
   - Crew returns to base same day

2. **Multi-Day Trips**: Layover only for intermediate days
   - Days 1 through N-1: `layover_station = arrival_station` of last leg
   - Day N (last day): `layover_station = None` (returning to base)

### Examples:

**1-Day Trip:**
```
Day 1: ORD → LAX → SFO → ORD
  layover_station: None
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

## Updated: 2025-12-27

This document defines the authoritative field order and parsing rules for the pairing parser.
