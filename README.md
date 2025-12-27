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
streamlit run dashboard_with_maps.py
```

Opens at: http://localhost:8501

## Project Structure

```
.
├── dashboard_with_maps.py       # Main dashboard with interactive maps
├── main.py                      # PDF parser CLI
├── mongodb_import.py            # MongoDB import utility
├── fix_layover_stations_v3.py  # Layover data correction script
├── requirements.txt             # Python dependencies
├── src/
│   └── parsers/
│       └── pairing_parser.py   # PDF parsing logic
├── output/                      # Parsed JSON files
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

## License

MIT License
