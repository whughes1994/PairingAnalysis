# Quality Assurance Guide

This guide explains how to use the QA tools to validate and correct parsing errors.

## Overview

The QA workflow consists of three tools:

1. **validate_parsing.py** - Automated validation (command-line)
2. **qa_workbench.py** - Interactive inspection (web interface)
3. **qa_annotations.py** - Issue tracking (web interface)

## Step 1: Automated Validation

Run the validation script to get a quick health check:

```bash
python3 validate_parsing.py "Pairing Source Docs/ORDDSL.pdf" output/ORD.json
```

### What it checks:

- ✅ Header validation (base, month)
- ✅ Bid period count
- ✅ Fleet assignments
- ✅ Pairing counts
- ✅ FTM/TTL totals (critical!)
- ✅ Pairing structure
- ✅ Time formats (HH:MM)
- ✅ Station codes (3-letter)
- ✅ Data completeness

### Exit codes:

- `0` = All checks passed
- `1` = Issues found

### Sample output:

```
================================================================================
CHECK: Totals Validation
================================================================================

  PDF Total 1:
    Fleet: 787
    FTM: 13,578:02
    TTL: 14,387:35
    Parsed FTM: 13,578:02
    Parsed TTL: 14,387:35
    ✓ Match

✅ ALL VALIDATION CHECKS PASSED!
```

## Step 2: Interactive Inspection (QA Workbench)

Launch the workbench for detailed inspection:

```bash
streamlit run qa_workbench.py
```

Opens at: http://localhost:8501

### Features:

#### **Overview Mode**
- Quick stats on PDF vs parsed data
- Fleet breakdown table
- Page count and data summary

#### **Fleet Totals Mode**
- Side-by-side comparison of FTM/TTL for each fleet
- Visual match/mismatch indicators
- PDF context viewer showing source text

**Use this when:** You need to verify the critical totals are correct

#### **Individual Pairing Mode**
- Select any pairing from dropdown
- See PDF source with highlighted pairing ID
- View complete parsed data structure
- Inspect duty periods and legs

**Use this when:** A specific pairing looks suspicious

#### **Search & Compare Mode**
- Search for any text (pairing ID, station, flight number)
- See all matches in both PDF and parsed data
- Useful for tracking down specific flights or routes

**Use this when:** You need to verify a specific value appears in both sources

#### **Validation Report Mode**
- Automated checks with visual indicators
- Issue summary
- Warning list

**Use this when:** You want a comprehensive validation report

## Step 3: Issue Tracking (QA Annotations)

Launch the annotations tool to document issues:

```bash
streamlit run qa_annotations.py
```

### Workflow:

#### **Add Annotation Tab**

Fill out the issue form:

1. **Pairing ID**: Which pairing has the issue (e.g., O8001)
2. **Issue Type**: Select from predefined categories:
   - Missing Data
   - Incorrect Time
   - Wrong Station Code
   - Incorrect Flight Number
   - Missing Leg
   - Extra Leg
   - Wrong Equipment
   - Incorrect Layover
   - FTM/TTL Mismatch
   - Date Error
   - Other

3. **Severity**: Low / Medium / High / Critical
4. **Field Affected**: Specific JSON field (e.g., departure_time)
5. **Expected Value**: What it should be (from PDF)
6. **Actual Value**: What was parsed
7. **Description**: Detailed explanation
8. **Notes**: Additional context

**Example annotation:**

```
Pairing ID: O8001
Issue Type: Incorrect Time
Severity: Medium
Field Affected: legs[0].departure_time_formatted
Expected Value: 09:20
Actual Value: 09:02
Description: First leg departure time parsed incorrectly. PDF shows 0920 but parsed as 09:02 instead of 09:20.
```

#### **View Annotations Tab**

- Filter by issue type, severity, or status
- Update status (Open → In Progress → Resolved)
- Review all documented issues
- Color-coded by severity (🔴 Critical, 🟠 High, 🟡 Medium, 🟢 Low)

#### **Export Report Tab**

- Summary statistics
- Issue breakdown by type and severity
- Most affected pairings
- Export as CSV or JSON

## Common Workflows

### Workflow 1: Validating a New Parse

```bash
# 1. Parse the PDF
python3 main.py --input "Pairing Source Docs/ORDDSL.pdf" --output output/ORD.json

# 2. Run automated validation
python3 validate_parsing.py "Pairing Source Docs/ORDDSL.pdf" output/ORD.json

# 3. If issues found, launch workbench for inspection
streamlit run qa_workbench.py

# 4. Document issues in annotations tool
streamlit run qa_annotations.py
```

### Workflow 2: Investigating Specific Issues

User reports: "Some 737 pairings have wrong departure times"

```bash
# 1. Launch QA Workbench
streamlit run qa_workbench.py

# 2. Use Search & Compare mode
#    - Search for "737"
#    - Review matched pairings
#    - Compare PDF vs parsed times

# 3. Switch to Individual Pairing mode
#    - Select suspicious pairing
#    - Examine duty periods
#    - Check time formats

# 4. Document in annotations
streamlit run qa_annotations.py
#    - Add annotation with expected/actual times
#    - Mark as "High" severity if affecting many pairings
```

### Workflow 3: Pre-Database Import Check

Before importing to MongoDB:

```bash
# 1. Run validation
python3 validate_parsing.py "Pairing Source Docs/ORDDSL.pdf" output/ORD.json

# 2. Check exit code
echo $?  # Should be 0

# 3. If passed, safe to import
python3 mongodb_import.py --connection "MONGO_URI" --file output/ORD.json --clear
```

## Annotation Storage

Annotations are saved in `qa_annotations/` directory:

```
qa_annotations/
├── ORD_annotations.json
├── LAX_annotations.json
└── ...
```

Each JSON file contains:
- All annotations for that parsed file
- Timestamps
- Status tracking
- Full audit trail

**Keep these files in version control** to track QA history over time.

## Tips

### For QA Reviewers

1. **Start with automated validation** - catches most issues quickly
2. **Spot-check critical data** - FTM/TTL totals are most important
3. **Use severity levels appropriately**:
   - **Critical**: Data corruption, missing entire bid periods
   - **High**: Wrong totals, missing flights
   - **Medium**: Incorrect times, wrong equipment
   - **Low**: Formatting issues, minor inconsistencies

4. **Document context** - Future you will thank you for detailed notes
5. **Track patterns** - If seeing same issue type repeatedly, may be parser bug

### For Developers

1. **Use annotations as test cases** - Convert issues to unit tests
2. **Track issue types** - Patterns indicate parser weaknesses
3. **Prioritize critical issues** - Fix FTM/TTL mismatches first
4. **Export annotations regularly** - CSV export good for spreadsheet analysis

## Validation Checklist

Before marking a parsed file as "production ready":

- [ ] Automated validation passes all checks
- [ ] FTM/TTL totals match for all fleets
- [ ] Spot-checked 5+ random pairings
- [ ] Searched for known problematic patterns
- [ ] No critical or high severity annotations
- [ ] All identified issues documented
- [ ] Annotations exported and archived

## Troubleshooting

### "No matches found in PDF"

- Check that PDF text extraction is working (try Overview mode)
- Search term might need different capitalization
- Some PDFs have image-based text (OCR needed)

### "Parsed data shows 0 pairings"

- JSON structure might be different (check Overview mode)
- File might be corrupted or incomplete
- Wrong file selected

### "Workbench won't load"

```bash
# Check Streamlit is installed
python3 -m pip list | grep streamlit

# Try with full python path
python3 -m streamlit run qa_workbench.py
```

## Next Steps

After documenting issues:

1. **Fix parser**: Update parsing logic in `src/parsers/pairing_parser.py`
2. **Re-parse**: Run parser again on source PDF
3. **Re-validate**: Run validation to confirm fixes
4. **Update annotations**: Mark issues as "Resolved"
5. **Import clean data**: Push to MongoDB

## Support

Issues or questions? Check:
- [Project README](README.md)
- [GitHub Issues](https://github.com/whughes1994/PairingAnalysis/issues)
