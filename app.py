import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import networkx as nx
from collections import defaultdict
import plotly.graph_objects as go
import plotly.express as px

# Page configuration
st.set_page_config(
    page_title="UPS Flight Routing Dashboard",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1e3a8a;
        font-weight: bold;
        margin-bottom: 2rem;
        text-align: center;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #475569;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f8fafc;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e2e8f0;
    }
    .success-message {
        background-color: #10b981;
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
    }
    .warning-message {
        background-color: #f59e0b;
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data(file):
    """Load and parse the Excel file"""
    try:
        # Read both sheets
        schedule_df = pd.read_excel(file, sheet_name='SchedDateLocalTimeFlightSchedul')
        routes_df = pd.read_excel(file, sheet_name='Data')
        
        # Parse dates properly
        schedule_df['Start Date (LZ)'] = pd.to_datetime(schedule_df['Start Date (LZ)'])
        schedule_df['End Date (LZ)'] = pd.to_datetime(schedule_df['End Date (LZ)'])
        
        # Clean time formats
        schedule_df['Sched Out(L)'] = schedule_df['Sched Out(L)'].astype(str)
        schedule_df['Sched In(L)'] = schedule_df['Sched In(L)'].astype(str)
        schedule_df['Blkhr'] = schedule_df['Blkhr'].astype(str)
        
        return schedule_df, routes_df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None, None

def parse_dow(dow_string):
    """Parse the DOW(S) string to get available days"""
    days = []
    day_map = {0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday', 
               4: 'Friday', 5: 'Saturday', 6: 'Sunday'}
    
    for i, char in enumerate(dow_string):
        if char != '.':
            days.append(day_map[i])
    return days

def is_flight_available(dow_string, date):
    """Check if flight is available on given date"""
    weekday = date.weekday()  # 0=Monday, 6=Sunday
    if weekday < len(dow_string):
        return dow_string[weekday] != '.'
    return False

def parse_time(time_str):
    """Parse time string to minutes since midnight"""
    try:
        if pd.isna(time_str) or time_str == 'nan':
            return None
        time_str = str(time_str).strip()
        if ':' in time_str:
            parts = time_str.split(':')
            hours = int(parts[0])
            minutes = int(parts[1]) if len(parts) > 1 else 0
            return hours * 60 + minutes
    except:
        return None
    return None

def parse_duration(duration_str):
    """Parse duration string to minutes"""
    try:
        if pd.isna(duration_str) or duration_str == 'nan':
            return None
        duration_str = str(duration_str).strip()
        if ':' in duration_str:
            parts = duration_str.split(':')
            hours = int(parts[0])
            minutes = int(parts[1]) if len(parts) > 1 else 0
            return hours * 60 + minutes
    except:
        return None
    return None

def format_time(minutes):
    """Format minutes to HH:MM string"""
    if minutes is None:
        return "N/A"
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours:02d}:{mins:02d}"

def find_direct_flights(schedule_df, origin, destination, date):
    """Find direct flights for a given route and date"""
    # Filter for the specific route
    route_flights = schedule_df[
        (schedule_df['Orig'] == origin) & 
        (schedule_df['Dest'] == destination)
    ]
    
    # Filter by date availability
    available_flights = []
    for _, flight in route_flights.iterrows():
        if is_flight_available(flight['DOW(S)'], date):
            if flight['Start Date (LZ)'] <= date <= flight['End Date (LZ)']:
                available_flights.append(flight)
    
    return available_flights

def build_flight_network(schedule_df, date):
    """Build a network graph of available flights on a given date"""
    G = nx.DiGraph()
    
    for _, flight in schedule_df.iterrows():
        if is_flight_available(flight['DOW(S)'], date):
            if flight['Start Date (LZ)'] <= date <= flight['End Date (LZ)']:
                dep_time = parse_time(flight['Sched Out(L)'])
                arr_time = parse_time(flight['Sched In(L)'])
                duration = parse_duration(flight['Blkhr'])
                
                if dep_time is not None and arr_time is not None:
                    # Handle overnight flights
                    if arr_time < dep_time:
                        arr_time += 24 * 60
                    
                    G.add_edge(
                        flight['Orig'],
                        flight['Dest'],
                        departure=dep_time,
                        arrival=arr_time,
                        duration=duration if duration else arr_time - dep_time,
                        flight_num=flight['Flight #'],
                        carrier=flight['Carrier'],
                        dep_str=flight['Sched Out(L)'],
                        arr_str=flight['Sched In(L)'],
                        dur_str=flight['Blkhr']
                    )
    
    return G

def find_connecting_flights(G, origin, destination, max_stops=2, min_connection_time=30, max_connection_time=480):
    """Find connecting flights with constraints"""
    routes = []
    
    try:
        # Find all simple paths up to max_stops + 1 edges
        all_paths = nx.all_simple_paths(G, origin, destination, cutoff=max_stops+1)
        
        for path in all_paths:
            if len(path) > 2:  # Multi-leg route
                valid_route = True
                route_info = {
                    'legs': [],
                    'total_duration': 0,
                    'stops': len(path) - 2
                }
                
                current_time = 0
                for i in range(len(path) - 1):
                    edge_data = G.get_edge_data(path[i], path[i+1])
                    
                    if i == 0:
                        current_time = edge_data['departure']
                        route_info['departure'] = edge_data['departure']
                        route_info['dep_str'] = edge_data['dep_str']
                    else:
                        # Check connection time
                        connection_time = edge_data['departure'] - prev_arrival
                        if connection_time < 0:  # Next day flight
                            connection_time += 24 * 60
                        
                        if connection_time < min_connection_time or connection_time > max_connection_time:
                            valid_route = False
                            break
                    
                    prev_arrival = edge_data['arrival']
                    
                    route_info['legs'].append({
                        'from': path[i],
                        'to': path[i+1],
                        'departure': edge_data['dep_str'],
                        'arrival': edge_data['arr_str'],
                        'duration': edge_data['dur_str'],
                        'flight': f"{edge_data['carrier']}{edge_data['flight_num']}"
                    })
                
                if valid_route:
                    route_info['arrival'] = prev_arrival
                    route_info['arr_str'] = route_info['legs'][-1]['arrival']
                    route_info['total_duration'] = prev_arrival - route_info['departure']
                    if route_info['total_duration'] < 0:
                        route_info['total_duration'] += 24 * 60
                    routes.append(route_info)
    
    except nx.NetworkXNoPath:
        pass
    
    # Sort by total duration
    routes.sort(key=lambda x: x['total_duration'])
    return routes[:5]  # Return top 5 routes

def display_flight_route(route_info, route_type="Direct"):
    """Display flight route information"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Route Type", route_type)
        st.metric("Departure", route_info.get('dep_str', 'N/A'))
    
    with col2:
        if route_type == "Direct":
            st.metric("Duration", route_info.get('dur_str', 'N/A'))
        else:
            duration_mins = route_info.get('total_duration', 0)
            hours = duration_mins // 60
            mins = duration_mins % 60
            st.metric("Total Duration", f"{hours}h {mins}m")
        st.metric("Arrival", route_info.get('arr_str', 'N/A'))
    
    with col3:
        if route_type == "Direct":
            st.metric("Flight", f"{route_info.get('carrier', '')}{route_info.get('flight_num', '')}")
        else:
            st.metric("Stops", route_info.get('stops', 0))
    
    if route_type == "Connecting":
        st.subheader("Flight Legs")
        for i, leg in enumerate(route_info['legs'], 1):
            st.write(f"**Leg {i}:** {leg['from']} → {leg['to']}")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.write(f"Flight: {leg['flight']}")
            with col2:
                st.write(f"Departure: {leg['departure']}")
            with col3:
                st.write(f"Arrival: {leg['arrival']}")
            with col4:
                st.write(f"Duration: {leg['duration']}")
            st.divider()

def create_route_visualization(route_info, schedule_df):
    """Create a visual representation of the route"""
    if 'legs' in route_info:  # Connecting flight
        airports = [route_info['legs'][0]['from']]
        for leg in route_info['legs']:
            airports.append(leg['to'])
    else:  # Direct flight
        airports = [route_info['Orig'], route_info['Dest']]
    
    # Create a simple visualization
    fig = go.Figure()
    
    # Add nodes (airports)
    for i, airport in enumerate(airports):
        fig.add_trace(go.Scatter(
            x=[i], y=[0],
            mode='markers+text',
            marker=dict(size=30, color='#1e3a8a'),
            text=airport,
            textposition="top center",
            name=airport
        ))
    
    # Add edges (flights)
    for i in range(len(airports) - 1):
        fig.add_trace(go.Scatter(
            x=[i, i+1], y=[0, 0],
            mode='lines',
            line=dict(color='#60a5fa', width=3),
            showlegend=False
        ))
    
    fig.update_layout(
        title="Flight Route",
        showlegend=False,
        height=200,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor='white'
    )
    
    return fig

# Main app
def main():
    st.markdown('<h1 class="main-header">✈️ UPS Flight Routing Dashboard</h1>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("📁 Data Upload")
        uploaded_file = st.file_uploader("Upload Excel file", type=['xlsx', 'xls'])
        
        if uploaded_file:
            st.success("File uploaded successfully!")
            st.divider()
            st.header("ℹ️ About")
            st.info("""
            This dashboard helps you find optimal flight routes for UPS shipments.
            
            **Features:**
            - Direct flight search
            - Multi-leg route calculation
            - Date-specific availability
            - Transit time optimization
            """)
    
    # Main content
    if uploaded_file:
        schedule_df, routes_df = load_data(uploaded_file)
        
        if schedule_df is not None and routes_df is not None:
            # Create tabs
            tab1, tab2, tab3, tab4 = st.tabs(["🔍 Route Finder", "📊 Analytics", "🗺️ Network View", "📋 Data Explorer"])
            
            with tab1:
                st.markdown('<h2 class="sub-header">Find Optimal Route</h2>', unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Get unique route pairs from the Data sheet
                    route_pairs = routes_df[['Origin Airport', 'Destination Airport']].drop_duplicates()
                    route_options = [f"{row['Origin Airport']} → {row['Destination Airport']}" 
                                   for _, row in route_pairs.iterrows()]
                    
                    selected_route = st.selectbox(
                        "Select Route (from Data sheet)",
                        options=route_options,
                        help="These are the predefined routes from your Data sheet"
                    )
                    
                    if selected_route:
                        origin = selected_route.split(' → ')[0]
                        destination = selected_route.split(' → ')[1]
                
                with col2:
                    # Date selection
                    min_date = schedule_df['Start Date (LZ)'].min().date()
                    max_date = schedule_df['End Date (LZ)'].max().date()
                    
                    selected_date = st.date_input(
                        "Select Date",
                        value=min_date,
                        min_value=min_date,
                        max_value=max_date
                    )
                
                st.divider()
                
                if st.button("🔍 Find Routes", type="primary"):
                    with st.spinner("Searching for optimal routes..."):
                        # Convert date to datetime
                        search_date = pd.Timestamp(selected_date)
                        
                        # Search for direct flights
                        direct_flights = find_direct_flights(schedule_df, origin, destination, search_date)
                        
                        if direct_flights:
                            st.success(f"Found {len(direct_flights)} direct flight(s)!")
                            
                            for i, flight in enumerate(direct_flights, 1):
                                with st.expander(f"Direct Flight Option {i}", expanded=True):
                                    route_info = {
                                        'dep_str': flight['Sched Out(L)'],
                                        'arr_str': flight['Sched In(L)'],
                                        'dur_str': flight['Blkhr'],
                                        'carrier': flight['Carrier'],
                                        'flight_num': flight['Flight #'],
                                        'Orig': origin,
                                        'Dest': destination
                                    }
                                    display_flight_route(route_info, "Direct")
                                    
                                    # Visualize route
                                    fig = create_route_visualization(route_info, schedule_df)
                                    st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.warning("No direct flights found. Searching for connecting flights...")
                            
                            # Build network and find connecting flights
                            G = build_flight_network(schedule_df, search_date)
                            connecting_routes = find_connecting_flights(G, origin, destination)
                            
                            if connecting_routes:
                                st.success(f"Found {len(connecting_routes)} connecting route(s)!")
                                
                                for i, route in enumerate(connecting_routes, 1):
                                    with st.expander(f"Connecting Route Option {i} ({route['stops']} stop(s))", 
                                                   expanded=(i==1)):
                                        display_flight_route(route, "Connecting")
                                        
                                        # Visualize route
                                        fig = create_route_visualization(route, schedule_df)
                                        st.plotly_chart(fig, use_container_width=True)
                            else:
                                st.error(f"No routes found from {origin} to {destination} on {selected_date}")
                                st.info("Try selecting a different date or check if the airports are in the flight network.")
            
            with tab2:
                st.markdown('<h2 class="sub-header">Flight Network Analytics</h2>', unsafe_allow_html=True)
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    total_flights = len(schedule_df)
                    st.metric("Total Flights", f"{total_flights:,}")
                
                with col2:
                    unique_origins = schedule_df['Orig'].nunique()
                    st.metric("Origin Airports", unique_origins)
                
                with col3:
                    unique_dests = schedule_df['Dest'].nunique()
                    st.metric("Destination Airports", unique_dests)
                
                with col4:
                    total_routes = len(route_pairs)
                    st.metric("Tracked Routes", total_routes)
                
                st.divider()
                
                # Top routes by frequency
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Top 10 Most Frequent Routes")
                    route_freq = schedule_df.groupby(['Orig', 'Dest']).size().reset_index(name='Frequency')
                    route_freq['Route'] = route_freq['Orig'] + ' → ' + route_freq['Dest']
                    top_routes = route_freq.nlargest(10, 'Frequency')
                    
                    fig = px.bar(top_routes, x='Frequency', y='Route', orientation='h',
                                color='Frequency', color_continuous_scale='Blues')
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.subheader("Busiest Airports")
                    orig_count = schedule_df['Orig'].value_counts().reset_index()
                    orig_count.columns = ['Airport', 'Departures']
                    dest_count = schedule_df['Dest'].value_counts().reset_index()
                    dest_count.columns = ['Airport', 'Arrivals']
                    
                    airport_activity = pd.merge(orig_count, dest_count, on='Airport', how='outer').fillna(0)
                    airport_activity['Total'] = airport_activity['Departures'] + airport_activity['Arrivals']
                    top_airports = airport_activity.nlargest(10, 'Total')
                    
                    fig = px.bar(top_airports, x='Airport', y=['Departures', 'Arrivals'],
                                title="Top 10 Busiest Airports")
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
                
                # Day of week analysis
                st.subheader("Flight Availability by Day of Week")
                days_data = []
                day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                
                for day_idx, day_name in enumerate(day_names):
                    count = 0
                    for dow_str in schedule_df['DOW(S)']:
                        if day_idx < len(dow_str) and dow_str[day_idx] != '.':
                            count += 1
                    days_data.append({'Day': day_name, 'Flights': count})
                
                days_df = pd.DataFrame(days_data)
                fig = px.line(days_df, x='Day', y='Flights', markers=True,
                            title="Flight Distribution Across Week")
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
            
            with tab3:
                st.markdown('<h2 class="sub-header">Network Visualization</h2>', unsafe_allow_html=True)
                
                # Select date for network visualization
                network_date = st.date_input(
                    "Select Date for Network View",
                    value=min_date,
                    min_value=min_date,
                    max_value=max_date,
                    key="network_date"
                )
                
                if st.button("Generate Network", type="secondary"):
                    with st.spinner("Building flight network..."):
                        G = build_flight_network(schedule_df, pd.Timestamp(network_date))
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Active Airports", G.number_of_nodes())
                        with col2:
                            st.metric("Active Routes", G.number_of_edges())
                        with col3:
                            if G.number_of_nodes() > 0:
                                density = nx.density(G)
                                st.metric("Network Density", f"{density:.3f}")
                        
                        # Network statistics
                        if G.number_of_nodes() > 0:
                            st.subheader("Network Hubs (Top 10)")
                            degree_centrality = nx.degree_centrality(G)
                            top_hubs = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)[:10]
                            
                            hub_data = pd.DataFrame(top_hubs, columns=['Airport', 'Centrality'])
                            fig = px.bar(hub_data, x='Airport', y='Centrality',
                                       title="Most Connected Airports")
                            st.plotly_chart(fig, use_container_width=True)
            
            with tab4:
                st.markdown('<h2 class="sub-header">Data Explorer</h2>', unsafe_allow_html=True)
                
                data_choice = st.radio("Select Dataset", ["Flight Schedule", "Route Pairs"])
                
                if data_choice == "Flight Schedule":
                    st.subheader("Flight Schedule Data")
                    
                    # Filters
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        orig_filter = st.multiselect("Filter by Origin", 
                                                    options=sorted(schedule_df['Orig'].unique()))
                    with col2:
                        dest_filter = st.multiselect("Filter by Destination",
                                                    options=sorted(schedule_df['Dest'].unique()))
                    with col3:
                        carrier_filter = st.multiselect("Filter by Carrier",
                                                       options=sorted(schedule_df['Carrier'].unique()))
                    
                    # Apply filters
                    filtered_df = schedule_df.copy()
                    if orig_filter:
                        filtered_df = filtered_df[filtered_df['Orig'].isin(orig_filter)]
                    if dest_filter:
                        filtered_df = filtered_df[filtered_df['Dest'].isin(dest_filter)]
                    if carrier_filter:
                        filtered_df = filtered_df[filtered_df['Carrier'].isin(carrier_filter)]
                    
                    st.dataframe(filtered_df, use_container_width=True, height=500)
                    
                    # Download button
                    csv = filtered_df.to_csv(index=False)
                    st.download_button(
                        label="Download Filtered Data as CSV",
                        data=csv,
                        file_name=f"filtered_schedule_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                
                else:
                    st.subheader("Route Pairs Data")
                    
                    # Filters
                    col1, col2 = st.columns(2)
                    with col1:
                        orig_route_filter = st.multiselect("Filter by Origin Airport",
                                                          options=sorted(routes_df['Origin Airport'].unique()))
                    with col2:
                        dest_route_filter = st.multiselect("Filter by Destination Airport",
                                                          options=sorted(routes_df['Destination Airport'].unique()))
                    
                    # Apply filters
                    filtered_routes = routes_df.copy()
                    if orig_route_filter:
                        filtered_routes = filtered_routes[filtered_routes['Origin Airport'].isin(orig_route_filter)]
                    if dest_route_filter:
                        filtered_routes = filtered_routes[filtered_routes['Destination Airport'].isin(dest_route_filter)]
                    
                    st.dataframe(filtered_routes, use_container_width=True, height=500)
                    
                    # Download button
                    csv = filtered_routes.to_csv(index=False)
                    st.download_button(
                        label="Download Filtered Routes as CSV",
                        data=csv,
                        file_name=f"filtered_routes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
        else:
            st.error("Failed to load data. Please check the Excel file format.")
    else:
        # Welcome screen
        st.info("👈 Please upload the UPS Flights Excel file to begin.")
        
        # Instructions
        with st.expander("📖 How to Use This Dashboard"):
            st.markdown("""
            1. **Upload Data**: Upload your Excel file with flight schedules and route pairs
            2. **Route Finder**: Select origin-destination pairs and dates to find optimal routes
            3. **Analytics**: View network statistics and flight patterns
            4. **Network View**: Visualize the flight network on specific dates
            5. **Data Explorer**: Browse and filter the raw data
            
            **File Requirements:**
            - Sheet 1: "SchedDateLocalTimeFlightSchedul" with flight schedule data
            - Sheet 2: "Data" with origin-destination pairs to track
            """)

if __name__ == "__main__":
    main()
