import io
import heapq
from dataclasses import dataclass
from datetime import datetime, date, time, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import streamlit as st


# =========================
# Utilities
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

def ensure_upper(s) -> str:
    if pd.isna(s) or s is None:
        return ""
    return str(s).strip().upper()

def parse_hhmm_to_minutes(val) -> Optional[int]:
    if pd.isna(val):
        return None
    s = str(val).strip()
    try:
        hh, mm = s.split(":")
        return int(hh) * 60 + int(mm)
    except Exception:
        return None

def parse_excel_date(d) -> Optional[date]:
    if pd.isna(d):
        return None
    dt = pd.to_datetime(d, errors="coerce", dayfirst=False)
    if pd.isna(dt):
        return None
    return dt.date()

def minutes_to_hhmm(m: int) -> str:
    m = int(m)
    return f"{(m // 60) % 24:02d}:{m % 60:02d}"

def timedelta_to_hhmm(td: timedelta) -> str:
    total_min = int(td.total_seconds() // 60)
    h, m = divmod(total_min, 60)
    return f"{h:02d}:{m:02d}"

def combine_date_time(d: date, minutes_since_midnight: int) -> datetime:
    return datetime(d.year, d.month, d.day, minutes_since_midnight // 60, minutes_since_midnight % 60)


# =========================
# Column expectations
# =========================

REQUIRED_SCHED_COLS = {
    "orig", "dest", "startdatelz", "enddatelz", "dows", "schedoutl", "schedinl", "blkhr"
}
DATA_ORIG_CANDS = ["Origin Airport", "Origin", "Orig"]
DATA_DEST_CANDS = ["Destination Airport", "Destination", "Dest"]


# =========================
# Vectorized preprocess
# =========================

def _dow_to_mask_vec(series: pd.Series) -> np.ndarray:
    """
    Turn DOW strings ('.2345..', '1......', etc.) into 7-bit masks (Mon=bit0 ... Sun=bit6).
    Any non-dot counts as 'operates'.
    """
    masks = np.zeros(len(series), dtype=np.uint8)
    vals = series.fillna("").astype(str).str.strip().str.slice(0, 7).str.pad(7, side="right", fillchar=".")
    for i, s in enumerate(vals):
        m = 0
        for k, ch in enumerate(s):
            if ch != ".":
                m |= (1 << k)  # 0=Mon ... 6=Sun
        masks[i] = m
    return masks


def _compute_arrival_offset_vec(dep_min: np.ndarray, arr_min: np.ndarray, blk_min: np.ndarray) -> np.ndarray:
    """
    For each row choose k in {-1,0,1,2} so (arr - dep + 1440*k) ~= blk with minimal absolute error.
    Vectorized across all rows.
    """
    ks = np.array([-1, 0, 1, 2], dtype=np.int16)[:, None]                    # shape (4, N)
    diffs = (arr_min - dep_min)[None, :] + ks * 1440                          # (4, N)
    errs = np.abs(diffs - blk_min[None, :])                                   # (4, N)
    # prefer 0/1 on ties → add tiny bias
    bias = np.array([0.01, 0.0, 0.0, 0.01], dtype=float)[:, None]
    idx = np.argmin(errs + bias, axis=0)                                      # (N,)
    return ks[idx, np.arange(dep_min.size)].astype(np.int8)


@st.cache_data(show_spinner=False)
def load_and_preprocess(file_bytes: bytes, sched_sheet_hint: Optional[str], data_sheet_hint: Optional[str]):
    """Read Excel, detect sheets, and return:
       - sched_df_pre (normalized + typed)
       - pairs_df (unique (Origin, Destination) from Data sheet)
       - chosen sheet names
    """
    xls = pd.ExcelFile(io.BytesIO(file_bytes))
    sheet_names = xls.sheet_names

    # Detect schedule sheet
    def detect_sched():
        for sh in sheet_names:
            df = xls.parse(sh, nrows=50)
            cols = {_norm_col(c) for c in df.columns}
            if REQUIRED_SCHED_COLS.issubset(cols):
                return sh
        return None

    # Detect data sheet
    def detect_data():
        for sh in sheet_names:
            df = xls.parse(sh, nrows=50)
            cols = {_norm_col(c) for c in df.columns}
            has_o = any(_norm_col(c) in cols for c in DATA_ORIG_CANDS)
            has_d = any(_norm_col(c) in cols for c in DATA_DEST_CANDS)
            if has_o and has_d:
                return sh
        return None

    sched_sheet = sched_sheet_hint or detect_sched() or "SchedDateLocalTimeFlightSchedul"
    data_sheet = data_sheet_hint or detect_data() or "Data"

    # Full sheets
    sched_raw = xls.parse(sched_sheet)
    data_raw = xls.parse(data_sheet)

    # Validate schedule columns
    have = {_norm_col(c) for c in sched_raw.columns}
    missing = REQUIRED_SCHED_COLS - have
    if missing:
        raise ValueError(f"Missing schedule columns: {sorted(list(missing))}")

    # Build normalized column map
    cmap = {_norm_col(c): c for c in sched_raw.columns}
    Orig = cmap["orig"]
    Dest = cmap["dest"]
    StartDate = cmap["startdatelz"]
    EndDate = cmap["enddatelz"]
    DOWS = cmap["dows"]
    SchedOut = cmap["schedoutl"]
    SchedIn = cmap["schedinl"]
    Blkhr = cmap["blkhr"]

    # Normalize schedule → typed narrow frame
    df = sched_raw[[Orig, Dest, StartDate, EndDate, DOWS, SchedOut, SchedIn, Blkhr]].copy()
    df["orig"] = df[Orig].map(ensure_upper)
    df["dest"] = df[Dest].map(ensure_upper)
    df["start_date"] = pd.to_datetime(df[StartDate], errors="coerce").dt.date
    df["end_date"] = pd.to_datetime(df[EndDate], errors="coerce").dt.date
    df["dep_min"] = df[SchedOut].map(parse_hhmm_to_minutes)
    df["arr_min"] = df[SchedIn].map(parse_hhmm_to_minutes)
    df["blk_min"] = df[Blkhr].map(parse_hhmm_to_minutes)
    df["dow_mask"] = _dow_to_mask_vec(df[DOWS])

    # Drop invalids early
    df = df.dropna(subset=["start_date", "end_date", "dep_min", "arr_min", "blk_min"]).reset_index(drop=True)

    # Vectorized arrival day offset
    dep_arr_blk = (df["dep_min"].astype(int).to_numpy(),
                   df["arr_min"].astype(int).to_numpy(),
                   df["blk_min"].astype(int).to_numpy())
    df["arr_offset"] = _compute_arrival_offset_vec(*dep_arr_blk)

    # Dtypes compact
    df = df[["orig", "dest", "start_date", "end_date", "dow_mask", "dep_min", "arr_min", "blk_min", "arr_offset"]].copy()
    df["dep_min"] = df["dep_min"].astype(np.int32)
    df["arr_min"] = df["arr_min"].astype(np.int32)
    df["blk_min"] = df["blk_min"].astype(np.int32)
    df["arr_offset"] = df["arr_offset"].astype(np.int8)
    df["orig"] = df["orig"].astype("string")
    df["dest"] = df["dest"].astype("string")

    # Pairs from Data sheet
    # Find actual origin/destination columns
    dmap = {_norm_col(c): c for c in data_raw.columns}
    def _find(cands): 
        for c in cands:
            if _norm_col(c) in dmap: 
                return dmap[_norm_col(c)]
        return None
    ocol = _find(DATA_ORIG_CANDS)
    dcol = _find(DATA_DEST_CANDS)
    if ocol is None or dcol is None:
        raise ValueError("Could not find 'Origin Airport' and 'Destination Airport' in Data sheet.")

    pairs_df = (
        data_raw[[ocol, dcol]].dropna()
        .assign(**{
            ocol: lambda d: d[ocol].astype(str).str.strip().str.upper(),
            dcol: lambda d: d[dcol].astype(str).str.strip().str.upper()
        })
        .drop_duplicates()
        .sort_values([ocol, dcol])
        .reset_index(drop=True)
    )
    pairs_df.columns = ["Origin", "Destination"]

    return df, pairs_df, sched_sheet, data_sheet, sheet_names


# =========================
# Fast leg generation for a date window
# =========================

@st.cache_data(show_spinner=False)
def generate_legs_for_window(
    sched_df: pd.DataFrame,
    start_date: date,
    horizon_days: int
) -> pd.DataFrame:
    """
    Vectorized filtering & materialization of legs for dates in [start_date, start_date + horizon_days - 1].
    Returns a DataFrame with columns: origin, destination, dep_dt_local, arr_dt_local, blk_min
    """
    frames = []
    for i in range(horizon_days):
        d = start_date + timedelta(days=i)
        # filter rows valid on this date
        m = (
            (sched_df["start_date"] <= d) &
            (d <= sched_df["end_date"]) &
            (((sched_df["dow_mask"] >> d.weekday()) & 1) == 1)
        )
        if not m.any():
            continue
        sub = sched_df.loc[m, ["orig", "dest", "dep_min", "arr_min", "blk_min", "arr_offset"]].copy()
        base = pd.Timestamp(d)
        sub["dep_dt_local"] = base + pd.to_timedelta(sub["dep_min"].astype(int), unit="m")
        sub["arr_dt_local"] = base + pd.to_timedelta(sub["arr_min"].astype(int), unit="m") + pd.to_timedelta(1440 * sub["arr_offset"].astype(int), unit="m")
        sub.rename(columns={"orig": "origin", "dest": "destination"}, inplace=True)
        frames.append(sub[["origin", "destination", "dep_dt_local", "arr_dt_local", "blk_min"]])

    if not frames:
        return pd.DataFrame(columns=["origin", "destination", "dep_dt_local", "arr_dt_local", "blk_min"])

    legs = pd.concat(frames, ignore_index=True)
    legs.sort_values(["origin", "dep_dt_local", "destination"], inplace=True, kind="mergesort")
    legs.reset_index(drop=True, inplace=True)
    return legs


# =========================
# Indexed adjacency for fast routing
# =========================

@dataclass
class OriginIndex:
    dep_times: np.ndarray           # numpy datetime64[ns] sorted
    arr_times: np.ndarray           # numpy datetime64[ns]
    blk_min: np.ndarray             # int32
    dests: np.ndarray               # numpy object/string
    # we keep rows aligned across arrays

def build_origin_index(legs_df: pd.DataFrame) -> Dict[str, OriginIndex]:
    idx: Dict[str, OriginIndex] = {}
    for origin, g in legs_df.groupby("origin", sort=False):
        g = g.sort_values("dep_dt_local")
        dep_times = g["dep_dt_local"].values.astype("datetime64[ns]")
        arr_times = g["arr_dt_local"].values.astype("datetime64[ns]")
        blk = g["blk_min"].to_numpy(dtype=np.int32)
        dests = g["destination"].astype(str).to_numpy()
        idx[str(origin)] = OriginIndex(dep_times, arr_times, blk, dests)
    return idx


# =========================
# Earliest-arrival search (fast)
# =========================

def plan_itinerary_fast(
    index: Dict[str, OriginIndex],
    origin: str,
    destination: str,
    start_date: date,
    earliest_dep_min: int,
    min_connect_min: int,
    max_stops: int
) -> Optional[dict]:
    origin = ensure_upper(origin)
    destination = ensure_upper(destination)

    start_dt = datetime.combine(start_date, time(0, 0)) + timedelta(minutes=int(earliest_dep_min))

    # PQ ordered by current arrival time (earliest first)
    # item: (current_arrival_dt, airport, stops, total_elapsed_min, first_dep_dt, path_list)
    pq: List[Tuple[datetime, str, int, int, Optional[datetime], list]] = []
    heapq.heappush(pq, (start_dt, origin, 0, 0, None, []))

    # best known arrival at (airport, stops) to prune
    best_arrival: Dict[Tuple[str, int], datetime] = {}

    while pq:
        cur_time, ap, stops, elapsed, first_dep, path = heapq.heappop(pq)

        # Arrived
        if ap == destination and path:
            return {
                "total_elapsed": timedelta(minutes=int(elapsed)),
                "legs": path,
                "stops": max(0, len(path) - 1),
                "depart_at": first_dep,
                "arrive_at": cur_time,
            }

        if stops > max_stops:
            continue

        key = (ap, stops)
        if key in best_arrival and best_arrival[key] <= cur_time:
            continue
        best_arrival[key] = cur_time

        # Outgoing legs
        oi = index.get(ap)
        if oi is None or oi.dep_times.size == 0:
            continue

        # Required earliest departure for next leg from this airport
        min_wait = 0 if not path else min_connect_min
        earliest_next_dep = np.datetime64(cur_time + timedelta(minutes=min_wait), "ns")

        # Binary search to the first feasible leg (dep >= earliest_next_dep)
        i = np.searchsorted(oi.dep_times, earliest_next_dep, side="left")

        # Iterate feasible legs from i onward (already time-sorted)
        # This is usually small since horizon is small.
        for j in range(i, oi.dep_times.size):
            dep_dt = pd.Timestamp(oi.dep_times[j]).to_pydatetime()
            arr_dt = pd.Timestamp(oi.arr_times[j]).to_pydatetime()
            wait_min = max(0, int((dep_dt - cur_time).total_seconds() // 60))
            if wait_min < min_wait:
                continue

            leg_blk = int(oi.blk_min[j])
            new_elapsed = elapsed + wait_min + leg_blk
            new_ap = str(oi.dests[j])

            new_first_dep = first_dep or dep_dt
            new_path = path + [{
                "origin": ap,
                "destination": new_ap,
                "dep_dt_local": dep_dt,
                "arr_dt_local": arr_dt,
                "blk_min": leg_blk,
                "wait_min_before": wait_min
            }]

            # Push next state with priority on new arrival time
            heapq.heappush(pq, (arr_dt, new_ap, stops + 1, new_elapsed, new_first_dep, new_path))

    return None


# =========================
# Streamlit UI
# =========================

st.set_page_config(page_title="Flight Route Planner (Fast)", page_icon="✈️", layout="wide")
st.title("✈️ Flight Route Planner — Fast Version")
st.caption("Upload your Excel. Select an Origin→Destination pair from the Data sheet and a date. The app finds the **fastest** itinerary (direct or with connections).")

with st.sidebar:
    st.header("Settings")
    earliest_dep_str = st.text_input("Earliest departure (HH:MM at origin)", value="00:00")
    earliest_dep_min = parse_hhmm_to_minutes(earliest_dep_str) or 0
    min_connect = st.number_input("Minimum connection time (min)", min_value=0, max_value=360, value=45, step=5)
    max_stops = st.select_slider("Max stops (connections)", options=[0, 1, 2, 3], value=2)
    horizon_days = st.slider("Search horizon (days from selected date)", min_value=1, max_value=5, value=2,
                             help="Smaller horizon = faster. Increase only if needed.")

uploaded = st.file_uploader("Upload Excel (.xlsx)", type=["xlsx"])

if not uploaded:
    st.info("Please upload your Excel file to continue.")
    st.stop()

# Preprocess (cached)
try:
    sched_df_pre, pairs_df, sched_sheet, data_sheet, sheet_names = load_and_preprocess(
        uploaded.getvalue(), None, None
    )
except Exception as e:
    st.error(str(e))
    st.stop()

c1, c2 = st.columns(2)
with c1:
    pair_display = pairs_df.apply(lambda r: f"{r['Origin']} → {r['Destination']}", axis=1)
    idx = st.selectbox("Route pair (from Data sheet)", options=pair_display.index,
                       format_func=lambda i: pair_display.iloc[i])
    sel_o = pairs_df.iloc[idx]["Origin"]
    sel_d = pairs_df.iloc[idx]["Destination"]
with c2:
    sel_date = st.date_input("Date", value=date.today())

with st.spinner("Building legs and routing..."):
    legs_df = generate_legs_for_window(sched_df_pre, sel_date, horizon_days)
    origin_index = build_origin_index(legs_df)
    itinerary = plan_itinerary_fast(
        origin_index, sel_o, sel_d, sel_date,
        earliest_dep_min=earliest_dep_min,
        min_connect_min=min_connect,
        max_stops=max_stops
    )

st.markdown("### Result")

if itinerary is None:
    st.warning("No feasible route found with the current settings. Try increasing horizon, allowing more stops, or changing earliest departure.")
else:
    total = itinerary["total_elapsed"]
    depart = itinerary["depart_at"]
    arrive = itinerary["arrive_at"]
    stops = itinerary["stops"]

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Departure (local)", depart.strftime("%Y-%m-%d %H:%M"))
    m2.metric("Arrival (local)", arrive.strftime("%Y-%m-%d %H:%M"))
    m3.metric("Transit time", timedelta_to_hhmm(total))
    m4.metric("Stops", stops)

    # Legs table
    rows = []
    for i, leg in enumerate(itinerary["legs"],  start=1):
        rows.append({
            "Leg #": i,
            "Origin": leg["origin"],
            "Destination": leg["destination"],
            "Wait before (min)": leg["wait_min_before"],
            "Dep (local)": leg["dep_dt_local"].strftime("%Y-%m-%d %H:%M"),
            "Arr (local)": leg["arr_dt_local"].strftime("%Y-%m-%d %H:%M"),
            "Block (min)": leg["blk_min"],
        })
    legs_out = pd.DataFrame(rows)
    st.dataframe(legs_out, use_container_width=True)

    csv = legs_out.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download itinerary CSV",
        data=csv,
        file_name=f"itinerary_{sel_o}_{sel_d}_{sel_date}.csv",
        mime="text/csv"
    )

st.markdown("---")
with st.expander("How performance is improved"):
    st.write(
        "- Preprocessing is cached (normalized columns, vectorized time parsing, DOW masks, arrival-day offsets).\n"
        "- Leg generation is vectorized per date (no Python per-row loops).\n"
        "- Per-origin departure arrays are indexed and binary-searched to the first feasible connection.\n"
        "- Pruning stores the best seen arrival per (airport, stops) to cut branches fast."
    )
