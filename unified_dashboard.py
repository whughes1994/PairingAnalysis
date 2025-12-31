#!/usr/bin/env python3
#TEST COMMENT
"""
Unified Pairing Dashboard with QA Workbench

Combines the main pairing explorer with QA validation tools in one interface.
"""

import streamlit as st
import json
import pdfplumber
from pathlib import Path
import pandas as pd
from datetime import datetime
import re
from pymongo import MongoClient
import plotly.express as px
import plotly.graph_objects as go
import airportsdata

# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="Pairing Analysis & QA",
    page_icon="✈️",
    layout="wide"
)

# ============================================================================
# MONGODB CONNECTION
# ============================================================================

@st.cache_resource
def get_mongodb_connection():
    """Connect to MongoDB using credentials from secrets."""
    try:
        import certifi

        mongo_uri = st.secrets["MONGO_URI"]
        client = MongoClient(
            mongo_uri,
            serverSelectionTimeoutMS=5000,
            tlsCAFile=certifi.where()  # Use certifi's CA certificates
        )
        client.admin.command('ping')
        return client['airline_pairings']
    except Exception as e:
        st.error(f"MongoDB connection failed: {e}")
        return None

db = get_mongodb_connection()

# ============================================================================
# AIRPORT DATA
# ============================================================================

@st.cache_data
def get_airport_coords(code):
    """Get airport coordinates from airportsdata."""
    airports = airportsdata.load('IATA')
    airport = airports.get(code)
    if airport:
        return airport['lat'], airport['lon'], airport.get('city', code)
    return None, None, code

# ============================================================================
# DATA LOADING FUNCTIONS
# ============================================================================

@st.cache_data(ttl=600)
def get_fleet_stats(bid_month=None, base=None):
    """Get fleet statistics from MongoDB, filtered by bid month and base."""
    match_stage = {}

    # Filter by bid month
    if bid_month and bid_month != 'All':
        bid_period_ids = [
            bp['_id'] for bp in
            db.bid_periods.find({'bid_month_year': bid_month}, {'_id': 1})
        ]
        if bid_period_ids:
            match_stage['bid_period_id'] = {'$in': bid_period_ids}

    # Filter by base
    if base and base != 'All':
        base_filter = {'base': base}
        if bid_month and bid_month != 'All':
            base_filter['bid_month_year'] = bid_month
        bid_period_ids = [
            bp['_id'] for bp in
            db.bid_periods.find(base_filter, {'_id': 1})
        ]
        if bid_period_ids:
            if 'bid_period_id' in match_stage:
                # Intersect with existing filter
                match_stage['bid_period_id']['$in'] = list(set(match_stage['bid_period_id']['$in']) & set(bid_period_ids))
            else:
                match_stage['bid_period_id'] = {'$in': bid_period_ids}

    pipeline = []
    if match_stage:
        pipeline.append({'$match': match_stage})

    pipeline.extend([
        {
            '$group': {
                '_id': '$fleet',
                'total_pairings': {'$sum': 1},
                'avg_credit_hours': {'$avg': {'$divide': ['$credit_minutes', 60]}}
            }
        },
        {'$sort': {'total_pairings': -1}}
    ])

    results = list(db.pairings.aggregate(pipeline))
    return pd.DataFrame(results).rename(columns={'_id': 'fleet'})

@st.cache_data(ttl=600)
def get_layover_stats(fleet=None, category=None, min_credit=0, max_credit=100, days=None,
                      bid_month=None, base=None):
    """Get top layover destinations with coordinates, filtered by pairing criteria."""
    pairing_match = {'credit_minutes': {'$gte': min_credit * 60, '$lte': max_credit * 60}}

    # Filter by bid month
    if bid_month and bid_month != 'All':
        bid_period_ids = [
            bp['_id'] for bp in
            db.bid_periods.find({'bid_month_year': bid_month}, {'_id': 1})
        ]
        if bid_period_ids:
            pairing_match['bid_period_id'] = {'$in': bid_period_ids}

    # Filter by base
    if base and base != 'All':
        base_filter = {'base': base}
        if bid_month and bid_month != 'All':
            base_filter['bid_month_year'] = bid_month
        bid_period_ids = [
            bp['_id'] for bp in
            db.bid_periods.find(base_filter, {'_id': 1})
        ]
        if bid_period_ids:
            if 'bid_period_id' in pairing_match:
                # Intersect with existing filter
                pairing_match['bid_period_id']['$in'] = list(set(pairing_match['bid_period_id']['$in']) & set(bid_period_ids))
            else:
                pairing_match['bid_period_id'] = {'$in': bid_period_ids}

    if fleet and fleet != 'All':
        pairing_match['fleet'] = fleet

    if category and category != 'All':
        pairing_match['pairing_category'] = category

    if days and len(days) > 0:
        pairing_match['days'] = {'$in': [str(d) for d in days]}

    # Build initial match stage for legs collection (filter directly on legs.bid_period_id)
    legs_match = {'layover_station': {'$ne': None}}

    # Add bid_period_id filter directly to legs (since legs have bid_period_id field)
    if 'bid_period_id' in pairing_match:
        legs_match['bid_period_id'] = pairing_match['bid_period_id']
        # Remove from pairing_match since we're filtering on legs instead
        pairing_match_without_bid = {k: v for k, v in pairing_match.items() if k != 'bid_period_id'}
    else:
        pairing_match_without_bid = pairing_match

    pipeline = [
        {'$match': legs_match},
        {
            '$lookup': {
                'from': 'pairings',
                'localField': 'pairing_id',
                'foreignField': 'id',
                'as': 'pairing'
            }
        },
        {'$unwind': '$pairing'},
        {'$match': {f'pairing.{k}': v for k, v in pairing_match_without_bid.items()}},
        {
            '$addFields': {
                'is_away_from_base': {'$ne': ['$layover_station', '$pairing.base']}
            }
        },
        {'$match': {'is_away_from_base': True}},
        {
            '$group': {
                '_id': '$layover_station',
                'count': {'$sum': 1}
            }
        },
        {'$sort': {'count': -1}},
        {'$limit': 200}
    ]

    results = list(db.legs.aggregate(pipeline))
    df = pd.DataFrame(results).rename(columns={'_id': 'station', 'count': 'layovers'})

    df['lat'] = df['station'].apply(lambda x: get_airport_coords(x)[0])
    df['lon'] = df['station'].apply(lambda x: get_airport_coords(x)[1])
    df['city'] = df['station'].apply(lambda x: get_airport_coords(x)[2])

    df = df.dropna(subset=['lat', 'lon'])

    all_bases = set(db.pairings.distinct('base'))
    df = df[~df['station'].isin(all_bases)]

    return df

@st.cache_data(ttl=600)
def get_pairings_data(fleet=None, category=None, min_credit=0, max_credit=100, days=None,
                      layover_station=None, min_overnight_hours=None, max_overnight_hours=None,
                      bid_month=None, base=None):
    """Get pairings with filters including bid month and base."""
    query = {'credit_minutes': {'$gte': min_credit * 60, '$lte': max_credit * 60}}

    # Primary filters
    if bid_month and bid_month != 'All':
        # Get bid_period_id(s) for the selected bid month
        bid_period_ids = [
            bp['_id'] for bp in
            db.bid_periods.find({'bid_month_year': bid_month}, {'_id': 1})
        ]
        if bid_period_ids:
            query['bid_period_id'] = {'$in': bid_period_ids}

    if fleet and fleet != 'All':
        query['fleet'] = fleet

    if base and base != 'All':
        # Get bid_period_id(s) for the selected base
        base_filter = {'base': base}
        if bid_month and bid_month != 'All':
            base_filter['bid_month_year'] = bid_month
        bid_period_ids = [
            bp['_id'] for bp in
            db.bid_periods.find(base_filter, {'_id': 1})
        ]
        if bid_period_ids:
            if 'bid_period_id' in query:
                # Intersect with existing bid_period_id filter
                query['bid_period_id']['$in'] = list(set(query['bid_period_id']['$in']) & set(bid_period_ids))
            else:
                query['bid_period_id'] = {'$in': bid_period_ids}

    # Pairing filters
    if category and category != 'All':
        query['pairing_category'] = category

    if days and len(days) > 0:
        query['days'] = {'$in': [str(d) for d in days]}

    # Layover station filter
    if layover_station and layover_station != 'All':
        query['duty_periods.layover_station'] = layover_station

    pairings = list(db.pairings.find(
        query,
        {
            'id': 1, 'fleet': 1, 'base': 1, 'pairing_category': 1,
            'credit_minutes': 1, 'days': 1, 'flight_time_minutes': 1,
            'duty_periods': 1, 'bid_period_id': 1, '_id': 1
        }
    ).limit(500))

    for p in pairings:
        p['credit_hours'] = p['credit_minutes'] / 60
        p['flight_hours'] = p['flight_time_minutes'] / 60
        p['layovers'] = [dp.get('layover_station') for dp in p.get('duty_periods', [])
                        if dp.get('layover_station')]

        # Calculate overnight durations (time between release and next report)
        overnight_hours = []
        duty_periods = p.get('duty_periods', [])
        for i in range(len(duty_periods) - 1):
            current_dp = duty_periods[i]
            next_dp = duty_periods[i + 1]

            release_mins = current_dp.get('release_time_minutes')
            next_report_mins = next_dp.get('report_time_minutes')

            if release_mins is not None and next_report_mins is not None:
                # Handle overnight (next day)
                if next_report_mins < release_mins:
                    next_report_mins += 1440  # Add 24 hours

                overnight_mins = next_report_mins - release_mins
                overnight_hours.append(overnight_mins / 60)

        p['overnight_hours'] = overnight_hours
        p['max_overnight_hours'] = max(overnight_hours) if overnight_hours else 0
        p['min_overnight_hours'] = min(overnight_hours) if overnight_hours else 0

    df = pd.DataFrame(pairings)

    # Filter by overnight length if specified
    if not df.empty and (min_overnight_hours is not None or max_overnight_hours is not None):
        if min_overnight_hours is not None:
            df = df[df['max_overnight_hours'] >= min_overnight_hours]
        if max_overnight_hours is not None:
            df = df[df['max_overnight_hours'] <= max_overnight_hours]

    return df

# ============================================================================
# QA FUNCTIONS
# ============================================================================

@st.cache_data
def extract_pdf_text(pdf_path: str) -> dict:
    """Extract text from PDF by page."""
    pages = {}
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            pages[i] = page.extract_text() or ''
    return pages

@st.cache_data
def load_json_data(json_path: str) -> dict:
    """Load parsed JSON data."""
    with open(json_path, 'r') as f:
        raw_data = json.load(f)

    if 'data' in raw_data:
        return {
            'bid_periods': raw_data['data'],
            'base': raw_data['data'][0].get('base') if raw_data['data'] else None,
            'month': raw_data['data'][0].get('bid_month_year') if raw_data['data'] else None
        }
    else:
        return raw_data

def find_in_pdf(text: str, search_term: str, context_lines: int = 3) -> list:
    """Find search term in PDF text and return with context."""
    results = []
    lines = text.split('\n')

    for i, line in enumerate(lines):
        if search_term.upper() in line.upper():
            start = max(0, i - context_lines)
            end = min(len(lines), i + context_lines + 1)
            context = '\n'.join(lines[start:end])
            results.append({
                'line_number': i + 1,
                'context': context,
                'matched_line': line
            })

    return results

def highlight_text(text: str, search_term: str) -> str:
    """Highlight search term in text."""
    if not search_term:
        return text

    pattern = re.compile(f'({re.escape(search_term)})', re.IGNORECASE)
    return pattern.sub(r'**\1**', text)

# ============================================================================
# MAIN APP
# ============================================================================

# ============================================================================
# HORIZONTAL NAVIGATION BAR
# ============================================================================

# Custom CSS for horizontal nav menu
st.markdown("""
<style>
    .nav-menu {
        display: flex;
        gap: 10px;
        padding: 10px 0;
        border-bottom: 2px solid #f0f2f6;
        margin-bottom: 20px;
    }
    .nav-item {
        padding: 10px 20px;
        border-radius: 5px;
        cursor: pointer;
        font-weight: 500;
        text-align: center;
        flex: 1;
    }
    .nav-item.active {
        background-color: #ff4b4b;
        color: white;
    }
    .nav-item.inactive {
        background-color: #f0f2f6;
        color: #262730;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.title("✈️ Pairing Analysis & Quality Assurance")

# Initialize default page
if 'nav_page' not in st.session_state:
    st.session_state.nav_page = 'explorer'

# Horizontal navigation menu using columns
nav_col1, nav_col2, nav_col3 = st.columns(3)

with nav_col1:
    if st.button("📊 Pairing Explorer",
                 use_container_width=True,
                 type="primary" if st.session_state.nav_page == 'explorer' else "secondary",
                 key="nav_explorer"):
        st.session_state.nav_page = 'explorer'
        st.rerun()

with nav_col2:
    if st.button("🔍 QA Workbench",
                 use_container_width=True,
                 type="primary" if st.session_state.nav_page == 'qa' else "secondary",
                 key="nav_qa"):
        st.session_state.nav_page = 'qa'
        st.rerun()

with nav_col3:
    if st.button("📝 Annotations",
                 use_container_width=True,
                 type="primary" if st.session_state.nav_page == 'annotations' else "secondary",
                 key="nav_annotations"):
        st.session_state.nav_page = 'annotations'
        st.rerun()

st.markdown("---")

# ============================================================================
# VERTICAL SIDEBAR NAVIGATION - Always Visible
# ============================================================================

with st.sidebar:
    st.header("🧭 Navigation")

    # Page selector in sidebar as well
    page_options = {
        "📊 Pairing Explorer": "explorer",
        "🔍 QA Workbench": "qa",
        "📝 Annotations": "annotations"
    }

    # Find current page display name
    current_page_name = [k for k, v in page_options.items() if v == st.session_state.nav_page][0]

    selected_page = st.radio(
        "Select Page",
        options=list(page_options.keys()),
        index=list(page_options.values()).index(st.session_state.nav_page),
        key="sidebar_nav"
    )

    # Update page if changed via sidebar
    if page_options[selected_page] != st.session_state.nav_page:
        st.session_state.nav_page = page_options[selected_page]
        st.rerun()

    st.markdown("---")

    # ========================================================================
    # PAGE-SPECIFIC SIDEBAR FILTERS
    # ========================================================================

    # Show filters based on current page
    if st.session_state.nav_page == 'explorer' and db is not None:
        st.header("🎛️ Filters")

        # ========== PRIMARY FILTERS ==========
        st.subheader("🎯 Primary Filters")

        # 1. Bid Month filter (NEW - First filter, REQUIRED)
        bid_months = sorted(db.bid_periods.distinct('bid_month_year'))

        if not bid_months:
            st.warning("No bid periods found in database")
            st.stop()

        selected_bid_month = st.radio(
            "📅 Bid Month",
            bid_months,
            index=len(bid_months) - 1,  # Default to most recent (last in sorted list)
            help="Select the bid period to view pairings from"
        )

        # 2. Fleet filter
        fleet_options = ['All'] + sorted(db.pairings.distinct('fleet'))
        selected_fleet = st.selectbox("✈️ Fleet", fleet_options)

        # 3. Base filter (NEW)
        base_options = ['All'] + sorted([
            base for base in db.bid_periods.distinct('base')
            if base is not None
        ])
        selected_base = st.selectbox("🏠 Base", base_options)

        st.markdown("---")

        # ========== PAIRING FILTERS ==========
        st.subheader("📋 Pairing Filters")

        # Category filter
        category_options = ['All'] + sorted(db.pairings.distinct('pairing_category'))
        selected_category = st.selectbox("Category", category_options)

        # Credit hours filter
        credit_range = st.slider(
            "Credit Hours Range",
            min_value=0,
            max_value=50,
            value=(10, 30)
        )

        # Days filter
        days_options = st.multiselect(
            "Number of Days",
            options=[1, 2, 3, 4],
            default=None,
            help="Select specific day counts (leave empty for all)"
        )

        st.markdown("---")

        # ========== LAYOVER FILTERS ==========
        st.subheader("🏨 Layover Filters")

        # Layover station filter
        layover_stations = ['All'] + sorted([
            station for station in db.pairings.distinct('duty_periods.layover_station')
            if station is not None
        ])

        # Check if a layover was selected via quick filter button
        default_layover_index = 0
        if 'selected_layover_station' in st.session_state and st.session_state.selected_layover_station in layover_stations:
            default_layover_index = layover_stations.index(st.session_state.selected_layover_station)
            # Clear the session state after using it
            del st.session_state.selected_layover_station

        selected_layover = st.selectbox(
            "Layover Station",
            layover_stations,
            index=default_layover_index,
            help="Filter pairings with layovers in a specific city"
        )

        # Overnight duration filter
        overnight_enabled = st.checkbox("Filter by Overnight Duration", value=False)

        if overnight_enabled:
            overnight_range = st.slider(
                "Overnight Hours Range",
                min_value=0,
                max_value=48,
                value=(8, 24),
                step=1,
                help="Filter by length of overnight rest between duty periods"
            )
            min_overnight = overnight_range[0]
            max_overnight = overnight_range[1]
        else:
            min_overnight = None
            max_overnight = None

# ============================================================================
# PAGE 1: PAIRING EXPLORER
# ============================================================================

if st.session_state.nav_page == 'explorer':
    if db is None:
        st.error("⚠️ MongoDB connection required for Pairing Explorer")
        st.info("Configure MongoDB URI in .streamlit/secrets.toml")
        st.stop()

    st.header("Pairing Explorer")

    # Top metrics - filtered by selected bid month and base
    col1, col2, col3, col4 = st.columns(4)

    # Build query for total pairings count
    pairings_count_query = {}
    if selected_bid_month:
        bid_period_ids = [
            bp['_id'] for bp in
            db.bid_periods.find({'bid_month_year': selected_bid_month}, {'_id': 1})
        ]
        if bid_period_ids:
            pairings_count_query['bid_period_id'] = {'$in': bid_period_ids}

    if selected_base and selected_base != 'All':
        base_filter = {'base': selected_base}
        if selected_bid_month:
            base_filter['bid_month_year'] = selected_bid_month
        bid_period_ids = [
            bp['_id'] for bp in
            db.bid_periods.find(base_filter, {'_id': 1})
        ]
        if bid_period_ids:
            if 'bid_period_id' in pairings_count_query:
                pairings_count_query['bid_period_id']['$in'] = list(
                    set(pairings_count_query['bid_period_id']['$in']) & set(bid_period_ids)
                )
            else:
                pairings_count_query['bid_period_id'] = {'$in': bid_period_ids}

    with col1:
        total_pairings = db.pairings.count_documents(pairings_count_query)
        st.metric("Total Pairings", total_pairings)

    with col2:
        fleet_stats = get_fleet_stats(bid_month=selected_bid_month, base=selected_base)
        total_fleets = len(fleet_stats)
        st.metric("Fleets", total_fleets)

    with col3:
        if not fleet_stats.empty:
            avg_credit = fleet_stats['avg_credit_hours'].mean()
            st.metric("Avg Credit", f"{avg_credit:.1f}h")
        else:
            st.metric("Avg Credit", "N/A")

    with col4:
        layover_stats = get_layover_stats(
            fleet=selected_fleet,
            category=selected_category,
            min_credit=credit_range[0],
            max_credit=credit_range[1],
            days=days_options,
            bid_month=selected_bid_month,
            base=selected_base
        )
        total_layover_cities = len(layover_stats)
        st.metric("Layover Cities", total_layover_cities)

    st.markdown("---")

    # Maps section
    st.subheader("🗺️ Route Network & Layovers")

    # Show active filters
    active_filters = []
    # Primary filters (bid month always shown since it's required)
    active_filters.append(f"📅 Bid Month: {selected_bid_month}")
    if selected_fleet != 'All':
        active_filters.append(f"✈️ Fleet: {selected_fleet}")
    if selected_base != 'All':
        active_filters.append(f"🏠 Base: {selected_base}")
    # Pairing filters
    if selected_category != 'All':
        active_filters.append(f"Category: {selected_category}")
    if days_options and len(days_options) > 0:
        active_filters.append(f"Days: {', '.join(map(str, days_options))}")
    if credit_range != (10, 30):
        active_filters.append(f"Credit: {credit_range[0]}-{credit_range[1]}h")
    # Layover filters
    if selected_layover != 'All':
        active_filters.append(f"Layover: {selected_layover}")
    if overnight_enabled:
        active_filters.append(f"Overnight: {min_overnight}-{max_overnight}h")

    if active_filters:
        st.info(f"🔍 Active filters: {' • '.join(active_filters)}")

    # Layover map
    if not layover_stats.empty:
        fig_layover_map = px.scatter_geo(
            layover_stats,
            lat='lat',
            lon='lon',
            size='layovers',
            hover_name='city',
            hover_data={
                'station': True,
                'layovers': True,
                'lat': False,
                'lon': False
            },
            color='layovers',
            color_continuous_scale='OrRd',
            size_max=50,
            title='Layover Cities by Frequency',
            projection='natural earth'
        )

        fig_layover_map.update_traces(
            marker=dict(
                line=dict(width=1, color='darkred'),
                opacity=0.85
            )
        )

        # Calculate bounds for auto-zoom with padding
        lat_min, lat_max = layover_stats['lat'].min(), layover_stats['lat'].max()
        lon_min, lon_max = layover_stats['lon'].min(), layover_stats['lon'].max()

        # Add padding (10% of range)
        lat_range = lat_max - lat_min
        lon_range = lon_max - lon_min
        lat_padding = lat_range * 0.1 if lat_range > 0 else 5
        lon_padding = lon_range * 0.1 if lon_range > 0 else 5

        fig_layover_map.update_geos(
            showcountries=True,
            showcoastlines=True,
            showland=True,
            landcolor='rgb(243, 243, 243)',
            coastlinecolor='rgb(204, 204, 204)',
            # Auto-fit to data bounds
            fitbounds="locations",
            # Set center based on data
            center=dict(
                lat=(lat_min + lat_max) / 2,
                lon=(lon_min + lon_max) / 2
            ),
            # Visible bounds with padding
            lataxis=dict(range=[lat_min - lat_padding, lat_max + lat_padding]),
            lonaxis=dict(range=[lon_min - lon_padding, lon_max + lon_padding])
        )

        fig_layover_map.update_layout(
            height=600,
            margin={"r":0,"t":30,"l":0,"b":0},
            clickmode='event+select'
        )

        # Display map with click event handling
        st.plotly_chart(fig_layover_map, use_container_width=True, key=f"layover_map_{selected_bid_month}")

        # Add helpful instruction
        st.caption("💡 Tip: Use the layover filter in the sidebar to drill down to specific cities")

        # Optional: Add quick filter buttons for top layover cities
        st.markdown("**Quick Filters - Top Layover Cities:**")
        top_layovers = layover_stats.nlargest(10, 'layovers')

        # Create columns for quick filter buttons
        cols = st.columns(5)
        for idx, (_, layover_row) in enumerate(top_layovers.iterrows()):
            col_idx = idx % 5
            with cols[col_idx]:
                station = layover_row['station']
                count = int(layover_row['layovers'])
                if st.button(f"{station} ({count})", key=f"quick_filter_{station}_{selected_bid_month}", use_container_width=True):
                    st.session_state.selected_layover_station = station
                    st.rerun()

    # Pairing search section
    st.markdown("---")
    st.subheader("🔎 Pairing Search")

    pairings_df = get_pairings_data(
        fleet=selected_fleet,
        category=selected_category,
        min_credit=credit_range[0],
        max_credit=credit_range[1],
        days=days_options,
        layover_station=selected_layover,
        min_overnight_hours=min_overnight,
        max_overnight_hours=max_overnight,
        bid_month=selected_bid_month,
        base=selected_base
    )

    if not pairings_df.empty:
        st.write(f"Found **{len(pairings_df)}** pairings")

        # Prepare display columns
        display_cols = ['id', 'fleet', 'pairing_category', 'credit_hours', 'days', 'flight_hours', 'layovers']

        # Add overnight hours columns if available
        if 'max_overnight_hours' in pairings_df.columns:
            display_cols.append('max_overnight_hours')

        # Keep _id for detail lookup (but don't display it)
        display_df = pairings_df[display_cols + ['_id']].copy()
        display_df['credit_hours'] = display_df['credit_hours'].round(1)
        display_df['flight_hours'] = display_df['flight_hours'].round(1)
        display_df['layovers'] = display_df['layovers'].apply(lambda x: ', '.join(x) if x else 'None')

        if 'max_overnight_hours' in display_df.columns:
            display_df['max_overnight_hours'] = display_df['max_overnight_hours'].round(1)
            display_df = display_df.rename(columns={'max_overnight_hours': 'max_overnight_h'})

        # Display dataframe without _id column
        display_cols_for_table = [col for col in display_df.columns if col != '_id']
        st.dataframe(
            display_df[display_cols_for_table].sort_values('credit_hours', ascending=False),
            hide_index=True,
            use_container_width=True
        )

        # Pairing detail viewer
        st.markdown("---")
        st.subheader("🔍 Explore Pairing Details")

        # Create pairing options with index mapping to MongoDB _id
        pairing_option_to_id = {}
        pairing_options = ['Select a pairing...']

        for idx, row in display_df.iterrows():
            # Format layovers list
            layovers_str = row['layovers'] if isinstance(row['layovers'], str) else ', '.join(row['layovers']) if row['layovers'] else 'None'

            # Truncate if too long (keep first few layovers)
            if len(layovers_str) > 40:
                layover_parts = layovers_str.split(', ')
                if len(layover_parts) > 3:
                    layovers_str = ', '.join(layover_parts[:3]) + '...'
                else:
                    layovers_str = layovers_str[:37] + '...'

            option_text = f"{row['id']} - {row['fleet']} - {row['days']}D - {row['credit_hours']:.1f}h - [{layovers_str}]"
            pairing_options.append(option_text)
            pairing_option_to_id[option_text] = row['_id']

        # Create a dynamic key based on active filters to force re-render when filters change
        filter_key = f"{selected_bid_month}_{selected_fleet}_{selected_base}_{selected_category}_{selected_layover}"

        selected_pairing_option = st.selectbox(
            "Choose a pairing to see detailed route map and structure:",
            options=pairing_options,
            key=f"pairing_detail_selector_{filter_key}"
        )

        if selected_pairing_option != 'Select a pairing...':
            # Use MongoDB _id to get the exact pairing (handles duplicate pairing IDs across bid months)
            pairing_object_id = pairing_option_to_id[selected_pairing_option]
            pairing_details = db.pairings.find_one({'_id': pairing_object_id})

            if pairing_details:
                pairing_id = pairing_details.get('id')
                st.markdown(f"### Pairing **{pairing_id}** - {pairing_details.get('fleet')} Fleet")

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Days", pairing_details.get('days'))
                with col2:
                    st.metric("Credit Hours", f"{pairing_details.get('credit_minutes', 0) / 60:.1f}")
                with col3:
                    st.metric("Flight Hours", f"{pairing_details.get('flight_time_minutes', 0) / 60:.1f}")
                with col4:
                    duty_count = len(pairing_details.get('duty_periods', []))
                    st.metric("Duty Periods", duty_count)

                duty_periods = pairing_details.get('duty_periods', [])

                if duty_periods:
                    day_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']

                    fig_pairing = go.Figure()
                    all_stations = []

                    for dp_idx, dp in enumerate(duty_periods):
                        legs = dp.get('legs', [])
                        day_color = day_colors[dp_idx % len(day_colors)]

                        for leg in legs:
                            dep_code = leg.get('departure_station')
                            arr_code = leg.get('arrival_station')

                            if dep_code and arr_code:
                                dep_lat, dep_lon, dep_city = get_airport_coords(dep_code)
                                arr_lat, arr_lon, arr_city = get_airport_coords(arr_code)

                                if all([dep_lat, dep_lon, arr_lat, arr_lon]):
                                    is_deadhead = leg.get('deadhead', False)
                                    line_style = 'dash' if is_deadhead else 'solid'

                                    fig_pairing.add_trace(
                                        go.Scattergeo(
                                            lon=[dep_lon, arr_lon],
                                            lat=[dep_lat, arr_lat],
                                            mode='lines',
                                            line=dict(width=2, color=day_color, dash=line_style),
                                            hoverinfo='text',
                                            text=f"Day {dp_idx + 1}: {dep_code} → {arr_code}<br>FL{leg.get('flight_number', '')}<br>{leg.get('flight_time', '')}",
                                            showlegend=False
                                        )
                                    )

                                    all_stations.append({'code': dep_code, 'city': dep_city, 'lat': dep_lat, 'lon': dep_lon})
                                    all_stations.append({'code': arr_code, 'city': arr_city, 'lat': arr_lat, 'lon': arr_lon})

                    stations_df = pd.DataFrame(all_stations).drop_duplicates(subset='code')

                    if not stations_df.empty:
                        fig_pairing.add_trace(
                            go.Scattergeo(
                                lon=stations_df['lon'],
                                lat=stations_df['lat'],
                                mode='markers+text',
                                marker=dict(size=10, color='darkblue', line=dict(width=2, color='white')),
                                text=stations_df['code'],
                                textposition='top center',
                                hoverinfo='text',
                                hovertext=stations_df['city'],
                                showlegend=False
                            )
                        )

                    # Calculate bounds for auto-zoom
                    if all_stations:
                        all_lats = [s['lat'] for s in all_stations if s['lat']]
                        all_lons = [s['lon'] for s in all_stations if s['lon']]

                        if all_lats and all_lons:
                            lat_min, lat_max = min(all_lats), max(all_lats)
                            lon_min, lon_max = min(all_lons), max(all_lons)

                            # Add padding (15% of range for tighter zoom on route)
                            lat_range = lat_max - lat_min
                            lon_range = lon_max - lon_min
                            lat_padding = lat_range * 0.15 if lat_range > 0 else 5
                            lon_padding = lon_range * 0.15 if lon_range > 0 else 5

                            fig_pairing.update_geos(
                                projection_type='natural earth',
                                showcountries=True,
                                showcoastlines=True,
                                showland=True,
                                landcolor='rgb(243, 243, 243)',
                                coastlinecolor='rgb(204, 204, 204)',
                                # Auto-fit to route
                                center=dict(
                                    lat=(lat_min + lat_max) / 2,
                                    lon=(lon_min + lon_max) / 2
                                ),
                                lataxis=dict(range=[lat_min - lat_padding, lat_max + lat_padding]),
                                lonaxis=dict(range=[lon_min - lon_padding, lon_max + lon_padding])
                            )
                        else:
                            # Fallback if no valid coordinates
                            fig_pairing.update_geos(
                                projection_type='natural earth',
                                showcountries=True,
                                showcoastlines=True,
                                showland=True,
                                landcolor='rgb(243, 243, 243)',
                                coastlinecolor='rgb(204, 204, 204)',
                            )
                    else:
                        # Fallback if no stations
                        fig_pairing.update_geos(
                            projection_type='natural earth',
                            showcountries=True,
                            showcoastlines=True,
                            showland=True,
                            landcolor='rgb(243, 243, 243)',
                            coastlinecolor='rgb(204, 204, 204)',
                        )

                    fig_pairing.update_layout(
                        title=f'Route Map for Pairing {pairing_id}',
                        height=500,
                        margin={"r":0,"t":40,"l":0,"b":0}
                    )

                    st.plotly_chart(fig_pairing, use_container_width=True)

                    # Trip structure
                    st.markdown("#### Trip Structure")

                    for dp_idx, dp in enumerate(duty_periods):
                        day_color = day_colors[dp_idx % len(day_colors)]
                        legs = dp.get('legs', [])
                        layover = dp.get('layover_station')

                        # Calculate overnight duration if not last duty period
                        overnight_info = ""
                        if dp_idx < len(duty_periods) - 1:
                            next_dp = duty_periods[dp_idx + 1]
                            release_mins = dp.get('release_time_minutes')
                            next_report_mins = next_dp.get('report_time_minutes')

                            if release_mins is not None and next_report_mins is not None:
                                # Handle overnight (next day)
                                if next_report_mins < release_mins:
                                    next_report_mins += 1440  # Add 24 hours
                                overnight_mins = next_report_mins - release_mins
                                overnight_hrs = overnight_mins / 60
                                overnight_info = f" - Overnight: {overnight_hrs:.1f}h"

                        with st.expander(f"**Day {dp_idx + 1}** - {len(legs)} flights" + (f" - Layover: {layover}" if layover else " - Return to base") + overnight_info, expanded=(dp_idx == 0)):
                            st.markdown(f"**Report:** {dp.get('report_time_formatted', dp.get('report_time', 'N/A'))} | **Release:** {dp.get('release_time_formatted', dp.get('release_time', 'N/A'))}")

                            if layover:
                                hotel = dp.get('hotel')
                                hotel_phone = dp.get('hotel_phone')
                                if hotel:
                                    hotel_str = f"🏨 **Hotel:** {hotel}"
                                    if hotel_phone:
                                        hotel_str += f" | ☎️ {hotel_phone}"
                                    st.info(hotel_str)

                            legs_data = []
                            for leg_idx, leg in enumerate(legs):
                                legs_data.append({
                                    'Seq': leg_idx + 1,
                                    'Flight': f"{'DH ' if leg.get('deadhead') else ''}{leg.get('flight_number', '')}",
                                    'Route': f"{leg.get('departure_station', '')} → {leg.get('arrival_station', '')}",
                                    'Dept': leg.get('departure_time_formatted', leg.get('departure_time', '')),
                                    'Arr': leg.get('arrival_time_formatted', leg.get('arrival_time', '')),
                                    'Flight Time': leg.get('flight_time', ''),
                                    'Ground': leg.get('ground_time', ''),
                                    'Equipment': leg.get('equipment', '')
                                })

                            if legs_data:
                                legs_df = pd.DataFrame(legs_data)
                                st.dataframe(legs_df, hide_index=True, use_container_width=True)
    else:
        st.info("No pairings found matching the selected filters.")

# ============================================================================
# PAGE 2: QA WORKBENCH
# ============================================================================

elif st.session_state.nav_page == 'qa':
    st.header("🔍 QA Workbench")
    st.markdown("Compare PDF source with parsed JSON data")

    # File selection
    col1, col2 = st.columns(2)

    with col1:
        pdf_dir = Path("Pairing Source Docs")
        pdf_files = list(pdf_dir.glob("*.pdf")) if pdf_dir.exists() else []

        if not pdf_files:
            st.error("No PDF files found in 'Pairing Source Docs' directory")
        else:
            selected_pdf = st.selectbox(
                "Select PDF",
                options=pdf_files,
                format_func=lambda x: x.name,
                key="qa_pdf_selector"
            )

    with col2:
        json_dir = Path("output")
        json_files = list(json_dir.glob("*.json")) if json_dir.exists() else []

        if not json_files:
            st.error("No JSON files found in 'output' directory")
        else:
            selected_json = st.selectbox(
                "Select Parsed JSON",
                options=json_files,
                format_func=lambda x: x.name,
                key="qa_json_selector"
            )

    if pdf_files and json_files:
        # Load data
        pdf_text_by_page = extract_pdf_text(str(selected_pdf))
        all_pdf_text = '\n'.join(pdf_text_by_page.values())
        parsed_data = load_json_data(str(selected_json))

        # QA mode selector
        qa_mode = st.radio(
            "QA Mode",
            options=["Overview", "Fleet Totals", "Individual Pairing", "Search & Compare"],
            horizontal=True
        )

        st.markdown("---")

        # OVERVIEW MODE
        if qa_mode == "Overview":
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("📄 PDF Source")
                st.metric("Total Pages", len(pdf_text_by_page))
                st.metric("Total Characters", len(all_pdf_text))

                with st.expander("Preview First Page", expanded=False):
                    first_page = pdf_text_by_page.get(0, '')
                    st.text_area(
                        "Page 1",
                        value=first_page[:2000] + "..." if len(first_page) > 2000 else first_page,
                        height=400,
                        disabled=True,
                        key="qa_pdf_preview"
                    )

            with col2:
                st.subheader("📋 Parsed Data")
                bid_periods = parsed_data.get('bid_periods', [])
                st.metric("Bid Periods (Fleets)", len(bid_periods))

                total_pairings = sum(len(bp.get('pairings', [])) for bp in bid_periods)
                st.metric("Total Pairings", total_pairings)

                total_legs = 0
                for bp in bid_periods:
                    for pairing in bp.get('pairings', []):
                        for dp in pairing.get('duty_periods', []):
                            total_legs += len(dp.get('legs', []))
                st.metric("Total Legs", total_legs)

                with st.expander("Fleet Breakdown", expanded=False):
                    fleet_data = []
                    for bp in bid_periods:
                        fleet_data.append({
                            'Fleet': bp.get('fleet'),
                            'Base': bp.get('base'),
                            'Pairings': len(bp.get('pairings', [])),
                            'FTM': bp.get('ftm'),
                            'TTL': bp.get('ttl')
                        })

                    if fleet_data:
                        st.dataframe(
                            pd.DataFrame(fleet_data),
                            hide_index=True,
                            use_container_width=True
                        )

        # FLEET TOTALS MODE
        elif qa_mode == "Fleet Totals":
            st.subheader("Fleet Totals Validation")

            totals_pattern = re.compile(
                r'([A-Z]{3})\s+([0-9]{2,3}[A-Z]?)\s+FTM-\s*([\d:,]+)\s+TTL-\s*([\d:,]+)'
            )
            pdf_totals = totals_pattern.findall(all_pdf_text)
            bid_periods = parsed_data.get('bid_periods', [])

            for base, fleet, ftm, ttl in pdf_totals:
                st.subheader(f"Fleet {fleet}")

                col1, col2, col3 = st.columns([1, 1, 1])

                with col1:
                    st.markdown("**PDF Source**")
                    st.code(f"Base: {base}\nFTM: {ftm}\nTTL: {ttl}")

                with col2:
                    st.markdown("**Parsed Data**")

                    matching_bp = next((bp for bp in bid_periods if bp.get('fleet') == fleet), None)

                    if matching_bp:
                        parsed_ftm = matching_bp.get('ftm', 'N/A')
                        parsed_ttl = matching_bp.get('ttl', 'N/A')
                        parsed_base = matching_bp.get('base', 'N/A')

                        st.code(f"Base: {parsed_base}\nFTM: {parsed_ftm}\nTTL: {parsed_ttl}")
                    else:
                        st.error("Not found in parsed data")

                with col3:
                    st.markdown("**Status**")

                    if matching_bp:
                        ftm_match = parsed_ftm == ftm
                        ttl_match = parsed_ttl == ttl

                        st.write(f"FTM: {'✅' if ftm_match else '❌'}")
                        st.write(f"TTL: {'✅' if ttl_match else '❌'}")

                        if ftm_match and ttl_match:
                            st.success("Perfect match!")
                        else:
                            st.error("Mismatch detected")
                    else:
                        st.error("Missing from parsed data")

                st.markdown("---")

        # INDIVIDUAL PAIRING MODE
        elif qa_mode == "Individual Pairing":
            st.subheader("Individual Pairing Inspection")

            bid_periods = parsed_data.get('bid_periods', [])
            all_pairings = []
            for bp in bid_periods:
                fleet = bp.get('fleet')
                for pairing in bp.get('pairings', []):
                    all_pairings.append({
                        'id': pairing.get('id'),
                        'fleet': fleet,
                        'days': pairing.get('days'),
                        'credit_minutes': pairing.get('credit_minutes'),
                        'pairing_data': pairing
                    })

            if all_pairings:
                selected_pairing = st.selectbox(
                    "Select Pairing to Inspect",
                    options=all_pairings,
                    format_func=lambda x: f"{x['id']} - Fleet {x['fleet']} - {x['days']}D - {x['credit_minutes']/60:.1f}h",
                    key="qa_pairing_selector"
                )

                if selected_pairing:
                    pairing_id = selected_pairing['id']
                    pairing_data = selected_pairing['pairing_data']

                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("### 📄 PDF Source")

                        search_results = find_in_pdf(all_pdf_text, pairing_id, context_lines=10)

                        if search_results:
                            for idx, result in enumerate(search_results):
                                with st.expander(f"Occurrence {idx + 1} (Line {result['line_number']})", expanded=(idx == 0)):
                                    highlighted = highlight_text(result['context'], pairing_id)
                                    st.markdown(highlighted)
                        else:
                            st.warning(f"Pairing {pairing_id} not found in PDF text")

                    with col2:
                        st.markdown("### 📋 Parsed Data")

                        st.json({
                            'id': pairing_data.get('id'),
                            'fleet': selected_pairing['fleet'],
                            'days': pairing_data.get('days'),
                            'category': pairing_data.get('pairing_category'),
                            'credit_minutes': pairing_data.get('credit_minutes'),
                            'flight_time_minutes': pairing_data.get('flight_time_minutes')
                        })

                        st.markdown("#### Duty Periods")

                        duty_periods = pairing_data.get('duty_periods', [])
                        for dp_idx, dp in enumerate(duty_periods):
                            legs = dp.get('legs', [])

                            with st.expander(f"Day {dp_idx + 1} - {len(legs)} legs", expanded=(dp_idx == 0)):
                                st.write(f"**Report:** {dp.get('report_time_formatted', dp.get('report_time'))}")
                                st.write(f"**Release:** {dp.get('release_time_formatted', dp.get('release_time'))}")
                                st.write(f"**Layover:** {dp.get('layover_station', 'None')}")

                                if dp.get('hotel'):
                                    st.info(f"🏨 {dp.get('hotel')}")

                                legs_data = []
                                for leg in legs:
                                    legs_data.append({
                                        'Flight': f"{'DH ' if leg.get('deadhead') else ''}{leg.get('flight_number', '')}",
                                        'Route': f"{leg.get('departure_station')} → {leg.get('arrival_station')}",
                                        'Dept': leg.get('departure_time_formatted', leg.get('departure_time')),
                                        'Arr': leg.get('arrival_time_formatted', leg.get('arrival_time')),
                                        'Flight Time': leg.get('flight_time'),
                                        'Equipment': leg.get('equipment')
                                    })

                                if legs_data:
                                    st.dataframe(pd.DataFrame(legs_data), hide_index=True, use_container_width=True)
            else:
                st.warning("No pairings found in parsed data")

        # SEARCH & COMPARE MODE
        elif qa_mode == "Search & Compare":
            st.subheader("Search & Compare")

            search_term = st.text_input("Enter search term (pairing ID, station code, flight number, etc.)")

            if search_term:
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("### 📄 PDF Matches")

                    pdf_results = find_in_pdf(all_pdf_text, search_term, context_lines=3)

                    if pdf_results:
                        st.success(f"Found {len(pdf_results)} matches in PDF")

                        for idx, result in enumerate(pdf_results[:20]):
                            with st.expander(f"Match {idx + 1} (Line {result['line_number']})"):
                                highlighted = highlight_text(result['context'], search_term)
                                st.markdown(highlighted)
                    else:
                        st.info("No matches found in PDF")

                with col2:
                    st.markdown("### 📋 Parsed Data Matches")

                    bid_periods = parsed_data.get('bid_periods', [])
                    matches = []

                    for bp in bid_periods:
                        fleet = bp.get('fleet')

                        for pairing in bp.get('pairings', []):
                            pairing_str = json.dumps(pairing, default=str)

                            if search_term.upper() in pairing_str.upper():
                                matches.append({
                                    'fleet': fleet,
                                    'pairing_id': pairing.get('id'),
                                    'days': pairing.get('days'),
                                    'credit_hours': pairing.get('credit_minutes', 0) / 60
                                })

                    if matches:
                        st.success(f"Found {len(matches)} pairings with matches")

                        matches_df = pd.DataFrame(matches)
                        st.dataframe(
                            matches_df,
                            hide_index=True,
                            use_container_width=True
                        )
                    else:
                        st.info("No matches found in parsed data")

# ============================================================================
# PAGE 3: ANNOTATIONS (Placeholder)
# ============================================================================

elif st.session_state.nav_page == 'annotations':
    st.header("📝 QA Annotations")
    st.info("Use the standalone qa_annotations.py tool for full annotation functionality")
    st.markdown("""
    To launch the full annotations tool:
    ```bash
    python3 -m streamlit run qa_annotations.py
    ```

    Or use the launcher:
    ```bash
    ./launch.sh
    ```
    """)
