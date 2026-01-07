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

**Option A: Batch Process Entire Folder (Recommended)**

```bash
# Process all .DAT and .PDF files in a folder and import to MongoDB
python3 batch_process.py --folder "Pairing Source Docs/February 2026"

# Parse only (no import)
python3 batch_process.py --folder "Pairing Source Docs/February 2026" --no-import

# Process recursively through subdirectories
python3 batch_process.py --folder "Pairing Source Docs" --recursive
```

**Option B: Process Single File**

```bash
# Parse .DAT or .PDF file to JSON
python3 -m src.main -i "pairing.DAT" -o "output/ORD.json"

# Import to MongoDB
python3 mongodb_import.py --file output/ORD.json
```

### 4. Launch Dashboard

```bash
# Launch unified dashboard
python3 -m streamlit run unified_dashboard.py
```

Opens at: http://localhost:8501

**Unified Dashboard Features**:
- ✈️ Interactive layover and route maps
- 🔍 Advanced filtering (fleet, base, layovers, credit hours)
- 📊 Analytics and statistics
- 🗺️ Individual pairing route visualization

## Project Structure

```
.
├── unified_dashboard.py         # ⭐ Main dashboard with maps and filters
├── batch_process.py             # Batch folder processing script
├── mongodb_import.py            # MongoDB import utility
├── cleanup_project.sh           # Project cleanup script
├── requirements.txt             # Python dependencies
├── src/
│   ├── main.py                 # Parser entry point
│   ├── parsers/
│   │   └── pairing_parser.py  # Parsing logic
│   └── utils/
│       ├── pdf_reader.py      # PDF file reading
│       ├── text_reader.py     # .DAT file reading
│       └── file_utils.py      # JSON writing utilities
├── output/                      # Parsed JSON files (gitignored)
├── archive/                     # Old/obsolete files (gitignored)
│   ├── old_docs/               # Archived markdown files
│   └── old_scripts/            # Archived Python scripts
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

## Batch Processing

Process entire folders of pairing files at once:

```bash
# Process all files in February 2026 folder and import to MongoDB
python3 batch_process.py --folder "Pairing Source Docs/February 2026"

# Options:
#   --folder PATH      Folder containing .DAT or .PDF files (required)
#   --output PATH      Output directory for JSON files (default: output/)
#   --recursive        Search recursively through subdirectories
#   --no-import        Parse only, don't import to MongoDB
```

**Example Output:**
```
Found 12 file(s) to process:
  - February 2026/ORDDSL.DAT
  - February 2026/LAXDSL.DAT
  ...

✓ Successfully parsed ORDDSL.DAT
✓ Successfully imported ORDDSL.json

BATCH PROCESSING COMPLETE
Total files:           12
Successfully parsed:   12
Parse failures:        0
Successfully imported: 12
Import failures:       0
```

## Supported File Formats

- **`.DAT` files**: Plain text format (50-100x faster than PDF)
- **`.PDF` files**: PDF format (requires pdfplumber)

Both formats produce identical JSON output and are automatically detected by file extension.

## License

MIT License
