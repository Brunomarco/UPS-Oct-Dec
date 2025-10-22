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
    # So position 0 in string = Monday (1), position 6 = Sunday (7)
    # This matches Python's weekday() where Monday=0, Sunday=6
    
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

def parse_duration_to_minutes(duration_str):
    """Convert duration string (HH:MM) to total minutes"""
    try:
        if pd.isna(duration_str) or str(duration_str) == 'nan':
            return None
        duration_str = str(duration_str).strip()
        if ':' in duration_str:
            parts = duration_str.split(':')
            hours = int(parts[0])
            minutes = int(parts[1]) if len(parts) > 1 else 0
            return hours * 60 + minutes
        return None
    except:
        return None

def format_minutes_to_time(minutes):
    """Convert minutes to HH:MM format"""
    if minutes is None:
        return "N/A"
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours:02d}:{mins:02d}"

def find_direct_flights(schedule_df, origin, destination, date, check_next_days=7):
    """Find all direct flights for a given route on a specific date or next available days"""
    # Filter for the specific route
    route_flights = schedule_df[
        (schedule_df['Orig'] == origin) & 
        (schedule_df['Dest'] == destination)
    ].copy()
    
    # Try to find flights for the requested date and next available days
    results = []
    
    for day_offset in range(check_next_days + 1):
        check_date = date + timedelta(days=day_offset)
        available_flights = []
        
        for idx, flight in route_flights.iterrows():
            # Check if flight operates on this day of week
            if is_flight_available_on_date(flight['DOW(S)'], check_date):
                # Check if date is within flight's operating period
                if pd.notna(flight['Start Date (LZ)']) and pd.notna(flight['End Date (LZ)']):
                    if flight['Start Date (LZ)'].date() <= check_date.date() <= flight['End Date (LZ)'].date():
                        flight_copy = flight.copy()
                        flight_copy['flight_date'] = check_date
                        available_flights.append(flight_copy)
        
        if available_flights:
            results.append({
                'date': check_date,
                'flights': available_flights,
                'days_from_requested': day_offset
            })
    
    return results

def build_connection_network(schedule_df, date):
    """Build a dictionary of all available flights on a given date for routing"""
    network = {}
    
    for idx, flight in schedule_df.iterrows():
        # Check if flight operates on this date
        if is_flight_available_on_date(flight['DOW(S)'], date):
            if pd.notna(flight['Start Date (LZ)']) and pd.notna(flight['End Date (LZ)']):
                if flight['Start Date (LZ)'].date() <= date.date() <= flight['End Date (LZ)'].date():
                    origin = flight['Orig']
                    dest = flight['Dest']
                    
                    if origin not in network:
                        network[origin] = []
                    
                    dep_time = parse_time_to_minutes(flight['Sched Out(L)'])
                    arr_time = parse_time_to_minutes(flight['Sched In(L)'])
                    
                    if dep_time is not None and arr_time is not None:
                        # Handle overnight flights
                        if arr_time < dep_time:
                            arr_time += 24 * 60  # Add 24 hours
                        
                        network[origin].append({
                            'destination': dest,
                            'departure': dep_time,
                            'arrival': arr_time,
                            'dep_str': flight['Sched Out(L)'],
                            'arr_str': flight['Sched In(L)'],
                            'duration_str': flight['Blkhr'],
                            'flight_num': f"{flight.get('Carrier', '')}{flight.get('Flight #', '')}",
                            'duration': arr_time - dep_time
                        })
    
    return network

def find_connecting_routes(network, origin, destination, start_date, max_stops=2):
    """Find connecting flights using BFS approach with date tracking"""
    if origin not in network:
        return []
    
    # Queue: (current_airport, path, arrival_time, total_duration, current_date, route_dates)
    queue = [(origin, [origin], 0, 0, start_date, [])]
    all_routes = []
    visited = set()
    
    while queue:
        current_airport, path, last_arrival, total_duration, current_date, route_dates = queue.pop(0)
        
        # Skip if we've seen this state
        state = (current_airport, tuple(path), current_date.date())
        if state in visited:
            continue
        visited.add(state)
        
        # Check if we've reached destination
        if current_airport == destination and len(path) > 1:
            all_routes.append({
                'path': path,
                'stops': len(path) - 2,
                'total_duration': total_duration,
                'route_dates': route_dates
            })
            continue
        
        # Check stop limit
        if len(path) - 1 >= max_stops + 1:
            continue
        
        # Explore connections
        if current_airport in network:
            for flight in network[current_airport]:
                next_dest = flight['destination']
                
                # Avoid cycles
                if next_dest in path:
                    continue
                
                # For first flight or valid connection
                if len(path) == 1:
                    # First flight - can depart on the flight date
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
                    # Connection - need minimum 30 minutes layover
                    # Check if we need to take a flight on a later date
                    if flight['date'].date() > current_date.date():
                        # Flight is on a different day - add waiting time
                        days_diff = (flight['date'].date() - current_date.date()).days
                        connection_time = (days_diff * 24 * 60) + flight['departure'] - last_arrival
                    else:
                        # Same day connection
                        connection_time = flight['departure'] - last_arrival
                        if connection_time < 0:
                            # Need to take next day's flight
                            connection_time += 24 * 60
                    
                    if 30 <= connection_time <= 1440:  # 30 mins to 24 hours layover
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
    
    # Sort by total duration
    all_routes.sort(key=lambda x: x['total_duration'])
    return all_routes[:5]  # Return top 5 routes

def get_route_details(network, path, route_dates):
    """Get detailed information for a specific route path with dates"""
    legs = []
    
    for i in range(len(path) - 1):
        origin = path[i]
        dest = path[i + 1]
        flight_date = route_dates[i] if i < len(route_dates) else None
        
        # Find the flight
        if origin in network:
            for flight in network[origin]:
                if flight['destination'] == dest:
                    # Match by date if available
                    if flight_date and flight['date'].date() == flight_date.date():
                        legs.append({
                            'from': origin,
                            'to': dest,
                            'departure': flight['dep_str'],
                            'arrival': flight['arr_str'],
                            'duration': flight['duration_str'],
                            'flight': flight['flight_num'],
                            'date': flight_date.strftime('%Y-%m-%d'),
                            'day': flight_date.strftime('%A')
                        })
                        break
                    elif not flight_date:
                        # Fallback if no date info
                        legs.append({
                            'from': origin,
                            'to': dest,
                            'departure': flight['dep_str'],
                            'arrival': flight['arr_str'],
                            'duration': flight['duration_str'],
                            'flight': flight['flight_num'],
                            'date': 'N/A',
                            'day': 'N/A'
                        })
                        break
    
    return legs

# Main Application
def main():
    # Sidebar for file upload
    with st.sidebar:
        st.header("📁 Data Upload")
        uploaded_file = st.file_uploader(
            "Upload UPS Flight Schedule Excel",
            type=['xlsx', 'xls'],
            help="Upload the Excel file with 'SchedDateLocalTimeFlightSchedul' and 'Data' sheets"
        )
        
        if uploaded_file:
            st.success("✅ File uploaded successfully!")
            st.markdown("---")
            st.markdown("""
            ### 📋 Instructions:
            1. Select a route from the dropdown
            2. Choose a date for shipment
            3. Click 'Find Routes' to see options
            4. View direct or connecting flights
            """)
    
    # Main content area
    if uploaded_file:
        # Load data
        with st.spinner("Loading flight data..."):
            schedule_df, routes_df = load_data(uploaded_file)
        
        if schedule_df is not None and routes_df is not None:
            # Display basic statistics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Flights", f"{len(schedule_df):,}")
            with col2:
                st.metric("Unique Routes", f"{len(routes_df):,}")
            with col3:
                st.metric("Airports", f"{schedule_df['Orig'].nunique()}")
            with col4:
                unique_carriers = schedule_df.get('Carrier', pd.Series()).nunique()
                st.metric("Carriers", f"{unique_carriers}")
            
            st.markdown("---")
            
            # Route selection section
            st.subheader("🔍 Route Finder")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Get unique route pairs from Data sheet
                route_pairs = routes_df[['Origin Airport', 'Destination Airport']].drop_duplicates()
                route_pairs = route_pairs.dropna()
                
                # Create route options
                route_options = []
                route_dict = {}
                for idx, row in route_pairs.iterrows():
                    route_str = f"{row['Origin Airport']} → {row['Destination Airport']}"
                    route_options.append(route_str)
                    route_dict[route_str] = (row['Origin Airport'], row['Destination Airport'])
                
                selected_route = st.selectbox(
                    "Select Origin → Destination Route",
                    options=sorted(route_options),
                    help="These are the routes from your Data sheet"
                )
                
                if selected_route:
                    origin, destination = route_dict[selected_route]
                    st.info(f"Route: **{origin}** to **{destination}**")
            
            with col2:
                # Date selection
                min_date = schedule_df['Start Date (LZ)'].min()
                max_date = schedule_df['End Date (LZ)'].max()
                
                if pd.notna(min_date) and pd.notna(max_date):
                    selected_date = st.date_input(
                        "Select Shipment Date",
                        value=min_date.date(),
                        min_value=min_date.date(),
                        max_value=max_date.date(),
                        help="Choose the date for your shipment"
                    )
                    
                    # Show day of week
                    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                    day_of_week = day_names[selected_date.weekday()]
                    st.info(f"Day: **{day_of_week}**")
                else:
                    st.error("Invalid date range in data")
                    return
            
                        # Search button
            if st.button("🔍 Find Available Routes", type="primary", use_container_width=True):
                if selected_route:
                    search_date = pd.Timestamp(selected_date)
                    
                    with st.spinner(f"Searching routes from {origin} to {destination}..."):
                        # First, look for direct flights (checking current date and next 7 days)
                        direct_flight_results = find_direct_flights(schedule_df, origin, destination, search_date, check_next_days=7)
                        
                        if direct_flight_results:
                            st.success(f"✅ Found direct flights!")
                            
                            for result in direct_flight_results:
                                date_diff = result['days_from_requested']
                                date_label = "on requested date" if date_diff == 0 else f"+{date_diff} day(s) from requested"
                                
                                st.subheader(f"📅 {result['date'].strftime('%Y-%m-%d (%A)')} - {date_label}")
                                
                                for i, flight in enumerate(result['flights'], 1):
                                    with st.expander(f"✈️ Direct Flight Option {i}", expanded=(date_diff == 0 and i == 1)):
                                        col1, col2, col3, col4, col5 = st.columns(5)
                                        
                                        with col1:
                                            st.markdown("**Date**")
                                            st.markdown(f"📅 {result['date'].strftime('%Y-%m-%d')}")
                                            st.markdown(f"({result['date'].strftime('%A')})")
                                        
                                        with col2:
                                            st.markdown("**Departure**")
                                            st.markdown(f"🛫 {flight['Sched Out(L)']}")
                                            st.markdown(f"from {origin}")
                                        
                                        with col3:
                                            st.markdown("**Arrival**")
                                            st.markdown(f"🛬 {flight['Sched In(L)']}")
                                            st.markdown(f"at {destination}")
                                        
                                        with col4:
                                            st.markdown("**Duration**")
                                            st.markdown(f"⏱️ {flight['Blkhr']}")
                                        
                                        with col5:
                                            st.markdown("**Flight**")
                                            st.markdown(f"✈️ {flight.get('Carrier', '')}{flight.get('Flight #', '')}")
                                        
                                        st.markdown("---")
                                        st.markdown(f"**Route:** {origin} → {destination} (Direct)")
                                        st.info(f"**Total Travel Time:** {flight['Blkhr']}")
                        
                        else:
                            # No direct flights, look for connections
                            st.warning("No direct flights available. Searching for connecting routes...")
                            
                            # Build network for multiple dates
                            network = build_connection_network(schedule_df, search_date, check_next_days=3)
                            
                            # Find connecting routes
                            connecting_routes = find_connecting_routes(network, origin, destination, search_date, max_stops=2)
                            
                            if connecting_routes:
                                st.success(f"✅ Found {len(connecting_routes)} connecting route(s)!")
                                
                                for i, route in enumerate(connecting_routes, 1):
                                    route_str = " → ".join(route['path'])
                                    
                                    # Calculate total time including layovers
                                    total_hours = route['total_duration'] // 60
                                    total_mins = route['total_duration'] % 60
                                    
                                    # Determine date range of journey
                                    if route['route_dates']:
                                        start_date = route['route_dates'][0]
                                        end_date = route['route_dates'][-1]
                                        date_range = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}" if start_date != end_date else start_date.strftime('%Y-%m-%d')
                                    else:
                                        date_range = "Date info not available"
                                    
                                    with st.expander(f"🔄 Route Option {i}: {route_str} ({route['stops']} stop(s)) - Total: {total_hours}h {total_mins}m", 
                                                   expanded=(i == 1)):
                                        
                                        # Summary box
                                        st.info(f"""
                                        **📍 Route:** {route_str}  
                                        **📅 Journey Dates:** {date_range}  
                                        **⏱️ Total Journey Time (including layovers):** {total_hours} hours {total_mins} minutes  
                                        **🔄 Number of Stops:** {route['stops']}
                                        """)
                                        
                                        # Get route details
                                        legs = get_route_details(network, route['path'], route['route_dates'])
                                        
                                        if legs:
                                            st.markdown("### ✈️ Flight Segments:")
                                            
                                            for j, leg in enumerate(legs, 1):
                                                st.markdown(f"**Segment {j}: {leg['from']} → {leg['to']}**")
                                                
                                                col1, col2, col3, col4, col5, col6 = st.columns(6)
                                                with col1:
                                                    st.write("**Date**")
                                                    st.write(f"{leg['date']}")
                                                    st.write(f"({leg['day']})")
                                                with col2:
                                                    st.write("**Flight**")
                                                    st.write(f"{leg['flight']}")
                                                with col3:
                                                    st.write("**Departure**")
                                                    st.write(f"{leg['departure']}")
                                                with col4:
                                                    st.write("**Arrival**")
                                                    st.write(f"{leg['arrival']}")
                                                with col5:
                                                    st.write("**Duration**")
                                                    st.write(f"{leg['duration']}")
                                                with col6:
                                                    st.write("**Airports**")
                                                    st.write(f"{leg['from']} → {leg['to']}")
                                                
                                                if j < len(legs):
                                                    # Show layover time
                                                    if j < len(route['route_dates']):
                                                        current_arrival = parse_time_to_minutes(leg['arrival'])
                                                        next_departure = parse_time_to_minutes(legs[j]['departure'])
                                                        
                                                        # Calculate layover considering date change
                                                        current_date = route['route_dates'][j-1] if j-1 < len(route['route_dates']) else None
                                                        next_date = route['route_dates'][j] if j < len(route['route_dates']) else None
                                                        
                                                        if current_date and next_date:
                                                            days_diff = (next_date.date() - current_date.date()).days
                                                            if days_diff > 0:
                                                                layover = (days_diff * 24 * 60) + next_departure - current_arrival
                                                            else:
                                                                layover = next_departure - current_arrival
                                                                if layover < 0:
                                                                    layover += 24 * 60
                                                            
                                                            layover_hours = layover // 60
                                                            layover_mins = layover % 60
                                                            st.warning(f"⏳ Layover at {leg['to']}: {layover_hours}h {layover_mins}m")
                                                    st.markdown("↓")
                            else:
                                st.error(f"""
                                ❌ No routes found from {origin} to {destination} starting from {selected_date}
                                
                                **Suggestions:**
                                - Try a different date
                                - Check if both airports exist in the flight network
                                - Some routes may not have service on certain days
                                - The route might require more than 2 stops
                                """)


    
    else:
        # Welcome screen when no file is uploaded
        st.info("👈 Please upload the UPS Flight Schedule Excel file to begin")
        
        st.markdown("---")
        
        with st.expander("📖 How to Use This Dashboard"):
            st.markdown("""
            ### Required Excel Format:
            
            **Sheet 1: SchedDateLocalTimeFlightSchedul**
            - `Orig`: Origin airport code
            - `Dest`: Destination airport code  
            - `Start Date (LZ)`: Flight start date
            - `End Date (LZ)`: Flight end date
            - `Sched Out(L)`: Departure time (local)
            - `Sched In(L)`: Arrival time (local)
            - `Blkhr`: Block hours (flight duration)
            - `DOW(S)`: Days of operation (7 characters: 1=Mon, 2=Tue... 7=Sun, dots for no service)
            
            **Sheet 2: Data**
            - `Origin Airport`: Origin airport code
            - `Destination Airport`: Destination airport code
            
            ### Features:
            - ✈️ Finds direct flights when available
            - 🔄 Calculates connecting flights (up to 2 stops)
            - ⏱️ Optimizes for shortest total transit time
            - 📅 Considers day-of-week availability
            - 🕐 Ensures realistic connection times (30min - 8hrs)
            """)

if __name__ == "__main__":
    main()
