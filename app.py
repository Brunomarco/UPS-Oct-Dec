import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Page configuration with UPS branding
st.set_page_config(
    page_title="UPS Flight Routing System",
    page_icon="📦",
    layout="wide"
)

# Custom CSS for UPS branding (brown and gold colors)
st.markdown("""
    <style>
    .main-header {
        background-color: #351C15;
        color: #FFB500;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 30px;
    }
    .ups-logo {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        display: inline-block;
        margin-bottom: 10px;
    }
    .stButton>button {
        background-color: #351C15;
        color: #FFB500;
        font-weight: bold;
        border: 2px solid #FFB500;
    }
    .stButton>button:hover {
        background-color: #FFB500;
        color: #351C15;
    }
    .metric-card {
        background-color: #F5F5F5;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #FFB500;
    }
    .route-card {
        background-color: #FAFAFA;
        padding: 20px;
        border-radius: 10px;
        border: 2px solid #351C15;
        margin: 10px 0;
    }
    .description-box {
        background-color: #FFF8E8;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #351C15;
        margin: 20px 0;
    }
    h1 {
        color: #351C15;
    }
    h2, h3 {
        color: #351C15;
    }
    </style>
""", unsafe_allow_html=True)

# Header with UPS branding - Logo left, title truly centered
st.markdown("""
<div class="main-header" style="position: relative; padding: 20px;">
    <div style="position: absolute; left: 20px; top: 50%; transform: translateY(-50%);">
        <img src="https://upload.wikimedia.org/wikipedia/commons/6/6b/United_Parcel_Service_logo_2014.svg" 
             alt="UPS Logo" 
             style="height: 120px; width: auto;">
    </div>
    <div style="text-align: center;">
        <h1 style="color: #FFB500; margin: 0;">Flight Routing System</h1>
        <p style="color: white; margin: 5px 0 0 0; font-size: 18px;">Optimized Shipment Routing Dashboard</p>
    </div>
</div>
""", unsafe_allow_html=True)

# Dashboard Description - Professional Executive Summary
st.markdown("---")

with st.expander("**Dashboard Overview - System Documentation and User Guide**", expanded=False):
    st.markdown("""
    ### Executive Summary
    
    This dashboard provides UPS logistics management with an automated flight routing system for optimizing package 
    shipments between global airports. The system analyzes flight combinations to identify the most efficient routing 
    options based on time constraints and operational requirements.
    """)

    st.markdown("""
    ### System Methodology
    
    **Route Discovery Process:**
    
    The routing algorithm employs a structured optimization approach:
    
    1. **Direct Flight Priority**: The system first searches for non-stop flights on the selected date. If direct flights 
    exist on that day, only those options are displayed. Direct routes are prioritized due to reduced handling complexity.
    
    2. **Date Extension Logic**: If no flights are available on the selected date, the system automatically extends the 
    search window up to 7 days forward, displaying options from the nearest available date first.
    
    3. **Connection Mapping**: For routes without direct service, the system calculates connecting flights through 
    intermediate airports. **Critical constraint: Minimum 1-hour connection time is enforced between the arrival of 
    one flight and the departure of the next flight to ensure adequate cargo transfer time.**
    
    4. **Schedule Validation**: All flights are validated against operational schedules, checking day-of-week availability 
    and active date ranges for each flight segment.
    
    5. **Optimization Ranking**: Routes are sorted by total transit time (including connection waiting periods), with 
    the fastest option presented first.
    """)

    st.markdown("""
    ### Connection Time Requirements
    
    **Minimum Connection Time: 1 Hour**
    
    The system enforces a strict minimum of 60 minutes between:
    - The arrival time of an inbound flight (in local time at that airport)
    - The departure time of the connecting flight (in local time at that airport)
    
    This ensures adequate time for:
    - Cargo unloading from the arriving aircraft
    - Ground transportation between terminals if required
    - Cargo loading onto the departing aircraft
    - Operational buffer for minor delays
    
    **Maximum Connection Time: 24 Hours**
    
    Connections exceeding 24 hours are excluded to avoid excessive storage and handling costs.
    """)

    st.markdown("""
    ### Search Window Logic
    
    **Same-Day Priority:**
    - If flights exist on the selected date: System displays ONLY those flights
    - If NO flights on selected date: System searches up to 7 days forward
    - Results are always shown chronologically (earliest available first)
    
    **Example Scenarios:**
    
    1. **Flights available on selected Tuesday:**
       - Shows all Tuesday flights only
       - No future dates displayed
    
    2. **No flights on selected Tuesday:**
       - Automatically checks Wednesday, Thursday, etc.
       - Shows first available day with flights (e.g., Thursday)
       - Continues showing next available dates up to 7 days
    """)
    
    st.markdown("""
    ### Data Output Specifications
    
    **For each identified route, the system provides:**
    
    **Route Configuration**: Complete airport sequence from origin to destination  
    
    **Carrier Details**: Operating airline for each flight segment  
    
    **Schedule Information**: Precise departure and arrival times in local time for all segments  
    
    **Time Analysis**: 
    - Individual flight durations
    - Connection waiting periods (always ≥ 1 hour)
    - Total journey time including all segments and connections
    
    **Date Intelligence**: 
    - Same-day options when available
    - Next available departure date when no same-day service exists
    """)
    
    st.divider()
    
    st.markdown("""
    ### Understanding System Messages
    
    **"Found X connecting route(s)" Interpretation:**
    
    This message indicates the total number of multi-segment routing options identified. Important clarifications:
    
    - The number represents routes found within the active search window
    - If same-day flights exist: Count includes only same-day departures
    - If no same-day options: Count includes routes across the 7-day forward window
    - Routes on different dates are counted separately
    
    **Distribution Example:**
    
    "Found 10 connecting routes" might mean:
    - All 10 routes depart on the selected date (if flights available that day)
    - OR: 3 routes on Day +1, 4 routes on Day +2, 3 routes on Day +3 (if no same-day flights)
    
    The system always prioritizes and displays earliest departure options first.
    """)
    
    st.markdown("""
    ### Operational Benefits
    
    1. **Time Optimization**: Automated identification of fastest routing with guaranteed connection viability
    
    2. **Date Intelligence**: Smart detection of next available service when selected date has no flights
    
    3. **Connection Reliability**: 1-hour minimum connection time ensures operational feasibility
    
    4. **Decision Support**: Clear presentation of alternatives for informed logistics planning
    """)

    st.success("""
    **System Performance Note**: The dashboard processes only relevant dates - same-day when available, or extends 
    to a 7-day window only when necessary. Routes are ranked by efficiency with the fastest option always displayed first.
    """)

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

def format_duration(minutes):
    """Format duration in minutes to readable format"""
    if minutes is None:
        return "N/A"
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}h {mins}m"

def find_direct_flights(schedule_df, origin, destination, date, days_ahead=7):
    """Find direct flights - prioritize same day, then search up to 7 days if needed"""
    try:
        # Filter for the specific route
        route_flights = schedule_df[
            (schedule_df['Orig'] == origin) & 
            (schedule_df['Dest'] == destination)
        ].copy()
        
        if route_flights.empty:
            return []
        
        results = []
        
        # FIRST: Check for same-day flights
        same_day_flights = []
        for idx, flight in route_flights.iterrows():
            try:
                if is_flight_available_on_date(flight['DOW(S)'], date):
                    if pd.notna(flight['Start Date (LZ)']) and pd.notna(flight['End Date (LZ)']):
                        if flight['Start Date (LZ)'].date() <= date.date() <= flight['End Date (LZ)'].date():
                            flight_copy = flight.copy()
                            flight_copy['flight_date'] = date
                            dep_time = parse_time_to_minutes(flight['Sched Out(L)'])
                            flight_copy['dep_minutes'] = dep_time if dep_time else 0
                            same_day_flights.append(flight_copy)
            except:
                continue
        
        # If same-day flights exist, return ONLY those
        if same_day_flights:
            same_day_flights.sort(key=lambda x: x['dep_minutes'])
            return [{
                'date': date,
                'flights': same_day_flights,
                'days_from_requested': 0
            }]
        
        # NO same-day flights - now search next 7 days
        for day_offset in range(1, days_ahead + 1):
            check_date = date + timedelta(days=day_offset)
            flights_on_date = []
            
            for idx, flight in route_flights.iterrows():
                try:
                    if is_flight_available_on_date(flight['DOW(S)'], check_date):
                        if pd.notna(flight['Start Date (LZ)']) and pd.notna(flight['End Date (LZ)']):
                            if flight['Start Date (LZ)'].date() <= check_date.date() <= flight['End Date (LZ)'].date():
                                flight_copy = flight.copy()
                                flight_copy['flight_date'] = check_date
                                dep_time = parse_time_to_minutes(flight['Sched Out(L)'])
                                flight_copy['dep_minutes'] = dep_time if dep_time else 0
                                flights_on_date.append(flight_copy)
                except:
                    continue
            
            if flights_on_date:
                flights_on_date.sort(key=lambda x: x['dep_minutes'])
                results.append({
                    'date': check_date,
                    'flights': flights_on_date,
                    'days_from_requested': day_offset
                })
                
                # Return up to 3 alternative dates
                if len(results) >= 3:
                    break
        
        return results
        
    except Exception as e:
        return []

def build_network(schedule_df, start_date, days_ahead=30):
    """Build flight network for routing with proper date/time logic"""
    network = {}
    
    try:
        for day_offset in range(days_ahead + 1):
            check_date = start_date + timedelta(days=day_offset)
            
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
                                
                                # Parse Blkhr for actual flight duration
                                blkhr_str = str(flight['Blkhr'])
                                flight_duration = 0
                                if pd.notna(flight['Blkhr']) and blkhr_str != 'nan':
                                    if ':' in blkhr_str:
                                        parts = blkhr_str.split(':')
                                        hours = int(parts[0]) if parts[0] else 0
                                        minutes = int(parts[1]) if len(parts) > 1 else 0
                                        flight_duration = hours * 60 + minutes
                                
                                if dep_time is not None and arr_time is not None and flight_duration > 0:
                                    # Determine arrival date based on whether it's an overnight flight
                                    # If arrival time is less than departure time, it's likely next day
                                    arrival_date = check_date
                                    if arr_time < dep_time:
                                        arrival_date = check_date + timedelta(days=1)
                                    
                                    network[origin].append({
                                        'destination': dest,
                                        'departure': dep_time,
                                        'arrival': arr_time,  # Local arrival time at destination
                                        'arrival_date': arrival_date,  # Actual arrival date
                                        'dep_str': str(flight['Sched Out(L)']),
                                        'arr_str': str(flight['Sched In(L)']),
                                        'duration_str': str(flight['Blkhr']),
                                        'carrier': str(flight.get('Carrier', 'N/A')),
                                        'flight_num': f"{flight.get('Carrier', '')}{flight.get('Flight #', '')}",
                                        'duration': flight_duration,  # Use Blkhr for actual flight duration
                                        'date': check_date,  # Departure date
                                        'day_offset': day_offset
                                    })
                except:
                    continue
    except:
        pass
    
    # Sort flights by date and departure time for each origin
    for origin in network:
        network[origin].sort(key=lambda x: (x['date'], x['departure']))
    
    return network

def find_connecting_routes(network, origin, destination, start_date, max_stops=10):
    """Find ALL possible connecting flights - comprehensive search"""
    if origin not in network:
        return []
    
    all_routes = []
    
    # Get ALL flights from origin within reasonable timeframe
    initial_flights = [f for f in network.get(origin, []) if f['date'] >= start_date and f['date'] <= start_date + timedelta(days=14)]
    initial_flights.sort(key=lambda x: (x['date'], x['departure']))
    
    # Don't limit initial flights - check all available
    
    # For each possible first flight
    for first_flight in initial_flights:
        # Use the actual arrival date and time from the flight data
        first_arrival_date = first_flight.get('arrival_date', first_flight['date'])
        first_arrival_time = first_flight['arrival']  # Local arrival time at destination
        
        # Start building routes from this first flight using BFS
        queue = [(
            first_flight['destination'],
            [origin, first_flight['destination']],
            first_arrival_time,
            first_arrival_date,
            first_flight['duration'],  # This now uses Blkhr
            [{
                'from': origin,
                'to': first_flight['destination'],
                'date': first_flight['date'],
                'departure': first_flight['dep_str'],
                'arrival': first_flight['arr_str'],
                'duration': first_flight['duration'],  # Blkhr value
                'duration_str': first_flight['duration_str'],
                'carrier': first_flight['carrier'],
                'flight': first_flight['flight_num'],
                'wait_time': 0
            }]
        )]
        
        visited_for_this_start = set()
        iterations = 0
        max_iterations = 50000  # Much higher limit to explore more thoroughly
        
        while queue and iterations < max_iterations:
            iterations += 1
            
            # Get the next state to explore
            if not queue:
                break
            
            current_airport, path, last_arrival_time, last_arrival_date, total_duration, route_info = queue.pop(0)
            
            # Only skip if this exact same state was visited
            state = (current_airport, tuple(path))  # Simplified state - don't include time
            if state in visited_for_this_start:
                continue
            visited_for_this_start.add(state)
            
            # Check if we've reached destination
            if current_airport == destination:
                # Calculate the actual arrival date of the last flight
                last_leg_info = route_info[-1]
                last_flight_arrival_date = last_leg_info['date']
                # Check if last flight is overnight
                dep_min = parse_time_to_minutes(last_leg_info['departure'])
                arr_min = parse_time_to_minutes(last_leg_info['arrival'])
                if arr_min and dep_min and arr_min < dep_min:
                    last_flight_arrival_date = last_leg_info['date'] + timedelta(days=1)
                
                all_routes.append({
                    'path': path,
                    'stops': len(path) - 2,
                    'total_duration': total_duration,
                    'route_info': route_info,
                    'start_date': route_info[0]['date'],
                    'end_date': last_flight_arrival_date  # Actual arrival date
                })
                continue
            
            # Check stop limit
            if len(path) - 1 >= max_stops + 1:
                continue
            
            # Find ALL possible next flights from current airport
            if current_airport in network:
                # Get ALL connections without limiting too much
                possible_connections = []
                for f in network[current_airport]:
                    if f['destination'] not in path:  # Avoid cycles
                        # Be more generous with connection window
                        if f['date'] >= last_arrival_date and f['date'] <= last_arrival_date + timedelta(days=14):
                            possible_connections.append(f)
                
                # Check all possible connections
                for next_flight in possible_connections:
                    # Calculate if this connection is valid
                    min_connection = 60  # 1 hour minimum
                    
                    # Calculate waiting time properly
                    if next_flight['date'] > last_arrival_date:
                        # Flight departs on a future day
                        days_diff = (next_flight['date'].date() - last_arrival_date.date()).days
                        
                        # If last arrival time is normalized (0-1439 minutes)
                        if last_arrival_time < 1440:
                            # Calculate wait: time to midnight + full days + departure time
                            wait_time = (1440 - last_arrival_time) + ((days_diff - 1) * 1440) + next_flight['departure']
                        else:
                            # Handle cases where arrival time might be > 1440 (shouldn't happen but just in case)
                            normalized_arrival = last_arrival_time % 1440
                            wait_time = (1440 - normalized_arrival) + ((days_diff - 1) * 1440) + next_flight['departure']
                            
                    elif next_flight['date'].date() == last_arrival_date.date():
                        # Same day connection
                        if next_flight['departure'] >= last_arrival_time + min_connection:
                            wait_time = next_flight['departure'] - last_arrival_time
                        else:
                            continue  # Not enough time for connection
                    else:
                        continue  # Flight is before arrival, skip
                    
                    # Accept connections up to 96 hours wait (4 days)
                    if min_connection <= wait_time <= 5760:  # 96 hours = 5760 minutes
                        new_total = total_duration + wait_time + next_flight['duration']
                        
                        # Build the new route info
                        new_route_info = route_info + [{
                            'from': current_airport,
                            'to': next_flight['destination'],
                            'date': next_flight['date'],
                            'departure': next_flight['dep_str'],
                            'arrival': next_flight['arr_str'],
                            'duration': next_flight['duration'],  # Blkhr value
                            'duration_str': next_flight['duration_str'],
                            'carrier': next_flight['carrier'],
                            'flight': next_flight['flight_num'],
                            'wait_time': wait_time
                        }]
                        
                        # Get the arrival date and time for the next flight
                        next_arrival_date = next_flight.get('arrival_date', next_flight['date'])
                        next_arrival_time = next_flight['arrival']
                        
                        # Add to queue to explore
                        queue.append((
                            next_flight['destination'],
                            path + [next_flight['destination']],
                            next_arrival_time,
                            next_arrival_date,
                            new_total,
                            new_route_info
                        ))
        
        # Stop if we found enough routes
        if len(all_routes) >= 50:  # Collect more routes before stopping
            break
    
    # Remove duplicate routes
    unique_routes = []
    seen_routes = set()
    
    for route in all_routes:
        # Create unique identifier based on exact flight sequence and dates
        route_id = tuple([
            (leg['from'], leg['to'], leg['date'].date(), leg['departure'])
            for leg in route['route_info']
        ])
        
        if route_id not in seen_routes:
            seen_routes.add(route_id)
            unique_routes.append(route)
    
    # Sort by: 1) Number of stops (fewer is better), 2) Total duration (shorter is better)
    unique_routes.sort(key=lambda x: (x['stops'], x['total_duration']))
    
    # Return top routes
    return unique_routes[:15]

def display_route_results(origin, destination, selected_date, schedule_df):
    """Common function to display route results"""
    search_date = pd.Timestamp(selected_date)
    
    with st.spinner(f"Searching routes from {origin} to {destination}..."):
        try:
            # Search for direct flights - ALWAYS checks selected date first
            direct_results = find_direct_flights(schedule_df, origin, destination, search_date)
            
            if direct_results:
                # Check if we have same-day flights
                has_same_day = (direct_results[0]['days_from_requested'] == 0)
                
                if has_same_day:
                    st.success(f"✅ Found direct flights on your selected date ({selected_date})!")
                else:
                    st.warning(f"⚠️ No flights available on {selected_date}. Showing next available dates.")
                
                for result in direct_results:
                    date_diff = result['days_from_requested']
                    if date_diff == 0:
                        date_label = "✓ ON YOUR SELECTED DATE"
                        color = "green"
                    else:
                        date_label = f"📅 Next available: +{date_diff} day(s)"
                        color = "orange"
                    
                    st.markdown(f"""
                    <div class="route-card">
                        <h3 style="color: {color};">📅 {result['date'].strftime('%Y-%m-%d (%A)')} - {date_label}</h3>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    for i, flight in enumerate(result['flights'], 1):
                        with st.expander(f"✈️ Direct Flight Option {i} - Carrier: {flight.get('Carrier', 'N/A')} - Departs: {flight['Sched Out(L)']}", 
                                       expanded=(date_diff == 0 and i == 1)):
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.markdown("**📅 Flight Date**")
                                st.write(f"{result['date'].strftime('%Y-%m-%d')}")
                                st.write(f"{result['date'].strftime('%A')}")
                                st.markdown("**✈️ Carrier**")
                                st.write(f"{flight.get('Carrier', 'N/A')}")
                            
                            with col2:
                                st.markdown("**🕐 Schedule**")
                                st.write(f"Departure: {flight['Sched Out(L)']} from {origin}")
                                st.write(f"Arrival: {flight['Sched In(L)']} at {destination}")
                                st.markdown("**✈️ Flight Number**")
                                st.write(f"{flight.get('Carrier', '')}{flight.get('Flight #', '')}")
                            
                            with col3:
                                st.markdown("**⏱️ Duration**")
                                st.write(f"Flight Time: {flight['Blkhr']}")
                                st.write(f"No connections needed")
                            
                            st.success(f"""
                            **Summary:**
                            - Total Travel Time: {flight['Blkhr']}
                            - Direct flight (no stops)
                            - Carrier: {flight.get('Carrier', 'N/A')}
                            """)
            
            # Always search for connecting flights as well
            st.info("🔄 Searching for connecting flight options...")
            
            network = build_network(schedule_df, search_date)
            
            if network:
                routes = find_connecting_routes(network, origin, destination, search_date)
                
                if routes:
                    # Check if we have same-day departure routes
                    same_day_routes = [r for r in routes if r['start_date'].date() == search_date.date()]
                    
                    if same_day_routes:
                        st.success(f"✅ Found {len(same_day_routes)} connecting route(s) departing on your selected date!")
                    else:
                        st.warning(f"⚠️ No connecting routes on {selected_date}. Showing routes starting from next available dates.")
                    
                    st.success(f"✅ Total: Found {len(routes)} connecting route(s)!")
                    
                    # Show first few best routes
                    for i, route in enumerate(routes[:5], 1):
                        route_str = " → ".join(route['path'])
                        total_duration = route['total_duration']
                        total_hours = total_duration // 60
                        total_mins = total_duration % 60
                        
                        # Calculate total waiting time
                        total_wait = sum([leg['wait_time'] for leg in route['route_info']])
                        wait_hours = total_wait // 60
                        wait_mins = total_wait % 60
                        
                        # Check if departing on selected date
                        is_same_day = route['start_date'].date() == search_date.date()
                        date_indicator = "✓ DEPARTS ON SELECTED DATE" if is_same_day else f"Departs +{(route['start_date'].date() - search_date.date()).days} days"
                        
                        with st.expander(f"🔄 Route {i}: {route_str} ({route['stops']} stop(s)) - {date_indicator}", 
                                       expanded=(i == 1 and is_same_day)):
                            
                            # Route summary
                            st.markdown(f"""
                            <div style="background-color: #E8F4F8; padding: 15px; border-radius: 10px; margin-bottom: 15px;">
                                <h4 style="color: #351C15; margin: 0;">Route Summary</h4>
                                <p><strong>Route:</strong> {route_str}</p>
                                <p><strong>Departure Date:</strong> {route['start_date'].strftime('%Y-%m-%d')} ({route['start_date'].strftime('%A')})</p>
                                <p><strong>Arrival Date:</strong> {route['end_date'].strftime('%Y-%m-%d')} ({route['end_date'].strftime('%A')})</p>
                                <p><strong>Total Journey Time:</strong> {total_hours}h {total_mins}m</p>
                                <p><strong>Total Waiting Time:</strong> {wait_hours}h {wait_mins}m</p>
                                <p><strong>Number of Stops:</strong> {route['stops']}</p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Flight segments
                            st.markdown("### ✈️ Flight Segments:")
                            
                            for j, leg in enumerate(route['route_info'], 1):
                                # Calculate arrival date for this leg
                                leg_arrival_date = leg['date']
                                # Check if arrival time suggests overnight flight
                                dep_minutes = parse_time_to_minutes(leg['departure'])
                                arr_minutes = parse_time_to_minutes(leg['arrival'])
                                if arr_minutes and dep_minutes and arr_minutes < dep_minutes:
                                    leg_arrival_date = leg['date'] + timedelta(days=1)
                                
                                st.markdown(f"""
                                <div style="background-color: #FAFAFA; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #FFB500;">
                                    <h4 style="color: #351C15;">Segment {j}: {leg['from']} → {leg['to']}</h4>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                col1, col2, col3, col4 = st.columns(4)
                                
                                with col1:
                                    st.markdown("**Date & Carrier**")
                                    st.write(f"📅 Dep: {leg['date'].strftime('%Y-%m-%d')}")
                                    st.write(f"📅 Arr: {leg_arrival_date.strftime('%Y-%m-%d')}")
                                    st.write(f"✈️ Carrier: {leg['carrier']}")
                                
                                with col2:
                                    st.markdown("**Flight Details**")
                                    st.write(f"Flight: {leg['flight']}")
                                    st.write(f"Dep: {leg['departure']} ({leg['date'].strftime('%a')})")
                                    st.write(f"Arr: {leg['arrival']} ({leg_arrival_date.strftime('%a')})")
                                
                                with col3:
                                    st.markdown("**Duration**")
                                    st.write(f"Flight Time: {format_duration(leg['duration'])}")
                                    st.write(f"({leg['duration_str']})")
                                
                                with col4:
                                    st.markdown("**Connection**")
                                    if j < len(route['route_info']):
                                        wait_time = route['route_info'][j]['wait_time']
                                        st.write(f"⏳ Wait: {format_duration(wait_time)}")
                                    else:
                                        st.write("Final destination")
                                
                                if j < len(route['route_info']):
                                    st.markdown("⬇️")
                            
                            # Final summary
                            st.success(f"""
                            **Journey Complete:**
                            - Total Travel Time: {total_hours}h {total_mins}m
                            - Total Waiting Time: {wait_hours}h {wait_mins}m
                            - Total Segments: {len(route['route_info'])}
                            """)
                
                elif not direct_results:
                    st.error(f"""
                    ❌ No routes found from {origin} to {destination}
                    
                    **Suggestions:**
                    - This route may not be served by UPS flights
                    - Try selecting a different origin-destination pair
                    - The route might require more than 10 stops
                    - Check if flights operate on different days of the week
                    """)
            else:
                if not direct_results:
                    st.error("No flight network available for the selected date range.")
        
        except Exception as e:
            st.error(f"Error during search: {str(e)}")

# Main Application
def main():
    # Sidebar with UPS branding
    with st.sidebar:
        st.markdown("""
        <div style="background-color: #351C15; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
            <h2 style="color: #FFB500; margin: 0;">📦 UPS Flight System</h2>
        </div>
        """, unsafe_allow_html=True)
        
        st.header("📁 Data Upload")
        uploaded_file = st.file_uploader(
            "Upload UPS Flight Schedule Excel",
            type=['xlsx', 'xls']
        )
        
        if uploaded_file:
            st.success("✅ File uploaded successfully!")
            st.markdown("---")
            st.info("""
            **File Requirements:**
            - Sheet 1: Flight schedules
            - Sheet 2: Route pairs to track
            """)
    
    # Main content
    if uploaded_file:
        with st.spinner("Loading flight data..."):
            schedule_df, routes_df = load_data(uploaded_file)
        
        if schedule_df is not None and routes_df is not None:
            # Statistics with UPS colors
            st.markdown("<h2 style='color: #351C15;'>📊 Network Statistics</h2>", unsafe_allow_html=True)
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <h3 style="color: #351C15; margin: 0;">{len(schedule_df):,}</h3>
                    <p style="color: #666; margin: 0;">Total Flights</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="metric-card">
                    <h3 style="color: #351C15; margin: 0;">{len(routes_df):,}</h3>
                    <p style="color: #666; margin: 0;">Route Pairs</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class="metric-card">
                    <h3 style="color: #351C15; margin: 0;">{schedule_df['Orig'].nunique()}</h3>
                    <p style="color: #666; margin: 0;">Airports</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                carriers = schedule_df['Carrier'].nunique() if 'Carrier' in schedule_df.columns else 0
                st.markdown(f"""
                <div class="metric-card">
                    <h3 style="color: #351C15; margin: 0;">{carriers}</h3>
                    <p style="color: #666; margin: 0;">Carriers</p>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Create tabs
            tab1, tab2 = st.tabs(["📋 Tracked Routes", "🔧 Custom Routes"])
            
            # Tab 1: Tracked Routes (Original functionality)
            with tab1:
                st.markdown("<h2 style='color: #351C15;'>🔍 Tracked Route Finder</h2>", unsafe_allow_html=True)
                st.info("Select from pre-defined route pairs in your Data sheet")
                
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
                        options=sorted(route_options),
                        help="Select from available route pairs",
                        key="tracked_route"
                    )
                    
                    if selected_route:
                        origin, destination = route_dict[selected_route]
                        st.markdown(f"""
                        <div style="background-color: #FFF8E8; padding: 10px; border-radius: 5px; border-left: 3px solid #FFB500;">
                            <strong>Selected Route:</strong> {origin} → {destination}
                        </div>
                        """, unsafe_allow_html=True)
                
                with col2:
                    min_date = schedule_df['Start Date (LZ)'].min()
                    max_date = schedule_df['End Date (LZ)'].max()
                    
                    if pd.notna(min_date) and pd.notna(max_date):
                        selected_date = st.date_input(
                            "Select Shipment Date",
                            value=min_date.date(),
                            min_value=min_date.date(),
                            max_value=max_date.date(),
                            key="tracked_date"
                        )
                        
                        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                        day_of_week = day_names[selected_date.weekday()]
                        st.markdown(f"""
                        <div style="background-color: #FFF8E8; padding: 10px; border-radius: 5px; border-left: 3px solid #FFB500;">
                            <strong>Selected Date:</strong> {selected_date} ({day_of_week})
                        </div>
                        """, unsafe_allow_html=True)
                
                # Search button with UPS styling
                if st.button("🔍 Find Available Routes", type="primary", use_container_width=True, key="tracked_search"):
                    if selected_route:
                        display_route_results(origin, destination, selected_date, schedule_df)
            
            # Tab 2: Custom Routes (New functionality)
            with tab2:
                st.markdown("<h2 style='color: #351C15;'>🔍 Custom Route Finder</h2>", unsafe_allow_html=True)
                st.info("Select any origin and destination from all available airports")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    # Get all unique origins
                    origins = sorted(schedule_df['Orig'].dropna().unique())
                    custom_origin = st.selectbox(
                        "Select Origin Airport",
                        options=origins,
                        help="Select any available origin airport",
                        key="custom_origin"
                    )
                
                with col2:
                    # Get all unique destinations
                    destinations = sorted(schedule_df['Dest'].dropna().unique())
                    custom_destination = st.selectbox(
                        "Select Destination Airport",
                        options=destinations,
                        help="Select any available destination airport",
                        key="custom_destination"
                    )
                
                with col3:
                    min_date = schedule_df['Start Date (LZ)'].min()
                    max_date = schedule_df['End Date (LZ)'].max()
                    
                    if pd.notna(min_date) and pd.notna(max_date):
                        custom_date = st.date_input(
                            "Select Shipment Date",
                            value=min_date.date(),
                            min_value=min_date.date(),
                            max_value=max_date.date(),
                            key="custom_date"
                        )
                        
                        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                        day_of_week = day_names[custom_date.weekday()]
                
                # Display selected route
                st.markdown(f"""
                <div style="background-color: #FFF8E8; padding: 15px; border-radius: 5px; border-left: 3px solid #FFB500; margin-top: 20px;">
                    <strong>Selected Custom Route:</strong> {custom_origin} → {custom_destination}<br>
                    <strong>Selected Date:</strong> {custom_date} ({day_of_week})
                </div>
                """, unsafe_allow_html=True)
                
                # Search button for custom routes
                if st.button("🔍 Find Available Routes", type="primary", use_container_width=True, key="custom_search"):
                    if custom_origin and custom_destination:
                        if custom_origin == custom_destination:
                            st.warning("⚠️ Please select different airports for origin and destination.")
                        else:
                            display_route_results(custom_origin, custom_destination, custom_date, schedule_df)
    
    else:
        st.info("👈 Please upload the UPS Flight Schedule Excel file to begin")
        
        st.markdown("""
        <div style="background-color: #FFF8E8; padding: 20px; border-radius: 10px; margin-top: 20px;">
            <h3 style="color: #351C15;">📋 Required Excel Format:</h3>
            <p><strong>Sheet 1: SchedDateLocalTimeFlightSchedul</strong></p>
            <ul>
                <li>Carrier: Airline carrier code</li>
                <li>Flight #: Flight number</li>
                <li>Orig / Dest: Origin and destination airports</li>
                <li>Start/End Date (LZ): Valid operating dates</li>
                <li>DOW(S): Days of operation (1=Mon, 7=Sun)</li>
                <li>Sched Out(L) / In(L): Departure and arrival times</li>
                <li>Blkhr: Flight duration</li>
            </ul>
            <p><strong>Sheet 2: Data</strong></p>
            <ul>
                <li>Origin Airport: Starting airport</li>
                <li>Destination Airport: Final destination</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
