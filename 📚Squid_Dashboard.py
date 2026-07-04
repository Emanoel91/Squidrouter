import streamlit as st
import requests
import pandas as pd

from datetime import datetime, timedelta

# PAGE CONFIG --------------------------------------------------------------------------------------------------

st.set_page_config(
    page_title="SquidRouter On-Chain Analytics",
    page_icon="https://images.cryptorank.io/coins/150x150.squid1675241862798.png",
    layout="wide"
)

# CUSTOM CSS --------------------------------------------------------------------------------------------------

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

# TITLE --------------------------------------------------------------------------------------------------

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

# BUILDER INFO --------------------------------------------------------------------------------------------------

st.markdown(
    """
    <div style="margin-top:20px;margin-bottom:20px;font-size:16px;">
        <div style="display:flex;align-items:center;gap:10px;">
            <img src="https://pbs.twimg.com/profile_images/2060406047391559681/sA9zPNKM_400x400.jpg"
                 style="width:25px;height:25px;border-radius:50%;">
            <span>
                Built by:
                <a href="https://x.com/0xeman_raz" target="_blank">
                    Eman Raz
                </a>
            </span>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# INFO --------------------------------------------------------------------------------------------------

st.info("📊 Charts initially display data for a default time range. "
    "Select a custom range to view results for your desired period."
)

st.info(
    "⏳ On-chain data retrieval may take a few moments. "
    "Please wait while the results load."
)

# FILTERS --------------------------------------------------------------------------------------------------

st.markdown("## Filters")
today = datetime.utcnow().date()
filter1, filter2, filter3 = st.columns([1.3, 1.3, 0.8])
with filter1:
    start_date = st.date_input("Start Date", value=today - timedelta(days=180))
with filter2:
    end_date = st.date_input("End Date", value=today)
with filter3:
    timeframe = st.selectbox("Time Frame", ["Day", "Week", "Month"])
st.divider()

# SQUID CONTRACTS --------------------------------------------------------------------------------------------------

CONTRACTS = [
    "0xce16F69375520ab01377ce7B88f5BA8C48F8D666",
    "0x492751eC3c57141deb205eC2da8bFcb410738630",
    "0xDC3D8e1Abe590BCa428a8a2FC4CfDbD1AcF57Bd9",
    "0xdf4fFDa22270c12d0b5b3788F1669D709476111E",
    "0xe6B3949F9bBF168f4E3EFc82bc8FD849868CC6d8"
]

# FORMATTERS --------------------------------------------------------------------------------------------------

def format_volume(value):
    value = float(value)
    if value >= 1_000_000_000:
        return f"${value/1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"${value/1_000_000:.2f}M"
    if value >= 1_000:
        return f"${value/1_000:.2f}K"
    return f"${value:,.2f}"
def format_transactions(value):
    value = int(value)
    if value >= 1_000_000_000:
        return f"{value/1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"{value/1_000_000:.2f}M"
    if value >= 1_000:
        return f"{value/1_000:.2f}K"
    return f"{value:,}"

# LOAD DATA --------------------------------------------------------------------------------------------------

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
        response = requests.get(url, timeout=60)
        if response.status_code != 200:
            continue
        data = response.json().get("data", [])
        if len(data) == 0:
            continue
        df = pd.DataFrame(data)
        dfs.append(df)
    if len(dfs) == 0:
        return pd.DataFrame()
    df = pd.concat(
        dfs,
        ignore_index=True
    )
    numeric_columns = [
        "volume",
        "num_txs",
        "gmp_volume",
        "gmp_num_txs",
        "transfers_volume",
        "transfers_num_txs"
    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        ).fillna(0)
    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        unit="s"
    )
    return df

try:

    df = load_data(start_date, end_date)

    if df.empty:
        st.warning("No data found for the selected period.")
        st.stop()

except Exception as e:

    st.error(f"Error loading data: {e}")
    st.stop()

# AGGREGATE ALL SQUID CONTRACTS --------------------------------------------------------------------

df = (
    df.groupby("timestamp", as_index=False)
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
)

df = df.sort_values("timestamp")

# APPLY TIMEFRAME ----------------------------------------------------------------------------------

if timeframe == "Day":

    chart_df = df.copy()

elif timeframe == "Week":

    chart_df = (
        df.set_index("timestamp")
          .resample("W")
          .sum()
          .reset_index()
    )

elif timeframe == "Month":

    chart_df = (
        df.set_index("timestamp")
          .resample("ME")
          .sum()
          .reset_index()
    )

# KPI CALCULATIONS ---------------------------------------------------------------------------------

total_volume = chart_df["volume"].sum()

total_transactions = int(
    chart_df["num_txs"].sum()
)

avg_volume_per_txn = (
    total_volume / total_transactions
    if total_transactions > 0
    else 0
)

# KPI ROW ------------------------------------------------------------------------------------------

kpi1, kpi2, kpi3 = st.columns(3)

with kpi1:

    st.metric(
        label="Total Volume",
        value=format_volume(total_volume)
    )

with kpi2:

    st.metric(
        label="Total Transactions",
        value=format_transactions(total_transactions)
    )

with kpi3:

    st.metric(
        label="Avg Volume per Txn",
        value=format_volume(avg_volume_per_txn)
    )

st.divider()
