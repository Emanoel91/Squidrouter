import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import datetime

# --- Page Config ------------------------------------------------------------------------------------------------------
st.set_page_config(
    page_title="Daily Stats on Squid router",
    page_icon="https://img.cryptorank.io/coins/squid1675241862798.png",
    layout="wide"
)

# --- Title with Logo -----------------------------------------------------------------------------------------------------
st.markdown(
    """
    <div style="display: flex; align-items: center; gap: 15px;">
        <img src="https://img.cryptorank.io/coins/squid1675241862798.png" alt="Squid Logo" style="width:60px; height:60px;">
        <h1 style="margin: 0;">Daily Stats on Squid router</h1>
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

st.info("⏳This dashboard displays the performance of the Squid bridge over the past 24 hours, with data continuously being updated. If the data is not up to date, click on the (...) in the top-right corner of the dashboard and select 'Clear Cache' and 'Rerun' to refresh the data.")

# --- API List -----------------------------------------------------------------------------------------------------
APIS = [
    "https://api.axelarscan.io/gmp/GMPChart?contractAddress=0xce16F69375520ab01377ce7B88f5BA8C48F8D666",
    "https://api.axelarscan.io/gmp/GMPChart?contractAddress=0x492751eC3c57141deb205eC2da8bFcb410738630",
    "https://api.axelarscan.io/gmp/GMPChart?contractAddress=0xDC3D8e1Abe590BCa428a8a2FC4CfDbD1AcF57Bd9",
    "https://api.axelarscan.io/gmp/GMPChart?contractAddress=0xdf4fFDa22270c12d0b5b3788F1669D709476111E",
    "https://api.axelarscan.io/gmp/GMPChart?contractAddress=0xe6B3949F9bBF168f4E3EFc82bc8FD849868CC6d8",
    "https://api.axelarscan.io/token/transfersChart?contractAddress=0xce16F69375520ab01377ce7B88f5BA8C48F8D666",
    "https://api.axelarscan.io/token/transfersChart?contractAddress=0x492751eC3c57141deb205eC2da8bFcb410738630",
    "https://api.axelarscan.io/token/transfersChart?contractAddress=0xDC3D8e1Abe590BCa428a8a2FC4CfDbD1AcF57Bd9",
    "https://api.axelarscan.io/token/transfersChart?contractAddress=0xdf4fFDa22270c12d0b5b3788F1669D709476111E",
    "https://api.axelarscan.io/token/transfersChart?contractAddress=0xe6B3949F9bBF168f4E3EFc82bc8FD849868CC6d8"
]

# --- Date Setup --------------------------------------------------------------------------------------------------
today = datetime.date.today()
yesterday = today - datetime.timedelta(days=1)
day_before = today - datetime.timedelta(days=2)

st.subheader(f"📊 Results for {yesterday}")

# --- Fetch Data --------------------------------------------------------------------------------------------------
def fetch_data():
    all_data = []
    for url in APIS:
        try:
            r = requests.get(url)
            r.raise_for_status()
            data = r.json().get("data", [])
            all_data.extend(data)
        except Exception as e:
            st.error(f"Error fetching {url}: {e}")
    return pd.DataFrame(all_data)

raw_df = fetch_data()

if not raw_df.empty:
    # Convert timestamp to date
    raw_df["date"] = pd.to_datetime(raw_df["timestamp"], unit="ms").dt.date

    # Aggregate daily totals
    daily_df = raw_df.groupby("date").agg({"volume": "sum", "num_txs": "sum"}).reset_index()

    # Get yesterday + day before
    y_row = daily_df[daily_df["date"] == yesterday]
    d_row = daily_df[daily_df["date"] == day_before]

    vol_y, txs_y = (y_row["volume"].sum(), y_row["num_txs"].sum()) if not y_row.empty else (0, 0)
    vol_d, txs_d = (d_row["volume"].sum(), d_row["num_txs"].sum()) if not d_row.empty else (0, 0)

    # Percentage change
    vol_change = ((vol_y - vol_d) / vol_d * 100) if vol_d != 0 else 0
    txs_change = ((txs_y - txs_d) / txs_d * 100) if txs_d != 0 else 0

    # --- KPI Layout ---------------------------------------------------------------------------------------------
    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            label="Volume of Swaps",
            value=f"{vol_y:,.2f}",
            delta=f"{vol_change:.2f}%",
            delta_color="normal"
        )

    with col2:
        st.metric(
            label="Number of Swaps",
            value=f"{txs_y:,}",
            delta=f"{txs_change:.2f}%",
            delta_color="normal"
        )
else:
    st.warning("No data available.")

# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# --- Dates --------------------------------------------------------------------------------------------------------
today = datetime.date.today()
yesterday = today - datetime.timedelta(days=1)
day_before = today - datetime.timedelta(days=2)

# unix timestamps for GMPStatsByChains API
from_ts = int(datetime.datetime.combine(yesterday, datetime.time.min).timestamp())
to_ts   = int(datetime.datetime.combine(yesterday, datetime.time.max).timestamp())

# --- GMPStatsByChains APIs ----------------------------------------------------------------------------------------
CHAIN_APIS = [
    f"https://api.axelarscan.io/gmp/GMPStatsByChains?contractAddress=0xce16F69375520ab01377ce7B88f5BA8C48F8D666&fromTime={from_ts}&toTime={to_ts}",
    f"https://api.axelarscan.io/gmp/GMPStatsByChains?contractAddress=0x492751eC3c57141deb205eC2da8bFcb410738630&fromTime={from_ts}&toTime={to_ts}",
    f"https://api.axelarscan.io/gmp/GMPStatsByChains?contractAddress=0xDC3D8e1Abe590BCa428a8a2FC4CfDbD1AcF57Bd9&fromTime={from_ts}&toTime={to_ts}",
    f"https://api.axelarscan.io/gmp/GMPStatsByChains?contractAddress=0xdf4fFDa22270c12d0b5b3788F1669D709476111E&fromTime={from_ts}&toTime={to_ts}",
    f"https://api.axelarscan.io/gmp/GMPStatsByChains?contractAddress=0xe6B3949F9bBF168f4E3EFc82bc8FD849868CC6d8&fromTime={from_ts}&toTime={to_ts}"
]

# --- Fetch Chain Stats ---------------------------------------------------------------------------------------------------
def fetch_chain_stats():
    source_records, dest_records, path_records = [], [], []
    for url in CHAIN_APIS:
        try:
            r = requests.get(url)
            r.raise_for_status()
            chains = r.json().get("source_chains", [])
            for sc in chains:
                source_records.append({
                    "chain": sc["key"],
                    "num_txs": sc.get("num_txs", 0),
                    "volume": sc.get("volume", 0)
                })
                for dc in sc.get("destination_chains", []):
                    dest_records.append({
                        "chain": dc["key"],
                        "num_txs": dc.get("num_txs", 0),
                        "volume": dc.get("volume", 0)
                    })
                    path_records.append({
                        "path": f"{sc['key']} ➡ {dc['key']}",
                        "num_txs": dc.get("num_txs", 0),
                        "volume": dc.get("volume", 0)
                    })
        except Exception as e:
            st.error(f"Error fetching {url}: {e}")
    return pd.DataFrame(source_records), pd.DataFrame(dest_records), pd.DataFrame(path_records)

src_df, dst_df, path_df = fetch_chain_stats()

if not src_df.empty:
    # Aggregate unique counts
    num_sources = src_df["chain"].nunique()
    num_dests = dst_df["chain"].nunique()
    num_paths = path_df["path"].nunique()

    col1, col2, col3 = st.columns(3)
    col1.metric("Number of Source Chains", f"{num_sources}")
    col2.metric("Number of Destination Chains", f"{num_dests}")
    col3.metric("Number of Paths", f"{num_paths}")

    # --- Aggregated Tables ----------------------------------------------------------------------------------------
    src_agg = src_df.groupby("chain").agg({"volume": "sum", "num_txs": "sum"}).reset_index().rename(
        columns={"chain": "Source Chain", "volume": "Swap Volume", "num_txs": "Swap Count"}
    )
    dst_agg = dst_df.groupby("chain").agg({"volume": "sum", "num_txs": "sum"}).reset_index().rename(
        columns={"chain": "Destination Chain", "volume": "Swap Volume", "num_txs": "Swap Count"}
    )
    path_agg = path_df.groupby("path").agg({"volume": "sum", "num_txs": "sum"}).reset_index().rename(
        columns={"path": "Path", "volume": "Swap Volume", "num_txs": "Swap Count"}
    )

    # helper function to sort + reset index starting from 1
    def _one_based_index(df, sort_by):
        out = df.sort_values(sort_by, ascending=False).reset_index(drop=True)
        out.index = range(1, len(out) + 1)
        return out

    c1, c2, c3 = st.columns(3)
    with c1:
        st.dataframe(_one_based_index(src_agg, "Swap Volume"), use_container_width=True)
    with c2:
        st.dataframe(_one_based_index(dst_agg, "Swap Volume"), use_container_width=True)
    with c3:
        st.dataframe(_one_based_index(path_agg, "Swap Volume"), use_container_width=True)

    # --- Charts ---------------------------------------------------------------------------------------------------
    c1, c2, c3 = st.columns(3)
    with c1:
        fig = px.bar(src_agg.sort_values("Swap Volume", ascending=False).head(5),
                     x="Swap Volume", y="Source Chain", orientation="h",
                     title="Top 5 Source Chains By Swap Volume")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = px.bar(dst_agg.sort_values("Swap Volume", ascending=False).head(5),
                     x="Swap Volume", y="Destination Chain", orientation="h",
                     title="Top 5 Destination Chains By Swap Volume")
        st.plotly_chart(fig, use_container_width=True)
    with c3:
        fig = px.bar(path_agg.sort_values("Swap Volume", ascending=False).head(5),
                     x="Swap Volume", y="Path", orientation="h",
                     title="Top 5 Paths By Swap Volume")
        st.plotly_chart(fig, use_container_width=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        fig = px.bar(src_agg.sort_values("Swap Count", ascending=False).head(5),
                     x="Swap Count", y="Source Chain", orientation="h",
                     title="Top 5 Source Chains By Swap Count")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = px.bar(dst_agg.sort_values("Swap Count", ascending=False).head(5),
                     x="Swap Count", y="Destination Chain", orientation="h",
                     title="Top 5 Destination Chains By Swap Count")
        st.plotly_chart(fig, use_container_width=True)
    with c3:
        fig = px.bar(path_agg.sort_values("Swap Count", ascending=False).head(5),
                     x="Swap Count", y="Path", orientation="h",
                     title="Top 5 Paths By Swap Count")
        st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("No GMPStatsByChains data available.")
