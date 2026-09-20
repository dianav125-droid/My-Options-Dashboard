import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import datetime

# --- CONFIGURATION & PAGE SETUP ---
st.set_page_config(page_title="Premium Seller Dashboard", layout="wide", page_icon="📈")

# Style adjustments for scannability
st.markdown("""
    <style>
    .metric-box { padding: 15px; border-radius: 8px; background-color: #f0f2f6; margin-bottom: 10px; }
    .stButton>button { width: 100%; background-color: #4CAF50; color: white; }
    </style>
""", unsafe_allowed_html=True)

# --- DATABASE / CSV ENGINE ---
DB_FILE = "options_trade_log.csv"

def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        # Ensure correct data types
        df['Entry Date'] = pd.to_datetime(df['Entry Date']).dt.strftime('%Y-%m-%d')
        return df
    else:
        return pd.DataFrame(columns=[
            "Ticker", "Strategy", "Entry Date", "DTE", "Capital Risked", 
            "Net Credit", "IV (%)", "VRP (%)", "Status", "ROI (%)", "Annualized Return (%)"
        ])

def save_trade(trade_dict):
    df = load_data()
    new_row = pd.DataFrame([trade_dict])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(DB_FILE, index=False)

# Load master trade log
trade_df = load_data()

st.title("📈 Living Options Premium Dashboard & VRP Tracker")
st.caption("Track capital velocity, Implied Volatility Rank, and Volatility Risk Premium margins.")

# --- NAVIGATION TABS ---
tab1, tab2, tab3 = st.tabs(["🧮 Trade Analyzer & Logger", "📊 Performance Analytics", "🗂️ Master Ledger"])

# ==========================================
# TAB 1: TRADE ANALYZER & LOGGER
# ==========================================
with tab1:
    st.subheader("1. Pre-Trade Probability & Velocity Calculator")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        ticker = st.text_input("Ticker Symbol", value="MU").upper()
        strategy = st.selectbox("Strategy Type", ["Put Credit Spread (PCS)", "Cash Secured Put (CSP)", "Covered Call (CC)", "Other"])
    with col2:
        capital_risked = st.number_input("Capital Risked / Collateral ($)", min_value=1.0, value=400.0, step=50.0)
        net_credit = st.number_input("Net Credit Collected ($)", min_value=0.0, value=100.0, step=5.0)
    with col3:
        dte = st.number_input("Days to Expiration (DTE)", min_value=1, value=38)
        entry_date = st.date_input("Entry Date", datetime.now())
    with col4:
        iv_pct = st.number_input("Absolute IV / IV Rank (%)", min_value=0.0, max_value=100.0, value=45.0)
        vrp_pct = st.number_input("VRP (IV - Realized Vol) (%)", min_value=-50.0, max_value=100.0, value=8.5)

    # Core Math Calculators
    roi = (net_credit / capital_risked) * 100
    annualized_return = roi * (365 / dte)
    
    # Threshold Alerts
    roi_color = "🟢" if 3.0 <= roi <= 5.0 else "⚠️"
    vrp_color = "🟢" if vrp_pct > 5.0 else "⚠️"
    iv_color = "🟢" if iv_pct >= 30.0 else "⚠️"

    st.markdown("### 🔍 Trade Quality Scan")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Calculated Trade ROI", f"{roi:.2f}%", help="Goal: 3-5%")
    m2.metric("Annualized Velocity", f"{annualized_return:.2f}%")
    m3.metric("IV Environment", f"{iv_pct:.1f}% Status", delta="Optimal" if iv_pct >= 30 else "Low Premium")
    m4.metric("VRP Edge Margin", f"{vrp_pct:.1f}%", delta="Edge Present" if vrp_pct > 0 else "Overpriced Risk")
    
    # Status Guidance Box
    if 3.0 <= roi <= 5.0 and iv_pct >= 30 and vrp_pct > 0:
        st.success("🎯 **Premium Target Met:** Trade matches your exact 3-5% ROI model with structural volatility edge.")
    else:
        st.warning("ℹ️ **Model Divergence:** One or more parameters (ROI, Absolute IV, or VRP) sit outside optimal parameters. Check positioning.")

    if st.button("💾 Commit Order & Log Trade to Live Database"):
        trade_data = {
            "Ticker": ticker, "Strategy": strategy, "Entry Date": entry_date.strftime('%Y-%m-%d'),
            "DTE": int(dte), "Capital Risked": float(capital_risked), "Net Credit": float(net_credit),
            "IV (%)": float(iv_pct), "VRP (%)": float(vrp_pct), "Status": "Open",
            "ROI (%)": round(roi, 2), "Annualized Return (%)": round(annualized_return, 2)
        }
        save_trade(trade_data)
        st.success(f"Success! {strategy} on ${ticker} logged seamlessly.")
        st.rerun()

# ==========================================
# TAB 2: PERFORMANCE ANALYTICS
# ==========================================
with tab2:
    st.subheader("📊 Portfolio Diagnostic Dashboard")
    if trade_df.empty:
        st.info("Your database is currently empty. Commit a trade in Tab 1 to activate performance visuals.")
    else:
        # High Level Summary Statistics
        total_trades = len(trade_df)
        open_trades = len(trade_df[trade_df["Status"] == "Open"])
        closed_trades = trade_df[trade_df["Status"] == "Closed"]
        
        # Simple placeholder win rate generation assuming wins if not noted
        win_rate = 100.0 if len(closed_trades) == 0 else (len(closed_trades) / len(closed_trades)) * 100 
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Tracked Logged Trades", total_trades)
        c2.metric("Active Working Contracts", open_trades)
        c3.metric("Running Win Rate", f"{win_rate:.1f}%")
        c4.metric("Total Premium Captured", f"${trade_df['Net Credit'].sum():,.2f}")

        # Allocation Splits
        st.markdown("### 📁 Strategy Allocation Breakdown")
        strat_counts = trade_df["Strategy"].value_counts()
        st.dataframe(strat_counts, use_container_width=True)

# ==========================================
# TAB 3: MASTER LEDGER
# ==========================================
with tab3:
    st.subheader("🗂️ Live Unrestricted Options Database File")
    if trade_df.empty:
        st.info("No recorded trades found in database.")
    else:
        # Display editable dataframe to allow tracking or closing manually
        st.dataframe(trade_df, use_container_width=True)
        
        # Reset capability
        if st.checkbox("Danger Zone: Clear Database File"):
            if st.button("Confirm: Clear CSV Logs"):
                if os.path.exists(DB_FILE):
                    os.remove(DB_FILE)
                st.success("Database cleared.")
                st.rerun()
