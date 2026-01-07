# Analytics Dashboard Ideas

Comprehensive dashboard concepts for pilot pairing data analysis and insights.

---

## 1. Trip Distribution Analytics

### Trip Length Distribution (Pie/Bar Chart)
**Metric:** Percentage breakdown of pairings by duration

**Visualization:** Pie chart or stacked bar chart
- 1-Day Trips: X%
- 2-Day Trips: X%
- 3-Day Trips: X%
- 4-Day Trips: X%
- 5-Day Trips: X%

**Calculation:**
```python
trip_length_counts = Counter([p['days'] for p in pairings])
total_pairings = len(pairings)
percentages = {days: (count/total_pairings)*100 for days, count in trip_length_counts.items()}
```

**Filters:** Fleet, Base, Bid Month, Category

**Value:** Shows scheduling patterns and helps pilots understand trip distribution preferences

---

## 2. Trip Efficiency Score

### Credit-to-TAFB Efficiency Gauge
**Metric:** Credit Hours ÷ Time Away From Base (TAFB)

**Visualization:** Gauge chart (0.0 - 1.0 scale)
- 🔴 Low Efficiency: 0.0 - 0.3 (sitting reserve, long layovers)
- 🟡 Medium Efficiency: 0.3 - 0.5 (typical multi-day trips)
- 🟢 High Efficiency: 0.5 - 1.0 (productive turns, 1-day trips)

**Calculation:**
```python
efficiency = credit_minutes / tafb_minutes
# Note: 1-day trips have tafb_minutes = 0, so exclude or handle separately
```

**Display Options:**
- Overall fleet efficiency (average)
- Per-base efficiency comparison
- Per-pairing efficiency ranking
- Efficiency by trip length (2-day vs 3-day vs 4-day)

**Value:** Helps pilots identify high-value pairings for bidding

---

## 3. Flying Intensity Metrics

### Average Legs per Duty Day
**Metric:** Total legs ÷ Total duty days

**Visualization:** Bar chart by fleet/base
- Shows workload intensity
- Compare across fleets (widebody vs narrowbody)

**Calculation:**
```python
total_legs = sum(len(leg) for p in pairings for dp in p['duty_periods'] for leg in dp['legs'])
total_duty_days = sum(len(p['duty_periods']) for p in pairings)
avg_legs_per_day = total_legs / total_duty_days
```

**Additional Metrics:**
- Minimum legs per duty day
- Maximum legs per duty day
- Distribution histogram (1-leg days, 2-leg days, 3-leg days, etc.)

---

### Average Leg Duration
**Metric:** Mean flight time per leg

**Visualization:**
- Box plot showing distribution
- Comparison by fleet (widebody = longer, narrowbody = shorter)

**Calculation:**
```python
leg_durations = [leg['flight_time_minutes']/60 for all legs]
avg_duration = mean(leg_durations)
```

**Insights:**
- Widebody fleets (787, 767) = longer legs (4-10 hours)
- Narrowbody fleets (737, 320) = shorter legs (1-4 hours)

---

## 4. Credit vs Block Time Analysis

### Credit-to-Block Ratio
**Metric:** Credit Hours ÷ Flight Time (Block Hours)

**Visualization:** Scatter plot or histogram
- Shows how much "rig" credit is earned beyond flight time
- Typically ranges from 1.0 (straight time) to 2.0+ (high credit rigs)

**Calculation:**
```python
ratio = credit_minutes / flight_time_minutes
```

**Categories:**
- **Straight Time** (1.0 - 1.1): Mostly flying
- **Moderate Rig** (1.1 - 1.5): Some credit protection
- **High Rig** (1.5+): Significant duty/layover credit

**Filters:** By trip length, fleet, base

**Value:** Identifies pairings with better credit protection

---

## 5. Layover Analysis

### Top Layover Destinations
**Metric:** Most frequent overnight stations

**Visualization:**
- Horizontal bar chart (top 20 cities)
- Bubble map with size = frequency

**Data Points:**
- Total layovers per station
- Average layover duration (hours)
- Percentage of total layovers

**Calculation:**
```python
layover_counts = Counter([leg['layover_station'] for all legs if leg['layover_station']])
```

**Enhanced Metrics:**
- Layover duration distribution (short <12h vs long >24h)
- Best layover cities by duration
- International vs domestic layovers

---

### Layover Duration Patterns
**Metric:** Time spent at layover cities

**Visualization:** Box plot or histogram
- Short layovers (<12 hours)
- Standard layovers (12-24 hours)
- Long layovers (24-48 hours)
- Extra-long layovers (48+ hours)

**Value:** Helps pilots identify quick-turn vs relaxed pairings

---

## 6. Duty Day Metrics

### Duty Period Length Distribution
**Metric:** Report to release time

**Visualization:** Histogram with ranges
- Short duty (<8 hours)
- Standard duty (8-12 hours)
- Long duty (12-14 hours)
- Max duty (14+ hours)

**Calculation:**
```python
duty_duration = parse_time(release_time) - parse_time(report_time)
```

**Filters:** By fleet (widebody vs narrowbody), by base

**Value:** Shows scheduling intensity and FAR compliance patterns

---

### Ground Time Analysis
**Metric:** Time between legs (sit time)

**Visualization:**
- Average ground time per leg
- Distribution (quick turns vs long sits)

**Categories:**
- Quick turn (<45 min)
- Standard turn (45-90 min)
- Long turn (90+ min)

**Calculation:**
```python
ground_time = leg['ground_time_minutes'] / 60
```

---

## 7. Fleet Comparison Dashboard

### Side-by-Side Fleet Metrics
**Visualization:** Multi-panel comparison

**Metrics to Compare:**
- Average credit hours
- Average trip length (days)
- Average legs per duty day
- Average leg duration
- Efficiency score
- Most common layover cities
- Duty day length

**Format:** Table or radar chart

**Example:**
```
Metric              | 787   | 756   | 737   | 320
--------------------|-------|-------|-------|-------
Avg Credit Hours    | 24.5  | 22.1  | 19.8  | 18.2
Avg Trip Length     | 3.2   | 2.8   | 2.5   | 2.3
Legs per Duty Day   | 1.5   | 1.8   | 2.4   | 2.8
Avg Leg Duration    | 6.2h  | 5.1h  | 2.8h  | 2.1h
```

---

## 8. Base Comparison Dashboard

### Performance by Base
**Metric:** Compare operational characteristics across bases

**Visualizations:**
- Total pairings per base
- Average credit per base
- Fleet mix per base (pie charts)
- Efficiency scores per base
- Top destinations per base

**Value:** Helps pilots understand base differences for bidding transfers

---

## 9. Credit Distribution

### Credit Hours Histogram
**Metric:** Distribution of credit hours across all pairings

**Visualization:** Histogram with bins
- Low credit (0-15 hours)
- Medium credit (15-25 hours)
- High credit (25-35 hours)
- Premium credit (35+ hours)

**Additional Stats:**
- Mean credit hours
- Median credit hours
- Standard deviation
- Percentiles (25th, 50th, 75th, 90th)

**Filters:** By trip length, fleet, base

---

### Credit vs Days Scatter Plot
**Metric:** Credit earned per trip day

**Visualization:** Scatter plot with trend line
- X-axis: Trip length (days)
- Y-axis: Total credit hours
- Color: Fleet type
- Size: Number of legs

**Value:** Shows credit efficiency by trip length

---

## 10. International vs Domestic Analysis

### Route Type Breakdown
**Metric:** Percentage of international vs domestic flying

**Visualization:** Pie chart or stacked bar

**Categories:**
- Domestic only
- Mixed (domestic + international)
- International only

**Calculation:**
```python
# Classify legs based on station codes (international = 3-letter ICAO)
is_international = len(departure_station) == 4 or len(arrival_station) == 4
```

**Enhanced Metrics:**
- Average credit for international vs domestic
- Average duty time
- Layover preferences

---

## 11. Time of Day Analysis

### Report Time Distribution
**Metric:** When do pairings typically start?

**Visualization:** Histogram by hour
- Early morning (0000-0600)
- Morning (0600-1200)
- Afternoon (1200-1800)
- Evening (1800-2400)

**Calculation:**
```python
report_hour = int(report_time[:2])
```

**Value:** Helps pilots identify early vs late pairings

---

### Release Time Distribution
**Metric:** When do pairings typically end?

**Visualization:** Similar histogram showing end times

---

## 12. Pairing Category Analysis

### Category Distribution
**Metric:** Breakdown by pairing type

**Visualization:** Pie chart
- Basic
- Premium
- Reserve
- Other categories

**Metrics per Category:**
- Average credit
- Average days
- Average efficiency
- Trip length distribution

---

## 13. Monthly Trends Dashboard

### Comparison Across Bid Months
**Metric:** How metrics change month-to-month

**Visualizations:** Line charts showing trends
- Total pairings per month
- Average credit per month
- Fleet distribution changes
- Efficiency trends

**Data:** Requires multiple bid months imported

**Value:** Identify seasonal patterns and bidding strategies

---

## 14. Commutability Analysis

### Early/Late Pairings for Commuters
**Metric:** Pairings suitable for commuting

**Categories:**
- **Commutable Start:** Report time after 1000
- **Commutable End:** Release time before 1800
- **Both:** Good for both start and end commute

**Visualization:** Bar chart showing percentages

**Filters:** By base (helps commuters identify friendly bases)

---

## 15. Quality of Life Metrics

### Weekend Impact
**Metric:** Pairings that touch weekends

**Calculation:**
```python
# Check if pairing includes Saturday or Sunday
touches_weekend = overlaps_with_weekend(effective_date, through_date)
```

**Visualization:** Percentage breakdown
- Weekday only
- Touches one weekend day
- Touches both weekend days

---

### Overnight Rest Quality
**Metric:** Layover duration adequacy

**Visualization:** Bar chart
- Short rest (<10 hours)
- Reduced rest (10-12 hours)
- Standard rest (12-18 hours)
- Long rest (18+ hours)

---

## 16. Advanced KPIs

### Value Score (Custom Metric)
**Formula:** Weighted combination of factors

```python
value_score = (
    (credit_hours * 2) +           # Credit is valuable
    (efficiency * 10) +             # Efficiency matters
    (layover_quality * 5) -         # Good layovers are valuable
    (duty_intensity * 3) -          # Fewer legs is better
    (weekend_impact * 2)            # Avoid weekends
)
```

**Visualization:** Ranked list of "best" pairings

**Customizable:** Pilots adjust weights based on priorities

---

## 17. Network Visualization

### Route Network Graph
**Metric:** All city pairs flown

**Visualization:** Network diagram
- Nodes: Cities
- Edges: Flight routes
- Edge thickness: Frequency
- Node size: Total flights in/out

**Interactive:** Click to filter by origin/destination

---

## 18. Deadhead Analysis

### Deadhead Frequency
**Metric:** Percentage of legs that are deadheads

**Visualization:**
- Percentage of total legs
- Deadhead vs revenue legs by fleet
- Most common deadhead routes

**Calculation:**
```python
is_deadhead = leg.get('equipment') in ['DH', 'UX']
```

---

## Implementation Priority

### Phase 1 - Essential Dashboards
1. ✅ Trip Length Distribution (pie chart)
2. ✅ Efficiency Gauge (credit/TAFB)
3. ✅ Average Legs per Day (bar chart)
4. ✅ Average Leg Duration (metric)
5. ✅ Top Layover Destinations (bar chart)

### Phase 2 - Enhanced Analytics
6. Credit Distribution (histogram)
7. Fleet Comparison (multi-panel)
8. Credit vs Block Time (scatter)
9. Duty Period Distribution (histogram)
10. Base Comparison (table)

### Phase 3 - Advanced Features
11. Time of Day Analysis
12. Monthly Trends
13. Commutability Analysis
14. Quality of Life Metrics
15. Value Score Rankings
16. Network Visualization

---

## Dashboard Layout Suggestions

### **Dashboard 1: Overview**
- Total pairings metric
- Trip length distribution (pie)
- Average credit hours (metric)
- Fleet distribution (bar)

### **Dashboard 2: Efficiency**
- Efficiency gauge (primary)
- Credit vs TAFB scatter
- Efficiency by trip length (bar)
- Top efficiency pairings (table)

### **Dashboard 3: Flying Characteristics**
- Legs per duty day (bar)
- Leg duration distribution (histogram)
- Duty period length (histogram)
- Ground time analysis (box plot)

### **Dashboard 4: Destinations**
- Layover map (bubble map)
- Top layovers (bar chart)
- Layover duration (histogram)
- International vs domestic (pie)

### **Dashboard 5: Comparison**
- Fleet comparison (table)
- Base comparison (table)
- Category analysis (bar charts)
- Monthly trends (line charts)

---

## Technical Notes

### Data Requirements
All metrics can be calculated from existing JSON output:
- `credit_minutes` (convert to hours ÷ 60)
- `tafb_minutes` (convert to hours ÷ 60)
- `flight_time_minutes` (convert to hours ÷ 60)
- `days`
- `duty_periods[].legs[]`
- `layover_station`
- `report_time`, `release_time`

### Recommended Tools
- **Streamlit**: Interactive dashboards
- **Plotly**: Interactive charts (gauges, maps, scatter)
- **Pandas**: Data aggregation and analysis
- **Altair**: Declarative visualizations

### Performance Considerations
- Cache aggregated metrics using `@st.cache_data`
- Pre-calculate statistics in MongoDB aggregation pipelines
- Use indexes on commonly filtered fields (fleet, base, bid_month)

---

## Next Steps

1. Create `analytics_dashboard.py` with Phase 1 dashboards
2. Add to main navigation in `unified_dashboard.py`
3. Implement MongoDB aggregation queries for efficiency
4. Add export functionality (CSV, PDF reports)
5. Build custom "Bidding Assistant" with value scores
