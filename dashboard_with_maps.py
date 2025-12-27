#!/usr/bin/env python3
"""
Pilot Pairing Dashboard with Interactive Maps
Shows layover destinations and route networks on world map

Run: python3 -m streamlit run dashboard_with_maps.py
"""

import streamlit as st
import pandas as pd
from pymongo import MongoClient
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import airportsdata

# Page config
st.set_page_config(
    page_title="Pilot Pairing Dashboard",
    page_icon="✈️",
    layout="wide"
)

# Load airport data (lat/lon for all airports worldwide)
@st.cache_resource
def get_airport_data():
    """Load airport coordinates from airportsdata."""
    airports = airportsdata.load('IATA')  # Load by IATA code (ORD, LAX, etc.)

    # Convert to DataFrame for easy lookup
    airport_df = pd.DataFrame([
        {
            'iata': code,
            'name': data['name'],
            'city': data['city'],
            'country': data['country'],
            'lat': data['lat'],
            'lon': data['lon']
        }
        for code, data in airports.items()
    ])

    return airport_df.set_index('iata')

airports = get_airport_data()

# MongoDB connection
@st.cache_resource
def get_database():
    """Connect to MongoDB."""
    connection_string = st.secrets.get("MONGO_URI", "mongodb://localhost:27017/")
    client = MongoClient(connection_string)
    return client['airline_pairings']

db = get_database()

# Helper function to get airport coordinates
def get_airport_coords(iata_code):
    """Get lat/lon for airport code."""
    try:
        airport = airports.loc[iata_code]
        return airport['lat'], airport['lon'], airport['city']
    except:
        return None, None, iata_code

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
def get_layover_stats(fleet=None, category=None, min_credit=0, max_credit=100, days=None):
    """Get top layover destinations with coordinates, filtered by pairing criteria."""
    # Build pairing filter
    pairing_match = {'credit_minutes': {'$gte': min_credit * 60, '$lte': max_credit * 60}}

    if fleet and fleet != 'All':
        pairing_match['fleet'] = fleet

    if category and category != 'All':
        pairing_match['pairing_category'] = category

    if days and len(days) > 0:
        pairing_match['days'] = {'$in': [str(d) for d in days]}

    # Aggregate from legs, join with pairings to filter
    pipeline = [
        {'$match': {'layover_station': {'$ne': None}}},
        {
            '$lookup': {
                'from': 'pairings',
                'localField': 'pairing_id',
                'foreignField': 'id',
                'as': 'pairing'
            }
        },
        {'$unwind': '$pairing'},
        {'$match': {f'pairing.{k}': v for k, v in pairing_match.items()}},
        # Exclude layovers that are at the pairing's home base
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
        {'$limit': 200}  # Increased limit to show more data
    ]

    results = list(db.legs.aggregate(pipeline))
    df = pd.DataFrame(results).rename(columns={'_id': 'station', 'count': 'layovers'})

    # Add coordinates
    df['lat'] = df['station'].apply(lambda x: get_airport_coords(x)[0])
    df['lon'] = df['station'].apply(lambda x: get_airport_coords(x)[1])
    df['city'] = df['station'].apply(lambda x: get_airport_coords(x)[2])

    # Remove entries without coordinates
    df = df.dropna(subset=['lat', 'lon'])

    # Additional filter: Remove home base (ORD for this dataset)
    # Get all possible bases from the database
    all_bases = set(db.pairings.distinct('base'))
    df = df[~df['station'].isin(all_bases)]

    return df

@st.cache_data(ttl=600)
def get_route_data(fleet=None, category=None, min_credit=0, max_credit=100, days=None, limit=300):
    """Get most common routes with coordinates, filtered by pairing criteria."""
    # Build pairing filter
    pairing_match = {'credit_minutes': {'$gte': min_credit * 60, '$lte': max_credit * 60}}

    if fleet and fleet != 'All':
        pairing_match['fleet'] = fleet

    if category and category != 'All':
        pairing_match['pairing_category'] = category

    if days and len(days) > 0:
        pairing_match['days'] = {'$in': [str(d) for d in days]}

    # Aggregate from legs, join with pairings to filter
    pipeline = [
        {
            '$match': {
                'departure_station': {'$ne': None},
                'arrival_station': {'$ne': None},
                'deadhead': False  # Only real flights
            }
        },
        {
            '$lookup': {
                'from': 'pairings',
                'localField': 'pairing_id',
                'foreignField': 'id',
                'as': 'pairing'
            }
        },
        {'$unwind': '$pairing'},
        {'$match': {f'pairing.{k}': v for k, v in pairing_match.items()}},
        {
            '$group': {
                '_id': {
                    'from': '$departure_station',
                    'to': '$arrival_station'
                },
                'count': {'$sum': 1},
                'avg_flight_time': {'$avg': '$flight_time_minutes'}
            }
        },
        {'$sort': {'count': -1}},
        {'$limit': limit}
    ]

    results = list(db.legs.aggregate(pipeline))

    # Process results
    routes = []
    for r in results:
        from_code = r['_id']['from']
        to_code = r['_id']['to']

        from_lat, from_lon, from_city = get_airport_coords(from_code)
        to_lat, to_lon, to_city = get_airport_coords(to_code)

        if all([from_lat, from_lon, to_lat, to_lon]):
            routes.append({
                'from_code': from_code,
                'to_code': to_code,
                'from_city': from_city,
                'to_city': to_city,
                'from_lat': from_lat,
                'from_lon': from_lon,
                'to_lat': to_lat,
                'to_lon': to_lon,
                'count': r['count'],
                'avg_flight_hours': r['avg_flight_time'] / 60 if r['avg_flight_time'] else 0
            })

    return pd.DataFrame(routes)

@st.cache_data(ttl=600)
def get_pairings_by_layover(layover_station, fleet=None, category=None, min_credit=0, max_credit=100, days=None):
    """Get all pairings that layover at a specific station."""
    # Build pairing filter
    query = {'credit_minutes': {'$gte': min_credit * 60, '$lte': max_credit * 60}}

    if fleet and fleet != 'All':
        query['fleet'] = fleet

    if category and category != 'All':
        query['pairing_category'] = category

    if days and len(days) > 0:
        query['days'] = {'$in': [str(d) for d in days]}

    # Find pairings with this layover station in duty_periods
    query['duty_periods.layover_station'] = layover_station

    pairings = list(db.pairings.find(
        query,
        {
            'id': 1, 'fleet': 1, 'base': 1, 'pairing_category': 1,
            'credit_minutes': 1, 'days': 1, 'flight_time_minutes': 1,
            'duty_periods': 1
        }
    ).limit(100))

    # Process data
    for p in pairings:
        p['credit_hours'] = p['credit_minutes'] / 60
        p['flight_hours'] = p['flight_time_minutes'] / 60
        p['layovers'] = [dp.get('layover_station') for dp in p.get('duty_periods', [])
                        if dp.get('layover_station')]

    return pd.DataFrame(pairings)

@st.cache_data(ttl=600)
def get_pairings_data(fleet=None, category=None, min_credit=0, max_credit=100, days=None):
    """Get pairings with filters."""
    query = {'credit_minutes': {'$gte': min_credit * 60, '$lte': max_credit * 60}}

    if fleet and fleet != 'All':
        query['fleet'] = fleet

    if category and category != 'All':
        query['pairing_category'] = category

    if days and len(days) > 0:
        # Convert days to strings for MongoDB query (days stored as strings like "3")
        query['days'] = {'$in': [str(d) for d in days]}

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

# Days filter
days_options = st.sidebar.multiselect(
    "Number of Days",
    options=[1, 2, 3, 4],
    default=None,
    help="Select specific day counts (leave empty for all)"
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
    layover_stats = get_layover_stats(
        fleet=selected_fleet,
        category=selected_category,
        min_credit=credit_range[0],
        max_credit=credit_range[1],
        days=days_options
    )
    total_layover_cities = len(layover_stats)
    st.metric("Layover Cities", total_layover_cities)

st.markdown("---")

# ============================================================================
# MAPS SECTION - NEW!
# ============================================================================

st.header("🗺️ Route Network & Layovers")

# Show active filters info
active_filters = []
if selected_fleet != 'All':
    active_filters.append(f"Fleet: {selected_fleet}")
if selected_category != 'All':
    active_filters.append(f"Category: {selected_category}")
if days_options and len(days_options) > 0:
    active_filters.append(f"Days: {', '.join(map(str, days_options))}")
if credit_range != (10, 30):
    active_filters.append(f"Credit: {credit_range[0]}-{credit_range[1]}h")

if active_filters:
    st.info(f"🔍 Active filters: {' • '.join(active_filters)}")

tab1, tab2 = st.tabs(["Layover Cities Map", "Route Network Map"])

with tab1:
    st.subheader("Overnight Destinations")

    layover_data = get_layover_stats(
        fleet=selected_fleet,
        category=selected_category,
        min_credit=credit_range[0],
        max_credit=credit_range[1],
        days=days_options
    )

    if not layover_data.empty:
        # Create bubble map
        fig_layover_map = px.scatter_geo(
            layover_data,
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
            color_continuous_scale='OrRd',  # Darker orange-red scale
            size_max=50,
            title='Layover Cities by Frequency (excluding home base)',
            projection='natural earth'
        )

        # Make markers darker with border
        fig_layover_map.update_traces(
            marker=dict(
                line=dict(width=1, color='darkred'),
                opacity=0.85
            )
        )

        fig_layover_map.update_geos(
            showcountries=True,
            showcoastlines=True,
            showland=True,
            landcolor='rgb(243, 243, 243)',
            coastlinecolor='rgb(204, 204, 204)',
        )

        fig_layover_map.update_layout(
            height=600,
            margin={"r":0,"t":30,"l":0,"b":0}
        )

        st.plotly_chart(fig_layover_map, use_container_width=True)

        # City selector and pairings display
        st.markdown("---")
        st.subheader("📋 Explore Pairings by Layover City")

        # Create dropdown with city names and codes
        city_options = ['Select a city...'] + [
            f"{row['city']} ({row['station']}) - {row['layovers']} layovers"
            for _, row in layover_data.sort_values('layovers', ascending=False).iterrows()
        ]

        selected_city = st.selectbox(
            "Choose a layover city to see all pairings:",
            options=city_options,
            key="layover_city_selector"
        )

        # If a city is selected, show pairings
        if selected_city != 'Select a city...':
            # Extract station code from selection (e.g., "ORD" from "Chicago (ORD) - 100 layovers")
            station_code = selected_city.split('(')[1].split(')')[0]
            city_name = selected_city.split(' (')[0]

            st.markdown(f"### Pairings with layovers in **{city_name}** ({station_code})")

            # Get pairings for this layover
            city_pairings = get_pairings_by_layover(
                layover_station=station_code,
                fleet=selected_fleet,
                category=selected_category,
                min_credit=credit_range[0],
                max_credit=credit_range[1],
                days=days_options
            )

            if not city_pairings.empty:
                st.write(f"Found **{len(city_pairings)}** pairings with layovers in {city_name}")

                # Display table
                display_df = city_pairings[['id', 'fleet', 'pairing_category', 'credit_hours', 'days', 'flight_hours', 'layovers']].copy()
                display_df['credit_hours'] = display_df['credit_hours'].round(1)
                display_df['flight_hours'] = display_df['flight_hours'].round(1)
                display_df['layovers'] = display_df['layovers'].apply(lambda x: ', '.join(x) if x else 'None')

                st.dataframe(
                    display_df.sort_values('credit_hours', ascending=False),
                    hide_index=True,
                    use_container_width=True,
                    column_config={
                        "id": "Pairing ID",
                        "fleet": "Fleet",
                        "pairing_category": "Category",
                        "credit_hours": st.column_config.NumberColumn("Credit (h)", format="%.1f"),
                        "days": "Days",
                        "flight_hours": st.column_config.NumberColumn("Flight (h)", format="%.1f"),
                        "layovers": "All Layovers"
                    }
                )

                # Download button for this city
                csv = display_df.to_csv(index=False)
                st.download_button(
                    label=f"📥 Download {city_name} Pairings as CSV",
                    data=csv,
                    file_name=f"pairings_layover_{station_code}.csv",
                    mime="text/csv"
                )
            else:
                st.info(f"No pairings found with layovers in {city_name} matching current filters")
    else:
        st.info("No layover data available")

with tab2:
    st.subheader("Flight Routes")

    route_data = get_route_data(
        fleet=selected_fleet,
        category=selected_category,
        min_credit=credit_range[0],
        max_credit=credit_range[1],
        days=days_options,
        limit=300
    )

    if not route_data.empty:
        # Create route map with lines
        fig_routes = go.Figure()

        # Add route lines
        for idx, row in route_data.iterrows():
            fig_routes.add_trace(
                go.Scattergeo(
                    lon=[row['from_lon'], row['to_lon']],
                    lat=[row['from_lat'], row['to_lat']],
                    mode='lines',
                    line=dict(
                        width=1,
                        color='rgba(31, 119, 180, 0.3)'
                    ),
                    hoverinfo='text',
                    text=f"{row['from_code']} → {row['to_code']}<br>{row['count']} flights<br>{row['avg_flight_hours']:.1f}h avg",
                    showlegend=False
                )
            )

        # Add airport markers
        all_airports = pd.concat([
            route_data[['from_code', 'from_city', 'from_lat', 'from_lon']].rename(
                columns={'from_code': 'code', 'from_city': 'city', 'from_lat': 'lat', 'from_lon': 'lon'}
            ),
            route_data[['to_code', 'to_city', 'to_lat', 'to_lon']].rename(
                columns={'to_code': 'code', 'to_city': 'city', 'to_lat': 'lat', 'to_lon': 'lon'}
            )
        ]).drop_duplicates(subset='code')

        fig_routes.add_trace(
            go.Scattergeo(
                lon=all_airports['lon'],
                lat=all_airports['lat'],
                mode='markers',
                marker=dict(
                    size=8,
                    color='red',
                    line=dict(width=1, color='white')
                ),
                text=all_airports['code'] + ' - ' + all_airports['city'],
                hoverinfo='text',
                name='Airports'
            )
        )

        fig_routes.update_geos(
            projection_type='natural earth',
            showcountries=True,
            showcoastlines=True,
            showland=True,
            landcolor='rgb(243, 243, 243)',
            coastlinecolor='rgb(204, 204, 204)',
        )

        fig_routes.update_layout(
            title='Top 50 Most Common Routes',
            height=600,
            margin={"r":0,"t":30,"l":0,"b":0},
            showlegend=False
        )

        st.plotly_chart(fig_routes, use_container_width=True)

        # Top routes table
        st.dataframe(
            route_data[['from_code', 'to_code', 'from_city', 'to_city', 'count', 'avg_flight_hours']].head(15).rename(
                columns={
                    'from_code': 'From',
                    'to_code': 'To',
                    'from_city': 'Origin City',
                    'to_city': 'Dest City',
                    'count': 'Flights',
                    'avg_flight_hours': 'Avg Hours'
                }
            ),
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("No route data available")

st.markdown("---")

# ============================================================================
# FLEET OVERVIEW (Original)
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

st.markdown("---")

# ============================================================================
# PAIRING SEARCH & RESULTS
# ============================================================================

st.header("🔎 Pairing Search")

# Get filtered data
pairings_df = get_pairings_data(
    fleet=selected_fleet,
    category=selected_category,
    min_credit=credit_range[0],
    max_credit=credit_range[1],
    days=days_options
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

    # ========================================================================
    # PAIRING DETAIL VIEW WITH MAP
    # ========================================================================

    st.markdown("---")
    st.subheader("🔍 Explore Pairing Details")

    # Pairing selector
    pairing_options = ['Select a pairing...'] + [
        f"{row['id']} - {row['fleet']} - {row['days']}D - {row['credit_hours']:.1f}h"
        for _, row in display_df.iterrows()
    ]

    selected_pairing_option = st.selectbox(
        "Choose a pairing to see detailed route map and structure:",
        options=pairing_options,
        key="pairing_detail_selector"
    )

    if selected_pairing_option != 'Select a pairing...':
        # Extract pairing ID
        pairing_id = selected_pairing_option.split(' - ')[0]

        # Get full pairing details from MongoDB
        pairing_details = db.pairings.find_one({'id': pairing_id})

        if pairing_details:
            st.markdown(f"### Pairing **{pairing_id}** - {pairing_details.get('fleet')} Fleet")

            # Summary info
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

            # Duty period details and map
            duty_periods = pairing_details.get('duty_periods', [])

            if duty_periods:
                # Color palette for different days
                day_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']

                # Build map data
                fig_pairing = go.Figure()

                all_stations = []

                for dp_idx, dp in enumerate(duty_periods):
                    legs = dp.get('legs', [])
                    day_color = day_colors[dp_idx % len(day_colors)]

                    # Add route lines for this duty period
                    for leg in legs:
                        dep_code = leg.get('departure_station')
                        arr_code = leg.get('arrival_station')

                        if dep_code and arr_code:
                            dep_lat, dep_lon, dep_city = get_airport_coords(dep_code)
                            arr_lat, arr_lon, arr_city = get_airport_coords(arr_code)

                            if all([dep_lat, dep_lon, arr_lat, arr_lon]):
                                # Add flight line
                                is_deadhead = leg.get('deadhead', False)
                                line_style = 'dash' if is_deadhead else 'solid'

                                fig_pairing.add_trace(
                                    go.Scattergeo(
                                        lon=[dep_lon, arr_lon],
                                        lat=[dep_lat, arr_lat],
                                        mode='lines',
                                        line=dict(
                                            width=2,
                                            color=day_color,
                                            dash=line_style
                                        ),
                                        hoverinfo='text',
                                        text=f"Day {dp_idx + 1}: {dep_code} → {arr_code}<br>FL{leg.get('flight_number', '')}<br>{leg.get('flight_time', '')}",
                                        showlegend=False
                                    )
                                )

                                # Collect stations
                                all_stations.append({'code': dep_code, 'city': dep_city, 'lat': dep_lat, 'lon': dep_lon})
                                all_stations.append({'code': arr_code, 'city': arr_city, 'lat': arr_lat, 'lon': arr_lon})

                # Remove duplicate stations
                stations_df = pd.DataFrame(all_stations).drop_duplicates(subset='code')

                # Add airport markers
                if not stations_df.empty:
                    fig_pairing.add_trace(
                        go.Scattergeo(
                            lon=stations_df['lon'],
                            lat=stations_df['lat'],
                            mode='markers+text',
                            marker=dict(
                                size=10,
                                color='darkblue',
                                line=dict(width=2, color='white')
                            ),
                            text=stations_df['code'],
                            textposition='top center',
                            hoverinfo='text',
                            hovertext=stations_df['city'],
                            showlegend=False
                        )
                    )

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

                # Trip structure details
                st.markdown("#### Trip Structure")

                for dp_idx, dp in enumerate(duty_periods):
                    day_color = day_colors[dp_idx % len(day_colors)]
                    legs = dp.get('legs', [])
                    layover = dp.get('layover_station')

                    with st.expander(f"**Day {dp_idx + 1}** - {len(legs)} flights" + (f" - Layover: {layover}" if layover else " - Return to base"), expanded=(dp_idx == 0)):
                        st.markdown(f"**Report:** {dp.get('report_time_formatted', dp.get('report_time', 'N/A'))} | **Release:** {dp.get('release_time_formatted', dp.get('release_time', 'N/A'))}")

                        if layover:
                            hotel = dp.get('hotel')
                            if hotel:
                                st.info(f"🏨 **Hotel:** {hotel}")

                        # Legs table
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
# FOOTER
# ============================================================================

st.markdown("---")
st.caption("Pilot Pairing Dashboard • Interactive Maps • Built with Streamlit & MongoDB")
