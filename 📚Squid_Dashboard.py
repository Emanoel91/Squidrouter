import requests
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

# --- Page Config: Tab Title & Icon -------------------------------------------------------------------------------------
st.set_page_config(
    page_title="SquidRouter On-Chain Analytics",
    page_icon="https://images.cryptorank.io/coins/150x150.squid1675241862798.png",
    layout="wide"
)

# --- Title with Logo ---------------------------------------------------------------------------------------------------
st.markdown(
    """
    <div style="display: flex; align-items: center; gap: 15px;">
        <img src="https://images.cryptorank.io/coins/150x150.squid1675241862798.png" alt="squid Logo" style="width:60px; height:60px;">
        <h1 style="margin: 0;">SquidRouter On-Chain Analytics</h1>
    </div>
    """,
    unsafe_allow_html=True
)

# --- Builder Info ---------------------------------------------------------------------------------------------------------
st.markdown(
    """
    <div style="margin-top: 20px; margin-bottom: 20px; font-size: 16px;">
        <div style="display: flex; align-items: center; gap: 10px;">
            <img src="https://pbs.twimg.com/profile_images/2060406047391559681/sA9zPNKM_400x400.jpg" style="width:25px; height:25px; border-radius: 50%;">
            <span>Built by: <a href="https://x.com/0xeman_raz" target="_blank">Eman Raz</a></span>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

st.info("📊Charts initially display data for a default time range. Select a custom range to view results for your desired period.")

st.info("⏳On-chain data retrieval may take a few moments. Please wait while the results load.")

# -------------------------- Contracts List --------------------------------------
CONTRACTS = [
    "0xce16F69375520ab01377ce7B88f5BA8C48F8D666",
    "0x492751eC3c57141deb205eC2da8bFcb410738630",
    "0xDC3D8e1Abe590BCa428a8a2FC4CfDbD1AcF57Bd9",
    "0xdf4fFDa22270c12d0b5b3788F1669D709476111E",
    "0xe6B3949F9bBF168f4E3EFc82bc8FD849868CC6d8"
]
# -------------------------- Sidebar Filters --------------------------------------
st.sidebar.header("Filters")

today = datetime.utcnow().date()

start_date = st.sidebar.date_input(
    "Start Date",
    today - timedelta(days=180)
)

end_date = st.sidebar.date_input(
    "End Date",
    today
)

timeframe = st.sidebar.selectbox(
    "Time Frame",
    ["Day", "Week", "Month"]
)

# --------------------------- API Data ---------------------------------------------
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

        r = requests.get(url)

        if r.status_code == 200:

            data = r.json()["data"]

            if len(data):

                df = pd.DataFrame(data)

                dfs.append(df)

    if len(dfs) == 0:
        return pd.DataFrame()

    df = pd.concat(dfs)

    numeric_cols = [
        "volume",
        "num_txs",
        "gmp_volume",
        "gmp_num_txs",
        "transfers_volume",
        "transfers_num_txs"
    ]

    for c in numeric_cols:
        df[c] = pd.to_numeric(df[c])

    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")

    return df

# ----------------------- Contrac Integration ------------------------------------
df = load_data(start_date, end_date)

if df.empty:
    st.warning("No data found.")
    st.stop()

df = (
    df.groupby("timestamp", as_index=False)
      .agg({
          "volume":"sum",
          "num_txs":"sum",
          "gmp_volume":"sum",
          "gmp_num_txs":"sum",
          "transfers_volume":"sum",
          "transfers_num_txs":"sum"
      })
)

# ----------------------- Time Frame Addition -----------------------------------
if timeframe == "Day":

    chart_df = df.copy()

elif timeframe == "Week":

    chart_df = (
        df.set_index("timestamp")
          .resample("W")
          .sum()
          .reset_index()
    )

else:

    chart_df = (
        df.set_index("timestamp")
          .resample("M")
          .sum()
          .reset_index()
    )

# -------------- KPI: Row 1 ---------------------------------------
total_volume = chart_df["volume"].sum()

total_transactions = int(chart_df["num_txs"].sum())

avg_volume_txn = (
    total_volume / total_transactions
    if total_transactions > 0
    else 0
)

col1, col2, col3 = st.columns(3)

col1.metric(
    "Total Volume",
    f"${total_volume:,.2f}"
)

col2.metric(
    "Total Transactions",
    f"{total_transactions:,}"
)

col3.metric(
    "Avg Volume per Txn",
    f"${avg_volume_txn:,.2f}"
)
