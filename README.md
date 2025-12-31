# Pilot Pairing Dashboard

An interactive web dashboard for pilots to explore and analyze airline pairings with real-time visualizations, route maps, and detailed trip breakdowns.

## Features

### 🗺️ Interactive Maps
- **Layover Cities Map**: Bubble map showing overnight destinations by frequency (excluding home base)
- **Route Network Map**: Flight paths with color-coded routes showing most common connections
- **Individual Pairing Maps**: Detailed route visualization for each pairing with day-by-day color coding

### 📊 Advanced Filtering
- Filter by fleet (787, 756, 737, 320)
- Filter by pairing category
- Filter by credit hours range
- Filter by number of days (1-4 day trips)

### 🔍 Pairing Explorer
- Click on any layover city to see all pairings that overnight there
- Select individual pairings to see detailed:
  - Route map with color-coded days
  - Day-by-day duty period breakdown
  - Flight-by-flight details with times, equipment, and ground times
  - Hotel information for layovers

### 📈 Analytics
- Fleet distribution charts
- Credit hours distribution
- Top layover destinations
- Summary statistics

## Tech Stack

- **Frontend**: Streamlit
- **Database**: MongoDB Atlas
- **Mapping**: Plotly + airportsdata
- **Data Processing**: Pandas + Pydantic
- **PDF Parsing**: pdfplumber

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure MongoDB

Create `.streamlit/secrets.toml`:

```toml
MONGO_URI = "mongodb+srv://username:password@cluster.mongodb.net/"
```

### 3. Parse Pairing Data

```bash
# Parse PDF to JSON
python3 main.py --input pairing.pdf --output output/ORD.json

# Import to MongoDB
python3 mongodb_import.py \
  --connection "YOUR_MONGO_URI" \
  --file output/ORD.json \
  --clear
```

### 4. Fix Layover Stations

```bash
python3 fix_layover_stations_v3.py "YOUR_MONGO_URI"
```

### 5. Launch Dashboard

```bash
# Option 1: Unified Dashboard (Recommended - includes QA tools)
python3 -m streamlit run unified_dashboard.py

# Option 2: Original Dashboard
python3 -m streamlit run dashboard_with_maps.py

# Option 3: Use launcher menu
./launch.sh
```

Opens at: http://localhost:8501

**New Unified Dashboard** combines:
- ✈️ Pairing Explorer (maps, filters, route visualization)
- 🔍 QA Workbench (PDF vs JSON comparison)
- All in one tabbed interface!

## Project Structure

```
.
├── unified_dashboard.py         # ⭐ Unified dashboard (Pairing Explorer + QA)
├── dashboard_with_maps.py       # Original dashboard with interactive maps
├── qa_workbench.py              # Standalone QA workbench
├── qa_annotations.py            # QA annotations and issue tracking
├── validate_parsing.py          # Automated validation script
├── quick_compare.py             # Fast CLI comparison tool
├── main.py                      # PDF parser CLI
├── mongodb_import.py            # MongoDB import utility
├── fix_layover_stations_v3.py  # Layover data correction script
├── launch.sh                    # Dashboard launcher menu
├── stop_streamlit.sh            # Helper to stop running dashboards
├── requirements.txt             # Python dependencies
├── QA_GUIDE.md                  # Quality assurance documentation
├── QA_QUICK_REFERENCE.md        # QA tools cheat sheet
├── src/
│   └── parsers/
│       └── pairing_parser.py   # PDF parsing logic
├── output/                      # Parsed JSON files
├── qa_annotations/              # QA issue tracking data
└── .streamlit/
    ├── config.toml             # Dashboard theme
    └── secrets.toml            # MongoDB credentials (gitignored)
```

## Data Model

### Pairings Collection
- Pairing ID, fleet, base, category
- Credit hours, flight hours, days
- Duty periods with legs and layovers

### Legs Collection
- Individual flight segments
- Departure/arrival stations and times
- Layover station (null for last duty period and 1-day trips)
- Origin station, flight time, ground time

## Quality Assurance

### Validation Framework

Automated validation to ensure parsing accuracy:

```bash
python3 validate_parsing.py "Pairing Source Docs/ORDDSL.pdf" output/ORD.json
```

Validates:
- Header information (base, month)
- Bid period count
- Fleet assignments
- FTM/TTL totals matching
- Pairing structure completeness
- Time format consistency
- Station code validity
- Data completeness metrics

### QA Workbench

Interactive tool for human-in-the-loop quality assurance:

```bash
streamlit run qa_workbench.py
```

Features:
- Side-by-side PDF vs parsed data comparison
- Fleet totals validation
- Individual pairing inspection
- Search & compare across both sources
- Automated validation report

### QA Annotations

Issue tracking and annotation tool for QA reviewers:

```bash
streamlit run qa_annotations.py
```

Capabilities:
- Document parsing issues with severity levels
- Track expected vs actual values
- Status tracking (Open, In Progress, Resolved)
- Export annotation reports (CSV, JSON)
- Issue statistics and analytics

## License

MIT License
