# ==================================================================================================
# IMPORTS
# ==================================================================================================

import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta


# ==================================================================================================
# PAGE CONFIG
# ==================================================================================================

st.set_page_config(
    page_title="SquidRouter On-Chain Analytics",
    page_icon="https://images.cryptorank.io/coins/150x150.squid1675241862798.png",
    layout="wide"
)


# ==================================================================================================
# CUSTOM CSS (KPI styling)
# ==================================================================================================

st.markdown(
    """
    <style>

    div[data-testid="stMetricValue"] {
        font-size: 34px !important;
        font-weight: bold !important;
    }

    div[data-testid="stMetricLabel"] {
        font-size: 16px !important;
        font-weight: bold !important;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ==================================================================================================
# HEADER
# ==================================================================================================

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


# ==================================================================================================
# BUILDER INFO
# ==================================================================================================

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


# ==================================================================================================
# INFO BOXES
# ==================================================================================================

st.info("📊 On-chain analytics dashboard for SquidRouter cross-chain activity.")
st.info("⏳ Data is fetched from AxelarScan APIs and may take a few seconds.")


# ==================================================================================================
# FILTERS (TOP OF PAGE)
# ==================================================================================================

st.markdown("## Filters")

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
        ["Day", "Week", "Month"]
    )

st.divider()


# ==================================================================================================
# CONTRACTS
# ==================================================================================================

CONTRACTS = [
    "0xce16F69375520ab01377ce7B88f5BA8C48F8D666",
    "0x492751eC3c57141deb205eC2da8bFcb410738630",
    "0xDC3D8e1Abe590BCa428a8a2FC4CfDbD1AcF57Bd9",
    "0xdf4fFDa22270c12d0b5b3788F1669D709476111E",
    "0xe6B3949F9bBF168f4E3EFc82bc8FD849868CC6d8"
]


# ==================================================================================================
# LOAD FUNCTION (FILTERED DATA)
# ==================================================================================================

@st.cache_data(ttl=3600)
def load_data(start_date, end_date):

    from_time = int(datetime.combine(start_date, datetime.min.time()).timestamp())
    to_time = int(datetime.combine(end_date, datetime.max.time()).timestamp())

    dfs = []

    for contract in CONTRACTS:

        url = (
            "https://api.axelarscan.io/api/interchainChart"
            f"?contractAddress={contract}"
            f"&fromTime={from_time}"
            f"&toTime={to_time}"
        )

        r = requests.get(url, timeout=60)

        if r.status_code != 200:
            continue

        data = r.json().get("data", [])

        if not data:
            continue

        df = pd.DataFrame(data)
        dfs.append(df)

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

    for c in numeric_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")

    return df

# ==================================================================================================
# LOAD FILTERED DATA (AFFECTED BY UI FILTERS)
# ==================================================================================================

filtered_df = load_data(start_date, end_date)

if filtered_df.empty:
    st.warning("No data found for selected range.")
    st.stop()


# ==================================================================================================
# AGGREGATE ALL CONTRACTS (DAILY BASE MERGE)
# ==================================================================================================

filtered_df = (
    filtered_df.groupby("timestamp", as_index=False)
    .agg({
        "volume": "sum",
        "num_txs": "sum",
        "gmp_volume": "sum",
        "gmp_num_txs": "sum",
        "transfers_volume": "sum",
        "transfers_num_txs": "sum"
    })
    .sort_values("timestamp")
    .reset_index(drop=True)
)


# ==================================================================================================
# TIMEFRAME TRANSFORMATION (FOR CHARTS ONLY)
# ==================================================================================================

if timeframe == "Day":
    chart_df = filtered_df.copy()

elif timeframe == "Week":
    chart_df = (
        filtered_df.set_index("timestamp")
        .resample("W")
        .sum()
        .reset_index()
    )

elif timeframe == "Month":
    chart_df = (
        filtered_df.set_index("timestamp")
        .resample("M")
        .sum()
        .reset_index()
    )


# ==================================================================================================
# BASE KPI CALCULATIONS (FILTERED - DEPENDS ON USER INPUT)
# ==================================================================================================

total_volume = chart_df["volume"].sum()

total_transactions = int(chart_df["num_txs"].sum())

avg_volume_per_txn = (
    total_volume / total_transactions
    if total_transactions > 0
    else 0
)


# ==================================================================================================
# KPI RENDER ROW
# ==================================================================================================

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

st.divider()

# ==================================================================================================
# FULL DATASET (INDEPENDENT FROM FILTERS)
# ==================================================================================================
# این دیتاست برای KPIهای Growth استفاده می‌شود
# و نباید تحت تأثیر start_date / end_date باشد

full_start = datetime(2024, 1, 1).date()
full_end = datetime.utcnow().date()

full_df = load_data(full_start, full_end)

if full_df.empty:
    st.warning("No full dataset available for growth metrics.")
    st.stop()


# ==================================================================================================
# AGGREGATE FULL DATASET (DAILY BASE)
# ==================================================================================================

full_df = (
    full_df.groupby("timestamp", as_index=False)
    .agg({
        "volume": "sum",
        "num_txs": "sum",
        "gmp_volume": "sum",
        "gmp_num_txs": "sum",
        "transfers_volume": "sum",
        "transfers_num_txs": "sum"
    })
    .sort_values("timestamp")
    .reset_index(drop=True)
)


# ==================================================================================================
# GROWTH FUNCTION (BASED ON LAST OBSERVATION)
# ==================================================================================================

def growth_from_last(df, col, days):

    if len(df) < days + 1:
        return 0

    latest = df[col].iloc[-1]
    past = df[col].iloc[-(days + 1)]

    if past == 0:
        return 0

    return ((latest - past) / past) * 100


# ==================================================================================================
# GROWTH KPIs — VOLUME (INDEPENDENT)
# ==================================================================================================

volume_7d = growth_from_last(full_df, "volume", 7)
volume_30d = growth_from_last(full_df, "volume", 30)
volume_6m = growth_from_last(full_df, "volume", 180)


# ==================================================================================================
# GROWTH KPIs — TRANSACTIONS (INDEPENDENT)
# ==================================================================================================

tx_7d = growth_from_last(full_df, "num_txs", 7)
tx_30d = growth_from_last(full_df, "num_txs", 30)
tx_6m = growth_from_last(full_df, "num_txs", 180)


# ==================================================================================================
# DISPLAY — VOLUME GROWTH
# ==================================================================================================

st.markdown("## 📊 Volume Change (Independent of Filters)")

v1, v2, v3 = st.columns(3)

with v1:
    st.metric(
        "7D Volume Growth",
        f"{volume_7d:.2f}%"
    )

with v2:
    st.metric(
        "30D Volume Growth",
        f"{volume_30d:.2f}%"
    )

with v3:
    st.metric(
        "6M Volume Growth",
        f"{volume_6m:.2f}%"
    )

st.divider()


# ==================================================================================================
# DISPLAY — TRANSACTIONS GROWTH
# ==================================================================================================

st.markdown("## 🔄 Transaction Change (Independent of Filters)")

t1, t2, t3 = st.columns(3)

with t1:
    st.metric(
        "7D Tx Growth",
        f"{tx_7d:.2f}%"
    )

with t2:
    st.metric(
        "30D Tx Growth",
        f"{tx_30d:.2f}%"
    )

with t3:
    st.metric(
        "6M Tx Growth",
        f"{tx_6m:.2f}%"
    )

st.divider()
