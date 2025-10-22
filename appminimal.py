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

# Header with UPS branding
st.markdown("""
<div class="main-header">
    <div class="ups-logo">
        <h1 style="color: #351C15; margin: 0; font-size: 48px; font-weight: bold;">UPS</h1>
    </div>
    <h1 style="color: #FFB500; margin: 10px 0;">Flight Routing System</h1>
    <p style="color: white; margin: 0;">Optimized Shipment Routing Dashboard</p>
</div>
""", unsafe_allow_html=True)

# Dashboard Description
st.markdown("""
<div class="description-box">
    <h2>📦 Dashboard Overview</h2>
    <p><strong>Purpose:</strong> This dashboard analyzes UPS flight schedules to find the optimal routing for shipments between origin and destination airports.</p>
    
    <h3>🔄 How It Works:</h3>
    <ul>
        <li><strong>Data Processing:</strong> Loads flight schedules with departure/arrival times, operating days (DOW), and valid date ranges</li>
        <li><strong>Route Finding:</strong> Searches for direct flights first, then automatically calculates connecting flights if needed</li>
        <li><strong>Time Optimization:</strong> Ensures minimum 1-hour connection time between flights and finds the fastest total journey time</li>
        <li><strong>Date Intelligence:</strong> Checks flight availability based on day of week and operating period</li>
    </ul>
    
    <h3>📊 Outputs:</h3>
    <ul>
        <li>✈️ <strong>Direct Flights:</strong> Shows all available direct flights with carrier, times, and duration</li>
        <li>🔄 <strong>Connecting Routes:</strong> Up to 2 stops with detailed segment information</li>
        <li>⏱️ <strong>Complete Timing:</strong> Total journey time, individual flight durations, and layover times</li>
        <li>📅 <strong>Date Flexibility:</strong> If no flights on selected date, automatically finds next available options</li>
    </ul>
</div>
""", unsafe_allow_html=True)

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
                
                # Return at least 2 route options if we've found them
                if len(results) >= 2:
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
    """Find connecting flights with proper time sequencing"""
    if origin not in network:
        return []
    
    all_routes = []
    visited = set()
    
    # Queue: (current_airport, path, last_arrival_time, last_arrival_date, total_duration, route_info)
    initial_flights = network.get(origin, [])
    
    for flight in initial_flights:
        queue = [(
            flight['destination'],
            [origin, flight['destination']],
            flight['arrival'],
            flight['date'],
            flight['duration'],
            [{
                'from': origin,
                'to': flight['destination'],
                'date': flight['date'],
                'departure': flight['dep_str'],
                'arrival': flight['arr_str'],
                'duration': flight['duration'],
                'duration_str': flight['duration_str'],
                'carrier': flight['carrier'],
                'flight': flight['flight_num'],
                'wait_time': 0
            }]
        )]
        
        while queue:
            current_airport, path, last_arrival, last_date, total_duration, route_info = queue.pop(0)
            
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
            
            # Find connecting flights
            if current_airport in network:
                for next_flight in network[current_airport]:
                    if next_flight['destination'] in path:
                        continue
                    
                    # Check if next flight is after current arrival (minimum 1 hour connection)
                    min_connection = 60  # 1 hour minimum
                    
                    # Calculate actual connection time
                    if next_flight['date'].date() > last_date.date():
                        # Next flight is on a different day
                        days_diff = (next_flight['date'].date() - last_date.date()).days
                        wait_time = (days_diff * 24 * 60) - last_arrival + next_flight['departure']
                    else:
                        # Same day - check if departure is after arrival + minimum connection
                        if next_flight['date'].date() == last_date.date():
                            if next_flight['departure'] >= last_arrival + min_connection:
                                wait_time = next_flight['departure'] - last_arrival
                            else:
                                continue  # Skip this flight as it's too early
                        else:
                            continue  # Skip flights on earlier dates
                    
                    # Only accept reasonable connection times (1 hour to 24 hours)
                    if min_connection <= wait_time <= 1440:
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
    
    # Sort by total duration and return top routes
    all_routes.sort(key=lambda x: x['total_duration'])
    return all_routes[:5]

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
                            # Search for direct flights
                            direct_results = find_direct_flights(schedule_df, origin, destination, search_date)
                            
                            if direct_results:
                                st.success(f"✅ Found direct flights!")
                                
                                for result in direct_results[:2]:  # Show first 2 available dates
                                    date_diff = result['days_from_requested']
                                    date_label = "✓ On requested date" if date_diff == 0 else f"📅 Next available: +{date_diff} day(s)"
                                    
                                    st.markdown(f"""
                                    <div class="route-card">
                                        <h3 style="color: #351C15;">📅 {result['date'].strftime('%Y-%m-%d (%A)')} - {date_label}</h3>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    for i, flight in enumerate(result['flights'], 1):
                                        with st.expander(f"✈️ Direct Flight Option {i} - Carrier: {flight.get('Carrier', 'N/A')}", expanded=(date_diff == 0)):
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
                                    st.success(f"✅ Found {len(routes)} connecting route(s)!")
                                    
                                    # Show first 2 best routes
                                    for i, route in enumerate(routes[:2], 1):
                                        route_str = " → ".join(route['path'])
                                        total_duration = route['total_duration']
                                        total_hours = total_duration // 60
                                        total_mins = total_duration % 60
                                        
                                        # Calculate total waiting time
                                        total_wait = sum([leg['wait_time'] for leg in route['route_info']])
                                        wait_hours = total_wait // 60
                                        wait_mins = total_wait % 60
                                        
                                        with st.expander(f"🔄 Connecting Route {i}: {route_str} ({route['stops']} stop(s))", expanded=(i == 1)):
                                            
                                            # Route summary
                                            st.markdown(f"""
                                            <div style="background-color: #E8F4F8; padding: 15px; border-radius: 10px; margin-bottom: 15px;">
                                                <h4 style="color: #351C15; margin: 0;">Route Summary</h4>
                                                <p><strong>Route:</strong> {route_str}</p>
                                                <p><strong>Journey Dates:</strong> {route['start_date'].strftime('%Y-%m-%d')} to {route['end_date'].strftime('%Y-%m-%d')}</p>
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
