#!/usr/bin/env python3
"""
Pilot Pairing Dashboard - Interactive Web Interface
Built with Streamlit for quick POC

Run: streamlit run dashboard.py
"""

import streamlit as st
import pandas as pd
from pymongo import MongoClient
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Page config
st.set_page_config(
    page_title="Pilot Pairing Dashboard",
    page_icon="✈️",
    layout="wide"
)

# MongoDB connection
@st.cache_resource
def get_database():
    """Connect to MongoDB - modify connection string as needed."""
    # TODO: Replace with your Atlas connection string
    connection_string = st.secrets.get("MONGO_URI", "mongodb://localhost:27017/")
    client = MongoClient(connection_string)
    return client['airline_pairings']

db = get_database()

# Cache data queries
@st.cache_data(ttl=600)
def get_fleet_stats():
    """Get statistics by fleet."""
    pipeline = [
        {
            '$group': {
                '_id': '$fleet',
                'total_pairings': {'$sum': 1},
                'avg_credit_hours': {'$avg': {'$divide': ['$credit_minutes', 60]}},
                'avg_days': {'$avg': {'$toInt': '$days'}},
                'total_credit_hours': {'$sum': {'$divide': ['$credit_minutes', 60]}}
            }
        },
        {'$sort': {'total_pairings': -1}}
    ]
    results = list(db.pairings.aggregate(pipeline))
    return pd.DataFrame(results).rename(columns={'_id': 'fleet'})

@st.cache_data(ttl=600)
def get_pairings_data(fleet=None, category=None, min_credit=0, max_credit=100):
    """Get pairings with filters."""
    query = {'credit_minutes': {'$gte': min_credit * 60, '$lte': max_credit * 60}}

    if fleet and fleet != 'All':
        query['fleet'] = fleet

    if category and category != 'All':
        query['pairing_category'] = category

    pairings = list(db.pairings.find(
        query,
        {
            'id': 1, 'fleet': 1, 'base': 1, 'pairing_category': 1,
            'credit_minutes': 1, 'days': 1, 'flight_time_minutes': 1,
            'duty_periods': 1
        }
    ).limit(1000))

    # Process data
    for p in pairings:
        p['credit_hours'] = p['credit_minutes'] / 60
        p['flight_hours'] = p['flight_time_minutes'] / 60
        p['layovers'] = [dp.get('layover_station') for dp in p.get('duty_periods', [])
                        if dp.get('layover_station')]

    return pd.DataFrame(pairings)

@st.cache_data(ttl=600)
def get_layover_stats():
    """Get top layover destinations."""
    pipeline = [
        {'$match': {'layover_station': {'$ne': None}}},
        {
            '$group': {
                '_id': '$layover_station',
                'count': {'$sum': 1}
            }
        },
        {'$sort': {'count': -1}},
        {'$limit': 15}
    ]
    results = list(db.legs.aggregate(pipeline))
    return pd.DataFrame(results).rename(columns={'_id': 'station', 'count': 'layovers'})

@st.cache_data(ttl=600)
def get_categories():
    """Get all pairing categories."""
    return ['All'] + sorted(db.pairings.distinct('pairing_category'))

@st.cache_data(ttl=600)
def get_fleets():
    """Get all fleets."""
    return ['All'] + sorted(db.pairings.distinct('fleet'))

# ============================================================================
# MAIN DASHBOARD
# ============================================================================

st.title("✈️ Pilot Pairing Dashboard")
st.markdown("---")

# Sidebar filters
st.sidebar.header("🔍 Filters")

fleets = get_fleets()
categories = get_categories()

selected_fleet = st.sidebar.selectbox("Fleet", fleets)
selected_category = st.sidebar.selectbox("Category", categories)

credit_range = st.sidebar.slider(
    "Credit Hours Range",
    min_value=0,
    max_value=50,
    value=(10, 30)
)

# ============================================================================
# TOP METRICS
# ============================================================================

col1, col2, col3, col4 = st.columns(4)

with col1:
    total_pairings = db.pairings.count_documents({})
    st.metric("Total Pairings", f"{total_pairings:,}")

with col2:
    fleet_stats = get_fleet_stats()
    total_fleets = len(fleet_stats)
    st.metric("Fleets", total_fleets)

with col3:
    avg_credit = fleet_stats['avg_credit_hours'].mean()
    st.metric("Avg Credit", f"{avg_credit:.1f}h")

with col4:
    layover_stats = get_layover_stats()
    total_layover_cities = len(layover_stats)
    st.metric("Layover Cities", total_layover_cities)

st.markdown("---")

# ============================================================================
# FLEET OVERVIEW
# ============================================================================

st.header("📊 Fleet Overview")

col1, col2 = st.columns(2)

with col1:
    # Fleet distribution pie chart
    fig_pie = px.pie(
        fleet_stats,
        values='total_pairings',
        names='fleet',
        title='Pairings by Fleet',
        hole=0.4
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with col2:
    # Credit by fleet bar chart
    fig_bar = px.bar(
        fleet_stats,
        x='fleet',
        y='avg_credit_hours',
        title='Average Credit Hours by Fleet',
        color='avg_credit_hours',
        color_continuous_scale='Blues'
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# ============================================================================
# LAYOVER DESTINATIONS
# ============================================================================

st.header("🏨 Top Layover Destinations")

col1, col2 = st.columns([2, 1])

with col1:
    # Layover bar chart
    fig_layover = px.bar(
        layover_stats,
        x='station',
        y='layovers',
        title='Most Common Overnight Cities',
        color='layovers',
        color_continuous_scale='Greens'
    )
    st.plotly_chart(fig_layover, use_container_width=True)

with col2:
    # Layover table
    st.dataframe(
        layover_stats,
        hide_index=True,
        use_container_width=True
    )

# ============================================================================
# PAIRING SEARCH & RESULTS
# ============================================================================

st.header("🔎 Pairing Search")

# Get filtered data
pairings_df = get_pairings_data(
    fleet=selected_fleet,
    category=selected_category,
    min_credit=credit_range[0],
    max_credit=credit_range[1]
)

if not pairings_df.empty:
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader(f"Found {len(pairings_df)} pairings")

        # Credit distribution
        fig_hist = px.histogram(
            pairings_df,
            x='credit_hours',
            nbins=30,
            title='Credit Hours Distribution',
            color_discrete_sequence=['#636EFA']
        )
        st.plotly_chart(fig_hist, use_container_width=True)

    with col2:
        st.subheader("Summary Stats")
        st.metric("Min Credit", f"{pairings_df['credit_hours'].min():.1f}h")
        st.metric("Max Credit", f"{pairings_df['credit_hours'].max():.1f}h")
        st.metric("Avg Credit", f"{pairings_df['credit_hours'].mean():.1f}h")
        st.metric("Avg Days", f"{pairings_df['days'].astype(int).mean():.1f}")

    # Results table
    st.subheader("Pairing Details")

    display_df = pairings_df[[
        'id', 'fleet', 'pairing_category', 'credit_hours',
        'days', 'flight_hours', 'layovers'
    ]].copy()

    display_df['credit_hours'] = display_df['credit_hours'].round(1)
    display_df['flight_hours'] = display_df['flight_hours'].round(1)
    display_df['layovers'] = display_df['layovers'].apply(
        lambda x: ', '.join(x) if x else 'None'
    )

    # Sort by credit hours descending
    display_df = display_df.sort_values('credit_hours', ascending=False)

    st.dataframe(
        display_df,
        hide_index=True,
        use_container_width=True,
        column_config={
            "id": "Pairing ID",
            "fleet": "Fleet",
            "pairing_category": "Category",
            "credit_hours": st.column_config.NumberColumn("Credit (h)", format="%.1f"),
            "days": "Days",
            "flight_hours": st.column_config.NumberColumn("Flight (h)", format="%.1f"),
            "layovers": "Layovers"
        }
    )

    # Download button
    csv = display_df.to_csv(index=False)
    st.download_button(
        label="📥 Download Results as CSV",
        data=csv,
        file_name=f"pairings_{selected_fleet}_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

else:
    st.info("No pairings found matching the selected filters.")

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.caption("Pilot Pairing Dashboard • Data refreshes every 10 minutes • Built with Streamlit & MongoDB")
