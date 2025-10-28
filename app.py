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
       - System shows: All Tuesday flights only
    
    2. **No flights on selected Tuesday, flights on Thursday:**
       - System shows: Thursday flights (earliest available)
    
    3. **Connecting flights with date search:**
       - System checks connections for up to 7 days from selected date
       - Minimum 1-hour connection time must be met
       - Routes sorted by departure date, then by total journey time
    """)

    st.markdown("""
    ### Output Interpretation
    
    **Route Display Format:**
    - **Direct Flights**: Shows departure/arrival times, flight number, and carrier
    - **Connecting Flights**: Displays each segment with connection waiting times
    - **Total Journey Time**: Includes all flight times plus connection waiting periods
    - **Date Indicators**: Clearly shows if departing on selected date or days forward
    
    **Status Indicators:**
    - ✅ Green: Routes available on selected date
    - ⚠️ Yellow: Routes available but on future dates
    - ❌ Red: No routes available within search window
    """)

    st.markdown("""
    ### Operational Notes
    
    - All times displayed are in **local time** for each airport
    - Day of week codes: 1=Monday, 2=Tuesday, ..., 7=Sunday
    - Flight schedules respect active date ranges (Start/End Date LZ)
    - System validates that flights operate on the specific day of the week
    """)

st.markdown("---")

# Helper Functions
def format_duration(minutes):
    """Format duration from minutes to hours and minutes"""
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}h {mins}m"

def parse_time(time_str):
    """Parse time from various formats to datetime.time object"""
    if pd.isna(time_str) or time_str == '':
        return None
    
    time_str = str(time_str)
    
    # Handle datetime objects
    if isinstance(time_str, pd.Timestamp):
        return time_str.time()
    
    # Try different time formats
    for fmt in ['%H:%M:%S', '%H:%M', '%I:%M %p', '%I:%M:%S %p']:
        try:
            return datetime.strptime(time_str, fmt).time()
        except:
            continue
    
    return None

def is_flight_valid_for_date(flight, target_date):
    """Check if a flight operates on a given date"""
    # Check if date is within valid range
    start_date = pd.to_datetime(flight['Start Date (LZ)'], errors='coerce')
    end_date = pd.to_datetime(flight['End Date (LZ)'], errors='coerce')
    
    if pd.isna(start_date) or pd.isna(end_date):
        return False
    
    if not (start_date.date() <= target_date.date() <= end_date.date()):
        return False
    
    # Check day of week
    dow_str = str(flight.get('DOW(S)', ''))
    if dow_str and dow_str != 'nan':
        # Get the day of week for target_date (1=Monday, 7=Sunday)
        target_dow = target_date.isoweekday()
        
        # Check if this day is in the DOW(S) string
        if str(target_dow) not in dow_str:
            return False
    
    return True

def search_direct_flights(df, origin, destination, start_date, days_to_search=7):
    """Search for direct flights within a date range"""
    results = []
    
    for days_offset in range(days_to_search):
        search_date = start_date + timedelta(days=days_offset)
        
        # Filter for direct flights on this specific date
        mask = (
            (df['Orig'] == origin) & 
            (df['Dest'] == destination)
        )
        
        direct_flights = df[mask].copy()
        
        # Filter for flights valid on this date
        valid_flights = []
        for idx, flight in direct_flights.iterrows():
            if is_flight_valid_for_date(flight, search_date):
                flight_copy = flight.copy()
                flight_copy['departure_date'] = search_date
                valid_flights.append(flight_copy)
        
        if valid_flights:
            # If we found flights on the selected date, only return those
            if days_offset == 0:
                return valid_flights
            # Otherwise, return the first available date's flights
            else:
                return valid_flights
    
    return []

def build_network(df, base_date):
    """Build a network graph of flights for connecting routes"""
    network = {}
    
    for idx, row in df.iterrows():
        origin = row['Orig']
        dest = row['Dest']
        
        if origin not in network:
            network[origin] = []
        
        # Parse times
        dep_time = parse_time(row['Sched Out (L)'])
        arr_time = parse_time(row['Sched In (L)'])
        
        if dep_time and arr_time:
            # Calculate duration
            try:
                duration_str = str(row.get('Blkhr', '0:00'))
                if ':' in duration_str:
                    hours, minutes = duration_str.split(':')
                    duration_minutes = int(hours) * 60 + int(minutes)
                else:
                    duration_minutes = 0
            except:
                duration_minutes = 0
            
            flight_info = {
                'dest': dest,
                'flight': row.get('Flight #', 'N/A'),
                'carrier': row.get('Carrier', 'N/A'),
                'dep_time': dep_time,
                'arr_time': arr_time,
                'duration': duration_minutes,
                'duration_str': row.get('Blkhr', 'N/A'),
                'dow': str(row.get('DOW(S)', '')),
                'start_date': pd.to_datetime(row['Start Date (LZ)'], errors='coerce'),
                'end_date': pd.to_datetime(row['End Date (LZ)'], errors='coerce')
            }
            
            network[origin].append(flight_info)
    
    return network

def find_connecting_routes(network, origin, destination, base_date, max_stops=2, days_to_search=7):
    """Find all possible connecting routes"""
    all_routes = []
    
    # Search for routes starting on different days
    for day_offset in range(days_to_search):
        search_date = base_date + timedelta(days=day_offset)
        routes = find_routes_for_date(network, origin, destination, search_date, max_stops)
        all_routes.extend(routes)
    
    # Sort by departure date first, then by total duration
    all_routes.sort(key=lambda x: (x['start_date'], x['total_duration']))
    
    return all_routes

def find_routes_for_date(network, origin, destination, start_date, max_stops=2):
    """Find routes starting on a specific date"""
    routes = []
    
    def dfs(current_airport, target, path, stops, current_datetime, route_info):
        if stops > max_stops:
            return
        
        if current_airport == target and stops > 0:
            # Calculate total duration
            total_duration = int((current_datetime - start_date).total_seconds() / 60)
            
            routes.append({
                'path': path,
                'stops': stops - 1,  # Number of intermediate stops
                'total_duration': total_duration,
                'start_date': start_date,
                'end_date': current_datetime,
                'route_info': route_info
            })
            return
        
        if current_airport in network:
            for flight in network[current_airport]:
                # Check if flight is valid for the current day
                flight_date = current_datetime.date() if stops > 0 else start_date.date()
                
                # Check if date is within flight's valid range
                if pd.notna(flight['start_date']) and pd.notna(flight['end_date']):
                    if not (flight['start_date'].date() <= flight_date <= flight['end_date'].date()):
                        continue
                
                # Check day of week
                if flight['dow'] and flight['dow'] != 'nan':
                    dow = (flight_date.isoweekday())
                    if str(dow) not in flight['dow']:
                        continue
                
                # Calculate departure and arrival times
                dep_datetime = datetime.combine(flight_date, flight['dep_time'])
                
                # For connecting flights, ensure minimum connection time
                if stops > 0:
                    # Check minimum 1-hour connection time
                    time_diff = (dep_datetime - current_datetime).total_seconds() / 60
                    
                    if time_diff < 60:  # Less than 1 hour connection
                        # Try next day
                        dep_datetime = datetime.combine(flight_date + timedelta(days=1), flight['dep_time'])
                        time_diff = (dep_datetime - current_datetime).total_seconds() / 60
                        
                        # Check if next day is valid for this flight
                        next_day = (flight_date + timedelta(days=1)).isoweekday()
                        if flight['dow'] and str(next_day) not in flight['dow']:
                            continue
                        
                        if time_diff > 1440:  # More than 24 hours
                            continue
                    elif time_diff > 1440:  # More than 24 hours connection
                        continue
                
                # Calculate arrival time (handling day rollover)
                arr_datetime = dep_datetime + timedelta(minutes=flight['duration'])
                
                # Build route information
                new_route_info = route_info.copy()
                
                # Add waiting time for connections
                if stops > 0:
                    wait_time = int((dep_datetime - current_datetime).total_seconds() / 60)
                else:
                    wait_time = 0
                
                leg_info = {
                    'from': current_airport,
                    'to': flight['dest'],
                    'flight': flight['flight'],
                    'carrier': flight['carrier'],
                    'departure': flight['dep_time'].strftime('%H:%M'),
                    'arrival': flight['arr_time'].strftime('%H:%M'),
                    'duration': flight['duration'],
                    'duration_str': flight['duration_str'],
                    'date': dep_datetime,
                    'wait_time': wait_time
                }
                
                new_route_info.append(leg_info)
                
                # Continue search
                dfs(flight['dest'], target, path + [flight['dest']], 
                    stops + 1, arr_datetime, new_route_info)
    
    # Start DFS from origin
    dfs(origin, destination, [origin], 0, start_date, [])
    
    return routes

def main():
    # File Upload in Sidebar
    with st.sidebar:
        st.markdown("### 📁 Upload Flight Schedule")
        uploaded_file = st.file_uploader(
            "Upload UPS Flight Schedule Excel",
            type=['xlsx', 'xls'],
            help="Upload the Excel file with flight schedule data"
        )
        
        st.markdown("""
        <div style="background-color: #FFF8E8; padding: 15px; border-radius: 10px; margin-top: 20px;">
            <p style="color: #351C15; font-weight: bold;">📝 Required Excel Sheets:</p>
            <ol style="color: #351C15;">
                <li>SchedDateLocalTimeFlightSchedul</li>
                <li>Data (for Tab 1)</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
    
    # Main content area
    if uploaded_file is not None:
        try:
            # Load Excel sheets
            schedule_df = pd.read_excel(uploaded_file, sheet_name='SchedDateLocalTimeFlightSchedul')
            
            # Try to load Data sheet for Tab 1
            try:
                data_df = pd.read_excel(uploaded_file, sheet_name='Data')
                has_data_sheet = True
            except:
                has_data_sheet = False
                data_df = None
            
            # Get unique origins and destinations for Tab 2
            unique_origins = sorted(schedule_df['Orig'].dropna().unique())
            unique_destinations = sorted(schedule_df['Dest'].dropna().unique())
            
            # Create tabs
            tab1, tab2 = st.tabs(["📊 Tab 1: Predefined Routes", "🔍 Tab 2: Custom Route Selection"])
            
            # TAB 1 - Original functionality
            with tab1:
                st.markdown("### 📊 Predefined Route Analysis")
                st.info("This tab uses the origin-destination pair from the 'Data' sheet in your Excel file.")
                
                if has_data_sheet and data_df is not None and not data_df.empty:
                    # Extract origin and destination from Data sheet
                    origin = data_df.iloc[0]['Origin Airport']
                    destination = data_df.iloc[0]['Destination Airport']
                    
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3 style="color: #351C15;">Selected Route Information</h3>
                        <p><strong>Origin:</strong> {origin}</p>
                        <p><strong>Destination:</strong> {destination}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Date selection
                    st.markdown("### 📅 Select Travel Date")
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        selected_date = st.date_input(
                            "Choose departure date:",
                            value=datetime.today(),
                            min_value=datetime.today(),
                            max_value=datetime.today() + timedelta(days=365)
                        )
                    
                    with col2:
                        st.markdown(f"""
                        <div style="background-color: #E8F4F8; padding: 15px; border-radius: 10px; margin-top: 25px;">
                            <strong>Selected: {selected_date.strftime('%A')}</strong>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Search button
                    if st.button("🔍 Search Available Routes", key="search_tab1"):
                        search_date = datetime.combine(selected_date, datetime.min.time())
                        
                        with st.spinner(f"Searching for routes from {origin} to {destination}..."):
                            # Search for direct flights
                            st.info(f"🔍 Searching for direct flights from {origin} to {destination} starting from {selected_date}...")
                            
                            direct_results = search_direct_flights(schedule_df, origin, destination, search_date)
                            
                            if direct_results:
                                # Check if results are on selected date
                                first_flight_date = direct_results[0]['departure_date'].date()
                                days_difference = (first_flight_date - selected_date).days
                                
                                if days_difference == 0:
                                    st.success(f"✅ Found {len(direct_results)} direct flight(s) on your selected date!")
                                else:
                                    st.warning(f"⚠️ No flights on {selected_date}. Showing flights from {first_flight_date} (+{days_difference} days)")
                                
                                # Display direct flights
                                for i, flight in enumerate(direct_results, 1):
                                    departure_date = flight['departure_date']
                                    
                                    with st.expander(f"✈️ Direct Flight {i} - {departure_date.strftime('%Y-%m-%d')} ({departure_date.strftime('%A')})", expanded=i==1):
                                        col1, col2, col3, col4 = st.columns(4)
                                        
                                        with col1:
                                            st.markdown("**Flight Details**")
                                            st.write(f"Flight: {flight.get('Flight #', 'N/A')}")
                                            st.write(f"Carrier: {flight.get('Carrier', 'N/A')}")
                                        
                                        with col2:
                                            st.markdown("**Departure**")
                                            st.write(f"Airport: {origin}")
                                            st.write(f"Time: {flight.get('Sched Out (L)', 'N/A')}")
                                            st.write(f"Date: {departure_date.strftime('%Y-%m-%d')}")
                                        
                                        with col3:
                                            st.markdown("**Arrival**")
                                            st.write(f"Airport: {destination}")
                                            st.write(f"Time: {flight.get('Sched In (L)', 'N/A')}")
                                        
                                        with col4:
                                            st.markdown("**Duration**")
                                            st.write(f"Flight Time: {flight.get('Blkhr', 'N/A')}")
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
                        
                else:
                    st.warning("""
                    ⚠️ No 'Data' sheet found in the uploaded Excel file or the sheet is empty.
                    
                    Please ensure your Excel file contains a 'Data' sheet with columns:
                    - Origin Airport
                    - Destination Airport
                    
                    Alternatively, you can use Tab 2 to manually select origin and destination airports.
                    """)
            
            # TAB 2 - Custom selection
            with tab2:
                st.markdown("### 🔍 Custom Route Selection")
                st.info("Select your own origin and destination airports from the available options in the flight schedule.")
                
                # Origin and Destination Selection
                col1, col2 = st.columns(2)
                
                with col1:
                    selected_origin = st.selectbox(
                        "Select Origin Airport:",
                        options=unique_origins,
                        help="Choose the departure airport"
                    )
                
                with col2:
                    selected_destination = st.selectbox(
                        "Select Destination Airport:",
                        options=unique_destinations,
                        help="Choose the arrival airport"
                    )
                
                # Display selected route
                if selected_origin and selected_destination:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3 style="color: #351C15;">Selected Route</h3>
                        <p><strong>From:</strong> {selected_origin} → <strong>To:</strong> {selected_destination}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Date selection
                st.markdown("### 📅 Select Travel Date")
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    selected_date_tab2 = st.date_input(
                        "Choose departure date:",
                        value=datetime.today(),
                        min_value=datetime.today(),
                        max_value=datetime.today() + timedelta(days=365),
                        key="date_tab2"
                    )
                
                with col2:
                    st.markdown(f"""
                    <div style="background-color: #E8F4F8; padding: 15px; border-radius: 10px; margin-top: 25px;">
                        <strong>Selected: {selected_date_tab2.strftime('%A')}</strong>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Search button
                if st.button("🔍 Search Available Routes", key="search_tab2"):
                    if selected_origin == selected_destination:
                        st.error("❌ Origin and destination cannot be the same. Please select different airports.")
                    else:
                        search_date = datetime.combine(selected_date_tab2, datetime.min.time())
                        
                        with st.spinner(f"Searching for routes from {selected_origin} to {selected_destination}..."):
                            # Search for direct flights
                            st.info(f"🔍 Searching for direct flights from {selected_origin} to {selected_destination} starting from {selected_date_tab2}...")
                            
                            direct_results = search_direct_flights(schedule_df, selected_origin, selected_destination, search_date)
                            
                            if direct_results:
                                # Check if results are on selected date
                                first_flight_date = direct_results[0]['departure_date'].date()
                                days_difference = (first_flight_date - selected_date_tab2).days
                                
                                if days_difference == 0:
                                    st.success(f"✅ Found {len(direct_results)} direct flight(s) on your selected date!")
                                else:
                                    st.warning(f"⚠️ No flights on {selected_date_tab2}. Showing flights from {first_flight_date} (+{days_difference} days)")
                                
                                # Display direct flights
                                for i, flight in enumerate(direct_results, 1):
                                    departure_date = flight['departure_date']
                                    
                                    with st.expander(f"✈️ Direct Flight {i} - {departure_date.strftime('%Y-%m-%d')} ({departure_date.strftime('%A')})", expanded=i==1):
                                        col1, col2, col3, col4 = st.columns(4)
                                        
                                        with col1:
                                            st.markdown("**Flight Details**")
                                            st.write(f"Flight: {flight.get('Flight #', 'N/A')}")
                                            st.write(f"Carrier: {flight.get('Carrier', 'N/A')}")
                                        
                                        with col2:
                                            st.markdown("**Departure**")
                                            st.write(f"Airport: {selected_origin}")
                                            st.write(f"Time: {flight.get('Sched Out (L)', 'N/A')}")
                                            st.write(f"Date: {departure_date.strftime('%Y-%m-%d')}")
                                        
                                        with col3:
                                            st.markdown("**Arrival**")
                                            st.write(f"Airport: {selected_destination}")
                                            st.write(f"Time: {flight.get('Sched In (L)', 'N/A')}")
                                        
                                        with col4:
                                            st.markdown("**Duration**")
                                            st.write(f"Flight Time: {flight.get('Blkhr', 'N/A')}")
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
                                routes = find_connecting_routes(network, selected_origin, selected_destination, search_date)
                                
                                if routes:
                                    # Check if we have same-day departure routes
                                    same_day_routes = [r for r in routes if r['start_date'].date() == search_date.date()]
                                    
                                    if same_day_routes:
                                        st.success(f"✅ Found {len(same_day_routes)} connecting route(s) departing on your selected date!")
                                    else:
                                        st.warning(f"⚠️ No connecting routes on {selected_date_tab2}. Showing routes starting from next available dates.")
                                    
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
                                    ❌ No routes found from {selected_origin} to {selected_destination}
                                    
                                    **Suggestions:**
                                    - This route may not be served by UPS flights
                                    - Try selecting a different origin-destination pair
                                    - The route might require more than 2 stops
                                    """)
                            else:
                                if not direct_results:
                                    st.error("No flight network available for the selected date range.")
                        
        except Exception as e:
            st.error(f"Error loading Excel file: {str(e)}")
            st.info("Please ensure the Excel file has the correct sheets and format.")
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
            <p><strong>Sheet 2: Data</strong> (Optional for Tab 1)</p>
            <ul>
                <li>Origin Airport: Starting airport</li>
                <li>Destination Airport: Final destination</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
