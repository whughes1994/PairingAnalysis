# Pilot Pairing Dashboard - Setup Guide

## Quick Start (5 minutes)

### 1. Install Dependencies
```bash
pip3 install streamlit plotly pandas
```

### 2. Configure MongoDB Connection

Create a file `.streamlit/secrets.toml` in the project directory:

```bash
mkdir -p .streamlit
cat > .streamlit/secrets.toml << 'EOF'
# MongoDB Atlas connection string
MONGO_URI = "mongodb+srv://username:password@cluster.mongodb.net/"

# Or for local MongoDB
# MONGO_URI = "mongodb://localhost:27017/"
EOF
```

**Replace with your actual MongoDB Atlas connection string!**

### 3. Make Sure Data is Imported

```bash
# Re-import with the fixed fleet data
python3 mongodb_import.py \
  --connection "YOUR_ATLAS_CONNECTION_STRING" \
  --file output/ORD.json \
  --clear
```

### 4. Run the Dashboard

```bash
streamlit run dashboard.py
```

The dashboard will open in your browser at `http://localhost:8501`

---

## Dashboard Features

### 📊 **Fleet Overview**
- Total pairings across all fleets
- Average credit hours by fleet
- Interactive pie and bar charts
- Fleet distribution visualization

### 🏨 **Layover Destinations**
- Top 15 overnight cities
- Layover frequency charts
- Interactive filtering

### 🔎 **Pairing Search**
- **Filters:**
  - Fleet (787, 756, 737, 320, All)
  - Category (BASIC, GLOBAL, etc.)
  - Credit hours range (slider)
- **Results:**
  - Interactive table with all matching pairings
  - Shows ID, fleet, category, credit, days, layovers
  - Sortable columns
  - CSV download

### 📈 **Visualizations**
- Credit hours distribution histogram
- Real-time summary statistics
- Color-coded charts

---

## Customization

### Add More Filters

Edit `dashboard.py` and add to the sidebar section:

```python
# Add in sidebar section
min_days = st.sidebar.number_input("Minimum Days", value=1, min_value=1, max_value=7)
max_days = st.sidebar.number_input("Maximum Days", value=7, min_value=1, max_value=7)

# Add to query in get_pairings_data()
query['days'] = {'$gte': str(min_days), '$lte': str(max_days)}
```

### Add Layover City Filter

```python
# In sidebar
layover_city = st.sidebar.selectbox(
    "Layover City",
    ['Any'] + sorted(db.legs.distinct('layover_station'))
)

# In query
if layover_city != 'Any':
    query['duty_periods.layover_station'] = layover_city
```

### Add Date Range Filter

```python
from datetime import date

start_date = st.sidebar.date_input("Start Date")
end_date = st.sidebar.date_input("End Date")

# Convert to ISO format and add to query
query['effective_date_iso'] = {
    '$gte': start_date.isoformat(),
    '$lte': end_date.isoformat()
}
```

---

## Deployment Options

### Option 1: Streamlit Cloud (Free)
1. Push code to GitHub
2. Go to https://streamlit.io/cloud
3. Connect your GitHub repo
4. Add MongoDB connection string to Streamlit secrets
5. Deploy!

**Pros:** Free, easy, shareable URL
**Cons:** Public (or need paid plan for private)

### Option 2: Heroku
1. Create `Procfile`:
   ```
   web: streamlit run dashboard.py --server.port=$PORT
   ```
2. Deploy to Heroku
3. Set `MONGO_URI` environment variable

### Option 3: Docker
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "dashboard.py", "--server.address", "0.0.0.0"]
```

### Option 4: Internal Server
Run on a company server:
```bash
streamlit run dashboard.py --server.port 8501 --server.address 0.0.0.0
```

Access at `http://YOUR_SERVER_IP:8501`

---

## Advanced Features to Add

### 1. **User Authentication**
```python
import streamlit_authenticator as stauth

# Add login page
authenticator = stauth.Authenticate(...)
name, authentication_status, username = authenticator.login('Login', 'main')
```

### 2. **Bidding Preferences**
Allow pilots to save favorite pairings:
```python
if st.button("⭐ Add to Favorites"):
    db.favorites.insert_one({
        'user': username,
        'pairing_id': pairing_id,
        'saved_at': datetime.now()
    })
```

### 3. **Comparison Tool**
Compare multiple pairings side-by-side:
```python
selected_pairings = st.multiselect("Select pairings to compare", pairing_ids)
# Show comparison table
```

### 4. **Calendar View**
Show pairings on a calendar:
```python
import plotly.figure_factory as ff

# Create Gantt chart
fig = ff.create_gantt(df, index_col='id', show_colorbar=True)
st.plotly_chart(fig)
```

### 5. **Export to Excel**
```python
from io import BytesIO
import xlsxwriter

# Create Excel file
output = BytesIO()
with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
    df.to_excel(writer, sheet_name='Pairings')

st.download_button("📥 Download Excel", output.getvalue(), "pairings.xlsx")
```

---

## Troubleshooting

### "Connection refused"
- Make sure MongoDB is running (local) or connection string is correct (Atlas)
- Check firewall/IP whitelist for Atlas

### "Module not found: streamlit"
```bash
pip3 install streamlit plotly pandas
```

### Dashboard is slow
- Add more caching with `@st.cache_data`
- Limit query results (already limited to 1000)
- Add indexes to MongoDB (already done by import script)

### Can't access from other devices
```bash
# Run with external access
streamlit run dashboard.py --server.address 0.0.0.0
```

---

## Next Steps

1. **Test with pilots**: Get feedback on what filters/views they need
2. **Add more fleets**: Import data from other bases (DEN, LAX, etc.)
3. **Mobile optimization**: Streamlit is responsive by default
4. **Add notifications**: Alert when new pairings match preferences
5. **Integration**: Connect to crew scheduling systems

---

## Performance Tips

- Data refreshes every 10 minutes (`ttl=600`)
- Results limited to 1000 pairings
- MongoDB indexes already optimized
- Use `@st.cache_data` for expensive queries

---

## Support

For issues or feature requests:
1. Check MongoDB connection first
2. Verify data is imported correctly
3. Look at Streamlit logs in terminal
4. Check browser console for JavaScript errors

**Dashboard should work out of the box once MongoDB connection is configured!**
