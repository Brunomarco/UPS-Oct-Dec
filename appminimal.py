import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Page configuration
st.set_page_config(
    page_title="UPS Flight Routing System",
    page_icon="✈️",
    layout="wide"
)

# Title
st.title("✈️ UPS Flight Routing Dashboard")
st.markdown("---")

@st.cache_data
def load_data(file):
    """Load and parse the Excel file"""
    try:
        # Read both sheets
        schedule_df = pd.read_excel(file, sheet_name='SchedDateLocalTimeFlightSchedul')
        routes_df = pd.read_excel(file, sheet_name='Data')
        
        # Convert date columns
        schedule_df['Start Date (LZ)'] = pd.to_datetime(schedule_df['Start Date (LZ)'], errors='coerce')
        schedule_df['End Date (LZ)'] = pd.to_datetime(schedule_df['End Date (LZ)'], errors='coerce')
        
        # Ensure string format for time columns
        schedule_df['Sched Out(L)'] = schedule_df['Sched Out(L)'].astype(str)
        schedule_df['Sched In(L)'] = schedule_df['Sched In(L)'].astype(str)
        schedule_df['Blkhr'] = schedule_df['Blkhr'].astype(str)
        schedule_df['DOW(S)'] = schedule_df['DOW(S)'].astype(str)
        
        return schedule_df, routes_df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None, None

def is_flight_available_on_date(dow_string, date):
    """Check if flight operates on given date based on DOW(S) string"""
    if pd.isna(dow_string) or dow_string == 'nan' or dow_string == '':
        return False
    
    dow_string = str(dow_string).strip()
    weekday = date.weekday()  # Python: 0=Monday, 6=Sunday
    
    # DOW(S) format: 1=Monday, 2=Tuesday... 7=Sunday
    # Position 0 in string = Monday, position 6 = Sunday
    
    if weekday < len(dow_string):
        return dow_string[weekday] != '.'
    return False

def parse_time_to_minutes(time_str):
    """Convert time string (HH:MM) to minutes from midnight"""
    try:
        if pd.isna(time_str) or str(time_str) == 'nan':
            return None
        time_str = str(time_str).strip()
        if ':' in time_str:
            parts = time_str.split(':')
            hours = int(parts[0])
            minutes = int(parts[1]) if len(parts) > 1 else 0
            return hours * 60 + minutes
        return None
    except:
        return None

def find_direct_flights(schedule_df, origin, destination, date, days_ahead=7):
    """Find direct flights on the requested date or next available days"""
    try:
        # Filter for the specific route
        route_flights = schedule_df[
            (schedule_df['Orig'] == origin) & 
            (schedule_df['Dest'] == destination)
        ].copy()
        
        results = []
        
        for day_offset in range(days_ahead + 1):
            check_date = date + timedelta(days=day_offset)
            available_flights = []
            
            for idx, flight in route_flights.iterrows():
                try:
                    # Check if flight operates on this day of week
                    if is_flight_available_on_date(flight['DOW(S)'], check_date):
                        # Check if date is within flight's operating period
                        if pd.notna(flight['Start Date (LZ)']) and pd.notna(flight['End Date (LZ)']):
                            if flight['Start Date (LZ)'].date() <= check_date.date() <= flight['End Date (LZ)'].date():
                                flight_copy = flight.copy()
                                flight_copy['flight_date'] = check_date
                                available_flights.append(flight_copy)
                except:
                    continue
            
            if available_flights:
                results.append({
                    'date': check_date,
                    'flights': available_flights,
                    'days_from_requested': day_offset
                })
        
        return results
    except Exception as e:
        return []

def build_network(schedule_df, date, days_ahead=3):
    """Build flight network for routing"""
    network = {}
    
    try:
        for day_offset in range(days_ahead + 1):
            check_date = date + timedelta(days=day_offset)
            
            for idx, flight in schedule_df.iterrows():
                try:
                    if is_flight_available_on_date(flight['DOW(S)'], check_date):
                        if pd.notna(flight['Start Date (LZ)']) and pd.notna(flight['End Date (LZ)']):
                            if flight['Start Date (LZ)'].date() <= check_date.date() <= flight['End Date (LZ)'].date():
                                origin = str(flight['Orig'])
                                dest = str(flight['Dest'])
                                
                                if origin not in network:
                                    network[origin] = []
                                
                                dep_time = parse_time_to_minutes(flight['Sched Out(L)'])
                                arr_time = parse_time_to_minutes(flight['Sched In(L)'])
                                
                                if dep_time is not None and arr_time is not None:
                                    # Handle overnight flights
                                    if arr_time < dep_time:
                                        arr_time += 24 * 60
                                    
                                    network[origin].append({
                                        'destination': dest,
                                        'departure': dep_time,
                                        'arrival': arr_time,
                                        'dep_str': str(flight['Sched Out(L)']),
                                        'arr_str': str(flight['Sched In(L)']),
                                        'duration_str': str(flight['Blkhr']),
                                        'flight_num': f"{flight.get('Carrier', '')}{flight.get('Flight #', '')}",
                                        'duration': arr_time - dep_time,
                                        'date': check_date,
                                        'day_offset': day_offset
                                    })
                except:
                    continue
    except:
        pass
    
    return network

def find_connecting_routes(network, origin, destination, start_date, max_stops=2):
    """Find connecting flights with date tracking"""
    if origin not in network:
        return []
    
    queue = [(origin, [origin], 0, 0, start_date, [])]
    all_routes = []
    visited = set()
    
    while queue:
        current_airport, path, last_arrival, total_duration, current_date, route_dates = queue.pop(0)
        
        state = (current_airport, tuple(path))
        if state in visited:
            continue
        visited.add(state)
        
        if current_airport == destination and len(path) > 1:
            all_routes.append({
                'path': path,
                'stops': len(path) - 2,
                'total_duration': total_duration,
                'route_dates': route_dates
            })
            continue
        
        if len(path) - 1 >= max_stops + 1:
            continue
        
        if current_airport in network:
            for flight in network[current_airport]:
                next_dest = flight['destination']
                
                if next_dest in path:
                    continue
                
                if len(path) == 1:
                    new_duration = flight['duration']
                    new_dates = route_dates + [flight['date']]
                    queue.append((
                        next_dest,
                        path + [next_dest],
                        flight['arrival'],
                        new_duration,
                        flight['date'],
                        new_dates
                    ))
                else:
                    if flight['date'].date() > current_date.date():
                        days_diff = (flight['date'].date() - current_date.date()).days
                        connection_time = (days_diff * 24 * 60) + flight['departure'] - last_arrival
                    else:
                        connection_time = flight['departure'] - last_arrival
                        if connection_time < 0:
                            connection_time += 24 * 60
                    
                    if 30 <= connection_time <= 1440:
                        new_duration = total_duration + connection_time + flight['duration']
                        new_dates = route_dates + [flight['date']]
                        queue.append((
                            next_dest,
                            path + [next_dest],
                            flight['arrival'],
                            new_duration,
                            flight['date'],
                            new_dates
                        ))
    
    all_routes.sort(key=lambda x: x['total_duration'])
    return all_routes[:5]

def get_route_details(network, path, route_dates):
    """Get detailed flight information for a route"""
    legs = []
    
    try:
        for i in range(len(path) - 1):
            origin = str(path[i])
            dest = str(path[i + 1])
            flight_date = route_dates[i] if i < len(route_dates) else None
            
            if origin in network:
                for flight in network[origin]:
                    if str(flight['destination']) == dest:
                        if flight_date and hasattr(flight['date'], 'date'):
                            if flight['date'].date() == flight_date.date():
                                legs.append({
                                    'from': origin,
                                    'to': dest,
                                    'departure': str(flight['dep_str']),
                                    'arrival': str(flight['arr_str']),
                                    'duration': str(flight['duration_str']),
                                    'flight': str(flight['flight_num']),
                                    'date': flight_date.strftime('%Y-%m-%d'),
                                    'day': flight_date.strftime('%A')
                                })
                                break
    except:
        pass
    
    return legs

# Main Application
def main():
    # Sidebar
    with st.sidebar:
        st.header("📁 Data Upload")
        uploaded_file = st.file_uploader(
            "Upload UPS Flight Schedule Excel",
            type=['xlsx', 'xls']
        )
        
        if uploaded_file:
            st.success("✅ File uploaded successfully!")
    
    # Main content
    if uploaded_file:
        with st.spinner("Loading flight data..."):
            schedule_df, routes_df = load_data(uploaded_file)
        
        if schedule_df is not None and routes_df is not None:
            # Statistics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Flights", f"{len(schedule_df):,}")
            with col2:
                st.metric("Routes", f"{len(routes_df):,}")
            with col3:
                st.metric("Airports", f"{schedule_df['Orig'].nunique()}")
            with col4:
                st.metric("Carriers", f"{schedule_df.get('Carrier', pd.Series()).nunique()}")
            
            st.markdown("---")
            st.subheader("🔍 Route Finder")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Get route pairs
                route_pairs = routes_df[['Origin Airport', 'Destination Airport']].drop_duplicates()
                route_pairs = route_pairs.dropna()
                
                route_options = []
                route_dict = {}
                for idx, row in route_pairs.iterrows():
                    route_str = f"{row['Origin Airport']} → {row['Destination Airport']}"
                    route_options.append(route_str)
                    route_dict[route_str] = (row['Origin Airport'], row['Destination Airport'])
                
                selected_route = st.selectbox(
                    "Select Origin → Destination Route",
                    options=sorted(route_options)
                )
                
                if selected_route:
                    origin, destination = route_dict[selected_route]
                    st.info(f"Route: **{origin}** to **{destination}**")
            
            with col2:
                min_date = schedule_df['Start Date (LZ)'].min()
                max_date = schedule_df['End Date (LZ)'].max()
                
                if pd.notna(min_date) and pd.notna(max_date):
                    selected_date = st.date_input(
                        "Select Shipment Date",
                        value=min_date.date(),
                        min_value=min_date.date(),
                        max_value=max_date.date()
                    )
                    
                    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                    day_of_week = day_names[selected_date.weekday()]
                    st.info(f"Day: **{day_of_week}**")
            
            # Search button
            if st.button("🔍 Find Available Routes", type="primary", use_container_width=True):
                if selected_route:
                    search_date = pd.Timestamp(selected_date)
                    
                    with st.spinner(f"Searching routes from {origin} to {destination}..."):
                        try:
                            # Search for direct flights
                            direct_results = find_direct_flights(schedule_df, origin, destination, search_date)
                            
                            if direct_results:
                                st.success(f"✅ Found direct flights!")
                                
                                for result in direct_results:
                                    date_diff = result['days_from_requested']
                                    date_label = "on requested date" if date_diff == 0 else f"+{date_diff} day(s)"
                                    
                                    st.subheader(f"📅 {result['date'].strftime('%Y-%m-%d (%A)')} - {date_label}")
                                    
                                    for i, flight in enumerate(result['flights'], 1):
                                        with st.expander(f"✈️ Direct Flight {i}", expanded=(date_diff == 0)):
                                            col1, col2, col3, col4 = st.columns(4)
                                            
                                            with col1:
                                                st.markdown("**Date**")
                                                st.write(result['date'].strftime('%Y-%m-%d'))
                                                st.write(result['date'].strftime('%A'))
                                            
                                            with col2:
                                                st.markdown("**Times**")
                                                st.write(f"Dep: {flight['Sched Out(L)']} from {origin}")
                                                st.write(f"Arr: {flight['Sched In(L)']} at {destination}")
                                            
                                            with col3:
                                                st.markdown("**Duration**")
                                                st.write(f"{flight['Blkhr']}")
                                            
                                            with col4:
                                                st.markdown("**Flight**")
                                                st.write(f"{flight.get('Carrier', '')}{flight.get('Flight #', '')}")
                                            
                                            st.info(f"**Total Travel Time:** {flight['Blkhr']}")
                            else:
                                # Search for connecting flights
                                st.warning("No direct flights. Searching connections...")
                                
                                network = build_network(schedule_df, search_date)
                                
                                if network:
                                    routes = find_connecting_routes(network, origin, destination, search_date)
                                    
                                    if routes:
                                        st.success(f"✅ Found {len(routes)} connecting route(s)!")
                                        
                                        for i, route in enumerate(routes, 1):
                                            route_str = " → ".join(route['path'])
                                            total_hours = route['total_duration'] // 60
                                            total_mins = route['total_duration'] % 60
                                            
                                            with st.expander(f"🔄 Route {i}: {route_str} ({route['stops']} stop(s)) - {total_hours}h {total_mins}m", expanded=(i == 1)):
                                                
                                                st.info(f"""
                                                **Route:** {route_str}  
                                                **Total Time:** {total_hours} hours {total_mins} minutes  
                                                **Stops:** {route['stops']}
                                                """)
                                                
                                                legs = get_route_details(network, route['path'], route.get('route_dates', []))
                                                
                                                if legs:
                                                    st.markdown("### Flight Segments:")
                                                    for j, leg in enumerate(legs, 1):
                                                        st.markdown(f"**Segment {j}: {leg['from']} → {leg['to']}**")
                                                        col1, col2, col3 = st.columns(3)
                                                        with col1:
                                                            st.write(f"Date: {leg['date']} ({leg['day']})")
                                                        with col2:
                                                            st.write(f"Flight: {leg['flight']}")
                                                            st.write(f"Times: {leg['departure']} - {leg['arrival']}")
                                                        with col3:
                                                            st.write(f"Duration: {leg['duration']}")
                                                        
                                                        if j < len(legs):
                                                            st.markdown("↓")
                                    else:
                                        st.error("No connecting routes found within 2 stops.")
                                else:
                                    st.error("No flight network available for the selected date.")
                        
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
    else:
        st.info("👈 Please upload the UPS Flight Schedule Excel file to begin")

if __name__ == "__main__":
    main()
