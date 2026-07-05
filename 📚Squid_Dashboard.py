import streamlit as st
import requests
import pandas as pd
from datetime import date

# ---------------------------
# Contracts
# ---------------------------
CONTRACTS = [
    "0xce16F69375520ab01377ce7B88f5BA8C48F8D666",
    "0x492751eC3c57141deb205eC2da8bFcb410738630",
    "0xDC3D8e1Abe590BCa428a8a2FC4CfDbD1AcF57Bd9",
    "0xdf4fFDa22270c12d0b5b3788F1669D709476111E",
    "0xe6B3949F9bBF168f4E3EFc82bc8FD849868CC6d8"
]

BASE_URL = "https://api.axelarscan.io/api/interchainChart"


# ---------------------------
# Load Data
# ---------------------------
@st.cache_data(ttl=600)
def load_data(contract):
    url = f"{BASE_URL}?contractAddress={contract}"
    r = requests.get(url, timeout=20)
    df = pd.DataFrame(r.json()["data"])

    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
    df["volume"] = df["volume"].astype(float)
    df["num_txs"] = df["num_txs"].astype(int)

    return df


def get_full_data():
    dfs = [load_data(c) for c in CONTRACTS]
    df = pd.concat(dfs)

    # merge all contracts
    df = df.groupby("timestamp", as_index=False).sum()

    return df


df = get_full_data()


# =========================================================
# TOP FILTERS (NOT SIDEBAR)
# =========================================================
st.markdown("### 📊 Filters")

col1, col2, col3 = st.columns([2, 2, 2])

with col1:
    start_date = st.date_input("Start Date", value=date(2024, 1, 1))

with col2:
    end_date = st.date_input("End Date", value=date.today())

with col3:
    timeframe = st.selectbox("Timeframe", ["Day", "Week", "Month"])


# ---------------------------
# Apply Date Filter
# ---------------------------
df = df[
    (df["timestamp"] >= pd.to_datetime(start_date)) &
    (df["timestamp"] <= pd.to_datetime(end_date))
]


# ---------------------------
# Timeframe Aggregation
# ---------------------------
df = df.set_index("timestamp")

if timeframe == "Day":
    df = df.resample("D").sum()
elif timeframe == "Week":
    df = df.resample("W").sum()
elif timeframe == "Month":
    df = df.resample("M").sum()

df = df.reset_index()


# =========================================================
# KPI CALCULATIONS
# =========================================================
total_volume = df["volume"].sum()
total_txs = df["num_txs"].sum()
avg_vol_per_txn = total_volume / total_txs if total_txs > 0 else 0


# =========================================================
# KPI UI (ONE ROW)
# =========================================================
st.markdown("### 📈 Key Metrics")

col1, col2, col3 = st.columns(3)

col1.metric("Total Volume", f"{total_volume:,.2f}")
col2.metric("Total Transactions", f"{total_txs:,}")
col3.metric("Avg Vol per Txn", f"{avg_vol_per_txn:,.4f}")
