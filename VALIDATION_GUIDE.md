# Validation Guide

How to validate parsed JSON output against source PDFs.

## Quick Validation

```bash
python3 validate_output.py --pdf ORDDSLMini.pdf --json output/test.json
```

## What Gets Validated

### 1. Pairing Count
- Compares number of pairings in PDF vs JSON
- Alerts if mismatch > 5%

### 2. Data Quality Checks
- **Missing critical fields**: ID, category, stations
- **Zero values**: Flight time, duty time (for non-deadhead legs)
- **Field misalignment**: Meal codes that are numbers (indicates parsing error)
- **Suspicious values**: Ground time > 24 hours, invalid station codes

### 3. Spot Checks
- Verifies sample pairings exist in PDF
- Cross-references pairing IDs and categories

### 4. Field Consistency
- Validates equipment codes (2-4 characters)
- Validates station codes (3 letters)
- Reports unique values found

## Validation Results

### ✅ Passing Validation
```
✅ VALIDATION PASSED - No errors or warnings
```
All data parsed correctly.

### ⚠️ Passing with Warnings
```
⚠️ VALIDATION PASSED WITH WARNINGS - X warnings
```
Data is usable but has minor issues (e.g., very long ground times, missing optional fields).

### ❌ Failing Validation
```
❌ VALIDATION FAILED - X critical errors found
```
Significant parsing errors detected. Review and fix before using data.

## Common Issues and Fixes

### Issue: Zero Flight Time
**Symptom**: `Non-deadhead leg has zero flight time`

**Cause**: Field misalignment - parser is reading wrong columns

**Fix**: Check if PDF uses different leg format (787 vs 737)

---

### Issue: Meal Code is Number
**Symptom**: `Meal code appears to be a number: 2.57`

**Cause**: Fields shifted - meal_code field contains flight time

**Fix**: PDF format has different number of fields than expected

---

### Issue: Count Mismatch
**Symptom**: `Pairing count mismatch: PDF has 245, JSON has 70`

**Cause**: Parser stopped early or header detection failing

**Fix**: Check bid period finalization logic and header detection

---

## Current Status (ORDDSL.pdf)

**Latest validation results:**
- ✓ Pairing count: 2047/2047 match
- ✓ Flight times: Parsing correctly
- ⚠️ Duty times: Not extracted for 737 format (non-critical)
- ⚠️ Some very long ground times (24+ hours) - likely layovers

**Formats supported:**
1. **787 format** (with service code): `eqp flt dept arr dtime atime gtime meal svc ft accum_ft dt d/c`
2. **737 format** (no service code): `eqp flt dept arr dtime atime gtime meal ft accum_ft [d/c]`
3. **Deadhead formats**: Both "D" marker and "DH" flight number

---

## Advanced Validation

### Sample Specific Pairings
```bash
python3 validate_output.py \
  --pdf ORDDSL.pdf \
  --json output/ORD.json \
  --sample 50
```

### Save Detailed Report
```bash
python3 validate_output.py \
  --pdf ORDDSL.pdf \
  --json output/ORD.json \
  --output validation_report.json
```

The report includes:
- All issues found
- All warnings
- Statistics
- Can be analyzed programmatically

---

## Interpreting Validation Output

```
================================================================================
VALIDATION SUMMARY
================================================================================

Statistics:
  Pairings in PDF:  2047
  Pairings in JSON: 2047
  Pairings checked: 100
  Legs checked:     528

❌ CRITICAL ERRORS (479):
  • O5724 DP1 Leg1: Leg has zero duty time
  ...

⚠️  WARNINGS (21):
  • O8525 DP1 Leg1: Very long ground time: 74:05
  ...
```

- **Pairings checked**: Sample size for detailed validation
- **Legs checked**: Total flight legs examined
- **Critical errors**: Must fix before production use
- **Warnings**: Review but may be acceptable

---

## Validation in CI/CD

Exit codes:
- `0`: Validation passed (no critical errors)
- `1`: Validation failed (critical errors found)

Example usage in scripts:
```bash
#!/bin/bash
python3 validate_output.py --pdf input.pdf --json output.json
if [ $? -ne 0 ]; then
    echo "Validation failed!"
    exit 1
fi
echo "Validation passed, proceeding..."
```

---

## Manual Spot Checking

To manually verify a specific pairing:

1. **Find in JSON**:
   ```bash
   python3 -c "
   import json
   with open('output/ORD.json') as f:
       data = json.load(f)
   for bp in data['data']:
       for p in bp['pairings']:
           if p['id'] == 'O8001':
               print(json.dumps(p, indent=2))
   "
   ```

2. **Find in PDF**:
   - Open PDF
   - Search for "ID O8001"
   - Compare fields manually

3. **Check specific leg**:
   ```python
   # Load JSON
   import json
   with open('output/ORD.json') as f:
       data = json.load(f)

   # Find pairing O8001, duty period 1, leg 1
   p = next(p for bp in data['data'] for p in bp['pairings'] if p['id'] == 'O8001')
   leg = p['duty_periods'][0]['legs'][0]

   print(f"Equipment: {leg['equipment']}")
   print(f"Route: {leg['departure_station']}->{leg['arrival_station']}")
   print(f"Flight time: {leg['flight_time']} ({leg['flight_time_minutes']} min)")
   ```

---

## Known Limitations

1. **Duty Time (737 format)**: Not currently extracted for 737 fleet pairings (field format differs)
2. **Calendar dates**: Embedded in leg lines, not separately validated
3. **Reserve pairings**: May have empty duty periods (expected behavior)
4. **Ground time >24h**: Likely correct (long layovers) but flagged as warning

---

## Next Steps

1. **Run validation** after every parsing run
2. **Review critical errors** before importing to database
3. **Document warnings** that are expected/acceptable
4. **Update parser** if new PDF formats encountered
5. **Add regression tests** for known-good pairings

Validation ensures data quality and catches parsing regressions early!
