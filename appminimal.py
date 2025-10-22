import streamlit as st
import pandas as pd
from datetime import datetime
import networkx as nx

# Page configuration
st.set_page_config(
    page_title="UPS Flight Routing",
    page_icon="✈️",
    layout="wide"
)

st.title("✈️ UPS Flight Routing Dashboard (Lite)")

@st.cache_data(ttl=3600)
def load_data(file):
    """Load Excel file"""
    try:
        schedule_df = pd.read_excel(file, sheet_name='SchedDateLocalTimeFlightSchedul')
        routes_df = pd.read_excel(file, sheet_name='Data')
        
        schedule_df['Start Date (LZ)'] = pd.to_datetime(schedule_df['Start Date (LZ)'], errors='coerce')
        schedule_df['End Date (LZ)'] = pd.to_datetime(schedule_df['End Date (LZ)'], errors='coerce')
        
        return schedule_df, routes_df
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None, None

def is_flight_available(dow_string, date):
    """Check if flight is available on given date"""
    weekday = date.weekday()
    if weekday < len(dow_string):
        return dow_string[weekday] != '.'
    return False

def parse_time(time_str):
    """Parse time string to minutes"""
    try:
        if pd.isna(time_str) or str(time_str) == 'nan':
            return None
        time_str = str(time_str).strip()
        if ':' in time_str:
            h, m = time_str.split(':')
            return int(h) * 60 + int(m)
    except:
        return None
    return None

def find_direct_flights(schedule_df, origin, destination, date):
    """Find direct flights"""
    route_flights = schedule_df[
        (schedule_df['Orig'] == origin) & 
        (schedule_df['Dest'] == destination)
    ]
    
    available_flights = []
    for _, flight in route_flights.iterrows():
        if is_flight_available(str(flight['DOW(S)']), date):
            if flight['Start Date (LZ)'] <= date <= flight['End Date (LZ)']:
                available_flights.append(flight)
    
    return available_flights

def build_flight_network(schedule_df, date):
    """Build network graph of flights"""
    G = nx.DiGraph()
    
    for _, flight in schedule_df.iterrows():
        if is_flight_available(str(flight['DOW(S)']), date):
            if flight['Start Date (LZ)'] <= date <= flight['End Date (LZ)']:
                dep_time = parse_time(flight['Sched Out(L)'])
                arr_time = parse_time(flight['Sched In(L)'])
                
                if dep_time is not None and arr_time is not None:
                    if arr_time < dep_time:
                        arr_time += 24 * 60
                    
                    G.add_edge(
                        flight['Orig'],
                        flight['Dest'],
                        departure=dep_time,
                        arrival=arr_time,
                        duration=arr_time - dep_time,
                        flight_num=flight['Flight #'],
                        carrier=flight['Carrier'],
                        dep_str=str(flight['Sched Out(L)']),
                        arr_str=str(flight['Sched In(L)']),
                        dur_str=str(flight['Blkhr'])
                    )
    
    return G

def find_connecting_flights(G, origin, destination, max_stops=2):
    """Find connecting flights"""
    routes = []
    
    try:
        all_paths = list(nx.all_simple_paths(G, origin, destination, cutoff=max_stops+1))
        
        for path in all_paths[:10]:  # Limit to 10 paths for performance
            if len(path) > 2:
                route_info = {
                    'legs': [],
                    'total_duration': 0,
                    'stops': len(path) - 2,
                    'path': ' → '.join(path)
                }
                
                valid_route = True
                for i in range(len(path) - 1):
                    edge_data = G.get_edge_data(path[i], path[i+1])
                    if edge_data:
                        route_info['legs'].append({
                            'from': path[i],
                            'to': path[i+1],
                            'departure': edge_data['dep_str'],
                            'arrival': edge_data['arr_str'],
                            'flight': f"{edge_data['carrier']}{edge_data['flight_num']}"
                        })
                        
                        if i == 0:
                            route_info['departure'] = edge_data['departure']
                            route_info['dep_str'] = edge_data['dep_str']
                        
                        if i == len(path) - 2:
                            route_info['arrival'] = edge_data['arrival']
                            route_info['arr_str'] = edge_data['arr_str']
                    else:
                        valid_route = False
                        break
                
                if valid_route:
                    route_info['total_duration'] = route_info['arrival'] - route_info['departure']
                    if route_info['total_duration'] < 0:
                        route_info['total_duration'] += 24 * 60
                    routes.append(route_info)
    except:
        pass
    
    routes.sort(key=lambda x: x['total_duration'])
    return routes[:5]

# Main app
with st.sidebar:
    st.header("📁 Upload Data")
    uploaded_file = st.file_uploader("Upload Excel file", type=['xlsx', 'xls'])

if uploaded_file:
    schedule_df, routes_df = load_data(uploaded_file)
    
    if schedule_df is not None and routes_df is not None:
        st.success("✅ File loaded successfully!")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Get route pairs
            route_pairs = routes_df[['Origin Airport', 'Destination Airport']].drop_duplicates()
            route_options = [f"{row['Origin Airport']} → {row['Destination Airport']}" 
                           for _, row in route_pairs.iterrows()]
            
            selected_route = st.selectbox("Select Route", options=route_options)
            
            if selected_route:
                origin = selected_route.split(' → ')[0]
                destination = selected_route.split(' → ')[1]
        
        with col2:
            min_date = schedule_df['Start Date (LZ)'].min().date()
            max_date = schedule_df['End Date (LZ)'].max().date()
            
            selected_date = st.date_input(
                "Select Date",
                value=min_date,
                min_value=min_date,
                max_value=max_date
            )
        
        with col3:
            if st.button("🔍 Find Routes", type="primary", use_container_width=True):
                st.session_state.search = True
        
        if 'search' in st.session_state and st.session_state.search:
            st.divider()
            
            with st.spinner("Searching..."):
                search_date = pd.Timestamp(selected_date)
                
                # Search for direct flights
                direct_flights = find_direct_flights(schedule_df, origin, destination, search_date)
                
                if direct_flights:
                    st.success(f"✅ Found {len(direct_flights)} direct flight(s)")
                    
                    for i, flight in enumerate(direct_flights, 1):
                        with st.expander(f"Direct Flight {i}", expanded=True):
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("Departure", str(flight['Sched Out(L)']))
                            with col2:
                                st.metric("Arrival", str(flight['Sched In(L)']))
                            with col3:
                                st.metric("Duration", str(flight['Blkhr']))
                            with col4:
                                st.metric("Flight", f"{flight['Carrier']}{flight['Flight #']}")
                else:
                    st.warning("No direct flights. Searching connections...")
                    
                    # Find connecting flights
                    G = build_flight_network(schedule_df, search_date)
                    connecting_routes = find_connecting_flights(G, origin, destination)
                    
                    if connecting_routes:
                        st.success(f"✅ Found {len(connecting_routes)} connecting route(s)")
                        
                        for i, route in enumerate(connecting_routes, 1):
                            with st.expander(f"Route {i}: {route['path']}", expanded=(i==1)):
                                duration_hours = route['total_duration'] // 60
                                duration_mins = route['total_duration'] % 60
                                
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Departure", route['dep_str'])
                                with col2:
                                    st.metric("Arrival", route['arr_str'])
                                with col3:
                                    st.metric("Total Time", f"{duration_hours}h {duration_mins}m")
                                
                                st.write("**Flight Legs:**")
                                for j, leg in enumerate(route['legs'], 1):
                                    st.write(f"{j}. {leg['from']} → {leg['to']}: {leg['flight']} ({leg['departure']} - {leg['arrival']})")
                    else:
                        st.error(f"❌ No routes found from {origin} to {destination} on {selected_date}")
        
        # Show statistics
        with st.expander("📊 Quick Stats"):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Flights", len(schedule_df))
            with col2:
                st.metric("Airports", schedule_df['Orig'].nunique())
            with col3:
                st.metric("Routes to Track", len(route_pairs))
            with col4:
                st.metric("Carriers", schedule_df['Carrier'].nunique())
else:
    st.info("👈 Please upload the UPS Flights Excel file to begin")
    
    with st.expander("📖 Instructions"):
        st.markdown("""
        1. Upload your Excel file with two sheets:
           - **SchedDateLocalTimeFlightSchedul**: Flight schedules
           - **Data**: Origin-Destination pairs to track
        2. Select a route from the dropdown
        3. Choose a date
        4. Click 'Find Routes' to see available options
        
        The system will find direct flights first, then connecting flights if needed.
        """)
