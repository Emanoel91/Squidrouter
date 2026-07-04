import streamlit as st
import pandas as pd
import snowflake.connector
import plotly.express as px
import plotly.graph_objects as go
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

# --- Page Config: Tab Title & Icon -------------------------------------------------------------------------------------
st.set_page_config(
    page_title="ATH Interchain Transfers Using Axelar ITS",
    page_icon="https://pbs.twimg.com/profile_images/1869486848646537216/rs71wCQo_400x400.jpg",
    layout="wide"
)

# --- Title with Logo ---------------------------------------------------------------------------------------------------
st.markdown(
    """
    <div style="display: flex; align-items: center; gap: 15px;">
        <img src="https://img.cryptorank.io/coins/aethir1731483767528.png" alt="Aethir Logo" style="width:60px; height:60px;">
        <h1 style="margin: 0;">ATH Interchain Transfers Using Axelar ITS</h1>
    </div>
    """,
    unsafe_allow_html=True
)

# --- Builder Info ---------------------------------------------------------------------------------------------------------
st.markdown(
    """
    <div style="margin-top: 20px; margin-bottom: 20px; font-size: 16px;">
        <div style="display: flex; align-items: center; gap: 10px;">
            <img src="https://pbs.twimg.com/profile_images/1841479747332608000/bindDGZQ_400x400.jpg" style="width:25px; height:25px; border-radius: 50%;">
            <span>Built by: <a href="https://x.com/0xeman_raz" target="_blank">Eman Raz</a></span>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# --- Info Box --------------------------------------------------------------------------------------------------------------
st.markdown(
    """
    <div style="background-color: #d9fd51; padding: 10px; border-radius: 1px; border: 1px solid #000000;">
        Aethir and Axelar have partnered to enhance the interoperability of Aethir's ATH token across multiple blockchains. 
        Aethir, a decentralized cloud infrastructure provider focused on gaming and AI, has integrated Axelar as its official 
        blockchain bridge platform to enable seamless cross-chain bridging of the ATH token between Ethereum mainnet and Arbitrum Layer-2 blockchain. 
        Axelar’s Interchain Token Service (ITS) supports this by allowing Aethir to deploy ERC-20 tokens across over many blockchains while maintaining 
        native token functionality. This partnership facilitates frictionless ATH token transfers for Aethir’s ecosystem, particularly for Checker Node 
        and Aethir Edge rewards (Arbitrum-based) and staking or exchange activities (Ethereum-based). 
        Axelar’s decentralized network, APIs, and development tools provide scalability and flexibility, enabling Aethir to potentially expand ATH to 
        additional blockchains. 
    </div>
    """,
    unsafe_allow_html=True
)

st.info(
    "📊Charts initially display data for a default time range. Select a custom range to view results for your desired period."

)

st.info(
    "⏳On-chain data retrieval may take a few moments. Please wait while the results load."
)
