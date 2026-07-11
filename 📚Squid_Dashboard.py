import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta


# ================ PAGE CONFIG ================

st.set_page_config(page_title="SquidRouter On-Chain Analytics", page_icon="https://images.cryptorank.io/coins/150x150.squid1675241862798.png", layout="wide")

# ================ CUSTOM CSS ================

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

# ================ HEADER ================

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

# ================ BUILDER INFO ================

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

# ================ INFO ================
st.info("📊 On-chain analytics dashboard for SquidRouter cross-chain activity.")
st.info("⏳ Data is fetched from AxelarScan APIs and may take a few seconds.")

# ================ FILTERS ================

today = datetime.utcnow().date()
c1, c2, c3 = st.columns([1.3, 1.3, 0.8])
with c1:
    start_date = st.date_input("Start Date", value=datetime(2022, 12, 1).date(), min_value=datetime(2022, 12, 1).date(), max_value=today)
with c2:
    end_date = st.date_input("End Date", value=today)
with c3:
    timeframe = st.selectbox("Time Frame", ["Month", "Week", "Day"])

st.divider()

# ================ CONTRACTS ================

CONTRACTS = ["0xce16F69375520ab01377ce7B88f5BA8C48F8D666", "0x492751eC3c57141deb205eC2da8bFcb410738630", "0xDC3D8e1Abe590BCa428a8a2FC4CfDbD1AcF57Bd9",
    "0xdf4fFDa22270c12d0b5b3788F1669D709476111E", "0xe6B3949F9bBF168f4E3EFc82bc8FD849868CC6d8"]

# ================ LOAD DATA ================ 

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

    numeric_cols = ["volume", "num_txs", "gmp_volume", "gmp_num_txs", "transfers_volume", "transfers_num_txs"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    return df

# ================ LOAD FILTERED DATA ================

filtered_df = load_data(start_date, end_date)
if filtered_df.empty:
    st.warning("No data found for selected range.")
    st.stop()

# ================ DAILY AGGREGATION ================

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

# ================ TIMEFRAME TRANSFORMATION ================

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

# ================ BASE KPI CALCULATIONS ================

total_volume = chart_df["volume"].sum()
total_transactions = int(chart_df["num_txs"].sum())
avg_volume_per_txn = (
    total_volume / total_transactions
    if total_transactions > 0
    else 0
)

# ================ KPI ROW ================

kpi1, kpi2, kpi3 = st.columns(3)
with kpi1:
    st.metric(label="Total Volume", value=f"${total_volume:,.2f}")
with kpi2:
    st.metric(label="Total Transactions", value=f"{total_transactions:,}")
with kpi3:
    st.metric(label="Avg Volume per Txn", value=f"${avg_volume_per_txn:,.2f}")

# ================ NUMBER FORMATTER ================

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

# ================ DAILY STATISTICS ================ 

daily_df = filtered_df.copy()

# ================ Volume Statistics ================

max_daily_volume = daily_df["volume"].max()
median_daily_volume = daily_df["volume"].median()
avg_daily_volume = daily_df["volume"].mean()

# ================ Transaction Statistics ================

max_daily_tx = int(daily_df["num_txs"].max())
median_daily_tx = int(daily_df["num_txs"].median())
avg_daily_tx = int(daily_df["num_txs"].mean())

# ================ DAILY KPI ROW ================

k1, k2, k3, k4, k5, k6 = st.columns(6)
with k1:
    st.metric("Max Daily Volume", format_number(max_daily_volume, "$"))
with k2:
    st.metric("Median Daily Volume", format_number(median_daily_volume, "$"))
with k3:
    st.metric("Avg Daily Volume", format_number(avg_daily_volume, "$"))
with k4:
    st.metric("Max Daily Txn", format_number(max_daily_tx))
with k5:
    st.metric("Median Daily Txn", format_number(median_daily_tx))
with k6:
    st.metric("Avg Daily Txn", format_number(avg_daily_tx))

st.divider()

# ================ LOAD FULL DATASET ================

full_start = datetime(2024, 1, 1).date()
full_end = datetime.utcnow().date()
full_df = load_data(full_start, full_end)
if full_df.empty:
    st.warning("No data available for KPIs")
    st.stop()

# ================ CLEAN TIMESTAMP ================

full_df["timestamp"] = pd.to_numeric(full_df["timestamp"], errors="coerce")
full_df = full_df.dropna(subset=["timestamp"])
full_df["timestamp"] = full_df["timestamp"].astype("int64")
full_df["timestamp"] = pd.to_datetime(full_df["timestamp"], unit="ms", errors="coerce")
full_df = full_df.dropna(subset=["timestamp"])

# ================ DAILY AGGREGATION ================

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

# ================ GROWTH FUNCTION ================

def growth_from_window(df, column, days):
    if len(df) < days * 2:
        return 0
    last_window = (df.iloc[-days:][column].sum())
    previous_window = (df.iloc[-(2 * days):-days][column].sum())
    if previous_window <= 0:
        return 0
    return ((last_window - previous_window) / previous_window) * 100

# ================ GROWTH KPI CALCULATIONS ================

volume_7d = growth_from_window(full_df, "volume", 7)
volume_30d = growth_from_window(full_df, "volume", 30)
volume_6m = growth_from_window(full_df, "volume", 180)
tx_7d = growth_from_window(full_df, "num_txs", 7)
tx_30d = growth_from_window(full_df, "num_txs", 30)
tx_6m = growth_from_window(full_df, "num_txs", 180)

# ================ GROWTH KPI ROW ================

c1, c2, c3, c4, c5, c6 = st.columns(6)
with c1:
    st.metric("7D Volume", f"{volume_7d:.2f}%")
with c2:
    st.metric("30D Volume", f"{volume_30d:.2f}%")
with c3:
    st.metric("6M Volume", f"{volume_6m:.2f}%")
with c4:
    st.metric("7D Tx", f"{tx_7d:.2f}%")
with c5:
    st.metric("30D Tx", f"{tx_30d:.2f}%")
with c6:
    st.metric("6M Tx", f"{tx_6m:.2f}%")

# ================ VOLUME & TRANSACTIONS OVER TIME ================

col1, col2 = st.columns(2)
with col1:
    fig = go.Figure()
    fig.add_trace(go.Bar(x=chart_df["timestamp"], y=chart_df["volume"], marker=dict(color="#c58ce2", line=dict( color="#c58ce2", width=0)),
            hovertemplate=
            "<b>%{x|%Y-%m-%d}</b><br>"
            "Volume: <b>$%{y:,.2f}</b>"
            "<extra></extra>"
        )
    )
    fig.update_layout(title="Cross-chain Volume Over Time", template="plotly_white", height=430, bargap=0.15, showlegend=False, hovermode="x unified", margin=dict(l=10,r=10,t=50,b=10),
        xaxis_title="", yaxis_title="Volume ($)")
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_xaxes(range=[pd.Timestamp(start_date), pd.Timestamp(end_date)])
    fig.update_yaxes( gridcolor="rgba(0,0,0,0.08)", zeroline=False)
    st.plotly_chart(fig, use_container_width=True)
with col2:
    fig = go.Figure()
    fig.add_trace(go.Bar(x=chart_df["timestamp"], y=chart_df["num_txs"], marker=dict(color="#e1fb43", line=dict(color="#e1fb43", width=0)),
            hovertemplate=
            "<b>%{x|%Y-%m-%d}</b><br>"
            "Transactions: <b>%{y:,}</b>"
            "<extra></extra>"
        )
    )
    fig.update_layout(title="Cross-chain Transactions Over Time", template="plotly_white", height=430, bargap=0.15, showlegend=False,
        hovermode="x unified", margin=dict(l=10, r=10, t=50, b=10), xaxis_title="", yaxis_title="Transactions")
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_xaxes(range=[pd.Timestamp(start_date), pd.Timestamp(end_date)])
    fig.update_yaxes(gridcolor="rgba(0,0,0,0.08)", zeroline=False)
    st.plotly_chart(fig, use_container_width=True)

# ================ CUMULATIVE & AVG CHARTS ================

cum_df = chart_df.copy()

cum_df["cumulative_volume"] = cum_df["volume"].cumsum()
cum_df["cumulative_txs"] = cum_df["num_txs"].cumsum()
cum_df["avg_volume_per_tx"] = (
    cum_df["volume"] / cum_df["num_txs"]
).replace([float("inf"), -float("inf")], 0).fillna(0)

col1, col2, col3 = st.columns(3)

# ================= Cumulative Volume =================

with col1:

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=cum_df["timestamp"],
            y=cum_df["cumulative_volume"],
            mode="lines",
            line=dict(color="#c58ce2", width=3),
            fill="tozeroy",
            fillcolor="rgba(197,140,226,0.25)",
            hovertemplate=
            "<b>%{x|%Y-%m-%d}</b><br>"
            "Cumulative Volume: <b>$%{y:,.2f}</b>"
            "<extra></extra>"
        )
    )

    fig.update_layout(
        title="Cumulative Volume Over Time",
        template="plotly_white",
        height=420,
        showlegend=False,
        hovermode="x unified",
        margin=dict(l=10, r=10, t=50, b=10),
        xaxis_title="",
        yaxis_title="Volume ($)"
    )

    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        range=[pd.Timestamp(start_date), pd.Timestamp(end_date)]
    )

    fig.update_yaxes(
        gridcolor="rgba(0,0,0,0.08)",
        zeroline=False
    )

    st.plotly_chart(fig, use_container_width=True)

# ================= Cumulative Transactions =================

with col2:

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=cum_df["timestamp"],
            y=cum_df["cumulative_txs"],
            mode="lines",
            line=dict(color="#c58ce2", width=3),
            fill="tozeroy",
            fillcolor="rgba(197,140,226,0.25)",
            hovertemplate=
            "<b>%{x|%Y-%m-%d}</b><br>"
            "Cumulative Transactions: <b>%{y:,}</b>"
            "<extra></extra>"
        )
    )

    fig.update_layout(
        title="Cumulative Transactions Over Time",
        template="plotly_white",
        height=420,
        showlegend=False,
        hovermode="x unified",
        margin=dict(l=10, r=10, t=50, b=10),
        xaxis_title="",
        yaxis_title="Transactions"
    )

    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        range=[pd.Timestamp(start_date), pd.Timestamp(end_date)]
    )

    fig.update_yaxes(
        gridcolor="rgba(0,0,0,0.08)",
        zeroline=False
    )

    st.plotly_chart(fig, use_container_width=True)

# ================= Average Volume per Transaction =================

with col3:

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=cum_df["timestamp"],
            y=cum_df["avg_volume_per_tx"],
            mode="lines",
            line=dict(color="#c58ce2", width=3),
            hovertemplate=
            "<b>%{x|%Y-%m-%d}</b><br>"
            "Avg Volume / Tx: <b>$%{y:,.2f}</b>"
            "<extra></extra>"
        )
    )

    fig.update_layout(
        title="Average Volume per Transaction Over Time",
        template="plotly_white",
        height=420,
        showlegend=False,
        hovermode="x unified",
        margin=dict(l=10, r=10, t=50, b=10),
        xaxis_title="",
        yaxis_title="USD"
    )

    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        range=[pd.Timestamp(start_date), pd.Timestamp(end_date)]
    )

    fig.update_yaxes(
        gridcolor="rgba(0,0,0,0.08)",
        zeroline=False
    )

    st.plotly_chart(fig, use_container_width=True)

# ================ MONTH x WEEKDAY HEATMAPS ================

heat_df = filtered_df.copy()

heat_df["month"] = heat_df["timestamp"].dt.month_name().str[:3]
heat_df["weekday"] = heat_df["timestamp"].dt.day_name()

month_order = [
    "Jan","Feb","Mar","Apr","May","Jun",
    "Jul","Aug","Sep","Oct","Nov","Dec"
]

weekday_order = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday"
]

# ---------- Volume Heatmap ----------

volume_matrix = (
    heat_df
    .groupby(["weekday", "month"])["volume"]
    .sum()
    .unstack(fill_value=0)
    .reindex(index=weekday_order, columns=month_order)
)

# ---------- Transaction Heatmap ----------

tx_matrix = (
    heat_df
    .groupby(["weekday", "month"])["num_txs"]
    .sum()
    .unstack(fill_value=0)
    .reindex(index=weekday_order, columns=month_order)
)

col1, col2 = st.columns(2)

# ================= Volume Heatmap =================

with col1:

    fig = go.Figure(
        data=go.Heatmap(
            z=volume_matrix.values,
            x=month_order,
            y=weekday_order,
            colorscale=[
                [0.00, "#ffffff"],
                [0.20, "#efe1f7"],
                [0.40, "#dfc0ef"],
                [0.60, "#cf9fe7"],
                [0.80, "#c58ce2"],
                [1.00, "#8c42b8"]
            ],
            hovertemplate=
            "<b>%{y}</b><br>"
            "Month: %{x}<br>"
            "Volume: <b>$%{z:,.2f}</b>"
            "<extra></extra>",
            colorbar=dict(title="Volume ($)")
        )
    )

    fig.update_layout(
        title="Cross-chain Volume Heatmap",
        template="plotly_white",
        height=430,
        margin=dict(l=10, r=10, t=50, b=10),
        xaxis_title="Month",
        yaxis_title=""
    )

    st.plotly_chart(fig, use_container_width=True)

# ================= Transactions Heatmap =================

with col2:

    fig = go.Figure(
        data=go.Heatmap(
            z=tx_matrix.values,
            x=month_order,
            y=weekday_order,
            colorscale=[
                [0.00, "#ffffff"],
                [0.20, "#efe1f7"],
                [0.40, "#dfc0ef"],
                [0.60, "#cf9fe7"],
                [0.80, "#c58ce2"],
                [1.00, "#8c42b8"]
            ],
            hovertemplate=
            "<b>%{y}</b><br>"
            "Month: %{x}<br>"
            "Transactions: <b>%{z:,}</b>"
            "<extra></extra>",
            colorbar=dict(title="Transactions")
        )
    )

    fig.update_layout(
        title="Cross-chain Transactions Heatmap",
        template="plotly_white",
        height=430,
        margin=dict(l=10, r=10, t=50, b=10),
        xaxis_title="Month",
        yaxis_title=""
    )

    st.plotly_chart(fig, use_container_width=True)

# ================ AVERAGE BY WEEKDAY ================

weekday_df = filtered_df.copy()

weekday_df["weekday"] = weekday_df["timestamp"].dt.day_name()

weekday_order = [
    "Sunday",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday"
]

avg_weekday = (
    weekday_df
    .groupby("weekday", as_index=False)
    .agg(
        avg_volume=("volume", "mean"),
        avg_txs=("num_txs", "mean")
    )
)

avg_weekday["weekday"] = pd.Categorical(
    avg_weekday["weekday"],
    categories=weekday_order,
    ordered=True
)

avg_weekday = avg_weekday.sort_values("weekday")


# ---------- Color Helper ----------

BASE_COLOR = "#c58ce2"
MIN_COLOR = "#f4a6a6"     # Soft Red
MAX_COLOR = "#8fd19e"     # Soft Green


def highlight_colors(values):

    colors = [BASE_COLOR] * len(values)

    min_value = values.min()
    max_value = values.max()

    for i, v in enumerate(values):
        if v == min_value:
            colors[i] = MIN_COLOR
        if v == max_value:
            colors[i] = MAX_COLOR

    return colors


volume_colors = highlight_colors(avg_weekday["avg_volume"])
tx_colors = highlight_colors(avg_weekday["avg_txs"])

col1, col2 = st.columns(2)

# ================= Average Volume =================

with col1:

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=avg_weekday["weekday"],
            y=avg_weekday["avg_volume"],
            marker=dict(
                color=volume_colors,
                line=dict(color=volume_colors, width=1)
            ),
            hovertemplate=
            "<b>%{x}</b><br>"
            "Average Volume: <b>$%{y:,.2f}</b>"
            "<extra></extra>"
        )
    )

    fig.update_layout(
        title="Average Daily Volume by Weekday",
        template="plotly_white",
        height=430,
        showlegend=False,
        margin=dict(l=10, r=10, t=50, b=10),
        xaxis_title="",
        yaxis_title="Average Volume ($)"
    )

    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="rgba(0,0,0,0.08)")

    st.plotly_chart(fig, use_container_width=True)

# ================= Average Transactions =================

with col2:

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=avg_weekday["weekday"],
            y=avg_weekday["avg_txs"],
            marker=dict(
                color=tx_colors,
                line=dict(color=tx_colors, width=1)
            ),
            hovertemplate=
            "<b>%{x}</b><br>"
            "Average Transactions: <b>%{y:,.1f}</b>"
            "<extra></extra>"
        )
    )

    fig.update_layout(
        title="Average Daily Transactions by Weekday",
        template="plotly_white",
        height=430,
        showlegend=False,
        margin=dict(l=10, r=10, t=50, b=10),
        xaxis_title="",
        yaxis_title="Average Transactions"
    )

    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="rgba(0,0,0,0.08)")

    st.plotly_chart(fig, use_container_width=True)

# ================================================================== Part II: User Analysis ==============================================================================
# ================ USER ANALYTICS FILTERS ================

st.divider()
st.header("👥 User Analytics")

today = datetime.utcnow().date()

u1, u2 = st.columns(2)

with u1:
    user_start_date = st.date_input(
        "Start Date",
        value=datetime(2024,1,1).date(),
        key="user_start"
    )

with u2:
    user_end_date = st.date_input(
        "End Date",
        value=today,
        key="user_end"
    )

# ================ LOAD USER DATA ================

@st.cache_data(ttl=3600)
def load_user_data(start_date, end_date):

    from_time = int(datetime.combine(start_date, datetime.min.time()).timestamp())
    to_time = int(datetime.combine(end_date, datetime.max.time()).timestamp())

    dfs = []

    for contract in CONTRACTS:

        url = (
            "https://api.axelarscan.io/gmp/GMPTopUsers"
            f"?contractAddress={contract}"
            f"&fromTime={from_time}"
            f"&toTime={to_time}"
        )

        try:

            r = requests.get(url, timeout=60)

            if r.status_code != 200:
                continue

            data = r.json().get("data", [])

            if len(data) == 0:
                continue

            df = pd.DataFrame(data)

            dfs.append(df)

        except Exception:
            continue

    if len(dfs) == 0:
        return pd.DataFrame()

    df = pd.concat(dfs, ignore_index=True)

    df["volume"] = pd.to_numeric(df["volume"], errors="coerce").fillna(0)
    df["num_txs"] = pd.to_numeric(df["num_txs"], errors="coerce").fillna(0)

    # -------- Aggregate same users across contracts --------

    df = (
        df.groupby("key", as_index=False)
        .agg(
            volume=("volume","sum"),
            num_txs=("num_txs","sum")
        )
        .sort_values("volume", ascending=False)
        .reset_index(drop=True)
    )

    return df

user_df = load_user_data(user_start_date, user_end_date)

if user_df.empty:
    st.warning("No user data found.")
    st.stop()

# ================ USER KPIs ================

unique_users = len(user_df)

avg_volume_user = user_df["volume"].mean()

avg_tx_user = user_df["num_txs"].mean()

median_volume_user = user_df["volume"].median()

median_tx_user = user_df["num_txs"].median()


k1,k2,k3,k4,k5 = st.columns(5)

with k1:
    st.metric(
        "Unique Users",
        format_number(unique_users)
    )

with k2:
    st.metric(
        "Avg Volume per User",
        format_number(avg_volume_user,"$")
    )

with k3:
    st.metric(
        "Avg Txn per User",
        f"{avg_tx_user:.2f}"
    )

with k4:
    st.metric(
        "Median Volume per User",
        format_number(median_volume_user,"$")
    )

with k5:
    st.metric(
        "Median Txn per User",
        f"{median_tx_user:.2f}"
    )

# ================ USER VOLUME DISTRIBUTION ================

dist_df = user_df.copy()

# -------- Buckets --------

bins = [
    0,
    100,
    1_000,
    10_000,
    100_000,
    1_000_000,
    float("inf")
]

labels = [
    "<$100",
    "$100-$1K",
    "$1K-$10K",
    "$10K-$100K",
    "$100K-$1M",
    ">$1M"
]

dist_df["bucket"] = pd.cut(
    dist_df["volume"],
    bins=bins,
    labels=labels,
    include_lowest=True
)

bucket_df = (
    dist_df
    .groupby("bucket", observed=False)
    .size()
    .reset_index(name="users")
)

bucket_df["percent"] = (
    bucket_df["users"]
    / bucket_df["users"].sum()
    * 100
)

bucket_df = bucket_df.sort_values("bucket")


# -------- Color Scale --------

base_rgb = (225, 251, 67)

vmin = bucket_df["users"].min()
vmax = bucket_df["users"].max()

colors = []

for value in bucket_df["users"]:

    if vmax == vmin:
        alpha = 1

    else:
        alpha = 0.30 + 0.70 * ((value - vmin) / (vmax - vmin))

    colors.append(
        f"rgba({base_rgb[0]},{base_rgb[1]},{base_rgb[2]},{alpha:.3f})"
    )

col1, col2 = st.columns(2)

# ================= PIE =================

with col1:

    fig = go.Figure()

    fig.add_trace(
        go.Pie(
            labels=bucket_df["bucket"],
            values=bucket_df["users"],
            hole=0.45,
            marker=dict(
                colors=colors,
                line=dict(color="white", width=2)
            ),
            textinfo="percent",
            textposition="inside",
            insidetextorientation="auto",
            hovertemplate=
            "<b>%{label}</b><br>"
            "Users: %{value:,}<br>"
            "Share: %{percent}"
            "<extra></extra>"
        )
    )

    fig.update_layout(
        title="User Volume Distribution",
        template="plotly_white",
        height=430,
        margin=dict(l=10, r=10, t=50, b=10),
        showlegend=True,
        legend=dict(
            title="Volume Bucket",
            orientation="v",
            y=0.5,
            yanchor="middle",
            x=1.02,
            xanchor="left",
            font=dict(size=13)
        )
    )

    st.plotly_chart(fig, use_container_width=True)

# ================= BAR =================

with col2:

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=bucket_df["bucket"],
            y=bucket_df["users"],
            marker=dict(
                color=colors,
                line=dict(color=colors,width=1)
            ),
            text=bucket_df["users"].map("{:,}".format),
            textposition="outside",
            cliponaxis=False,
            hovertemplate=
            "<b>%{x}</b><br>"
            "Users: %{y:,}"
            "<extra></extra>"
        )
    )

    fig.update_layout(
        title="Users by Volume Bucket",
        template="plotly_white",
        height=430,
        showlegend=False,
        margin=dict(l=10,r=10,t=50,b=10),
        xaxis_title="Volume Bucket",
        yaxis_title="Users"
    )

    fig.update_xaxes(showgrid=False)

    fig.update_yaxes(
        gridcolor="rgba(0,0,0,0.08)"
    )

    st.plotly_chart(fig,use_container_width=True)
