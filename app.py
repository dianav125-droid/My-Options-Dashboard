import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import datetime

# --- CONFIGURATION & PAGE SETUP ---
st.set_page_config(page_title="Premium Seller Command Center", layout="wide", page_icon="📊")

# Re-establishing high-visibility visual anchors
st.html("<style>.metric-box { padding: 15px; border-radius: 8px; background-color: #f0f2f6; margin-bottom: 10px; } .stButton>button { width: 100%; background-color: #1E3A8A; color: white; font-weight: bold; }</style>")

# --- CORE DATABASE FILE PATH ---
DB_FILE = "options_master_ledger.csv"

def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        df['Entry Date'] = pd.to_datetime(df['Entry Date'])
        return df
    else:
        # Re-built with every metric tracking feature from our deep-dive analysis tables
        return pd.DataFrame(columns=[
            "Ticker", "Sector", "Strategy", "Status", "Entry Date", 
            "Entry DTE", "Close DTE", "Capital Risked", "Net Credit", 
            "Exit Premium", "IV (%)", "VRP (%)", "Realized PnL ($)", "ROI (%)", "Annualized Return (%)"
        ])

def save_trade(trade_dict):
    df = load_data()
    new_row = pd.DataFrame([trade_dict])
    new_row['Entry Date'] = pd.to_datetime(new_row['Entry Date'])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(DB_FILE, index=False)

# Load master trade log
trade_df = load_data()

st.title("📊 The Premium Seller Command Center")
st.caption("Live Options Portfolio Log, Volatility Risk Premium (VRP) Index Engine, and Capital Velocity Calculator.")

# --- MASTER NAVIGATION TABS ---
tab1, tab2, tab3 = st.tabs(["🧮 Pre-Trade Quality Analyzer", "📈 Time-Horizon Performance Analytics", "🗂️ Unrestricted Master Ledger"])

# ==========================================
# TAB 1: PRE-TRADE QUALITY ANALYZER
# ==========================================
with tab1:
    st.subheader("💡 Pre-Trade Probability & Velocity Calculator")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        ticker = st.text_input("Ticker Symbol", value="MU").upper()
        sector = st.selectbox("Ticker Sector Allocation", ["Semiconductors", "Tech Infrastructure", "Tech Components", "Clean Energy", "Index / Macro", "Other"])
        strategy = st.selectbox("Strategy Architecture", ["Put Credit Spread (PCS)", "Cash Secured Put (CSP)", "Covered Call (CC)", "Long Call / Speculative Debit", "Other Premium Sale"])
    with col2:
        capital_risked = st.number_input("Capital Risked / Collateral Max Risk ($)", min_value=1.0, value=400.0, step=50.0)
        net_credit = st.number_input("Net Entry Credit Collected ($)", min_value=0.0, value=100.0, step=5.0)
    with col3:
        entry_dte = st.number_input("Days to Expiration at Entry (DTE)", min_value=1, value=40, help="Options Sweet Spot: ~40 DTE")
        entry_date = st.date_input("Execution Date", datetime.now())
    with col4:
        iv_pct = st.number_input("Absolute Implied Volatility / IV Rank (%)", min_value=0.0, max_value=100.0, value=45.0, help="Target high absolute IV to inflate option decay cushions.")
        vrp_pct = st.number_input("VRP Spread Margin (IV - Realized Vol) (%)", min_value=-50.0, max_value=100.0, value=8.5, help="Look for positive, wide premium variances to maximize historical edge.")

    # Mathematical Core Formulations
    roi = (net_credit / capital_risked) * 100
    annualized_return = roi * (365 / entry_dte)
    
    st.markdown("### 🔎 Statistical Quality Scan")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Expected Pre-Trade ROI", f"{roi:.2f}%", help="Your personal structural milestone: 3.00% to 5.00% ROI per position")
    m2.metric("Annualized Return Velocity", f"{annualized_return:.2f}%")
    m3.metric("Absolute IV Allocation Floor", f"{iv_pct:.1f}%", delta="Premium Expanded" if iv_pct >= 30 else "Flat Premium Environment")
    m4.metric("Volatility Risk Premium Edge", f"{vrp_pct:.1f}%", delta="Statistical Edge Verified" if vrp_pct > 0 else "Negative Edge/Risk Gapping")
    
    # Custom Dynamic Model Conformance Guidance 
    if 3.0 <= roi <= 5.0 and iv_pct >= 30 and vrp_pct > 0:
        st.success("✅ **Alpha Conformance Confirmed:** This position checks out against your alpha model parameters.")
    else:
        st.warning("⚠️ **Model Variance Present:** One or more tracking thresholds deviate from your 3-5% target framework or lack an optimal premium variance floor.")

    if st.button("💾 Commit Options Contract Order to Ledger File"):
        trade_data = {
            "Ticker": ticker, "Sector": sector, "Strategy": strategy, "Status": "Open", 
            "Entry Date": entry_date.strftime('%Y-%m-%d'), "Entry DTE": int(entry_dte), "Close DTE": 0,
            "Capital Risked": float(capital_risked), "Net Credit": float(net_credit), "Exit Premium": 0.0,
            "IV (%)": float(iv_pct), "VRP (%)": float(vrp_pct), "Realized PnL ($)": 0.0,
            "ROI (%)": round(roi, 2), "Annualized Return (%)": round(annualized_return, 2)
        }
        save_trade(trade_data)
        st.success(f"Successfully appended {strategy} execution data for ${ticker} into the database.")
        st.rerun()

# ==========================================
# TAB 2: TIME-HORIZON PERFORMANCE ANALYTICS
# ==========================================
with tab2:
    st.subheader("📈 Time-Horizon Summaries & Tactical Health Analytics")
    if trade_df.empty:
        st.info("The application database log is empty. Commit a position inside Tab 1 to initialize diagnostic analytics.")
    else:
        # High Level Portfolio Diagnostics
        total_count = len(trade_df)
        open_df = trade_df[trade_df["Status"] == "Open"]
        closed_df = trade_df[trade_df["Status"] == "Closed"]
        
        # Win rate definition modeled strictly off realized profits
        winning_trades = len(closed_df[closed_df["Realized PnL ($)"] >= 0])
        total_closed = len(closed_df)
        win_rate = (winning_trades / total_closed * 100) if total_closed > 0 else 100.0
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Logged Trades History", total_count)
        c2.metric("Active Open Working Options", len(open_df))
        c3.metric("Realized Win Rate Score", f"{win_rate:.1f}%")
        c4.metric("Aggregate Realized Account Return", f"${closed_df['Realized PnL ($)'].sum():,.2f}")

        # --- TIME HORIZON SUMMARIES ---
        st.markdown("### 🗓️ Rolling Portfolio Inflow Breakdowns")
        now = pd.Timestamp.now().normalize()
        
        df_today = trade_df[trade_df["Entry Date"] >= now]
        df_week = trade_df[trade_df["Entry Date"] >= (now - pd.Timedelta(days=now.dayofweek))]
        df_month = trade_df[trade_df["Entry Date"] >= now.replace(day=1)]
        df_year = trade_df[trade_df["Entry Date"] >= now.replace(month=1, day=1)]

        t1, t2, t3, t4 = st.columns(4)
        with t1:
            st.markdown("#### 📅 Daily Inflow (Today)")
            st.metric("Positions Taken", len(df_today))
            st.metric("Est. Total Credit", f"${df_today['Net Credit'].sum():,.2f}")
        with t2:
            st.markdown("#### 🗓️ Weekly Inflow (This Week)")
            st.metric("Positions Taken", len(df_week))
            st.metric("Est. Total Credit", f"${df_week['Net Credit'].sum():,.2f}")
        with t3:
            st.markdown("#### 🗒️ Monthly Inflow (This Month)")
            st.metric("Positions Taken", len(df_month))
            st.metric("Est. Total Credit", f"${df_month['Net Credit'].sum():,.2f}")
        with t4:
            st.markdown("#### 📊 Annual Inflow (YTD)")
            st.metric("Positions Taken", len(df_year))
            st.metric("Est. Total Credit", f"${df_year['Net Credit'].sum():,.2f}")

        # Ticker Insights
        st.markdown("---")
        st.markdown("### 🎯 Structural Asset & Ticker Performance Weights")
        ticker_summary = trade_df.groupby("Ticker").agg(
            Total_Trades=("Ticker", "count"),
            Total_Net_PnL=("Realized PnL ($)", "sum"),
            Avg_Entry_DTE=("Entry DTE", "mean"),
            Avg_Close_DTE=("Close DTE", "mean")
        )
        st.dataframe(ticker_summary, use_container_width=True)

# ==========================================
# TAB 3: UNRESTRICTED MASTER LEDGER
# ==========================================
with tab3:
    st.subheader("🗂️ Live Master Options Vault Ledger")
    if trade_df.empty:
        st.info("No recorded trades found in database.")
    else:
        # Option Status Modification Form Engine
        open_positions = trade_df[trade_df["Status"] == "Open"]
        
        if not open_positions.empty:
            st.markdown("### 🔄 Active Order Management Engine (Close/Manage Trades)")
            col_sel, col_prem, col_dte = st.columns([2, 1, 1])
            
            with col_sel:
                # Let user pick an active option position from their database index keys
                selected_idx = st.selectbox(
                    "Identify Open Contract to Modify Status", 
                    options=open_positions.index,
                    format_func=lambda x: f"[{trade_df.loc[x, 'Entry Date'].strftime('%Y-%m-%d')}] ${trade_df.loc[x, 'Ticker']} - {trade_df.loc[x, 'Strategy']} (Collected: ${trade_df.loc[x, 'Net Credit']})"
                )
            with col_prem:
                exit_premium = st.number_input("Final Buy-To-Close Premium Cost ($)", min_value=0.0, value=50.0, step=5.0, help="Enter $0.0 if option expired completely worthless for max profit.")
            with col_dte:
                close_dte = st.number_input("Days to Expiration at Close (DTE)", min_value=0, value=18, help="Premium sellers look to exit near ~18 DTE.")
                
            if st.button("🏁 Close Selected Position and Lock in Realized Returns"):
                # Load up un-mutated log copy
                raw_df = pd.read_csv(DB_FILE)
                
