import io
import heapq
from datetime import datetime, date, time, timedelta
from typing import List, Dict, Tuple, Optional

import pandas as pd
import numpy as np
import streamlit as st

# =========================
# Misc helpers
# =========================

def _norm_col(s: str) -> str:
    if s is None:
        return ""
    return (
        str(s)
        .strip()
        .lower()
        .replace(" ", "")
        .replace("\u00a0", "")
        .replace("(", "")
        .replace(")", "")
        .replace("[", "")
        .replace("]", "")
        .replace("/", "")
        .replace("\\", "")
        .replace(".", "")
        .replace("-", "")
        .replace(":", "")
    )

def ensure_upper_clean(v) -> str:
    if v is None or pd.isna(v):
        return ""
    return str(v).strip().upper()

def parse_hhmm_to_minutes(val) -> Optional[int]:
    if pd.isna(val):
        return None
    s = str(val).strip()
    try:
        hh, mm = s.split(":")
        return int(hh) * 60 + int(mm)
    except Exception:
        return None

def parse_blk_to_minutes(val) -> Optional[int]:
    return parse_hhmm_to_minutes(val)

def parse_excel_date(d) -> Optional[date]:
    if pd.isna(d):
        return None
    dt = pd.to_datetime(d, errors="coerce", dayfirst=False)
    if pd.isna(dt):
        return None
    return dt.date()

def dow_pattern_to_set(pattern: str) -> set:
    """
    Convert DOW(S) like '...4...' or '.2345..' to a set of active weekdays {0..6} (Mon..Sun).
    Any non-dot char means the flight operates that day.
    """
    s = str(pattern).strip() if pattern is not None else ""
    if len(s) < 7:
        s = s.ljust(7, ".")
    elif len(s) > 7:
        s = s[:7]
    active = set()
    for i, ch in enumerate(s):
        if ch != ".":
            active.add(i)  # 0=Mon .. 6=Sun
    return active

def minutes_to_hhmm(m: int) -> str:
    m = int(round(m))
    return f"{(m // 60) % 24:02d}:{m % 60:02d}"

def timedelta_to_hhmm(td: timedelta) -> str:
    total_min = int(td.total_seconds() // 60)
    hours, mins = divmod(total_min, 60)
    return f"{hours:02d}:{mins:02d}"

def combine_date_time(d: date, minutes_since_midnight: int) -> datetime:
    return datetime(d.year, d.month, d.day, minutes_since_midnight // 60, minutes_since_midnight % 60)

def best_arrival_day_offset(dep_min: int, arr_min: int, blk_min: int) -> int:
    """
    Infer arrival day offset k in {-1,0,1,2} so (arr - dep + 1440*k) ~= blk_min.
    Bias ties to 0/1.
    """
    best_k, best_err = 0, 10**9
    for k in (-1, 0, 1, 2):
        diff = (arr_min - dep_min) + k * 1440
        err = abs(diff - blk_min)
        if err < best_err or (err == best_err and k in (0, 1) and best_k not in (0, 1)):
            best_k, best_err = k, err
    return best_k

# =========================
# Excel ingest + autodetect
# =========================

REQUIRED_SCHED_COLS = {
    "carrier", "flight#", "startdatelz", "enddatelz", "dows",
    "orig", "schedoutl", "dest", "schedinl", "blkhr"
}

DATA_ORIG_CANDIDATES = ["Origin Airport", "Origin", "Orig"]
DATA_DEST_CANDIDATES = ["Destination Airport", "Destination", "Dest"]

@st.cache_data(show_spinner=False)
def read_excel(file_bytes: bytes) -> Tuple[pd.ExcelFile, List[str]]:
    bio = io.BytesIO(file_bytes)
    xls = pd.ExcelFile(bio)
    return xls, xls.sheet_names

def detect_sched_sheet(xls: pd.ExcelFile) -> Optional[str]:
    for sh in xls.sheet_names:
        df = xls.parse(sh, nrows=50)
        cols = {_norm_col(c) for c in df.columns}
        if REQUIRED_SCHED_COLS.issubset(cols):
            return sh
    return None

def detect_data_sheet(xls: pd.ExcelFile) -> Optional[str]:
    for sh in xls.sheet_names:
        df = xls.parse(sh, nrows=50)
        cols_norm = {_norm_col(c) for c in df.columns}
        has_o = any(_norm_col(c) in cols_norm for c in DATA_ORIG_CANDIDATES)
        has_d = any(_norm_col(c) in cols_norm for c in DATA_DEST_CANDIDATES)
        if has_o and has_d:
            return sh
    return None

def find_actual_col(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    norm_map = {_norm_col(c): c for c in df.columns}
    for c in candidates:
        cn = _norm_col(c)
        if cn in norm_map:
            return norm_map[cn]
    return None

# =========================
# Leg generation
# =========================

def date_range_inclusive(a: date, b: date) -> List[date]:
    if a is None or b is None: return []
    if b < a: a, b = b, a
    return [a + timedelta(days=i) for i in range((b - a).days + 1)]

def generate_concrete_legs(
    sched_df: pd.DataFrame,
    search_start: date,
    horizon_days: int = 3,
) -> List[dict]:
    """
    Build concrete legs (local datetimes) inside the [search_start, search_start + horizon_days - 1] window.
    Returns a list of dicts: {origin, destination, dep_dt_local, arr_dt_local, blk_min}
    """
    cn = {_norm_col(c): c for c in sched_df.columns}

    Orig = cn["orig"]
    Dest = cn["dest"]
    StartDate = cn["startdatelz"]
    EndDate = cn["enddatelz"]
    SchedOut = cn["schedoutl"]
    SchedIn = cn["schedinl"]
    Blkhr = cn["blkhr"]
    DOWS = cn["dows"]

    legs = []
    window_start = search_start
    window_end = search_start + timedelta(days=horizon_days - 1)

    for _, row in sched_df.iterrows():
        o = ensure_upper_clean(row[Orig])
        d = ensure_upper_clean(row[Dest])

        start_d = parse_excel_date(row[StartDate])
        end_d = parse_excel_date(row[EndDate])
        if start_d is None or end_d is None:
            continue

        dep_min = parse_hhmm_to_minutes(row[SchedOut])
        arr_min = parse_hhmm_to_minutes(row[SchedIn])
        blk_min = parse_blk_to_minutes(row[Blkhr])
        if dep_min is None or arr_min is None or blk_min is None:
            continue

        active = dow_pattern_to_set(row[DOWS])

        # intersect schedule with search window
        rng = date_range_inclusive(max(start_d, window_start), min(end_d, window_end))
        for dte in rng:
            if dte.weekday() not in active:
                continue
            dep_dt = combine_date_time(dte, dep_min)
            k = best_arrival_day_offset(dep_min, arr_min, blk_min)
            arr_dt = combine_date_time(dte + timedelta(days=k), arr_min)
            legs.append({
                "origin": o,
                "destination": d,
                "dep_dt_local": dep_dt,
                "arr_dt_local": arr_dt,
                "blk_min": int(blk_min),
            })

    legs.sort(key=lambda x: (x["origin"], x["dep_dt_local"], x["destination"]))
    return legs

# =========================
# Earliest-arrival routing
# =========================

def plan_itinerary(
    legs: List[dict],
    origin: str,
    destination: str,
    start_date: date,
    earliest_dep_min: int = 0,
    min_connect_min: int = 45,
    max_stops: int = 2,
) -> Optional[dict]:
    """
    Earliest-arrival path using a time-dependent Dijkstra-like search.
    Tracks times in *local* time per airport. Connection waits are computed in local time.
    """
    origin = ensure_upper_clean(origin)
    destination = ensure_upper_clean(destination)

    by_origin: Dict[str, List[dict]] = {}
    for leg in legs:
        by_origin.setdefault(leg["origin"], []).append(leg)
    for k in by_origin:
        by_origin[k].sort(key=lambda x: x["dep_dt_local"])

    start_local_dt = datetime.combine(start_date, time(0, 0)) + timedelta(minutes=earliest_dep_min)

    # priority queue: (elapsed_min, airport, current_local_dt, path_legs)
    pq = []
    heapq.heappush(pq, (0, origin, start_local_dt, []))
    # pruning: best elapsed at (airport, stops_so_far, date_key)
    visited = {}

    while pq:
        elapsed, ap, cur_dt, path = heapq.heappop(pq)

        if ap == destination and path:
            return {
                "total_elapsed": timedelta(minutes=int(elapsed)),
                "legs": path,
                "stops": max(0, len(path) - 1),
                "depart_at": path[0]["dep_dt_local"],
                "arrive_at": path[-1]["arr_dt_local"],
            }

        if len(path) > 0 and (len(path) - 1) > max_stops:
            continue

        key = (ap, len(path), cur_dt.date())
        if key in visited and visited[key] <= elapsed:
            continue
        visited[key] = elapsed

        for leg in by_origin.get(ap, []):
            dep_dt = leg["dep_dt_local"]
            # For first leg, allow >= earliest_dep; otherwise need >= min connection
            wait = (dep_dt - cur_dt).total_seconds() / 60.0
            if wait < (0 if len(path) == 0 else min_connect_min):
                continue

            new_elapsed = elapsed + int(np.ceil(max(0.0, wait))) + int(leg["blk_min"])
            arr_dt = leg["arr_dt_local"]
            new_path = path + [{**leg, "wait_min_before": int(np.ceil(max(0.0, wait)))}]
            heapq.heappush(pq, (new_elapsed, leg["destination"], arr_dt, new_path))

    return None

# =========================
# Streamlit UI
# =========================

st.set_page_config(page_title="Flight Route Planner", page_icon="✈️", layout="wide")
st.title("✈️ Flight Route Planner")
st.caption("Upload the Excel with **SchedDateLocalTimeFlightSchedul** (schedule) and **Data** (route pairs). The app computes the fastest itinerary (direct or with connections) for a selected date.")

with st.sidebar:
    st.header("Routing Settings")
    earliest_dep_str = st.text_input("Earliest departure (HH:MM at origin)", value="00:00")
    earliest_dep_min = parse_hhmm_to_minutes(earliest_dep_str) or 0
    min_connect = st.number_input("Minimum connection time (minutes)", min_value=0, max_value=360, value=45, step=5)
    max_stops = st.select_slider("Max stops (connections)", options=[0, 1, 2, 3], value=2)
    horizon_days = st.slider("Search horizon (days)", min_value=1, max_value=5, value=3, help="Generates flight legs for this window starting the selected date to enable overnight/next-day connections.")
    st.markdown("---")
    st.markdown("**Tips**")
    st.markdown("- If no route is found, widen the search horizon or allow more stops.\n- Adjust earliest departure to your cut-off (e.g., 18:00).")

uploaded = st.file_uploader("Upload Excel (.xlsx)", type=["xlsx"])

if not uploaded:
    st.info("Please upload your Excel file to continue.")
    st.stop()

# Read and detect sheets
xls, sheet_names = read_excel(uploaded.getvalue())
sched_sheet = detect_sched_sheet(xls) or "SchedDateLocalTimeFlightSchedul"
data_sheet = detect_data_sheet(xls) or "Data"

col1, col2 = st.columns(2)
with col1:
    chosen_sched_sheet = st.selectbox("Schedule sheet", sheet_names, index=sheet_names.index(sched_sheet) if sched_sheet in sheet_names else 0)
with col2:
    chosen_data_sheet = st.selectbox("Routes (Data) sheet", sheet_names, index=sheet_names.index(data_sheet) if data_sheet in sheet_names else 0)

# Load sheets
sched_df = xls.parse(chosen_sched_sheet)
data_df = xls.parse(chosen_data_sheet)

# Validate schedule columns
need = REQUIRED_SCHED_COLS - {_norm_col(c) for c in sched_df.columns}
if need:
    st.error(f"Missing required schedule columns: {sorted(list(need))}")
    st.stop()

# Extract route pairs from Data sheet
orig_col = find_actual_col(data_df, DATA_ORIG_CANDIDATES)
dest_col = find_actual_col(data_df, DATA_DEST_CANDIDATES)
if not orig_col or not dest_col:
    st.error("Could not find 'Origin Airport' and 'Destination Airport' columns in the Data sheet.")
    st.stop()

pairs_df = (
    data_df[[orig_col, dest_col]]
    .dropna()
    .assign(
        **{orig_col: lambda d: d[orig_col].astype(str).str.strip().str.upper(),
           dest_col: lambda d: d[dest_col].astype(str).str.strip().str.upper()}
    )
    .drop_duplicates()
    .sort_values([orig_col, dest_col])
    .reset_index(drop=True)
)

# Selection widgets
colA, colB, colC = st.columns([2, 2, 2])
with colA:
    pair_label = pairs_df.apply(lambda r: f"{r[orig_col]} → {r[dest_col]}", axis=1)
    idx = st.selectbox("Select route pair (from Data sheet)", options=pair_label.index, format_func=lambda i: pair_label.iloc[i])
    sel_o = pairs_df.loc[idx, orig_col]
    sel_d = pairs_df.loc[idx, dest_col]
with colB:
    sel_date = st.date_input("Select date", value=date.today())
with colC:
    st.metric("Unique route pairs", len(pairs_df))
    st.metric("Schedule rows", len(sched_df))

# Generate concrete legs in the selected window
with st.spinner("Generating flight legs and searching best itinerary..."):
    legs = generate_concrete_legs(sched_df, sel_date, horizon_days=horizon_days)

# Plan itinerary
itinerary = plan_itinerary(
    legs=legs,
    origin=sel_o,
    destination=sel_d,
    start_date=sel_date,
    earliest_dep_min=earliest_dep_min,
    min_connect_min=min_connect,
    max_stops=max_stops,
)

st.markdown("### Result")

if itinerary is None:
    st.warning("No feasible route found with the current settings. Try widening the search horizon, allowing more stops, or changing the earliest departure.")
else:
    total = itinerary["total_elapsed"]
    depart = itinerary["depart_at"]
    arrive = itinerary["arrive_at"]
    stops = itinerary["stops"]
    st.success("Itinerary found ✅")

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Departure (local)", depart.strftime("%Y-%m-%d %H:%M"))
    with m2:
        st.metric("Arrival (local)", arrive.strftime("%Y-%m-%d %H:%M"))
    with m3:
        st.metric("Transit time (HH:MM)", timedelta_to_hhmm(total))
    with m4:
        st.metric("Stops", stops)

    # Show legs table
    legs_tbl = []
    for i, leg in enumerate(itinerary["legs"], start=1):
        legs_tbl.append({
            "Leg #": i,
            "Origin": leg["origin"],
            "Destination": leg["destination"],
            "Wait before (min)": leg.get("wait_min_before", 0),
            "Dep (local)": leg["dep_dt_local"].strftime("%Y-%m-%d %H:%M"),
            "Arr (local)": leg["arr_dt_local"].strftime("%Y-%m-%d %H:%M"),
            "Block (min)": int(leg["blk_min"]),
        })
    legs_df = pd.DataFrame(legs_tbl)
    st.dataframe(legs_df, use_container_width=True)

    # Download CSV
    csv = legs_df.to_csv(index=False).encode("utf-8")
    st.download_button("Download itinerary as CSV", data=csv, file_name=f"itinerary_{sel_o}_{sel_d}_{sel_date}.csv", mime="text/csv")

st.markdown("---")
with st.expander("About this planner"):
    st.markdown(
        """
- Uses local schedule times and **Blkhr** to infer correct arrival day (e.g., overnight legs).
- **DOW(S)** is parsed as: any non-dot means the flight runs that weekday (Mon..Sun).
- The search is an earliest-arrival algorithm. Tune **Min connection**, **Max stops**, **Earliest depart**, and **Horizon** to broaden options.
- If a pair in *Data* has no direct flight that day, the app tries to connect through intermediate airports automatically.
        """
    )
