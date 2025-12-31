# Unified Dashboard Guide

## Overview

The **Unified Dashboard** combines pairing exploration and QA validation in one streamlined interface with three main tabs.

## Launch

```bash
python3 -m streamlit run unified_dashboard.py
```

Or use the launcher:
```bash
./launch.sh
# Select option 1
```

## Tab 1: 📊 Pairing Explorer

**What it does:** Browse, filter, and explore pairings with interactive maps

### Features:

#### Sidebar Filters
- **Fleet**: Filter by aircraft (787, 756, 737, 320)
- **Category**: Filter by pairing type (BASIC, etc.)
- **Credit Hours**: Slider to set min/max credit hours
- **Days**: Select 1-4 day trips

#### Top Metrics
- Total pairings count
- Number of fleets
- Average credit hours
- Layover cities count

#### Interactive Map
- **Layover Cities Map**: Bubble map showing overnight destinations
  - Size = frequency of layovers
  - Color = heat map (more = darker red)
  - Excludes home base
  - Click cities to explore pairings

#### Pairing Search
- Searchable table of all pairings
- Sort by any column
- Filter applied in real-time

#### Pairing Details
- Select any pairing from dropdown
- **Route Map**: Color-coded by day
  - Solid lines = regular flights
  - Dashed lines = deadheads
  - Airport markers with codes
- **Trip Structure**: Expandable day-by-day breakdown
  - Report/release times
  - Hotel information
  - Complete leg details with times and equipment

### Typical Workflow:

1. Set filters in sidebar (fleet, days, credit range)
2. View layover map to see patterns
3. Search for specific pairings
4. Select pairing for detailed route map
5. Expand days to see flight-by-flight details

---

## Tab 2: 🔍 QA Workbench

**What it does:** Compare PDF source with parsed JSON data for validation

### Features:

#### File Selection
- **PDF Selector**: Choose source PDF from "Pairing Source Docs"
- **JSON Selector**: Choose parsed JSON from "output"

#### QA Modes (Radio Buttons)

##### 1. Overview Mode
**Purpose:** Quick health check

**Left Column (PDF Source):**
- Total pages
- Total characters
- Preview first page

**Right Column (Parsed Data):**
- Bid periods count
- Total pairings
- Total legs
- Fleet breakdown table (Fleet, Base, Pairings, FTM, TTL)

**When to use:** Initial check when validating a new parse

---

##### 2. Fleet Totals Mode
**Purpose:** Validate FTM/TTL accuracy (most critical check)

**3-Column Layout per Fleet:**

**Column 1 - PDF Source:**
```
Base: ORD
FTM: 13,578:02
TTL: 14,387:35
```

**Column 2 - Parsed Data:**
```
Base: CHICAGO
FTM: 13,578:02
TTL: 14,387:35
```

**Column 3 - Status:**
```
FTM: ✅
TTL: ✅
Perfect match!
```

**When to use:** Before importing to MongoDB - this catches the most critical errors

---

##### 3. Individual Pairing Mode
**Purpose:** Deep dive into specific pairings

**Left Column (PDF Source):**
- Shows all occurrences of pairing ID in PDF
- Highlighted search term
- Surrounding context (10 lines before/after)
- Multiple expandable occurrences

**Right Column (Parsed Data):**
- JSON structure of pairing
- Expandable duty periods
- Complete leg details in tables
- Hotel information

**When to use:**
- Investigating specific pairing issues
- Verifying times and routes
- Checking hotel assignments

---

##### 4. Search & Compare Mode
**Purpose:** Find any value in both sources simultaneously

**Input:** Search term (pairing ID, station code, flight number, etc.)

**Left Column (PDF Matches):**
- Shows all lines containing search term
- Line numbers
- Expandable context

**Right Column (Parsed Matches):**
- Shows all pairings containing search term
- Table with fleet, ID, days, credit hours

**When to use:**
- Finding all occurrences of a station (e.g., "LAX")
- Tracking down specific flight numbers
- Verifying equipment types

### Typical QA Workflow:

1. **Overview**: Quick sanity check
2. **Fleet Totals**: Verify FTM/TTL (critical!)
3. **Search & Compare**: Spot-check random values
4. **Individual Pairing**: Deep dive if issues found

---

## Tab 3: 📝 Annotations

**What it does:** Placeholder for full annotations tool

**Note:** Full annotation functionality is in standalone `qa_annotations.py`

Launch standalone tool:
```bash
python3 -m streamlit run qa_annotations.py
```

---

## Tips & Tricks

### Pairing Explorer Tips

1. **Start broad, then narrow**: Begin with "All" filters, then add constraints
2. **Use days filter**: Great for finding trips that fit your schedule
3. **Sort by credit hours**: Click column headers in tables
4. **Explore layover cities**: Click cities on map to see all pairings

### QA Workbench Tips

1. **Always check Fleet Totals**: This is the most important validation
2. **Use Search for spot-checks**: Random station codes, flight numbers
3. **Compare side-by-side**: Keep PDF source in mind when reviewing parsed data
4. **Look for patterns**: If one pairing is wrong, others might be too

### Performance Tips

1. **Clear cache**: If data seems stale, refresh the page
2. **Limit results**: Use filters to reduce dataset size
3. **One tab at a time**: Focus on what you need

---

## Common Questions

### Q: Why can't I see my parsed data?
A: Make sure:
- JSON file is in `output/` directory
- MongoDB is connected (for Pairing Explorer)
- File selector shows your file

### Q: Fleet totals don't match - what now?
A:
1. Note the specific fleet with mismatch
2. Switch to Individual Pairing mode
3. Inspect several pairings from that fleet
4. Document issues using qa_annotations.py
5. Report parser bug if pattern found

### Q: How do I switch between QA and Explorer?
A: Just click the tabs at top! No need to restart.

### Q: Can I have both PDF and MongoDB open?
A: Yes!
- Tab 1 (Explorer) requires MongoDB
- Tab 2 (QA Workbench) uses local PDF/JSON files
- They work independently

---

## Keyboard Shortcuts

- `Ctrl+R` / `Cmd+R`: Refresh page
- `Esc`: Close modals/dialogs
- Tab navigation: Click tab names

---

## Next Steps

After using the dashboard:

1. **If validation passes**: Import to MongoDB
2. **If issues found**: Document in qa_annotations.py
3. **If critical errors**: Fix parser, re-parse, re-validate

---

## Getting Help

- **QA procedures**: See [QA_GUIDE.md](QA_GUIDE.md)
- **Quick commands**: See [QA_QUICK_REFERENCE.md](QA_QUICK_REFERENCE.md)
- **General setup**: See [README.md](README.md)
