import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import datetime

# --- CONFIGURATION & PAGE SETUP ---
st.set_page_config(page_title="Premium Seller Command Center", layout="wide", page_icon="📊")

# High-visibility visual anchors
st.html("<style>.metric-box { padding: 15px; border-radius: 8px; background-color: #f0f2f6; margin-bottom: 10px; } .stButton>button { width: 100%; background-color: #1E3A8A; color: white; font-weight: bold; }</style>")

# --- CORE DATABASE FILE PATH ---
DB_FILE = "options_master_ledger.csv"

def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        df['Entry Date'] = pd.to_datetime(df['Entry Date'])
        return df
    else:
        return pd.DataFrame(columns=[
            "Ticker", "Sector", "Strategy", "Flow Type", "Status", "Entry Date", 
            "Short Strike", "Long Strike", "Calculated DTE", "Close DTE", 
            "Capital Risked", "Net Premium ($)", "Exit Cost ($)", "IV (%)", 
            "Realized PnL ($)", "ROI (%)", "Annualized Return (%)"
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
st.caption("Live Options Portfolio Log, Automated Capital Collateral Engine, and Transaction Velocity Tracking.")

# --- MASTER NAVIGATION TABS ---
tab1, tab2, tab3 = st.tabs(["🧮 Automated Trade Calculator", "📈 Time-Horizon Performance Analytics", "🗂️ Unrestricted Master Ledger"])

# ==========================================
# TAB 1: AUTOMATED TRADE CALCULATOR
# ==========================================
with tab1:
    st.subheader("💡 Dynamic Position Sizing & Margin Optimizer")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        ticker = st.text_input("Ticker Symbol", value="MU").upper()
        sector = st.selectbox("Ticker Sector Allocation", ["Semiconductors", "Tech Infrastructure", "Tech Components", "Clean Energy", "Index / Macro", "Other"])
        strategy = st.selectbox("Strategy Architecture", ["Put Credit Spread (PCS)", "Cash Secured Put (CSP)", "Covered Call (CC)", "Call Debit Spread (CDS)", "Long Call / Speculative Debit", "Other Position"])
        flow_type = st.radio("Transaction Flow", ["Credit (Received)", "Debit (Paid)"], index=0, horizontal=True)
        
    with col2:
        # Automated Strike Sizing Block
        contracts = st.number_input("Number of Contracts", min_value=1, value=1, step=1)
        short_strike = st.number_input("Short Strike Price ($) [Leave 0 if none]", min_value=0.0, value=100.0, step=0.5)
        long_strike = st.number_input("Long Strike Price ($) [Leave 0 if naked]", min_value=0.0, value=95.0, step=0.5)
        
    with col3:
        # Premium and Time Inputs
        premium_per_contract = st.number_input("Premium Per Contract ($)", min_value=0.00, value=1.00, step=0.05, help="Enter the per-share premium price filled on Fidelity (e.g. 1.00 = $100 cash leg).")
        entry_date = st.date_input("Execution Date (Today)", datetime.now())
        exp_date = st.date_input("Contract Expiration Date", datetime.now() + pd.Timedelta(days=40))
        
    with col4:
        iv_pct = st.number_input("Implied Volatility (IV) (%)", min_value=0.0, max_value=250.0, value=45.0, help="Enter the standard option contract IV displayed on Fidelity.")

    # --- THE COGNITIVE AUTOMATED MARGIN ENGINE ---
    total_premium_value = premium_per_contract * 100 * contracts
    
    # Calculate automated DTE
    dte_delta = (exp_date - entry_date).days
    calculated_dte = max(int(dte_delta), 1)

    # Compute Capital Risk / Collateral Requirements dynamically based on choices
    if "Spread" in strategy or (short_strike > 0 and long_strike > 0):
        # Multi-leg spreads collateral math
        spread_width = abs(short_strike - long_strike)
        max_spread_collateral = spread_width * 100 * contracts
        
        if flow_type == "Credit (Received)":
            capital_risked = max_spread_collateral - total_premium_value
            net_gain_potential = total_premium_value
        else: # Debit Flow
            capital_risked = total_premium_value
            net_gain_potential = max_spread_collateral - total_premium_value
            
    elif "Put" in strategy or strategy == "Cash Secured Put (CSP)":
        # Naked/Cash Secured Puts cash allocation math
        capital_risked = short_strike * 100 * contracts
        net_gain_potential = total_premium_value if flow_type == "Credit (Received)" else 0.0
        
    else:
        # Standard long option / single directional legs fallback
        capital_risked = total_premium_value
        net_gain_potential = total_premium_value if flow_type == "Credit (Received)" else 500.0 # Arbitrary visual target

    # Formulate Core Return Ratios
    roi = (net_gain_potential / max(capital_risked, 1.0)) * 100
    annualized_return = roi * (365 / calculated_dte)
    
    st.markdown("### 🔍 Mathematical Position Profile")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Calculated Capital Required / Risk", f"${capital_risked:,.2f}", help="The true required collateral margin or out-of-pocket cash locked by Fidelity.")
    m2.metric("Max Return Potential", f"${net_gain_potential:,.2f}")
    m3.metric("Trade Geometry ROI", f"{roi:.2f}%", help="Goal: 3.00% to 5.00% standard velocity loop.")
    m4.metric("Annualized Time Decay Velocity", f"{annualized_return:.2f}%")

    # Custom Model Conformance Guidance Box
    if flow_type == "Credit (Received)" and 3.0 <= roi <= 5.0:
        st.success("✅ **Premium Model Target Achieved:** Trade falls directly inside your optimal 3-5% cash-flow setup.")
    elif flow_type == "Debit (Paid)":
        st.info("🎯 **Long Alpha Positioning:** Directional leverage strategy active. Volatility decay works against this contract structure; monitor closely.")
    else:
        st.warning("⚠️ **Model Variance Divergence:** Position configuration falls outside standard automated thresholds.")

    if st.button("💾 Commit Options Contract Order to Ledger File"):
        trade_data = {
            "Ticker": ticker, "Sector": sector, "Strategy": strategy, "Flow Type": flow_type, "Status": "Open", 
            "Entry Date": entry_date.strftime('%Y-%m-%d'), "Short Strike": float(short_strike), "Long Strike": float(long_strike),
            "Calculated DTE": int(calculated_dte), "Close DTE": 0, "Capital Risked": float(capital_risked), 
            "Net Premium ($)": float(total_premium_value), "Exit Cost ($)": 0.0, "IV (%)": float(iv_pct), 
            "Realized PnL ($)": 0.0, "ROI (%)": round(roi, 2), "Annualized Return (%)": round(annualized_return, 2)
        }
        save_trade(trade_data)
        st.success(f"Successfully appended {strategy} execution data for ${ticker} into your cloud repository.")
        st.rerun()

# ==========================================
# TAB 2: TIME-HORIZON PERFORMANCE ANALYTICS
# ==========================================
with tab2:
    st.subheader("📈 Time-Horizon Summaries & Tactical Health Analytics")
    if trade_df.empty:
        st.info("The application database log is empty. Commit a position inside Tab 1 to initialize diagnostic analytics.")
    else:
        total_count = len(trade_df)
        open_df = trade_df[trade_df["Status"] == "Open"]
        closed_df = trade_df[trade_df["Status"] == "Closed"]
        
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
            st.metric("Premium Allocated", f"${df_today['Net Premium ($)'].sum():,.2f}")
        with t2:
            st.markdown("#### 🗓️ Weekly Inflow (This Week)")
            st.metric("Positions Taken", len(df_week))
            st.metric("Premium Allocated", f"${df_week['Net Premium ($)'].sum():,.2f}")
        with t3:
            st.markdown("#### 🗒️ Monthly Inflow (This Month)")
            st.metric("Positions Taken", len(df_month))
            st.metric("Premium Allocated", f"${df_month['Net Premium ($)'].sum():,.2f}")
        with t4:
            st.markdown("#### 📊 Annual Inflow (YTD)")
            st.metric("Positions Taken", len(df_year))
            st.metric("Premium Allocated", f"${df_year['Net Premium ($)'].sum():,.2f}")

        st.markdown("---")
        st.markdown("### 🎯 Structural Asset & Ticker Performance Weights")
        ticker_summary = trade_df.groupby("Ticker").agg(
            Total_Trades=("Ticker", "count"),
            Total_Net_PnL=("Realized PnL ($)", "sum"),
            Avg_Entry_DTE=("Calculated DTE", "mean")
        )
        st.dataframe(ticker_summary, use_container_width=True)

# ==========================================
