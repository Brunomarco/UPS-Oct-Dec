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
    
    1. **Earliest Arrival Priority**: For routes departing on your selected date, the system identifies which routes 
    arrive earliest at the destination. This ensures optimal delivery times.
    
    2. **Minimum Stops Alternative**: For the same selected departure date, the system also identifies routes with 
    the fewest connections, which may be preferable for sensitive shipments even if arrival is slightly later.
    
    3. **Direct Flight Priority**: The system first searches for non-stop flights on the selected date.
    
    4. **Date Extension Logic**: If no flights are available on the selected date, the system automatically extends the 
    search window up to 7 days forward.
    
    5. **Connection Mapping**: For routes without direct service, the system calculates connecting flights through 
    intermediate airports. **Critical constraint: Minimum 1-hour connection time is enforced.**
    
    6. **Complex Route Handling**: Routes requiring 5 or more stops trigger a recommendation to contact the logistics
    team for personalized assistance.
    """)

    st.markdown("""
    ### Connection Time Requirements
    
    **Minimum Connection Time: 1 Hour**
    
    The system enforces a strict minimum of 60 minutes between:
    - The arrival time of an inbound flight (in local time at that airport)
    - The departure time of the connecting flight (in local time at that airport)
    
    **Maximum Connection Time: 24 Hours**
    
    Connections exceeding 24 hours are excluded to avoid excessive storage and handling costs.
    """)

    st.markdown("""
    ### Results Sections
    
    **🚀 Fastest Arriving Routes:**
    - Routes that DEPART on your selected date
    - Sorted by which route ARRIVES at the destination earliest
    - Best for time-critical shipments
    
    **🔗 Routes with Fewer Stops:**
    - Routes that DEPART on your selected date  
    - Shows routes with the minimum number of connections
    - Best for sensitive shipments where less handling is preferred
    - May arrive later than the fastest routes
    """)

    st.success("""
    **Key Point**: Both sections show routes departing on your selected date. The difference is the sorting criteria:
    fastest arrival time vs. fewest number of stops.
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
        route_flights = schedule_df[
            (schedule_df['Orig'] == origin) & 
            (schedule_df['Dest'] == destination)
        ].copy()
        
        if route_flights.empty:
            return []
        
        results = []
        all_flights_with_arrival = []
        
        for day_offset in range(0, 4):
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
                                
                                arrival_date = check_date
                                if arr_time and dep_time and arr_time < dep_time:
                                    arrival_date = check_date + timedelta(days=1)
                                
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
                flights_on_date.sort(key=lambda x: x['arrival_datetime'])
                results.append({
                    'date': check_date,
                    'flights': flights_on_date,
                    'days_from_requested': day_offset,
                    'arrives_earlier': False
                })
        
        if results and len(results) > 0:
            same_day_flights = results[0]['flights']
            earliest_same_day_arrival = min(f['arrival_datetime'] for f in same_day_flights)
            
            for day_offset in range(1, 4):
                check_date = date + timedelta(days=day_offset)
                earlier_flights = [f for f in all_flights_with_arrival 
                                  if f['day_offset'] == day_offset 
                                  and f['arrival_datetime'] < earliest_same_day_arrival]
                
                if earlier_flights:
                    earlier_flights.sort(key=lambda x: x['arrival_datetime'])
                    results.append({
                        'date': check_date,
                        'flights': earlier_flights,
                        'days_from_requested': day_offset,
                        'arrives_earlier': True
                    })
        
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
                    flights_on_date.sort(key=lambda x: x['arrival_datetime'])
                    results.append({
                        'date': check_date,
                        'flights': flights_on_date,
                        'days_from_requested': day_offset,
                        'arrives_earlier': False
                    })
                    
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
                                
                                blkhr_str = str(flight['Blkhr'])
                                flight_duration = 0
                                if pd.notna(flight['Blkhr']) and blkhr_str != 'nan':
                                    if ':' in blkhr_str:
                                        parts = blkhr_str.split(':')
                                        hours = int(parts[0]) if parts[0] else 0
                                        minutes = int(parts[1]) if len(parts) > 1 else 0
                                        flight_duration = hours * 60 + minutes
                                
                                if dep_time is not None and arr_time is not None and flight_duration > 0:
                                    arrival_date = check_date
                                    if arr_time < dep_time:
                                        arrival_date = check_date + timedelta(days=1)
                                    
                                    network[origin].append({
                                        'destination': dest,
                                        'departure': dep_time,
                                        'arrival': arr_time,
                                        'arrival_date': arrival_date,
                                        'dep_str': str(flight['Sched Out(L)']),
                                        'arr_str': str(flight['Sched In(L)']),
                                        'duration_str': str(flight['Blkhr']),
                                        'carrier': str(flight.get('Carrier', 'N/A')),
                                        'flight_num': f"{flight.get('Carrier', '')}{flight.get('Flight #', '')}",
                                        'duration': flight_duration,
                                        'date': check_date,
                                        'day_offset': day_offset
                                    })
                except:
                    continue
    except:
        pass
    
    for origin in network:
        network[origin].sort(key=lambda x: (x['date'], x['departure']))
    
    return network

def find_all_routes_for_date(network, origin, destination, target_date, max_stops=10):
    """
    Find ALL possible routes that DEPART on the target_date.
    Returns a list of all valid routes departing on the specified date.
    """
    if origin not in network:
        return []
    
    all_routes = []
    
    # Get ONLY flights from origin on the TARGET DATE
    initial_flights = [f for f in network.get(origin, []) 
                      if f['date'].date() == target_date.date()]
    
    if not initial_flights:
        return []
    
    initial_flights.sort(key=lambda x: x['departure'])
    
    counter = 0
    
    for first_flight in initial_flights:
        first_arrival_date = first_flight.get('arrival_date', first_flight['date'])
        first_arrival_time = first_flight['arrival']
        
        if first_arrival_time is not None:
            first_arrival_datetime = first_arrival_date.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(minutes=first_arrival_time)
        else:
            first_arrival_datetime = first_arrival_date
        
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
        
        # Use priority queue: prioritize by (stops, arrival_time) to find shorter routes first
        pq = []
        heapq.heappush(pq, (0, first_arrival_datetime.timestamp(), counter, initial_state))
        counter += 1
        
        visited = set()
        iterations = 0
        max_iterations = 50000
        
        while pq and iterations < max_iterations:
            iterations += 1
            
            priority_stops, priority_arrival, _, state = heapq.heappop(pq)
            current_airport, path, last_arrival_time, last_arrival_date, total_duration, route_info, current_arrival_dt = state
            
            state_key = (current_airport, tuple(path))
            if state_key in visited:
                continue
            visited.add(state_key)
            
            # Reached destination
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
                    'stops': len(path) - 2,  # Number of intermediate stops
                    'total_duration': total_duration,
                    'route_info': route_info,
                    'start_date': route_info[0]['date'],
                    'end_date': last_flight_arrival_date,
                    'arrival_datetime': arrival_datetime
                })
                continue
            
            # Check stop limit
            current_stops = len(path) - 1
            if current_stops >= max_stops + 1:
                continue
            
            # Find connecting flights
            if current_airport in network:
                for next_flight in network[current_airport]:
                    if next_flight['destination'] in path:
                        continue
                    
                    # Connection must be AFTER arrival
                    if next_flight['date'] < last_arrival_date:
                        continue
                    # Don't allow connections more than 7 days out
                    if next_flight['date'] > last_arrival_date + timedelta(days=7):
                        continue
                    
                    min_connection = 60  # 1 hour minimum
                    
                    # Calculate waiting time
                    if next_flight['date'].date() > last_arrival_date.date():
                        days_diff = (next_flight['date'].date() - last_arrival_date.date()).days
                        wait_time = (1440 - last_arrival_time) + ((days_diff - 1) * 1440) + next_flight['departure']
                    elif next_flight['date'].date() == last_arrival_date.date():
                        if next_flight['departure'] >= last_arrival_time + min_connection:
                            wait_time = next_flight['departure'] - last_arrival_time
                        else:
                            continue  # Not enough connection time
                    else:
                        continue
                    
                    # Connection time constraints
                    if wait_time < min_connection or wait_time > 1440:  # Max 24h wait
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
    
    # Remove duplicates
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
    
    return unique_routes

def get_fastest_and_fewest_stops_routes(all_routes_same_day):
    """
    From all routes departing on the same day:
    1. Fastest Arriving: sorted by arrival_datetime (earliest first)
    2. Fewest Stops: sorted by number of stops (minimum first)
    
    Returns two separate lists.
    """
    if not all_routes_same_day:
        return [], []
    
    # ============================================================
    # FASTEST ARRIVING ROUTES
    # Sort by arrival time at destination (earliest first)
    # ============================================================
    fastest_arriving = sorted(all_routes_same_day, key=lambda x: (x['arrival_datetime'], x['stops']))
    
    # ============================================================
    # FEWEST STOPS ROUTES
    # Sort by number of stops (minimum first), then by arrival time
    # ============================================================
    by_fewest_stops = sorted(all_routes_same_day, key=lambda x: (x['stops'], x['arrival_datetime']))
    
    # Find the minimum number of stops available
    min_stops = by_fewest_stops[0]['stops'] if by_fewest_stops else 0
    
    # Get all routes with minimum stops
    fewest_stops_routes = [r for r in by_fewest_stops if r['stops'] == min_stops]
    
    # Sort fewest stops routes by arrival time
    fewest_stops_routes = sorted(fewest_stops_routes, key=lambda x: x['arrival_datetime'])
    
    return fastest_arriving, fewest_stops_routes

def display_route_results(origin, destination, selected_date, schedule_df):
    """Common function to display route results"""
    search_date = pd.Timestamp(selected_date)
    
    with st.spinner(f"Searching routes from {origin} to {destination}..."):
        try:
            # Search for direct flights
            direct_results = find_direct_flights(schedule_df, origin, destination, search_date)
            
            if direct_results:
                has_same_day = any(r['days_from_requested'] == 0 for r in direct_results)
                has_earlier_arrivals = any(r.get('arrives_earlier', False) for r in direct_results)
                
                if has_same_day:
                    st.success(f"✅ Found direct flights on your selected date ({selected_date})!")
                    if has_earlier_arrivals:
                        st.info("💡 Also found flights departing later but arriving EARLIER than same-day options!")
                else:
                    st.warning(f"⚠️ No direct flights on {selected_date}. Showing next available dates.")
                
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
            
            # Search for connecting flights
            st.info("🔄 Searching for connecting flight options...")
            
            network = build_network(schedule_df, search_date)
            
            if network:
                # Find ALL routes departing on the selected date
                all_same_day_routes = find_all_routes_for_date(network, origin, destination, search_date)
                
                if all_same_day_routes:
                    # Get the two sorted lists
                    fastest_routes, fewest_stops_routes = get_fastest_and_fewest_stops_routes(all_same_day_routes)
                    
                    st.success(f"✅ Found {len(all_same_day_routes)} connecting route(s) departing on {selected_date}!")
                    
                    # Check for complex routes (5+ stops)
                    min_stops_overall = min(r['stops'] for r in all_same_day_routes)
                    all_routes_need_5_plus = min_stops_overall >= 5
                    
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
                    st.caption(f"Routes departing on {selected_date}, sorted by earliest arrival at {destination}")
                    
                    for i, route in enumerate(fastest_routes[:5], 1):
                        route_str = " → ".join(route['path'])
                        total_duration = route['total_duration']
                        total_hours = total_duration // 60
                        total_mins = total_duration % 60
                        
                        total_wait = sum([leg['wait_time'] for leg in route['route_info']])
                        wait_hours = total_wait // 60
                        wait_mins = total_wait % 60
                        
                        arrival_time_str = route['arrival_datetime'].strftime('%Y-%m-%d %H:%M')
                        
                        stops_display = f"{route['stops']} stop(s)"
                        if route['stops'] >= 5:
                            stops_display = f"⚠️ {route['stops']} stops - CONTACT FOR ASSISTANCE"
                        
                        with st.expander(f"🚀 Route {i}: {route_str} ({stops_display}) - Arrives: {arrival_time_str}", 
                                       expanded=(i == 1)):
                            
                            if route['stops'] >= 5:
                                st.error("""
                                ⚠️ **This route requires 5 or more stops.**
                                
                                For complex multi-stop routing, please **contact UPS Healthcare Logistics** for personalized assistance.
                                """)
                            
                            st.markdown(f"""
                            <div style="background-color: #E8F4F8; padding: 15px; border-radius: 10px; margin-bottom: 15px;">
                                <h4 style="color: #351C15; margin: 0;">Route Summary - Fastest Arriving</h4>
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
                    # SECTION 2: ROUTES WITH FEWEST STOPS
                    # ============================================================
                    st.markdown("---")
                    st.markdown("### 🔗 Routes with Fewest Stops")
                    st.caption(f"Routes departing on {selected_date} with minimum connections ({min_stops_overall} stop(s))")
                    
                    if min_stops_overall >= 5:
                        st.warning(f"""
                        ⚠️ **Minimum stops available: {min_stops_overall}**
                        
                        All routes for this origin-destination require {min_stops_overall} or more stops.
                        Please contact UPS Healthcare Logistics for assistance with complex routing.
                        """)
                    
                    st.info(f"""
                    💡 **Simpler Routing**: These routes have the fewest stops ({min_stops_overall}) available for this route on {selected_date}.
                    Fewer stops = less cargo handling = reduced risk for sensitive shipments.
                    """)
                    
                    for i, route in enumerate(fewest_stops_routes[:3], 1):
                        route_str = " → ".join(route['path'])
                        total_duration = route['total_duration']
                        total_hours = total_duration // 60
                        total_mins = total_duration % 60
                        
                        total_wait = sum([leg['wait_time'] for leg in route['route_info']])
                        wait_hours = total_wait // 60
                        wait_mins = total_wait % 60
                        
                        arrival_time_str = route['arrival_datetime'].strftime('%Y-%m-%d %H:%M')
                        
                        with st.expander(f"🔗 Fewest Stops Option {i}: {route_str} (✅ {route['stops']} stop(s)) - Arrives: {arrival_time_str}", 
                                       expanded=(i == 1)):
                            
                            if route['stops'] >= 5:
                                st.error("""
                                ⚠️ **This route requires 5 or more stops.**
                                
                                Please **contact UPS Healthcare Logistics** for personalized assistance with this complex routing.
                                """)
                            
                            st.markdown(f"""
                            <div style="background-color: #E8F8E8; padding: 15px; border-radius: 10px; margin-bottom: 15px; border-left: 4px solid #4CAF50;">
                                <h4 style="color: #2E7D32; margin: 0;">✅ Route with Fewest Stops</h4>
                                <p><strong>Route:</strong> {route_str}</p>
                                <p><strong>✅ Number of Stops:</strong> {route['stops']} (minimum available)</p>
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
                            **Journey Complete (Fewest Stops):**
                            - ✅ Only {route['stops']} stop(s) - Minimum handling
                            - 🎯 Arrival Time: {arrival_time_str}
                            - Total Travel Time: {total_hours}h {total_mins}m
                            - Total Segments: {len(route['route_info'])}
                            """)
                
                else:
                    # No routes on selected date - search for next available
                    st.warning(f"⚠️ No connecting routes departing on {selected_date}. Searching for next available dates...")
                    
                    found_alternative = False
                    for day_offset in range(1, 8):
                        alt_date = search_date + timedelta(days=day_offset)
                        alt_routes = find_all_routes_for_date(network, origin, destination, alt_date)
                        
                        if alt_routes:
                            st.info(f"📅 Found routes departing on {alt_date.strftime('%Y-%m-%d')} (+{day_offset} day(s))")
                            
                            fastest_routes, fewest_stops_routes = get_fastest_and_fewest_stops_routes(alt_routes)
                            
                            min_stops_overall = min(r['stops'] for r in alt_routes)
                            
                            # Show first fastest route
                            if fastest_routes:
                                route = fastest_routes[0]
                                route_str = " → ".join(route['path'])
                                arrival_time_str = route['arrival_datetime'].strftime('%Y-%m-%d %H:%M')
                                
                                st.markdown(f"""
                                **Fastest Route on {alt_date.strftime('%Y-%m-%d')}:**
                                - Route: {route_str}
                                - Stops: {route['stops']}
                                - Arrives: {arrival_time_str}
                                """)
                            
                            # Show first fewest stops route
                            if fewest_stops_routes:
                                route = fewest_stops_routes[0]
                                route_str = " → ".join(route['path'])
                                arrival_time_str = route['arrival_datetime'].strftime('%Y-%m-%d %H:%M')
                                
                                st.markdown(f"""
                                **Fewest Stops Route on {alt_date.strftime('%Y-%m-%d')}:**
                                - Route: {route_str}
                                - Stops: {route['stops']} (minimum)
                                - Arrives: {arrival_time_str}
                                """)
                            
                            found_alternative = True
                            break
                    
                    if not found_alternative and not direct_results:
                        st.error(f"""
                        ❌ No routes found from {origin} to {destination}
                        
                        **Suggestions:**
                        - This route may not be served by UPS flights
                        - Try selecting a different origin-destination pair
                        - Check if flights operate on different days of the week
                        """)
            else:
                if not direct_results:
                    st.error("No flight network available for the selected date range.")
        
        except Exception as e:
            st.error(f"Error during search: {str(e)}")
            import traceback
            st.error(traceback.format_exc())

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
            
            # Tab 1: Tracked Routes
            with tab1:
                st.markdown("<h2 style='color: #351C15;'>🔍 Tracked Route Finder</h2>", unsafe_allow_html=True)
                st.info("Select from pre-defined route pairs in your Data sheet")
                
                col1, col2 = st.columns(2)
                
                with col1:
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
                
                if st.button("🔍 Find Available Routes", type="primary", use_container_width=True, key="tracked_search"):
                    if selected_route:
                        display_route_results(origin, destination, selected_date, schedule_df)
            
            # Tab 2: Custom Routes
            with tab2:
                st.markdown("<h2 style='color: #351C15;'>🔍 Custom Route Finder</h2>", unsafe_allow_html=True)
                st.info("Select any origin and destination from all available airports")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    origins = sorted(schedule_df['Orig'].dropna().unique())
                    custom_origin = st.selectbox(
                        "Select Origin Airport",
                        options=origins,
                        help="Select any available origin airport",
                        key="custom_origin"
                    )
                
                with col2:
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
                
                st.markdown(f"""
                <div style="background-color: #FFF8E8; padding: 15px; border-radius: 5px; border-left: 3px solid #FFB500; margin-top: 20px;">
                    <strong>Selected Custom Route:</strong> {custom_origin} → {custom_destination}<br>
                    <strong>Selected Date:</strong> {custom_date} ({day_of_week})
                </div>
                """, unsafe_allow_html=True)
                
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
