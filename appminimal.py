import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from collections import deque

# Page configuration with UPS branding
st.set_page_config(
    page_title="UPS Flight Routing System",
    page_icon="📦",
    layout="wide"
)

# Initialize session state for tab persistence
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = 0

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
    
    The routing algorithm employs a comprehensive search approach:
    
    1. **Complete Route Discovery**: The system finds ALL possible routes from origin to destination that depart on your selected date.
    
    2. **Fastest Arriving Routes**: From all found routes, identifies which ones arrive EARLIEST at the destination - even if they have more stops. This is ideal for time-critical shipments.
    
    3. **Fewest Stops Routes**: From all found routes, identifies which ones have the MINIMUM number of connections - even if they arrive later. This is ideal for sensitive shipments where less handling is preferred.
    
    4. **Connection Rules**: Minimum 1-hour connection time between flights. Maximum 24-hour layover.
    
    5. **Complex Route Handling**: Routes requiring 5 or more stops trigger a recommendation to contact the logistics team.
    """)

    st.markdown("""
    ### Results Sections
    
    **🚀 Fastest Arriving Routes:**
    - All routes depart on your selected date
    - Sorted by which route ARRIVES at the destination EARLIEST
    - May have more stops if that gets cargo there faster
    - Best for time-critical shipments
    
    **🔗 Routes with Fewest Stops:**
    - All routes depart on your selected date  
    - Sorted by MINIMUM number of connections
    - May arrive later than fastest routes
    - Best for sensitive shipments where less handling is preferred
    """)

    st.success("""
    **Key Point**: Both sections show routes departing on your selected date. The difference is the optimization criteria:
    fastest arrival time vs. fewest number of stops.
    """)

st.markdown("---")

@st.cache_data
def load_data(file):
    """Load and parse the Excel file"""
    try:
        schedule_df = pd.read_excel(file, sheet_name='SchedDateLocalTimeFlightSchedul')
        routes_df = pd.read_excel(file, sheet_name='Data')
        
        schedule_df['Start Date (LZ)'] = pd.to_datetime(schedule_df['Start Date (LZ)'], errors='coerce')
        schedule_df['End Date (LZ)'] = pd.to_datetime(schedule_df['End Date (LZ)'], errors='coerce')
        
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
    weekday = date.weekday()
    
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

def build_network(schedule_df, start_date, days_ahead=14):
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
                                    
                                    # Calculate arrival datetime
                                    arrival_datetime = arrival_date.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(minutes=arr_time)
                                    
                                    network[origin].append({
                                        'destination': dest,
                                        'departure': dep_time,
                                        'arrival': arr_time,
                                        'arrival_date': arrival_date,
                                        'arrival_datetime': arrival_datetime,
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

def find_all_routes_bfs(network, origin, destination, target_date, max_stops=10):
    """
    Find ALL possible routes from origin to destination that depart on target_date.
    Uses BFS to explore ALL paths comprehensively.
    
    Returns list of all valid routes.
    """
    if origin not in network:
        return []
    
    all_routes = []
    
    # Get flights from origin on the TARGET DATE only
    initial_flights = [f for f in network.get(origin, []) 
                      if f['date'].date() == target_date.date()]
    
    if not initial_flights:
        return []
    
    # Sort by departure time
    initial_flights.sort(key=lambda x: x['departure'])
    
    # BFS queue: (current_airport, path, last_arrival_time, last_arrival_date, route_info)
    for first_flight in initial_flights:
        queue = deque()
        
        first_leg = {
            'from': origin,
            'to': first_flight['destination'],
            'date': first_flight['date'],
            'departure': first_flight['dep_str'],
            'arrival': first_flight['arr_str'],
            'duration': first_flight['duration'],
            'duration_str': first_flight['duration_str'],
            'carrier': first_flight['carrier'],
            'flight': first_flight['flight_num'],
            'wait_time': 0,
            'arrival_datetime': first_flight['arrival_datetime']
        }
        
        initial_state = (
            first_flight['destination'],  # current airport
            [origin, first_flight['destination']],  # path
            first_flight['arrival'],  # last arrival time (minutes)
            first_flight['arrival_date'],  # last arrival date
            [first_leg],  # route info
            first_flight['duration']  # total duration
        )
        
        queue.append(initial_state)
        
        # Track visited states to avoid infinite loops
        visited = set()
        
        while queue:
            current_airport, path, last_arrival_time, last_arrival_date, route_info, total_duration = queue.popleft()
            
            # Create state key
            state_key = (current_airport, tuple(path))
            if state_key in visited:
                continue
            visited.add(state_key)
            
            # Check if we reached the destination
            if current_airport == destination:
                # Calculate final arrival datetime
                last_leg = route_info[-1]
                final_arrival_datetime = last_leg['arrival_datetime']
                
                all_routes.append({
                    'path': path,
                    'stops': len(path) - 2,  # intermediate stops
                    'total_duration': total_duration,
                    'route_info': route_info,
                    'start_date': route_info[0]['date'],
                    'end_date': last_arrival_date,
                    'arrival_datetime': final_arrival_datetime
                })
                continue  # Continue searching for more routes
            
            # Check stop limit
            if len(path) - 1 > max_stops:
                continue
            
            # Find connecting flights from current airport
            if current_airport not in network:
                continue
            
            for next_flight in network[current_airport]:
                # Avoid cycles
                if next_flight['destination'] in path:
                    continue
                
                # Check connection timing
                next_dep_date = next_flight['date']
                
                # Connection must be after arrival
                if next_dep_date < last_arrival_date:
                    continue
                
                # Don't allow connections more than 7 days out
                if next_dep_date > last_arrival_date + timedelta(days=7):
                    continue
                
                # Calculate connection time
                min_connection = 60  # 1 hour minimum
                max_connection = 1440  # 24 hours maximum
                
                if next_dep_date.date() > last_arrival_date.date():
                    # Next day or later
                    days_diff = (next_dep_date.date() - last_arrival_date.date()).days
                    # Time from arrival to midnight + full days + departure time
                    wait_time = (1440 - last_arrival_time) + ((days_diff - 1) * 1440) + next_flight['departure']
                elif next_dep_date.date() == last_arrival_date.date():
                    # Same day
                    if next_flight['departure'] >= last_arrival_time + min_connection:
                        wait_time = next_flight['departure'] - last_arrival_time
                    else:
                        continue  # Not enough connection time
                else:
                    continue  # Flight is before arrival
                
                # Check connection time constraints
                if wait_time < min_connection or wait_time > max_connection:
                    continue
                
                # Valid connection found - add to queue
                new_leg = {
                    'from': current_airport,
                    'to': next_flight['destination'],
                    'date': next_flight['date'],
                    'departure': next_flight['dep_str'],
                    'arrival': next_flight['arr_str'],
                    'duration': next_flight['duration'],
                    'duration_str': next_flight['duration_str'],
                    'carrier': next_flight['carrier'],
                    'flight': next_flight['flight_num'],
                    'wait_time': wait_time,
                    'arrival_datetime': next_flight['arrival_datetime']
                }
                
                new_state = (
                    next_flight['destination'],
                    path + [next_flight['destination']],
                    next_flight['arrival'],
                    next_flight['arrival_date'],
                    route_info + [new_leg],
                    total_duration + wait_time + next_flight['duration']
                )
                
                queue.append(new_state)
    
    # Remove duplicate routes
    unique_routes = []
    seen = set()
    
    for route in all_routes:
        route_id = tuple([
            (leg['from'], leg['to'], str(leg['date'].date()), leg['departure'])
            for leg in route['route_info']
        ])
        
        if route_id not in seen:
            seen.add(route_id)
            unique_routes.append(route)
    
    return unique_routes

def get_fastest_and_fewest_stops(all_routes):
    """
    From all routes:
    1. Fastest Arriving: sorted by arrival_datetime at destination (earliest first)
    2. Fewest Stops: routes with the MINIMUM number of stops
    
    Returns two lists.
    """
    if not all_routes:
        return [], []
    
    # ============================================================
    # FASTEST ARRIVING ROUTES
    # Sort by arrival time at destination (earliest first)
    # If tied, prefer fewer stops
    # ============================================================
    fastest_arriving = sorted(all_routes, key=lambda x: (x['arrival_datetime'], x['stops']))
    
    # ============================================================
    # FEWEST STOPS ROUTES
    # Find the MINIMUM number of stops across all routes
    # Then get all routes with that minimum
    # Sort those by arrival time
    # ============================================================
    min_stops = min(route['stops'] for route in all_routes)
    
    # Get ALL routes with minimum stops
    fewest_stops_routes = [r for r in all_routes if r['stops'] == min_stops]
    
    # Sort by arrival time (earliest first)
    fewest_stops_routes = sorted(fewest_stops_routes, key=lambda x: x['arrival_datetime'])
    
    return fastest_arriving, fewest_stops_routes

def display_route_card(route, index, section_type, search_date):
    """Display a single route card"""
    route_str = " → ".join(route['path'])
    total_duration = route['total_duration']
    total_hours = total_duration // 60
    total_mins = total_duration % 60
    
    total_wait = sum([leg['wait_time'] for leg in route['route_info']])
    wait_hours = total_wait // 60
    wait_mins = total_wait % 60
    
    arrival_time_str = route['arrival_datetime'].strftime('%Y-%m-%d %H:%M')
    
    # Determine display style based on section type
    if section_type == "fastest":
        icon = "🚀"
        title_prefix = "Fastest Route"
        color = "#FFB500"
        bg_color = "#E8F4F8"
    else:
        icon = "🔗"
        title_prefix = "Fewest Stops"
        color = "#4CAF50"
        bg_color = "#E8F8E8"
    
    stops_display = f"{route['stops']} stop(s)"
    if route['stops'] >= 5:
        stops_display = f"⚠️ {route['stops']} stops - CONTACT FOR ASSISTANCE"
    
    with st.expander(f"{icon} {title_prefix} {index}: {route_str} ({stops_display}) - Arrives: {arrival_time_str}", 
                   expanded=(index == 1)):
        
        if route['stops'] >= 5:
            st.error("""
            ⚠️ **This route requires 5 or more stops.**
            
            For complex multi-stop routing, please **contact UPS Healthcare Logistics** for personalized assistance.
            """)
        
        st.markdown(f"""
        <div style="background-color: {bg_color}; padding: 15px; border-radius: 10px; margin-bottom: 15px; border-left: 4px solid {color};">
            <h4 style="color: #351C15; margin: 0;">{title_prefix} - Route Summary</h4>
            <p><strong>Route:</strong> {route_str}</p>
            <p><strong>Number of Stops:</strong> {route['stops']}</p>
            <p><strong>Departure:</strong> {route['start_date'].strftime('%Y-%m-%d')} ({route['start_date'].strftime('%A')})</p>
            <p><strong>🎯 Arrival:</strong> {arrival_time_str}</p>
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
            <div style="background-color: #FAFAFA; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 4px solid {color};">
                <h4 style="color: #351C15;">Segment {j}: {leg['from']} → {leg['to']}</h4>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown("**Date & Carrier**")
                st.write(f"📅 Dep: {leg_departure_date.strftime('%Y-%m-%d')}")
                st.write(f"📅 Arr: {leg_arrival_date.strftime('%Y-%m-%d')}")
                st.write(f"✈️ {leg['carrier']}")
            
            with col2:
                st.markdown("**Flight Details**")
                st.write(f"Flight: {leg['flight']}")
                st.write(f"Dep: {leg['departure']}")
                st.write(f"Arr: {leg['arrival']}")
            
            with col3:
                st.markdown("**Duration**")
                st.write(f"{format_duration(leg['duration'])}")
                st.write(f"({leg['duration_str']})")
            
            with col4:
                st.markdown("**Connection**")
                if j < len(route['route_info']):
                    wait_time = route['route_info'][j]['wait_time']
                    st.write(f"⏳ {format_duration(wait_time)}")
                else:
                    st.write("✅ Final")
            
            if j < len(route['route_info']):
                st.markdown("⬇️")
        
        st.success(f"""
        **Journey Complete:**
        - 🎯 Arrival: {arrival_time_str}
        - ⏱️ Total Time: {total_hours}h {total_mins}m
        - 🔄 Stops: {route['stops']}
        """)

def display_route_results(origin, destination, selected_date, schedule_df):
    """Common function to display route results"""
    search_date = pd.Timestamp(selected_date)
    
    with st.spinner(f"Searching routes from {origin} to {destination}..."):
        try:
            # Search for direct flights
            direct_results = find_direct_flights(schedule_df, origin, destination, search_date)
            
            if direct_results:
                has_same_day = any(r['days_from_requested'] == 0 for r in direct_results)
                
                if has_same_day:
                    st.success(f"✅ Found direct flights on {selected_date}!")
                else:
                    st.warning(f"⚠️ No direct flights on {selected_date}. Showing next available.")
                
                for result in direct_results:
                    date_diff = result['days_from_requested']
                    arrives_earlier = result.get('arrives_earlier', False)
                    
                    if date_diff == 0:
                        date_label = "✓ ON SELECTED DATE"
                        color = "green"
                    elif arrives_earlier:
                        date_label = f"🌟 ARRIVES EARLIER (+{date_diff} day departure)"
                        color = "blue"
                    else:
                        date_label = f"📅 +{date_diff} day(s)"
                        color = "orange"
                    
                    st.markdown(f"""
                    <div class="route-card">
                        <h3 style="color: {color};">📅 {result['date'].strftime('%Y-%m-%d (%A)')} - {date_label}</h3>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    for i, flight in enumerate(result['flights'], 1):
                        with st.expander(f"✈️ Direct {i}: {flight.get('Carrier', 'N/A')} - Arrives: {flight['Sched In(L)']}", 
                                       expanded=(date_diff == 0 and i == 1)):
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.write(f"**Date:** {result['date'].strftime('%Y-%m-%d')}")
                                st.write(f"**Carrier:** {flight.get('Carrier', 'N/A')}")
                            
                            with col2:
                                st.write(f"**Departs:** {flight['Sched Out(L)']} from {origin}")
                                st.write(f"**Arrives:** {flight['Sched In(L)']} at {destination}")
                            
                            with col3:
                                st.write(f"**Duration:** {flight['Blkhr']}")
                                st.write("**Stops:** None (Direct)")
            
            # Search for connecting flights
            st.info("🔄 Searching for connecting routes...")
            
            network = build_network(schedule_df, search_date)
            
            if network:
                # Find ALL routes departing on the selected date
                all_routes = find_all_routes_bfs(network, origin, destination, search_date)
                
                if all_routes:
                    # Get fastest arriving and fewest stops routes
                    fastest_routes, fewest_stops_routes = get_fastest_and_fewest_stops(all_routes)
                    
                    min_stops = min(r['stops'] for r in all_routes) if all_routes else 0
                    
                    st.success(f"✅ Found {len(all_routes)} connecting route(s) departing on {selected_date}")
                    
                    # Warning for 5+ stops
                    if min_stops >= 5:
                        st.markdown("""
                        <div class="contact-warning">
                            <h3 style="color: #856404; margin-top: 0;">⚠️ Complex Routing Required</h3>
                            <p><strong>All routes require 5+ stops.</strong> Please contact UPS Healthcare Logistics for assistance.</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # ============================================================
                    # SECTION 1: FASTEST ARRIVING ROUTES
                    # ============================================================
                    st.markdown("### 🚀 Fastest Arriving Routes")
                    st.caption(f"Routes departing {selected_date}, sorted by earliest arrival at {destination}")
                    
                    for i, route in enumerate(fastest_routes[:5], 1):
                        display_route_card(route, i, "fastest", search_date)
                    
                    # ============================================================
                    # SECTION 2: ROUTES WITH FEWEST STOPS
                    # ============================================================
                    st.markdown("---")
                    st.markdown("### 🔗 Routes with Fewest Stops")
                    st.caption(f"Routes with minimum connections ({min_stops} stop(s))")
                    
                    if min_stops >= 5:
                        st.warning(f"⚠️ Minimum available: {min_stops} stops. Contact logistics for assistance.")
                    
                    st.info(f"💡 These routes have only **{min_stops} stop(s)** - the minimum available for this route.")
                    
                    for i, route in enumerate(fewest_stops_routes[:3], 1):
                        display_route_card(route, i, "fewest", search_date)
                
                else:
                    # No routes on selected date
                    st.warning(f"⚠️ No connecting routes on {selected_date}. Searching next available...")
                    
                    for day_offset in range(1, 8):
                        alt_date = search_date + timedelta(days=day_offset)
                        alt_routes = find_all_routes_bfs(network, origin, destination, alt_date)
                        
                        if alt_routes:
                            st.info(f"📅 Found {len(alt_routes)} route(s) on {alt_date.strftime('%Y-%m-%d')} (+{day_offset} days)")
                            
                            fastest, fewest = get_fastest_and_fewest_stops(alt_routes)
                            
                            if fastest:
                                route = fastest[0]
                                st.markdown(f"""
                                **Fastest on {alt_date.strftime('%Y-%m-%d')}:** {" → ".join(route['path'])} 
                                ({route['stops']} stops) - Arrives: {route['arrival_datetime'].strftime('%H:%M')}
                                """)
                            
                            if fewest:
                                route = fewest[0]
                                st.markdown(f"""
                                **Fewest stops on {alt_date.strftime('%Y-%m-%d')}:** {" → ".join(route['path'])} 
                                ({route['stops']} stops) - Arrives: {route['arrival_datetime'].strftime('%H:%M')}
                                """)
                            break
                    else:
                        if not direct_results:
                            st.error(f"❌ No routes found from {origin} to {destination}")
            else:
                if not direct_results:
                    st.error("No flight network available.")
        
        except Exception as e:
            st.error(f"Error: {str(e)}")
            import traceback
            st.error(traceback.format_exc())

# Main Application
def main():
    # Sidebar
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
            st.success("✅ File uploaded!")
    
    # Main content
    if uploaded_file:
        with st.spinner("Loading flight data..."):
            schedule_df, routes_df = load_data(uploaded_file)
        
        if schedule_df is not None and routes_df is not None:
            # Statistics
            st.markdown("<h2 style='color: #351C15;'>📊 Network Statistics</h2>", unsafe_allow_html=True)
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Flights", f"{len(schedule_df):,}")
            with col2:
                st.metric("Route Pairs", f"{len(routes_df):,}")
            with col3:
                st.metric("Airports", f"{schedule_df['Orig'].nunique()}")
            with col4:
                carriers = schedule_df['Carrier'].nunique() if 'Carrier' in schedule_df.columns else 0
                st.metric("Carriers", f"{carriers}")
            
            st.markdown("---")
            
            # Tab selection using radio buttons to avoid rerun issues
            tab_selection = st.radio(
                "Select Route Type:",
                ["📋 Tracked Routes", "🔧 Custom Routes"],
                horizontal=True,
                key="tab_selector"
            )
            
            st.markdown("---")
            
            if tab_selection == "📋 Tracked Routes":
                # Tracked Routes
                st.markdown("<h2 style='color: #351C15;'>🔍 Tracked Route Finder</h2>", unsafe_allow_html=True)
                st.info("Select from pre-defined route pairs")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    route_pairs = routes_df[['Origin Airport', 'Destination Airport']].drop_duplicates().dropna()
                    
                    route_options = []
                    route_dict = {}
                    for idx, row in route_pairs.iterrows():
                        route_str = f"{row['Origin Airport']} → {row['Destination Airport']}"
                        route_options.append(route_str)
                        route_dict[route_str] = (row['Origin Airport'], row['Destination Airport'])
                    
                    selected_route = st.selectbox(
                        "Select Route",
                        options=sorted(route_options),
                        key="tracked_route_select"
                    )
                    
                    if selected_route:
                        origin, destination = route_dict[selected_route]
                
                with col2:
                    min_date = schedule_df['Start Date (LZ)'].min()
                    max_date = schedule_df['End Date (LZ)'].max()
                    
                    if pd.notna(min_date) and pd.notna(max_date):
                        selected_date = st.date_input(
                            "Select Date",
                            value=min_date.date(),
                            min_value=min_date.date(),
                            max_value=max_date.date(),
                            key="tracked_date_select"
                        )
                
                if st.button("🔍 Find Routes", type="primary", use_container_width=True, key="tracked_search_btn"):
                    if selected_route:
                        display_route_results(origin, destination, selected_date, schedule_df)
            
            else:
                # Custom Routes
                st.markdown("<h2 style='color: #351C15;'>🔍 Custom Route Finder</h2>", unsafe_allow_html=True)
                st.info("Select any origin and destination")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    origins = sorted(schedule_df['Orig'].dropna().unique())
                    custom_origin = st.selectbox(
                        "Origin Airport",
                        options=origins,
                        key="custom_origin_select"
                    )
                
                with col2:
                    destinations = sorted(schedule_df['Dest'].dropna().unique())
                    custom_destination = st.selectbox(
                        "Destination Airport",
                        options=destinations,
                        key="custom_dest_select"
                    )
                
                with col3:
                    min_date = schedule_df['Start Date (LZ)'].min()
                    max_date = schedule_df['End Date (LZ)'].max()
                    
                    if pd.notna(min_date) and pd.notna(max_date):
                        custom_date = st.date_input(
                            "Select Date",
                            value=min_date.date(),
                            min_value=min_date.date(),
                            max_value=max_date.date(),
                            key="custom_date_select"
                        )
                
                st.markdown(f"""
                <div style="background-color: #FFF8E8; padding: 15px; border-radius: 5px; border-left: 3px solid #FFB500; margin: 20px 0;">
                    <strong>Route:</strong> {custom_origin} → {custom_destination}<br>
                    <strong>Date:</strong> {custom_date}
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("🔍 Find Routes", type="primary", use_container_width=True, key="custom_search_btn"):
                    if custom_origin and custom_destination:
                        if custom_origin == custom_destination:
                            st.warning("⚠️ Select different airports.")
                        else:
                            display_route_results(custom_origin, custom_destination, custom_date, schedule_df)
    
    else:
        st.info("👈 Please upload the UPS Flight Schedule Excel file to begin")

if __name__ == "__main__":
    main()
