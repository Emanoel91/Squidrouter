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
# CUSTOM CSS
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
# TITLE
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
                <a href="https://x.com/0xeman_raz" target="_blank">
                    Eman Raz
                </a>
            </span>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)


# ==================================================================================================
# INFO
# ==================================================================================================

st.info(
    "📊 Charts initially display data for a default time range. "
    "Select a custom range to view results for your desired period."
)

st.info(
    "⏳ On-chain data retrieval may take a few moments. "
    "Please wait while the results load."
)


# ==================================================================================================
# FILTERS
# ==================================================================================================

st.markdown("## Filters")

today = datetime.utcnow().date()

filter1, filter2, filter3 = st.columns([1.3, 1.3, 0.8])

with filter1:

    start_date = st.date_input(
        "Start Date",
        value=today - timedelta(days=180)
    )

with filter2:

    end_date = st.date_input(
        "End Date",
        value=today
    )

with filter3:

    timeframe = st.selectbox(
        "Time Frame",
        [
            "Day",
            "Week",
            "Month"
        ]
    )

st.divider()


# ==================================================================================================
# SQUID CONTRACTS
# ==================================================================================================

CONTRACTS = [

    "0xce16F69375520ab01377ce7B88f5BA8C48F8D666",

    "0x492751eC3c57141deb205eC2da8bFcb410738630",

    "0xDC3D8e1Abe590BCa428a8a2FC4CfDbD1AcF57Bd9",

    "0xdf4fFDa22270c12d0b5b3788F1669D709476111E",

    "0xe6B3949F9bBF168f4E3EFc82bc8FD849868CC6d8"

]


# ==================================================================================================
# FORMATTERS
# ==================================================================================================

def format_volume(value):

    value = float(value)

    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"

    if value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"

    if value >= 1_000:
        return f"${value / 1_000:.2f}K"

    return f"${value:,.2f}"


def format_transactions(value):

    value = float(value)

    if value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f}B"

    if value >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"

    if value >= 1_000:
        return f"{value / 1_000:.2f}K"

    return f"{int(value):,}"


# ==================================================================================================
# LOAD DATA FUNCTION
# ==================================================================================================

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

# ==================================================================================================
# LOAD FILTERED DATA
# ==================================================================================================

try:

    filtered_df = load_data(start_date, end_date)

    if filtered_df.empty:
        st.warning("No data found for the selected period.")
        st.stop()

except Exception as e:

    st.error(f"Error loading data: {e}")
    st.stop()


# ==================================================================================================
# AGGREGATE ALL SQUID CONTRACTS
# ==================================================================================================

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
)

filtered_df = filtered_df.sort_values("timestamp")


# ==================================================================================================
# APPLY TIME FRAME
# ==================================================================================================

if timeframe == "Day":

    chart_df = filtered_df.copy()

elif timeframe == "Week":

    chart_df = (
        filtered_df
        .set_index("timestamp")
        .resample("W")
        .sum()
        .reset_index()
    )

elif timeframe == "Month":

    chart_df = (
        filtered_df
        .set_index("timestamp")
        .resample("M")
        .sum()
        .reset_index()
    )


# ==================================================================================================
# KPI CALCULATIONS (FILTER DEPENDENT)
# ==================================================================================================

total_volume = chart_df["volume"].sum()

total_transactions = int(
    chart_df["num_txs"].sum()
)

avg_volume_per_txn = (
    total_volume / total_transactions
    if total_transactions > 0
    else 0
)


# ==================================================================================================
# KPI ROW
# ==================================================================================================

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

# ==================================================================================================
# LOAD FULL DATASET (INDEPENDENT OF FILTERS)
# ==================================================================================================

full_start_date = datetime(2024, 1, 1).date()
full_end_date = datetime.utcnow().date()

try:

    full_df = load_data(full_start_date, full_end_date)

    if full_df.empty:
        st.warning("No historical data found.")
        st.stop()

except Exception as e:

    st.error(f"Error loading historical data: {e}")
    st.stop()


# ==================================================================================================
# AGGREGATE ALL SQUID CONTRACTS
# ==================================================================================================

full_df = (
    full_df
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
)

full_df = full_df.sort_values("timestamp").reset_index(drop=True)


# ==================================================================================================
# ROLLING GROWTH FUNCTION
# ==================================================================================================

def rolling_growth(df, column, period):

    latest_date = df["timestamp"].max()

    current_start = latest_date - timedelta(days=period - 1)
    previous_end = current_start - timedelta(days=1)
    previous_start = previous_end - timedelta(days=period - 1)

    current_period = df[
        (df["timestamp"] >= current_start) &
        (df["timestamp"] <= latest_date)
    ]

    previous_period = df[
        (df["timestamp"] >= previous_start) &
        (df["timestamp"] <= previous_end)
    ]

    current_value = current_period[column].sum()
    previous_value = previous_period[column].sum()

    if previous_value == 0:
        return 0

    return ((current_value - previous_value) / previous_value) * 100


# ==================================================================================================
# VOLUME GROWTH KPIs
# ==================================================================================================

volume_growth_7d = rolling_growth(full_df, "volume", 7)

volume_growth_30d = rolling_growth(full_df, "volume", 30)

volume_growth_6m = rolling_growth(full_df, "volume", 180)


# ==================================================================================================
# TRANSACTION GROWTH KPIs
# ==================================================================================================

transaction_growth_7d = rolling_growth(full_df, "num_txs", 7)

transaction_growth_30d = rolling_growth(full_df, "num_txs", 30)

transaction_growth_6m = rolling_growth(full_df, "num_txs", 180)


# ==================================================================================================
# DISPLAY VOLUME GROWTH
# ==================================================================================================

st.markdown("## 📈 Volume Growth")

col1, col2, col3 = st.columns(3)

with col1:

    st.metric(
        "7D Volume Growth",
        f"{volume_growth_7d:.2f}%"
    )

with col2:

    st.metric(
        "30D Volume Growth",
        f"{volume_growth_30d:.2f}%"
    )

with col3:

    st.metric(
        "6M Volume Growth",
        f"{volume_growth_6m:.2f}%"
    )


st.divider()


# ==================================================================================================
# DISPLAY TRANSACTION GROWTH
# ==================================================================================================

st.markdown("## 🔄 Transaction Growth")

col1, col2, col3 = st.columns(3)

with col1:

    st.metric(
        "7D Transaction Growth",
        f"{transaction_growth_7d:.2f}%"
    )

with col2:

    st.metric(
        "30D Transaction Growth",
        f"{transaction_growth_30d:.2f}%"
    )

with col3:

    st.metric(
        "6M Transaction Growth",
        f"{transaction_growth_6m:.2f}%"
    )


st.divider()

# ==================================================================================================
# LAST 30 DAYS DATA
# ==================================================================================================

latest_date = full_df["timestamp"].max()

last_30_days_df = full_df[
    full_df["timestamp"] >= (latest_date - timedelta(days=29))
].copy()


# ==================================================================================================
# LAST 30 DAYS KPIs
# ==================================================================================================

avg_daily_volume_30d = last_30_days_df["volume"].mean()

avg_daily_transactions_30d = last_30_days_df["num_txs"].mean()

max_daily_volume_30d = last_30_days_df["volume"].max()

max_daily_transactions_30d = last_30_days_df["num_txs"].max()

min_daily_volume_30d = last_30_days_df["volume"].min()

min_daily_transactions_30d = last_30_days_df["num_txs"].min()


# ==================================================================================================
# DAILY STATISTICS (LAST 30 DAYS)
# ==================================================================================================

st.markdown("## 📅 Daily Statistics (Last 30 Days)")

col1, col2, col3 = st.columns(3)

with col1:

    st.metric(
        "Avg Daily Volume",
        format_volume(avg_daily_volume_30d)
    )

with col2:

    st.metric(
        "Avg Daily Transactions",
        format_transactions(avg_daily_transactions_30d)
    )

with col3:

    st.metric(
        "Max Daily Volume",
        format_volume(max_daily_volume_30d)
    )


col4, col5, col6 = st.columns(3)

with col4:

    st.metric(
        "Max Daily Transactions",
        format_transactions(max_daily_transactions_30d)
    )

with col5:

    st.metric(
        "Min Daily Volume",
        format_volume(min_daily_volume_30d)
    )

with col6:

    st.metric(
        "Min Daily Transactions",
        format_transactions(min_daily_transactions_30d)
    )


st.divider()

# ==================================================================================================
# AGGREGATED DATA TABLE
# ==================================================================================================

st.subheader("📋 Aggregated Dataset")

table_df = chart_df.copy()

table_df["timestamp"] = table_df["timestamp"].dt.strftime("%Y-%m-%d")

table_df = table_df.rename(
    columns={
        "timestamp": "Date",
        "volume": "Volume",
        "num_txs": "Transactions",
        "gmp_volume": "GMP Volume",
        "gmp_num_txs": "GMP Transactions",
        "transfers_volume": "Transfers Volume",
        "transfers_num_txs": "Transfers Transactions",
    }
)

st.dataframe(
    table_df,
    use_container_width=True,
    hide_index=True
)
