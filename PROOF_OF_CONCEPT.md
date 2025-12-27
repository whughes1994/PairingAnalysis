# Pilot Pairing Dashboard - Proof of Concept

## Summary

Interactive web dashboard for pilots to explore and filter airline pairings with real-time visualizations.

## What You Have

✅ **Parser**: Extracts pairing data from PDFs (all 4 fleets: 787, 756, 737, 320)
✅ **Database**: MongoDB with 2,047 pairings indexed and optimized
✅ **Dashboard**: Streamlit web app with filters, charts, and export
✅ **Documentation**: Complete setup and customization guides

## Demo Features

### 1. **Fleet Overview**
- Pie chart showing pairing distribution across 4 fleets
- Bar chart of average credit hours by fleet
- Real-time metrics (total pairings, fleets, avg credit, cities)

### 2. **Layover Analysis**
- Top 15 overnight destinations
- Frequency bar charts
- Interactive data table

### 3. **Pairing Search & Filter**
- **Filter by:**
  - Fleet (787/756/737/320/All)
  - Category (BASIC/GLOBAL/etc.)
  - Credit hours range (0-50h slider)

- **View:**
  - Credit distribution histogram
  - Summary stats (min/max/avg)
  - Detailed results table
  - CSV download

### 4. **Interactive Data Table**
Shows for each pairing:
- ID
- Fleet
- Category
- Credit hours
- Days
- Flight hours
- Layover cities

## Quick Start

```bash
# 1. Configure MongoDB connection
cat > .streamlit/secrets.toml << 'EOF'
MONGO_URI = "YOUR_MONGODB_ATLAS_CONNECTION_STRING"
EOF

# 2. Install dependencies (already done)
pip3 install streamlit plotly pandas

# 3. Launch dashboard
streamlit run dashboard.py
```

**Opens at:** http://localhost:8501

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Frontend** | Streamlit | Web interface, no HTML/CSS needed |
| **Database** | MongoDB Atlas | Cloud database, scalable |
| **Charts** | Plotly | Interactive visualizations |
| **Data** | Pandas | Data manipulation |
| **Parser** | Pydantic + pdfplumber | PDF → JSON → MongoDB |

## Architecture

```
┌─────────────┐
│   PDF File  │
│ (ORDDSL.pdf)│
└──────┬──────┘
       │
       │ Parse (main.py)
       ▼
┌─────────────┐
│  JSON File  │
│ (ORD.json)  │
└──────┬──────┘
       │
       │ Import (mongodb_import.py)
       ▼
┌─────────────────┐
│  MongoDB Atlas  │
│  ┌───────────┐  │
│  │ pairings  │  │ 2,047 docs
│  │ legs      │  │ 10,741 docs
│  │bid_periods│  │ 4 docs
│  └───────────┘  │
└────────┬────────┘
         │
         │ Query
         ▼
┌────────────────────┐
│ Streamlit Dashboard│
│  - Filters         │
│  - Charts          │
│  - Export          │
└────────────────────┘
         │
         ▼
    🧑‍✈️ Pilots
```

## Data Flow

1. **Parse**: PDF → JSON (4 bid periods, 2,047 pairings, 10,741 legs)
2. **Import**: JSON → MongoDB (indexed collections)
3. **Query**: Dashboard → MongoDB (filtered results)
4. **Visualize**: Plotly charts + Streamlit UI
5. **Export**: CSV download

## Current Data (ORD Base)

- **Bid Periods**: 4 (787, 756, 737, 320)
- **Pairings**: 2,047 total
  - 787: 70 pairings
  - 756: 65 pairings
  - 737: 1,262 pairings
  - 320: 650 pairings
- **Legs**: 10,741 flight segments
- **Layover Cities**: 32 unique destinations

## Deployment Options

### Option 1: Local Development (Current)
```bash
streamlit run dashboard.py
# Access: http://localhost:8501
```

**Pros:** Instant, no setup
**Cons:** Only accessible on your machine

### Option 2: Streamlit Cloud (Recommended for Demo)
1. Push code to GitHub
2. Deploy on https://streamlit.io/cloud (free)
3. Add MongoDB connection to Streamlit secrets
4. Share link with stakeholders

**Pros:** Free, shareable URL, no server management
**Cons:** Public by default (paid for private)

### Option 3: Company Server
```bash
# Run on internal server
streamlit run dashboard.py --server.address 0.0.0.0 --server.port 8501
# Access: http://SERVER_IP:8501
```

**Pros:** Internal only, controlled access
**Cons:** Requires server setup

### Option 4: Heroku/AWS/Azure
Deploy as web app with custom domain

**Pros:** Professional, scalable, custom branding
**Cons:** Costs money, more complex setup

## Next Steps for Full Production

### Phase 1: Enhanced Filtering (1-2 days)
- [ ] Add date range picker
- [ ] Filter by layover city
- [ ] Filter by days (1-4 day trips)
- [ ] Filter by domestic/international
- [ ] Multi-fleet selection

### Phase 2: User Features (3-5 days)
- [ ] User authentication (login/logout)
- [ ] Save favorite pairings
- [ ] Personal preferences
- [ ] Comparison tool (side-by-side)
- [ ] Notifications for new matches

### Phase 3: More Data (1 week)
- [ ] Parse all bases (DEN, LAX, EWR, SFO, etc.)
- [ ] Historical data (past months)
- [ ] Auto-update from new PDFs
- [ ] Real-time sync with crew scheduling

### Phase 4: Mobile App (2-4 weeks)
- [ ] Convert to React Native/Flutter
- [ ] Native mobile apps (iOS/Android)
- [ ] Push notifications
- [ ] Offline mode

### Phase 5: Advanced Analytics (2-3 weeks)
- [ ] AI-powered recommendations
- [ ] Pairing quality scoring
- [ ] Predictive analytics (likelihood to hold)
- [ ] Historical bid analysis

## Costs

### Current POC (Free)
- MongoDB Atlas Free Tier: $0 (512MB storage)
- Streamlit: $0 (local or cloud free tier)
- **Total: $0/month**

### Production
- MongoDB Atlas (M10): ~$57/month (for all bases + users)
- Streamlit Cloud Private: $250/month (optional)
- Custom domain: $12/year
- **Total: ~$50-300/month** depending on features

## User Feedback Questions

1. What filters are most important?
2. What data is missing?
3. Do you prefer web or mobile?
4. Would you pay for premium features?
5. What other bases do you need?

## Success Metrics

- **User Adoption**: % of pilots using dashboard
- **Time Saved**: Reduced bid planning time
- **Satisfaction**: User survey scores
- **Accuracy**: Data validation vs PDF
- **Performance**: Page load time <2 seconds

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| PDF format changes | High | Automated validation, alerts |
| Database costs | Low | Start free tier, scale as needed |
| User adoption | Medium | Training, documentation, support |
| Data accuracy | High | Validation script, spot checks |
| Performance issues | Low | Indexes, caching, optimization |

## Support & Maintenance

- **Documentation**: README, setup guides, troubleshooting
- **Validation**: Automated checks against source PDFs
- **Updates**: Parser handles new PDF formats
- **Monitoring**: Streamlit logs, MongoDB metrics
- **Backup**: MongoDB Atlas automatic backups

## Files Included

```
.
├── dashboard.py              # Main Streamlit app
├── DASHBOARD_SETUP.md        # Detailed setup guide
├── README_DASHBOARD.md       # Quick start guide
├── PROOF_OF_CONCEPT.md       # This file
├── mongodb_import.py         # Import JSON → MongoDB
├── analytics_examples.py     # Pre-built queries
├── fix_layover_stations_v2.py # Update layover fields
├── debug_queries.mongodb.js  # MongoDB console queries
├── example_queries.mongodb.js # More query examples
├── .streamlit/
│   ├── config.toml           # Dashboard theme
│   └── secrets.toml.example  # MongoDB connection template
├── output/
│   └── ORD.json              # Parsed data (fixed fleets)
└── src/
    └── parsers/
        └── pairing_parser.py # PDF parser (fixed)
```

## Demo Script

**For stakeholders/pilots:**

1. **Launch**: `streamlit run dashboard.py`
2. **Overview**: "See 2,047 pairings across 4 fleets"
3. **Filter**: "Find high-credit 737 trips"
   - Select Fleet: 737
   - Credit range: 20-30 hours
4. **Results**: "Found 47 pairings"
5. **Visualize**: "See credit distribution"
6. **Details**: "Click any pairing for full info"
7. **Export**: "Download filtered results as CSV"
8. **Layovers**: "See most common overnight cities"

**5 minute demo covers all key features!**

---

## Conclusion

✅ **Working POC** with real data (2,047 pairings)
✅ **Interactive dashboard** with filters and visualizations
✅ **Scalable architecture** ready for more bases
✅ **$0 cost** to start, low cost to scale
✅ **Easy deployment** options (local, cloud, mobile)

**Ready to demo and gather user feedback!**

---

Questions? See [DASHBOARD_SETUP.md](DASHBOARD_SETUP.md) or [README_DASHBOARD.md](README_DASHBOARD.md)
