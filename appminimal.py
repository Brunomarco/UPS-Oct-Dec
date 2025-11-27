import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import heapq

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
    .contact-warning {
        background-color: #FFF3CD;
        border: 2px solid #FF6B00;
        padding: 20px;
        border-radius: 10px;
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
    
    1. **Earliest Arrival Priority**: The system searches for routes that arrive earliest at the destination, 
    not just routes that depart first. This ensures optimal delivery times.
    
    2. **Minimum Stops Alternative**: The system also identifies routes with the fewest connections,
    which may be preferable for sensitive shipments even if arrival is slightly later.
    
    3. **Direct Flight Priority**: The system first searches for non-stop flights on the selected date. If direct flights 
    exist on that day, only those options are displayed. Direct routes are prioritized due to reduced handling complexity.
    
    4. **Date Extension Logic**: If no flights are available on the selected date, the system automatically extends the 
    search window up to 7 days forward, displaying options from the nearest available date first.
    
    5. **Connection Mapping**: For routes without direct service, the system calculates connecting flights through 
    intermediate airports. **Critical constraint: Minimum 1-hour connection time is enforced between the arrival of 
    one flight and the departure of the next flight to ensure adequate cargo transfer time.**
    
    6. **Complex Route Handling**: Routes requiring 5 or more stops trigger a recommendation to contact the logistics
    team for personalized assistance.
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
    - Results are always shown by earliest arrival time first
    
    **Example Scenarios:**
    
    1. **Flights available on selected Tuesday:**
       - Shows all Tuesday flights only
       - Sorted by earliest arrival at destination
    
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
    
    **Routes with Fewer Stops**: 
    - Alternative routes optimized for minimal connections
    - Useful when simpler routing is preferred over fastest arrival
    """)
    
    st.divider()
    
    st.markdown("""
    ### Understanding System Messages
    
    **"Found X connecting route(s)" Interpretation:**
    
    This message indicates the total number of multi-segment routing options identified.
    
    **Routes with 5+ Stops:**
    
    If a route requires 5 or more stops, a prominent message will appear recommending to contact 
    the logistics team for personalized assistance, as such complex routing may benefit from 
    specialized planning.
    """)

    st.success("""
    **System Performance Note**: The dashboard processes only relevant dates - same-day when available, or extends 
    to a 7-day window only when necessary. Routes are ranked by earliest arrival time with the fastest-arriving option always displayed first.
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
        all_flights_with_arrival = []
        
        # FIRST: Check for same-day flights AND next 3 days to compare arrivals
        for day_offset in range(0, 4):  # Check selected day + next 3 days
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
                                arr_time = parse_time_to_minutes(flight['Sched In(L)'])
                                flight_copy['dep_minutes'] = dep_time if dep_time else 0
                                flight_copy['arr_minutes'] = arr_time if arr_time else 0
                                
                                # Calculate actual arrival datetime for comparison
                                arrival_date = check_date
                                if arr_time and dep_time and arr_time < dep_time:
                                    arrival_date = check_date + timedelta(days=1)
                                
                                # Store arrival datetime for comparison
                                if arr_time is not None:
                                    flight_copy['arrival_datetime'] = arrival_date.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(minutes=arr_time)
                                else:
                                    flight_copy['arrival_datetime'] = arrival_date
                                
                                flight_copy['day_offset'] = day_offset
                                flights_on_date.append(flight_copy)
                                all_flights_with_arrival.append(flight_copy)
                except:
                    continue
            
            if flights_on_date and day_offset == 0:
                # Sort same-day flights by ARRIVAL TIME (earliest arrival first)
                flights_on_date.sort(key=lambda x: x['arrival_datetime'])
                results.append({
                    'date': check_date,
                    'flights': flights_on_date,
                    'days_from_requested': day_offset,
                    'arrives_earlier': False
                })
        
        # Now check if any flights from days 1-3 arrive EARLIER than same-day flights
        if results and len(results) > 0:  # We have same-day flights
            same_day_flights = results[0]['flights']
            earliest_same_day_arrival = min(f['arrival_datetime'] for f in same_day_flights)
            
            # Check next 3 days for earlier arrivals
            for day_offset in range(1, 4):
                check_date = date + timedelta(days=day_offset)
                earlier_flights = [f for f in all_flights_with_arrival 
                                  if f['day_offset'] == day_offset 
                                  and f['arrival_datetime'] < earliest_same_day_arrival]
                
                if earlier_flights:
                    # Sort by arrival time
                    earlier_flights.sort(key=lambda x: x['arrival_datetime'])
                    results.append({
                        'date': check_date,
                        'flights': earlier_flights,
                        'days_from_requested': day_offset,
                        'arrives_earlier': True  # Flag these as arriving earlier
                    })
        
        # If no same-day flights, search normally for next available
        if not results:
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
                                    arr_time = parse_time_to_minutes(flight['Sched In(L)'])
                                    flight_copy['dep_minutes'] = dep_time if dep_time else 0
                                    flight_copy['arr_minutes'] = arr_time if arr_time else 0
                                    
                                    # Calculate actual arrival datetime
                                    arrival_date = check_date
                                    if arr_time and dep_time and arr_time < dep_time:
                                        arrival_date = check_date + timedelta(days=1)
                                    
                                    if arr_time is not None:
                                        flight_copy['arrival_datetime'] = arrival_date.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(minutes=arr_time)
                                    else:
                                        flight_copy['arrival_datetime'] = arrival_date
                                    
                                    flights_on_date.append(flight_copy)
                    except:
                        continue
                
                if flights_on_date:
                    # Sort by arrival time (earliest first)
                    flights_on_date.sort(key=lambda x: x['arrival_datetime'])
                    results.append({
                        'date': check_date,
                        'flights': flights_on_date,
                        'days_from_requested': day_offset,
                        'arrives_earlier': False
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
    """
    Find ALL possible connecting flights using priority queue.
    Returns two lists:
    1. Routes sorted by earliest arrival time
    2. Routes sorted by fewest stops (for simpler routing options)
    """
    if origin not in network:
        return [], []
    
    all_routes = []
    
    # Get flights from origin within selected date + next 3 days for comparison
    initial_flights = [f for f in network.get(origin, []) 
                      if f['date'] >= start_date 
                      and f['date'] <= start_date + timedelta(days=3)]
    initial_flights.sort(key=lambda x: (x['date'], x['departure']))
    
    # Use a priority queue that prioritizes by NUMBER OF STOPS first
    # This ensures we find shorter routes first
    # Priority: (num_stops, arrival_datetime_timestamp, counter)
    counter = 0
    
    for first_flight in initial_flights:
        first_arrival_date = first_flight.get('arrival_date', first_flight['date'])
        first_arrival_time = first_flight['arrival']
        
        # Calculate arrival datetime
        if first_arrival_time is not None:
            first_arrival_datetime = first_arrival_date.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(minutes=first_arrival_time)
        else:
            first_arrival_datetime = first_arrival_date
        
        # Priority queue entry: (num_stops, arrival_timestamp, counter, state)
        initial_state = (
            first_flight['destination'],
            [origin, first_flight['destination']],
            first_arrival_time,
            first_arrival_date,
            first_flight['duration'],
            [{
                'from': origin,
                'to': first_flight['destination'],
                'date': first_flight['date'],
                'departure': first_flight['dep_str'],
                'arrival': first_flight['arr_str'],
                'duration': first_flight['duration'],
                'duration_str': first_flight['duration_str'],
                'carrier': first_flight['carrier'],
                'flight': first_flight['flight_num'],
                'wait_time': 0
            }],
            first_arrival_datetime
        )
        
        # Use heapq with priority = (stops, arrival_timestamp, counter)
        pq = []
        heapq.heappush(pq, (0, first_arrival_datetime.timestamp(), counter, initial_state))
        counter += 1
        
        visited = set()
        iterations = 0
        max_iterations = 100000
        
        while pq and iterations < max_iterations:
            iterations += 1
            
            priority_stops, priority_arrival, _, state = heapq.heappop(pq)
            current_airport, path, last_arrival_time, last_arrival_date, total_duration, route_info, current_arrival_dt = state
            
            # Create state key for visited check
            state_key = (current_airport, tuple(path))
            if state_key in visited:
                continue
            visited.add(state_key)
            
            # Check if we've reached destination
            if current_airport == destination:
                last_leg_info = route_info[-1]
                last_flight_arrival_date = last_leg_info['date']
                dep_min = parse_time_to_minutes(last_leg_info['departure'])
                arr_min = parse_time_to_minutes(last_leg_info['arrival'])
                if arr_min and dep_min and arr_min < dep_min:
                    last_flight_arrival_date = last_leg_info['date'] + timedelta(days=1)
                
                if arr_min is not None:
                    arrival_datetime = last_flight_arrival_date.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(minutes=arr_min)
                else:
                    arrival_datetime = last_flight_arrival_date
                
                all_routes.append({
                    'path': path,
                    'stops': len(path) - 2,
                    'total_duration': total_duration,
                    'route_info': route_info,
                    'start_date': route_info[0]['date'],
                    'end_date': last_flight_arrival_date,
                    'arrival_datetime': arrival_datetime
                })
                
                # Continue searching for more routes (don't break)
                continue
            
            # Check stop limit
            current_stops = len(path) - 1
            if current_stops >= max_stops + 1:
                continue
            
            # Find next flights from current airport
            if current_airport in network:
                for next_flight in network[current_airport]:
                    if next_flight['destination'] in path:
                        continue
                    
                    if next_flight['date'] < last_arrival_date:
                        continue
                    if next_flight['date'] > last_arrival_date + timedelta(days=14):
                        continue
                    
                    min_connection = 60
                    
                    # Calculate waiting time
                    if next_flight['date'] > last_arrival_date:
                        days_diff = (next_flight['date'].date() - last_arrival_date.date()).days
                        if last_arrival_time < 1440:
                            wait_time = (1440 - last_arrival_time) + ((days_diff - 1) * 1440) + next_flight['departure']
                        else:
                            normalized_arrival = last_arrival_time % 1440
                            wait_time = (1440 - normalized_arrival) + ((days_diff - 1) * 1440) + next_flight['departure']
                    elif next_flight['date'].date() == last_arrival_date.date():
                        if next_flight['departure'] >= last_arrival_time + min_connection:
                            wait_time = next_flight['departure'] - last_arrival_time
                        else:
                            continue
                    else:
                        continue
                    
                    if wait_time < min_connection or wait_time > 5760:
                        continue
                    
                    new_total = total_duration + wait_time + next_flight['duration']
                    
                    new_route_info = route_info + [{
                        'from': current_airport,
                        'to': next_flight['destination'],
                        'date': next_flight['date'],
                        'departure': next_flight['dep_str'],
                        'arrival': next_flight['arr_str'],
                        'duration': next_flight['duration'],
                        'duration_str': next_flight['duration_str'],
                        'carrier': next_flight['carrier'],
                        'flight': next_flight['flight_num'],
                        'wait_time': wait_time
                    }]
                    
                    next_arrival_date = next_flight.get('arrival_date', next_flight['date'])
                    next_arrival_time = next_flight['arrival']
                    
                    if next_arrival_time is not None:
                        next_arrival_datetime = next_arrival_date.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(minutes=next_arrival_time)
                    else:
                        next_arrival_datetime = next_arrival_date
                    
                    new_state = (
                        next_flight['destination'],
                        path + [next_flight['destination']],
                        next_arrival_time,
                        next_arrival_date,
                        new_total,
                        new_route_info,
                        next_arrival_datetime
                    )
                    
                    new_stops = len(path) - 1
                    heapq.heappush(pq, (new_stops, next_arrival_datetime.timestamp(), counter, new_state))
                    counter += 1
        
        # Stop if we found many routes
        if len(all_routes) >= 200:
            break
    
    # Remove duplicate routes
    unique_routes = []
    seen_routes = set()
    
    for route in all_routes:
        route_id = tuple([
            (leg['from'], leg['to'], leg['date'].date(), leg['departure'])
            for leg in route['route_info']
        ])
        
        if route_id not in seen_routes:
            seen_routes.add(route_id)
            unique_routes.append(route)
    
    # Mark routes that depart later but arrive earlier
    same_day_routes = [r for r in unique_routes if r['start_date'].date() == start_date.date()]
    later_departure_routes = [r for r in unique_routes if r['start_date'].date() > start_date.date()]
    
    if same_day_routes and later_departure_routes:
        earliest_same_day_arrival = min(r.get('arrival_datetime', r['end_date']) for r in same_day_routes)
        for route in later_departure_routes:
            if route.get('arrival_datetime', route['end_date']) < earliest_same_day_arrival:
                route['arrives_earlier'] = True
    
    # ============================================================
    # CREATE TWO SEPARATE SORTED LISTS
    # ============================================================
    
    # List 1: Routes sorted by EARLIEST ARRIVAL (fastest to destination)
    fastest_arriving_routes = sorted(unique_routes, key=lambda x: (x['arrival_datetime'], x['stops']))[:15]
    
    # List 2: Routes sorted by FEWEST STOPS (simplest routing)
    # This is key for the CGN -> SDF -> BFI case
    routes_by_stops = sorted(unique_routes, key=lambda x: (x['stops'], x['arrival_datetime']))
    
    # Get routes with the minimum number of stops
    fewest_stops_routes = []
    if routes_by_stops:
        min_stops = routes_by_stops[0]['stops']
        
        # Get all routes with minimum stops (or minimum + 1)
        for route in routes_by_stops:
            # Only include if it has fewer stops than the fastest route shown
            if fastest_arriving_routes:
                fastest_shown_stops = min(r['stops'] for r in fastest_arriving_routes[:5])
                if route['stops'] < fastest_shown_stops:
                    # Check if not already in fastest routes
                    route_id = tuple([(leg['from'], leg['to'], leg['date'].date()) for leg in route['route_info']])
                    fastest_ids = [tuple([(leg['from'], leg['to'], leg['date'].date()) for leg in r['route_info']]) for r in fastest_arriving_routes[:5]]
                    
                    if route_id not in fastest_ids:
                        fewest_stops_routes.append(route)
                        if len(fewest_stops_routes) >= 3:
                            break
            else:
                if route['stops'] <= min_stops + 1:
                    fewest_stops_routes.append(route)
                    if len(fewest_stops_routes) >= 3:
                        break
    
    return fastest_arriving_routes, fewest_stops_routes

def display_route_results(origin, destination, selected_date, schedule_df):
    """Common function to display route results"""
    search_date = pd.Timestamp(selected_date)
    
    with st.spinner(f"Searching routes from {origin} to {destination}..."):
        try:
            # Search for direct flights - ALWAYS checks selected date first
            direct_results = find_direct_flights(schedule_df, origin, destination, search_date)
            
            if direct_results:
                # Check if we have same-day flights
                has_same_day = any(r['days_from_requested'] == 0 for r in direct_results)
                has_earlier_arrivals = any(r.get('arrives_earlier', False) for r in direct_results)
                
                if has_same_day:
                    st.success(f"✅ Found direct flights on your selected date ({selected_date})!")
                    if has_earlier_arrivals:
                        st.info("💡 Also found flights departing later but arriving EARLIER than same-day options!")
                else:
                    st.warning(f"⚠️ No flights available on {selected_date}. Showing next available dates.")
                
                for result in direct_results:
                    date_diff = result['days_from_requested']
                    arrives_earlier = result.get('arrives_earlier', False)
                    
                    if date_diff == 0:
                        date_label = "✓ ON YOUR SELECTED DATE"
                        color = "green"
                    elif arrives_earlier:
                        date_label = f"🌟 DEPARTS LATER BUT ARRIVES EARLIER! (+{date_diff} day(s) departure)"
                        color = "blue"
                    else:
                        date_label = f"📅 Next available: +{date_diff} day(s)"
                        color = "orange"
                    
                    st.markdown(f"""
                    <div class="route-card">
                        <h3 style="color: {color};">📅 {result['date'].strftime('%Y-%m-%d (%A)')} - {date_label}</h3>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    for i, flight in enumerate(result['flights'], 1):
                        with st.expander(f"✈️ Direct Flight Option {i} - Carrier: {flight.get('Carrier', 'N/A')} - Arrives: {flight['Sched In(L)']}", 
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
                # Get both fastest arriving routes AND fewest stops routes
                fastest_routes, fewest_stops_routes = find_connecting_routes(network, origin, destination, search_date)
                
                if fastest_routes:
                    # Check if we have same-day departure routes
                    same_day_routes = [r for r in fastest_routes if r['start_date'].date() == search_date.date()]
                    
                    # Check minimum stops in all found routes
                    all_routes_combined = fastest_routes + fewest_stops_routes
                    min_stops_found = min(r['stops'] for r in all_routes_combined) if all_routes_combined else 0
                    
                    # Check if ALL routes require 5+ stops (no simpler option exists)
                    all_routes_need_5_plus = min_stops_found >= 5
                    
                    if same_day_routes:
                        st.success(f"✅ Found {len(same_day_routes)} connecting route(s) departing on your selected date!")
                    else:
                        st.warning(f"⚠️ No connecting routes on {selected_date}. Showing routes starting from next available dates.")
                    
                    st.success(f"✅ Total: Found {len(fastest_routes)} connecting route(s) (sorted by earliest arrival)!")
                    
                    # ============================================================
                    # PROMINENT WARNING FOR 5+ STOPS ROUTES
                    # ============================================================
                    if all_routes_need_5_plus:
                        st.markdown("""
                        <div class="contact-warning">
                            <h3 style="color: #856404; margin-top: 0;">⚠️ Complex Routing Required</h3>
                            <p style="font-size: 16px; margin-bottom: 10px;">
                                <strong>All available routes for this origin-destination pair require 5 or more stops.</strong>
                            </p>
                            <p style="font-size: 15px; margin-bottom: 15px;">
                                For shipments requiring complex multi-stop routing, we strongly recommend contacting our logistics team 
                                for personalized assistance to ensure optimal handling and timing.
                            </p>
                            <p style="font-size: 14px; color: #666; margin-bottom: 0;">
                                📞 <strong>Please contact UPS Healthcare Logistics for assistance with this route.</strong>
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # ============================================================
                    # SECTION 1: FASTEST ARRIVING ROUTES
                    # ============================================================
                    st.markdown("### 🚀 Fastest Arriving Routes")
                    st.caption("Routes sorted by earliest arrival time at destination")
                    
                    for i, route in enumerate(fastest_routes[:5], 1):
                        route_str = " → ".join(route['path'])
                        total_duration = route['total_duration']
                        total_hours = total_duration // 60
                        total_mins = total_duration % 60
                        
                        total_wait = sum([leg['wait_time'] for leg in route['route_info']])
                        wait_hours = total_wait // 60
                        wait_mins = total_wait % 60
                        
                        is_same_day = route['start_date'].date() == search_date.date()
                        arrives_earlier = route.get('arrives_earlier', False)
                        
                        if is_same_day:
                            date_indicator = "✓ DEPARTS ON SELECTED DATE"
                        elif arrives_earlier:
                            date_indicator = f"🌟 Departs +{(route['start_date'].date() - search_date.date()).days} days BUT ARRIVES EARLIER!"
                        else:
                            date_indicator = f"Departs +{(route['start_date'].date() - search_date.date()).days} days"
                        
                        arrival_time_str = route['arrival_datetime'].strftime('%Y-%m-%d %H:%M')
                        
                        # Add warning for 5+ stops
                        stops_display = f"{route['stops']} stop(s)"
                        if route['stops'] >= 5:
                            stops_display = f"⚠️ {route['stops']} stops - CONTACT FOR ASSISTANCE"
                        
                        with st.expander(f"🔄 Route {i}: {route_str} ({stops_display}) - Arrives: {arrival_time_str}", 
                                       expanded=(i == 1)):
                            
                            # Warning for 5+ stops
                            if route['stops'] >= 5:
                                st.error("""
                                ⚠️ **This route requires 5 or more stops.**
                                
                                For complex multi-stop routing, please **contact UPS Healthcare Logistics** for personalized assistance 
                                to ensure optimal handling, timing, and cargo safety.
                                """)
                            
                            st.markdown(f"""
                            <div style="background-color: #E8F4F8; padding: 15px; border-radius: 10px; margin-bottom: 15px;">
                                <h4 style="color: #351C15; margin: 0;">Route Summary</h4>
                                <p><strong>Route:</strong> {route_str}</p>
                                <p><strong>Departure Date:</strong> {route['start_date'].strftime('%Y-%m-%d')} ({route['start_date'].strftime('%A')})</p>
                                <p><strong>Arrival Date:</strong> {route['end_date'].strftime('%Y-%m-%d')} ({route['end_date'].strftime('%A')})</p>
                                <p><strong>🎯 Arrival Time:</strong> {arrival_time_str}</p>
                                <p><strong>Total Journey Time:</strong> {total_hours}h {total_mins}m</p>
                                <p><strong>Total Waiting Time:</strong> {wait_hours}h {wait_mins}m</p>
                                <p><strong>Number of Stops:</strong> {route['stops']}</p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            st.markdown("### ✈️ Flight Segments:")
                            
                            for j, leg in enumerate(route['route_info'], 1):
                                leg_departure_date = leg['date']
                                leg_arrival_date = leg['date']
                                
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
                                    st.write(f"📅 Dep: {leg_departure_date.strftime('%Y-%m-%d')}")
                                    st.write(f"📅 Arr: {leg_arrival_date.strftime('%Y-%m-%d')}")
                                    st.write(f"✈️ Carrier: {leg['carrier']}")
                                
                                with col2:
                                    st.markdown("**Flight Details**")
                                    st.write(f"Flight: {leg['flight']}")
                                    st.write(f"Dep: {leg['departure']} ({leg_departure_date.strftime('%a')})")
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
                            
                            st.success(f"""
                            **Journey Complete:**
                            - 🎯 Arrival Time: {arrival_time_str}
                            - Total Travel Time: {total_hours}h {total_mins}m
                            - Total Waiting Time: {wait_hours}h {wait_mins}m
                            - Total Segments: {len(route['route_info'])}
                            """)
                    
                    # ============================================================
                    # SECTION 2: ROUTES WITH FEWER STOPS
                    # ============================================================
                    if fewest_stops_routes:
                        st.markdown("---")
                        st.markdown("### 🔗 Routes with Fewer Stops")
                        st.caption("Alternative routes with simpler connections (may have later arrival times)")
                        
                        st.info(f"""
                        💡 **Simpler Routing Options**: The routes below have fewer stops than the fastest arriving routes shown above.
                        These may be preferable for sensitive shipments or when minimizing handling is a priority.
                        """)
                        
                        for i, route in enumerate(fewest_stops_routes[:3], 1):
                            route_str = " → ".join(route['path'])
                            total_duration = route['total_duration']
                            total_hours = total_duration // 60
                            total_mins = total_duration % 60
                            
                            total_wait = sum([leg['wait_time'] for leg in route['route_info']])
                            wait_hours = total_wait // 60
                            wait_mins = total_wait % 60
                            
                            is_same_day = route['start_date'].date() == search_date.date()
                            
                            if is_same_day:
                                date_indicator = "✓ DEPARTS ON SELECTED DATE"
                            else:
                                date_indicator = f"Departs +{(route['start_date'].date() - search_date.date()).days} days"
                            
                            arrival_time_str = route['arrival_datetime'].strftime('%Y-%m-%d %H:%M')
                            
                            with st.expander(f"🔗 Simpler Route {i}: {route_str} (✅ Only {route['stops']} stop(s)) - Arrives: {arrival_time_str}", 
                                           expanded=(i == 1)):
                                
                                st.markdown(f"""
                                <div style="background-color: #E8F8E8; padding: 15px; border-radius: 10px; margin-bottom: 15px; border-left: 4px solid #4CAF50;">
                                    <h4 style="color: #2E7D32; margin: 0;">✅ Simpler Route - Fewer Stops</h4>
                                    <p><strong>Route:</strong> {route_str}</p>
                                    <p><strong>✅ Number of Stops:</strong> {route['stops']} (fewer connections = less handling)</p>
                                    <p><strong>Departure Date:</strong> {route['start_date'].strftime('%Y-%m-%d')} ({route['start_date'].strftime('%A')})</p>
                                    <p><strong>Arrival Date:</strong> {route['end_date'].strftime('%Y-%m-%d')} ({route['end_date'].strftime('%A')})</p>
                                    <p><strong>🎯 Arrival Time:</strong> {arrival_time_str}</p>
                                    <p><strong>Total Journey Time:</strong> {total_hours}h {total_mins}m</p>
                                    <p><strong>Total Waiting Time:</strong> {wait_hours}h {wait_mins}m</p>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                st.markdown("### ✈️ Flight Segments:")
                                
                                for j, leg in enumerate(route['route_info'], 1):
                                    leg_departure_date = leg['date']
                                    leg_arrival_date = leg['date']
                                    
                                    dep_minutes = parse_time_to_minutes(leg['departure'])
                                    arr_minutes = parse_time_to_minutes(leg['arrival'])
                                    if arr_minutes and dep_minutes and arr_minutes < dep_minutes:
                                        leg_arrival_date = leg['date'] + timedelta(days=1)
                                    
                                    st.markdown(f"""
                                    <div style="background-color: #FAFAFA; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #4CAF50;">
                                        <h4 style="color: #351C15;">Segment {j}: {leg['from']} → {leg['to']}</h4>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    col1, col2, col3, col4 = st.columns(4)
                                    
                                    with col1:
                                        st.markdown("**Date & Carrier**")
                                        st.write(f"📅 Dep: {leg_departure_date.strftime('%Y-%m-%d')}")
                                        st.write(f"📅 Arr: {leg_arrival_date.strftime('%Y-%m-%d')}")
                                        st.write(f"✈️ Carrier: {leg['carrier']}")
                                    
                                    with col2:
                                        st.markdown("**Flight Details**")
                                        st.write(f"Flight: {leg['flight']}")
                                        st.write(f"Dep: {leg['departure']} ({leg_departure_date.strftime('%a')})")
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
                                
                                st.success(f"""
                                **Journey Complete (Simpler Route):**
                                - ✅ Only {route['stops']} stop(s) - Less handling required
                                - 🎯 Arrival Time: {arrival_time_str}
                                - Total Travel Time: {total_hours}h {total_mins}m
                                - Total Segments: {len(route['route_info'])}
                                """)
                    else:
                        # Check if fastest routes already have minimal stops
                        if fastest_routes:
                            min_stops_in_fastest = min(r['stops'] for r in fastest_routes[:5])
                            st.markdown("---")
                            st.info(f"""
                            ℹ️ **No simpler alternatives found**: The fastest arriving routes shown above already have the minimum 
                            number of stops ({min_stops_in_fastest}) for this origin-destination pair.
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
