# ✈️ Pilot Pairing Dashboard - Quick Start

Interactive web dashboard for exploring airline pairing data.

## Screenshot Preview

```
┌────────────────────────────────────────────────────────────┐
│ ✈️ Pilot Pairing Dashboard                                 │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  Total Pairings    Fleets    Avg Credit    Layover Cities │
│      2,047           4         17.0h            32         │
│                                                             │
│  📊 Fleet Overview                                          │
│  ┌─────────────┐  ┌─────────────────────────────────────┐ │
│  │   787: 35%  │  │ Avg Credit Hours by Fleet           │ │
│  │   756: 3%   │  │ ████████████ 787                    │ │
│  │   737: 62%  │  │ ██████████   756                    │ │
│  │   320: 32%  │  │ ████████████ 737                    │ │
│  └─────────────┘  └─────────────────────────────────────┘ │
│                                                             │
│  🏨 Top Layover Destinations                                │
│  ┌────────────────────────────────────────────────────────┐│
│  │ ORD ████████████████████████  3,426                   ││
│  │ EWR ████  283                                          ││
│  │ SFO ███   244                                          ││
│  └────────────────────────────────────────────────────────┘│
│                                                             │
│  🔎 Pairing Search                                          │
│  ┌──────────┬────────┬──────────┬────────┬──────────────┐ │
│  │ ID       │ Fleet  │ Category │ Credit │ Layovers     │ │
│  ├──────────┼────────┼──────────┼────────┼──────────────┤ │
│  │ O8038    │ 787    │ GLOBAL   │ 35.8h  │ FRA          │ │
│  │ O3056    │ 737    │ BASIC    │ 27.6h  │ DEN, LAX     │ │
│  └──────────┴────────┴──────────┴────────┴──────────────┘ │
└────────────────────────────────────────────────────────────┘
```

## 🚀 Launch in 3 Steps

### 1. Configure MongoDB Connection

```bash
# Create secrets file
mkdir -p .streamlit
nano .streamlit/secrets.toml
```

Add your MongoDB connection string:
```toml
MONGO_URI = "mongodb+srv://user:pass@cluster.mongodb.net/"
```

### 2. Make Sure Data is Imported

```bash
# Import the fixed ORD data
python3 mongodb_import.py \
  --connection "YOUR_MONGO_URI" \
  --file output/ORD.json \
  --clear
```

### 3. Launch Dashboard

```bash
streamlit run dashboard.py
```

**Opens automatically in your browser at http://localhost:8501**

---

## 🎯 Features

### Interactive Filters
- **Fleet**: Filter by 787, 756, 737, 320, or All
- **Category**: BASIC, GLOBAL (EUR), BASIC (CAM), etc.
- **Credit Range**: Slider from 0-50 hours

### Real-Time Visualizations
- Fleet distribution pie chart
- Credit hours bar charts
- Layover frequency analysis
- Credit distribution histogram

### Pairing Details Table
- Sortable by any column
- Shows ID, fleet, category, credit, days, layovers
- Download results as CSV
- Updates instantly when filters change

### Summary Statistics
- Total pairings count
- Average credit per fleet
- Top 15 layover destinations
- Min/max/avg credit in results

---

## 📊 Use Cases

### For Pilots:
1. **Bid Planning**: Find high-credit trips in preferred categories
2. **Layover Preferences**: Filter by overnight cities
3. **Work-Life Balance**: Search by days (3-day vs 4-day trips)
4. **Comparison**: Download and compare multiple options

### For Schedulers:
1. **Fleet Analysis**: See distribution across aircraft types
2. **Coverage**: Ensure balanced pairing offerings
3. **Metrics**: Track average credit hours by category

### For Analysts:
1. **Data Exploration**: Interactive filtering and visualization
2. **Export**: Download filtered results for further analysis
3. **Trends**: See patterns in pairing construction

---

## 🔧 Customization

See [DASHBOARD_SETUP.md](DASHBOARD_SETUP.md) for:
- Adding more filters (dates, layover cities, days)
- Deployment options (Streamlit Cloud, Heroku, Docker)
- Advanced features (authentication, favorites, comparisons)
- Performance optimization

---

## 🐛 Troubleshooting

**Dashboard won't start:**
```bash
# Install dependencies
pip3 install streamlit plotly pandas pymongo
```

**Can't connect to MongoDB:**
- Check `.streamlit/secrets.toml` exists and has correct connection string
- For Atlas: Verify IP whitelist and credentials
- For local: Make sure MongoDB is running

**No data showing:**
```bash
# Re-import data
python3 mongodb_import.py --connection "YOUR_URI" --file output/ORD.json --clear
```

**Want to share with others:**
```bash
# Run with external access
streamlit run dashboard.py --server.address 0.0.0.0
# Access at http://YOUR_IP:8501
```

---

## 📱 Mobile Friendly

Dashboard is fully responsive and works on:
- Desktop browsers
- Tablets
- Mobile phones (filters collapse into sidebar)

---

## 🚀 Next Steps

1. **Import more bases**: Parse and import DEN, LAX, EWR, etc.
2. **Add user accounts**: Track favorites and preferences
3. **Schedule updates**: Auto-import new pairing data
4. **Mobile app**: Convert to native app with Flutter/React Native
5. **Integration**: Connect to crew scheduling systems

---

## 📄 Files

- `dashboard.py` - Main dashboard application
- `DASHBOARD_SETUP.md` - Detailed setup and customization guide
- `.streamlit/secrets.toml` - MongoDB connection (you create this)
- `requirements.txt` - Python dependencies

---

**Built with:** Streamlit + MongoDB + Plotly + Python
**License:** MIT
**Support:** See DASHBOARD_SETUP.md for troubleshooting

🎉 **Happy bidding!**
