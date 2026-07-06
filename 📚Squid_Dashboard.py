import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

# ==========================================================================================
# PAGE CONFIG
# ==========================================================================================

st.set_page_config(
    page_title="SquidRouter On-Chain Analytics",
    page_icon="https://images.cryptorank.io/coins/150x150.squid1675241862798.png",
    layout="wide"
)

# ==========================================================================================
# CUSTOM CSS
# ==========================================================================================

st.markdown(
    """
    <style>

    div[data-testid="stMetricValue"] {
        font-size:34px !important;
        font-weight:bold !important;
    }

    div[data-testid="stMetricLabel"] {
        font-size:16px !important;
        font-weight:bold !important;
    }

    </style>
    """,
    unsafe_allow_html=True
)

# ==========================================================================================
# HEADER
# ==========================================================================================

st.markdown(
    """
    <div style="display:flex;align-items:center;gap:15px;">
        <img src="https://images.cryptorank.io/coins/150x150.squid1675241862798.png"
             style="width:60px;height:60px;">
        <h1 style="margin:0;">SquidRouter On-Chain Analytics</h1>
    </div>
    """,
    unsafe_allow_html=True
)

# ==========================================================================================
# BUILDER INFO
# ==========================================================================================

st.markdown(
    """
    <div style="margin-top:20px;margin-bottom:20px;font-size:16px;">
        <div style="display:flex;align-items:center;gap:10px;">
            <img src="https://pbs.twimg.com/profile_images/2060406047391559681/sA9zPNKM_400x400.jpg"
                 style="width:25px;height:25px;border-radius:50%;">
            <span>
                Built by:
                <a href="https://x.com/0xeman_raz" target="_blank">Eman Raz</a>
            </span>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# ==========================================================================================
# INFO
# ==========================================================================================

st.info("📊 On-chain analytics dashboard for SquidRouter cross-chain activity.")
st.info("⏳ Data is fetched from AxelarScan APIs and may take a few seconds.")

# ==========================================================================================
# FILTERS
# ==========================================================================================

today = datetime.utcnow().date()

c1, c2, c3 = st.columns([1.3, 1.3, 0.8])

with c1:
    start_date = st.date_input(
        "Start Date",
        value=today - timedelta(days=180)
    )

with c2:
    end_date = st.date_input(
        "End Date",
        value=today
    )

with c3:
    timeframe = st.selectbox(
        "Time Frame",
        ["Month", "Week", "Day"]
    )

st.divider()

# ==========================================================================================
# CONTRACTS
# ==========================================================================================

CONTRACTS = [
    "0xce16F69375520ab01377ce7B88f5BA8C48F8D666",
    "0x492751eC3c57141deb205eC2da8bFcb410738630",
    "0xDC3D8e1Abe590BCa428a8a2FC4CfDbD1AcF57Bd9",
    "0xdf4fFDa22270c12d0b5b3788F1669D709476111E",
    "0xe6B3949F9bBF168f4E3EFc82bc8FD849868CC6d8"
]

# ==========================================================================================
# LOAD DATA
# ==========================================================================================

@st.cache_data(ttl=3600)
def load_data(start_date, end_date):

    from_time = int(
        datetime.combine(
            start_date,
            datetime.min.time()
        ).timestamp()
    )

    to_time = int(
        datetime.combine(
            end_date,
            datetime.max.time()
        ).timestamp()
    )

    dfs = []

    for contract in CONTRACTS:

        url = (
            "https://api.axelarscan.io/api/interchainChart"
            f"?contractAddress={contract}"
            f"&fromTime={from_time}"
            f"&toTime={to_time}"
        )

        try:
            r = requests.get(url, timeout=60)

            if r.status_code != 200:
                continue

            data = r.json().get("data", [])

            if not data:
                continue

            df = pd.DataFrame(data)
            dfs.append(df)

        except Exception:
            continue

    if not dfs:
        return pd.DataFrame()

    df = pd.concat(dfs, ignore_index=True)

    numeric_cols = [
        "volume",
        "num_txs",
        "gmp_volume",
        "gmp_num_txs",
        "transfers_volume",
        "transfers_num_txs"
    ]

    for col in numeric_cols:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        ).fillna(0)

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        unit="ms"
    )

    return df

# ==========================================================================================
# LOAD FILTERED DATA
# ==========================================================================================

filtered_df = load_data(
    start_date,
    end_date
)

if filtered_df.empty:
    st.warning("No data found for selected range.")
    st.stop()

# ==========================================================================================
# DAILY AGGREGATION
# ==========================================================================================

filtered_df = (
    filtered_df
    .groupby("timestamp", as_index=False)
    .agg(
        {
            "volume": "sum",
            "num_txs": "sum",
            "gmp_volume": "sum",
            "gmp_num_txs": "sum",
            "transfers_volume": "sum",
            "transfers_num_txs": "sum"
        }
    )
    .sort_values("timestamp")
    .reset_index(drop=True)
)

# ==========================================================================================
# TIMEFRAME TRANSFORMATION (OPTIMIZED)
# ==========================================================================================

filtered_df = filtered_df.copy()
filtered_df["timestamp"] = pd.to_datetime(filtered_df["timestamp"], errors="coerce")
filtered_df = filtered_df.dropna(subset=["timestamp"])

filtered_df = filtered_df.sort_values("timestamp")

freq_map = {
    "Month": "ME",
    "Week": "W",
    "Day": "D"
}

chart_df = (
    filtered_df
    .set_index("timestamp")
    .resample(freq_map[timeframe])
    .agg({
        "volume": "sum",
        "num_txs": "sum"
    })
    .reset_index()
)

chart_df = chart_df.dropna()

# ==========================================================================================
# BASE KPI CALCULATIONS
# ==========================================================================================

total_volume = chart_df["volume"].sum()

total_transactions = int(
    chart_df["num_txs"].sum()
)

avg_volume_per_txn = (
    total_volume / total_transactions
    if total_transactions > 0
    else 0
)

# ==========================================================================================
# KPI ROW
# ==========================================================================================

kpi1, kpi2, kpi3 = st.columns(3)

with kpi1:
    st.metric(
        label="Total Volume",
        value=f"${total_volume:,.2f}"
    )

with kpi2:
    st.metric(
        label="Total Transactions",
        value=f"{total_transactions:,}"
    )

with kpi3:
    st.metric(
        label="Avg Volume per Txn",
        value=f"${avg_volume_per_txn:,.2f}"
    )

# ==========================================================================================
# NUMBER FORMATTER
# ==========================================================================================

def format_number(value, prefix=""):

    if value >= 1_000_000_000:
        return f"{prefix}{value / 1_000_000_000:.2f}B"

    elif value >= 1_000_000:
        return f"{prefix}{value / 1_000_000:.2f}M"

    elif value >= 1_000:
        return f"{prefix}{value / 1_000:.2f}K"

    else:

        if isinstance(value, float):
            return f"{prefix}{value:,.2f}"

        return f"{prefix}{value:,}"

# ==========================================================================================
# DAILY STATISTICS
# ==========================================================================================

daily_df = filtered_df.copy()

# --------------------------
# Volume Statistics
# --------------------------

max_daily_volume = daily_df["volume"].max()

median_daily_volume = daily_df["volume"].median()

avg_daily_volume = daily_df["volume"].mean()

# --------------------------
# Transaction Statistics
# --------------------------

max_daily_tx = int(
    daily_df["num_txs"].max()
)

median_daily_tx = int(
    daily_df["num_txs"].median()
)

avg_daily_tx = int(
    daily_df["num_txs"].mean()
)

# ==========================================================================================
# DAILY KPI ROW
# ==========================================================================================

k1, k2, k3, k4, k5, k6 = st.columns(6)

with k1:
    st.metric(
        "Max Daily Volume",
        format_number(max_daily_volume, "$")
    )

with k2:
    st.metric(
        "Median Daily Volume",
        format_number(median_daily_volume, "$")
    )

with k3:
    st.metric(
        "Avg Daily Volume",
        format_number(avg_daily_volume, "$")
    )

with k4:
    st.metric(
        "Max Daily Txn",
        format_number(max_daily_tx)
    )

with k5:
    st.metric(
        "Median Daily Txn",
        format_number(median_daily_tx)
    )

with k6:
    st.metric(
        "Avg Daily Txn",
        format_number(avg_daily_tx)
    )

st.divider()

# ==========================================================================================
# LOAD FULL DATASET
# ==========================================================================================

full_start = datetime(2024, 1, 1).date()
full_end = datetime.utcnow().date()

full_df = load_data(
    full_start,
    full_end
)

if full_df.empty:
    st.warning("No data available for KPIs")
    st.stop()

# ==========================================================================================
# CLEAN TIMESTAMP
# ==========================================================================================

full_df["timestamp"] = pd.to_numeric(
    full_df["timestamp"],
    errors="coerce"
)

full_df = full_df.dropna(
    subset=["timestamp"]
)

full_df["timestamp"] = full_df["timestamp"].astype("int64")

full_df["timestamp"] = pd.to_datetime(
    full_df["timestamp"],
    unit="ms",
    errors="coerce"
)

full_df = full_df.dropna(
    subset=["timestamp"]
)

# ==========================================================================================
# DAILY AGGREGATION
# ==========================================================================================

full_df["date"] = full_df["timestamp"].dt.floor("D")

full_df = (
    full_df
    .groupby("date", as_index=False)
    .agg(
        {
            "volume": "sum",
            "num_txs": "sum",
            "gmp_volume": "sum",
            "gmp_num_txs": "sum",
            "transfers_volume": "sum",
            "transfers_num_txs": "sum"
        }
    )
    .sort_values("date")
    .reset_index(drop=True)
)

# ==========================================================================================
# GROWTH FUNCTION
# ==========================================================================================

def growth_from_window(df, column, days):

    if len(df) < days * 2:
        return 0

    last_window = (
        df.iloc[-days:][column].sum()
    )

    previous_window = (
        df.iloc[-(2 * days):-days][column].sum()
    )

    if previous_window <= 0:
        return 0

    return (
        (last_window - previous_window)
        / previous_window
    ) * 100

# ==========================================================================================
# GROWTH KPI CALCULATIONS
# ==========================================================================================

volume_7d = growth_from_window(
    full_df,
    "volume",
    7
)

volume_30d = growth_from_window(
    full_df,
    "volume",
    30
)

volume_6m = growth_from_window(
    full_df,
    "volume",
    180
)

tx_7d = growth_from_window(
    full_df,
    "num_txs",
    7
)

tx_30d = growth_from_window(
    full_df,
    "num_txs",
    30
)

tx_6m = growth_from_window(
    full_df,
    "num_txs",
    180
)

# ==========================================================================================
# GROWTH KPI ROW
# ==========================================================================================

c1, c2, c3, c4, c5, c6 = st.columns(6)

with c1:
    st.metric(
        "7D Volume",
        f"{volume_7d:.2f}%"
    )

with c2:
    st.metric(
        "30D Volume",
        f"{volume_30d:.2f}%"
    )

with c3:
    st.metric(
        "6M Volume",
        f"{volume_6m:.2f}%"
    )

with c4:
    st.metric(
        "7D Tx",
        f"{tx_7d:.2f}%"
    )

with c5:
    st.metric(
        "30D Tx",
        f"{tx_30d:.2f}%"
    )

with c6:
    st.metric(
        "6M Tx",
        f"{tx_6m:.2f}%"
    )

 
