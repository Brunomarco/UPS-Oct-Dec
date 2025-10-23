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

# Header with UPS branding - Exact shield logo from image
st.markdown("""
<div class="main-header">
    <div style="padding: 20px; display: inline-block;">
        <svg width="140" height="140" viewBox="0 0 200 230">
            <!-- Outer yellow/gold shield with curved top -->
            <path d="M 100 20 
                     C 100 20 180 40 180 40
                     L 180 130
                     C 180 130 180 190 100 210
                     C 20 190 20 130 20 130
                     L 20 40
                     C 20 40 100 20 100 20 Z" 
                  fill="#FCB514" stroke="none"/>
            
            <!-- Inner brown shield -->
            <path d="M 100 35 
                     C 100 35 165 50 165 50
                     L 165 125
                     C 165 125 165 175 100 190
                     C 35 175 35 125 35 125
                     L 35 50
                     C 35 50 100 35 100 35 Z" 
                  fill="#351C15" stroke="none"/>
            
            <!-- UPS Letters in gold/yellow -->
            <!-- U -->
            <path d="M 50 70 L 50 120 C 50 140 60 150 75 150 C 90 150 100 140 100 120 L 100 70 L 85 70 L 85 120 C 85 130 82 135 75 135 C 68 135 65 130 65 120 L 65 70 Z" 
                  fill="#FCB514"/>
            
            <!-- P -->
            <path d="M 105 70 L 105 150 L 120 150 L 120 110 L 130 110 C 145 110 155 100 155 90 C 155 80 145 70 130 70 Z M 120 85 L 130 85 C 135 85 140 87 140 90 C 140 93 135 95 130 95 L 120 95 Z" 
                  fill="#FCB514"/>
            
            <!-- S -->
            <path d="M 160 70 C 160 70 175 70 175 70 C 185 70 190 75 190 85 C 190 95 185 100 175 100 L 170 100 C 160 100 155 105 155 115 L 155 130 C 155 140 160 150 175 150 C 190 150 190 150 190 150 L 190 135 L 175 135 C 170 135 170 130 170 130 C 170 125 170 115 175 115 L 180 115 C 195 115 205 105 205 90 L 205 85 C 205 70 195 70 180 70 L 160 70 Z" 
                  fill="#FCB514" transform="scale(0.8) translate(45, 18)"/>
        </svg>
    </div>
    <h1 style="color: #FFB500; margin: 15px 0;">Flight Routing System</h1>
    <p style="color: white; margin: 0; font-size: 18px;">Optimized Shipment Routing Dashboard</p>
</div>
""", unsafe_allow_html=True)

# Dashboard Description - Collapsible Dropdown
st.markdown("---")

with st.expander("📦 **Dashboard Overview - Click to learn how this system works**", expanded=False):
    st.write("""
    This dashboard helps UPS logistics teams plan the best flight routes for package shipments between airports.

    Imagine you need to ship a package from Atlanta to Paris. There might not be a direct UPS flight, so you need 
    to find connecting flights through other cities like Louisville or Newark. This tool does that search automatically - 
    it looks through all available UPS flights and finds the fastest way to get your package from point A to point B.
    """)

    st.subheader("How the Dashboard Works:")

    st.write("""
    The system follows a simple but smart process to find your best shipping routes:

    **1. First, it checks for direct flights:**
    The dashboard looks for any non-stop flights between your selected airports. If a direct flight exists on your 
    chosen date (or within the next 14 days), it will show you those options first since they're usually fastest.

    **2. If no direct flights, it finds connections:**
    When there's no direct route, the system builds a map of all possible flight combinations. It looks for ways to 
    connect through other airports, making sure you have at least 1 hour between flights to transfer cargo (but not 
    more than 24 hours of waiting).

    **3. It respects flight schedules:**
    Not all flights operate every day. Some might only fly on Mondays and Thursdays, others daily. The dashboard 
    checks which flights are actually available on your selected date and only shows you real, bookable options.

    **4. Finally, it ranks by speed:**
    All found routes are sorted by total journey time (including waiting times at airports), showing you the fastest 
    options first.
    """)

    st.subheader("What Information You'll Get:")

    st.write("""
    For each route the dashboard finds, you'll see complete details to help you make shipping decisions:

    📍 **The Complete Route Path:** Which airports your package will go through
       Example: ATL → SDF → CDG means Atlanta to Louisville to Paris

    ✈️ **Carrier Information:** Which airline operates each flight segment
       Example: Flight 1 by 5X, Flight 2 by SRR

    🕐 **Precise Timing:** Departure and arrival times for each flight
       Example: Depart ATL at 14:30, Arrive SDF at 15:45

    ⏱️ **Duration Breakdown:** How long each flight takes and waiting times between connections
       Example: Flight time 1h 15m, Wait at SDF 2h 30m, Flight time 8h 20m

    📊 **Total Journey Time:** Complete time from origin to destination
       Example: Total journey: 12h 5m (including all flights and waiting times)

    📅 **Date Intelligence:** If no flights on your selected date, it automatically shows the next available options
       Example: No flights today, but found routes starting tomorrow
    """)
    
    st.divider()
    
    st.subheader("❓ What Does '✅ Found 10 connecting route(s)!' Mean?")
    
    st.info("""
    **This message appears after the system searches for routes with connections (stops).**
    
    When you see "✅ Found 10 connecting route(s)!", it means:
    
    • **✅** = Success! The search completed successfully
    • **10** = The system found 10 different ways to get from origin to destination
    • **connecting route(s)** = These routes require stops/connections (not direct flights)
    
    **Example:** If shipping from Miami (MIA) to Berlin (BER), the system might find:
    - Route 1: MIA → Louisville (SDF) → Cologne (CGN) → BER
    - Route 2: MIA → Philadelphia (PHL) → Frankfurt (FRA) → BER
    - Route 3: MIA → Newark (EWR) → Munich (MUC) → BER
    - ... and 7 more route options
    
    **Why show multiple routes?**
    Different routes offer different advantages:
    - Some are faster (shortest total time)
    - Some have shorter layovers (less waiting)
    - Some use preferred carriers
    - Some depart at more convenient times
    
    The system shows you up to 10 options so you can choose based on your specific needs.
    """)

    st.success("""
    💡 **Pro Tip:** The dashboard shows routes sorted from fastest to slowest total journey time. 
    The first route shown is usually the quickest way to get your package to its destination!
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

def find_direct_flights(schedule_df, origin, destination, date, days_ahead=14):
    """Find direct flights - ALWAYS check same day first, then next available days"""
    try:
        # Filter for the specific route
        route_flights = schedule_df[
            (schedule_df['Orig'] == origin) & 
            (schedule_df['Dest'] == destination)
        ].copy()
        
        if route_flights.empty:
            return []
        
        results = []
        flights_by_date = {}
        
        # ALWAYS start with the requested date (day 0)
        for day_offset in range(days_ahead + 1):
            check_date = date + timedelta(days=day_offset)
            flights_on_date = []
            
            for idx, flight in route_flights.iterrows():
                try:
                    # Check if flight operates on this day of week
                    if is_flight_available_on_date(flight['DOW(S)'], check_date):
                        # Check if date is within flight's operating period
                        if pd.notna(flight['Start Date (LZ)']) and pd.notna(flight['End Date (LZ)']):
                            if flight['Start Date (LZ)'].date() <= check_date.date() <= flight['End Date (LZ)'].date():
                                flight_copy = flight.copy()
                                flight_copy['flight_date'] = check_date
                                
                                # Add departure time for sorting
                                dep_time = parse_time_to_minutes(flight['Sched Out(L)'])
                                flight_copy['dep_minutes'] = dep_time if dep_time else 0
                                
                                flights_on_date.append(flight_copy)
                except:
                    continue
            
            if flights_on_date:
                # Sort flights by departure time (earliest first)
                flights_on_date.sort(key=lambda x: x['dep_minutes'])
                
                flights_by_date[check_date] = {
                    'date': check_date,
                    'flights': flights_on_date,
                    'days_from_requested': day_offset
                }
        
        # Convert to list, already in date order
        for date_key in sorted(flights_by_date.keys()):
            results.append(flights_by_date[date_key])
            if len(results) >= 3:  # Show up to 3 different dates
                break
        
        # If we found same-day flights, always show them first
        if results and results[0]['days_from_requested'] == 0:
            st.success(f"✅ Found {len(results[0]['flights'])} flight(s) on your selected date!")
        elif results:
            st.warning(f"No flights on selected date. Showing next available starting {results[0]['days_from_requested']} day(s) later.")
        
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
                                        'carrier': str(flight.get('Carrier', 'N/A')),
                                        'flight_num': f"{flight.get('Carrier', '')}{flight.get('Flight #', '')}",
                                        'duration': arr_time - dep_time,
                                        'date': check_date,
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

def find_connecting_routes(network, origin, destination, start_date, max_stops=2):
    """Find ALL possible connecting flights with proper time sequencing - earliest flights first"""
    if origin not in network:
        return []
    
    all_routes = []
    
    # Get ALL flights from origin, sorted by date and time
    initial_flights = network.get(origin, [])
    initial_flights.sort(key=lambda x: (x['date'], x['departure']))
    
    # Try each initial flight as a starting point
    for first_flight in initial_flights:
        # Queue for BFS from this starting flight
        queue = [(
            first_flight['destination'],
            [origin, first_flight['destination']],
            first_flight['arrival'],
            first_flight['date'],
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
            }]
        )]
        
        visited_for_this_start = set()
        
        while queue:
            current_airport, path, last_arrival, last_date, total_duration, route_info = queue.pop(0)
            
            # Create unique state for this path
            state = (current_airport, tuple(path), last_date.date(), last_arrival)
            if state in visited_for_this_start:
                continue
            visited_for_this_start.add(state)
            
            # Check if we've reached destination
            if current_airport == destination:
                all_routes.append({
                    'path': path,
                    'stops': len(path) - 2,
                    'total_duration': total_duration,
                    'route_info': route_info,
                    'start_date': route_info[0]['date'],
                    'end_date': route_info[-1]['date']
                })
                continue
            
            # Check stop limit
            if len(path) - 1 >= max_stops + 1:
                continue
            
            # Find ALL possible connecting flights from current airport
            if current_airport in network:
                # Get all flights from current airport, sorted by date and time
                possible_connections = sorted(network[current_airport], key=lambda x: (x['date'], x['departure']))
                
                for next_flight in possible_connections:
                    # Skip if destination already in path (no cycles)
                    if next_flight['destination'] in path:
                        continue
                    
                    # Calculate connection time
                    min_connection = 60  # 1 hour minimum
                    
                    # Determine if flight is valid based on timing
                    valid_connection = False
                    wait_time = 0
                    
                    if next_flight['date'].date() > last_date.date():
                        # Next flight is on a future day
                        days_diff = (next_flight['date'].date() - last_date.date()).days
                        wait_time = (days_diff - 1) * 24 * 60 + (24 * 60 - last_arrival) + next_flight['departure']
                        valid_connection = wait_time <= 1440  # Max 24 hours wait
                    elif next_flight['date'].date() == last_date.date():
                        # Same day - check if departure is after arrival + minimum connection
                        if next_flight['departure'] >= last_arrival + min_connection:
                            wait_time = next_flight['departure'] - last_arrival
                            valid_connection = wait_time <= 1440
                    
                    # Add this connection if valid
                    if valid_connection and min_connection <= wait_time <= 1440:
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
                        
                        queue.append((
                            next_flight['destination'],
                            path + [next_flight['destination']],
                            next_flight['arrival'],
                            next_flight['date'],
                            new_total,
                            new_route_info
                        ))
    
    # Remove duplicate routes (same path and timing)
    unique_routes = []
    seen_routes = set()
    
    for route in all_routes:
        # Create a unique identifier for each route based on path and dates
        route_id = (
            tuple(route['path']),
            route['start_date'].date(),
            route.get('end_date', route['start_date']).date(),
            route['total_duration']
        )
        
        if route_id not in seen_routes:
            seen_routes.add(route_id)
            unique_routes.append(route)
    
    # Sort by: 1) Start date (earliest first), 2) Total duration (shortest first)
    unique_routes.sort(key=lambda x: (x['start_date'], x['total_duration']))
    
    # Return top routes (max 10 to show variety)
    return unique_routes[:10]

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
            st.markdown("<h2 style='color: #351C15;'>🔍 Route Finder</h2>", unsafe_allow_html=True)
            
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
                    help="Select from available route pairs"
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
                        max_value=max_date.date()
                    )
                    
                    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                    day_of_week = day_names[selected_date.weekday()]
                    st.markdown(f"""
                    <div style="background-color: #FFF8E8; padding: 10px; border-radius: 5px; border-left: 3px solid #FFB500;">
                        <strong>Selected Date:</strong> {selected_date} ({day_of_week})
                    </div>
                    """, unsafe_allow_html=True)
            
            # Search button with UPS styling
            if st.button("🔍 Find Available Routes", type="primary", use_container_width=True):
                if selected_route:
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
                                                st.markdown(f"""
                                                <div style="background-color: #FAFAFA; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #FFB500;">
                                                    <h4 style="color: #351C15;">Segment {j}: {leg['from']} → {leg['to']}</h4>
                                                </div>
                                                """, unsafe_allow_html=True)
                                                
                                                col1, col2, col3, col4 = st.columns(4)
                                                
                                                with col1:
                                                    st.markdown("**Date & Carrier**")
                                                    st.write(f"📅 {leg['date'].strftime('%Y-%m-%d')}")
                                                    st.write(f"📅 {leg['date'].strftime('%A')}")
                                                    st.write(f"✈️ Carrier: {leg['carrier']}")
                                                
                                                with col2:
                                                    st.markdown("**Flight Details**")
                                                    st.write(f"Flight: {leg['flight']}")
                                                    st.write(f"Dep: {leg['departure']}")
                                                    st.write(f"Arr: {leg['arrival']}")
                                                
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
                                    - The route might require more than 2 stops
                                    """)
                            else:
                                if not direct_results:
                                    st.error("No flight network available for the selected date range.")
                        
                        except Exception as e:
                            st.error(f"Error during search: {str(e)}")
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
