import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import datetime

# --- CONFIGURATION & PAGE SETUP ---
st.set_page_config(page_title="Premium Seller Command Center", layout="wide", page_icon="📊")

st.html("<style>.metric-box { padding: 15px; border-radius: 8px; background-color: #f0f2f6; margin-bottom: 10px; } .stButton>button { width: 100%; background-color: #1E3A8A; color: white; font-weight: bold; }</style>")

# --- CORE DATABASE FILE PATH ---
DB_FILE = "options_master_ledger.csv"

REQUIRED_COLUMNS = [
    "Ticker", "Sector", "Strategy", "Flow Type", "Status", "Entry Date", "Expiration Date",
    "Contracts", "Short Strike", "Long Strike", "Calculated DTE", "Close DTE", 
    "Capital Risked", "Net Premium ($)", "Exit Cost ($)", "IV (%)", 
    "Realized PnL ($)", "ROI (%)", "Annualized Return (%)"
]

def load_data():
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            
            # Auto-repair missing columns dynamically
            mutated = False
            for col in REQUIRED_COLUMNS:
                if col not in df.columns:
                    if col == "Expiration Date":
                        df[col] = datetime.now().strftime('%Y-%m-%d')
                    elif col == "Contracts":
                        df[col] = 1
                    elif col in ["Short Strike", "Long Strike", "Exit Cost ($)", "Realized PnL ($)"]:
                        df[col] = 0.0
                    else:
                        df[col] = "Unknown"
                    mutated = True
            if mutated:
                df.to_csv(DB_FILE, index=False)
                
            return df
        except Exception as e:
            return pd.DataFrame(columns=REQUIRED_COLUMNS)
    else:
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

def save_trade(trade_dict):
    df = load_data()
    new_row = pd.DataFrame([trade_dict])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(DB_FILE, index=False)

# Load master trade log safely
trade_df = load_data()

st.title("📊 The Premium Seller Command Center")
st.caption("Live Options Portfolio Log, Automated Credit Leg Component Engine, and Transaction Tracking.")

tab1, tab2, tab3 = st.tabs(["🧮 Automated Trade Calculator", "📈 Time-Horizon Performance Analytics", "📜 Live Trade History"])

# ==========================================
# TAB 1: AUTOMATED TRADE CALCULATOR
# ==========================================
with tab1:
    st.subheader("💡 Dynamic Position Sizing & Margin Optimizer")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        ticker = st.text_input("Ticker Symbol", value="MU").upper()
        sector = st.selectbox("Ticker Sector Allocation", ["Semiconductors", "Tech Infrastructure", "Tech Components", "Clean Energy", "Index / Macro", "Other"])
        strategy = st.selectbox("Strategy Architecture", ["Put Credit Spread (PCS)", "Cash Secured Put (CSP)", "Covered Call (CC)", "Call Debit Spread (CDS)", "Long Call / Speculative Debit"])
        
    with col2:
        contracts = st.number_input("Number of Contracts", min_value=1, value=1, step=1)
        short_strike = st.number_input("Short Strike Price ($) [Leave 0 if none]", min_value=0.0, value=100.0, step=0.5)
        long_strike = st.number_input("Long Strike Price ($) [Leave 0 if naked]", min_value=0.0, value=95.0, step=0.5)
        
    with col3:
        short_prem_entry = st.number_input("Short Leg Entry Premium ($)", min_value=0.00, value=1.50, step=0.05)
        long_prem_entry = st.number_input("Long Leg Entry Premium ($) [0 if naked]", min_value=0.00, value=0.50, step=0.05)
        entry_date = st.date_input("Execution Date (Today)", datetime.now())
        exp_date = st.date_input("Contract Expiration Date", datetime.now() + pd.Timedelta(days=40))
        
    with col4:
        iv_pct = st.number_input("Implied Volatility (IV) (%)", min_value=0.0, max_value=250.0, value=45.0)

    # Core Logic Processing
    net_premium_per_contract = short_prem_entry - long_prem_entry
    total_premium_value = net_premium_per_contract * 100 * contracts
    
    # Clean string calculations to avoid formatting runtime bugs
    e_dt = datetime.combine(entry_date, datetime.min.time())
    ex_dt = datetime.combine(exp_date, datetime.min.time())
    calculated_dte = max(int((ex_dt - e_dt).days), 1)
    
    flow_type = "Credit (Received)" if net_premium_per_contract >= 0 else "Debit (Paid)"
    abs_premium_value = abs(total_premium_value)

    if long_strike > 0 and short_strike > 0:
        spread_width = abs(short_strike - long_strike)
        max_spread_collateral = spread_width * 100 * contracts
        capital_risked = max_spread_collateral - abs_premium_value if flow_type == "Credit (Received)" else abs_premium_value
        net_gain_potential = abs_premium_value if flow_type == "Credit (Received)" else max_spread_collateral - abs_premium_value
    elif "Put" in strategy or strategy == "Cash Secured Put (CSP)":
        capital_risked = short_strike * 100 * contracts
        net_gain_potential = abs_premium_value if flow_type == "Credit (Received)" else 0.0
    else:
        capital_risked = abs_premium_value
        net_gain_potential = abs_premium_value

    roi = (net_gain_potential / max(capital_risked, 1.0)) * 100
    annualized_return = roi * (365 / calculated_dte)
    
    st.markdown("### 🔍 Mathematical Position Profile")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Calculated Capital Required / Risk", f"${capital_risked:,.2f}")
    m2.metric("Net Calculated Entry Premium", f"${total_premium_value:,.2f}", delta=flow_type)
    m3.metric("Trade Geometry ROI", f"{roi:.2f}%")
    m4.metric("Annualized Time Decay Velocity", f"{annualized_return:.2f}%")

    if st.button("💾 Commit Options Contract Order to Ledger File"):
        trade_data = {
            "Ticker": ticker, "Sector": sector, "Strategy": strategy, "Flow Type": flow_type, "Status": "Open", 
            "Entry Date": entry_date.strftime('%Y-%m-%d'), "Expiration Date": exp_date.strftime('%Y-%m-%d'),
            "Contracts": int(contracts), "Short Strike": float(short_strike), "Long Strike": float(long_strike),
            "Calculated DTE": int(calculated_dte), "Close DTE": 0, "Capital Risked": float(capital_risked), 
            "Net Premium ($)": float(total_premium_value), "Exit Cost ($)": 0.0, "IV (%)": float(iv_pct), 
            "Realized PnL ($)": 0.0, "ROI (%)": round(roi, 2), "Annualized Return (%)": round(annualized_return, 2)
        }
        save_trade(trade_data)
        st.success(f"Successfully appended {strategy} execution data into your cloud repository.")
        st.write("Refreshing data vault...")
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

# ==========================================
# TAB 3: LIVE TRADE HISTORY
# ==========================================
with tab3:
    st.subheader("📜 Running Options Trade History Log")
    
    # 📋 ALWAYS DISPLAY THE VIEWABLE DATA SHEET AT THE TOP
    st.markdown("### 📋 Active Master History Log Sheet")
    if trade_df.empty:
        st.dataframe(pd.DataFrame(columns=["Performance", "Ticker", "Strategy", "Status", "Entry Date", "Capital Risked", "Net Premium ($)", "Realized PnL ($)"]), use_container_width=True)
        st.info("No recorded trades found in history database. Input an active contract in Tab 1 to populate this sheet.")
    else:
        presentation_df = trade_df.copy()
        
        badges = []
        for idx, row in presentation_df.iterrows():
            if str(row["Status"]).strip().upper() == "OPEN":
                badges.append("🔵 OPEN")
            elif float(row["Realized PnL ($)"]) >= 0:
                badges.append("🟢 WIN")
            else:
                badges.append("🔴 LOSS")
        presentation_df.insert(0, "📊 Performance", badges)
        
        col_order = ["📊 Performance", "Ticker", "Strategy", "Entry Date", "Expiration Date", "Contracts", "Calculated DTE", "Close DTE", "Capital Risked", "Net Premium ($)", "Exit Cost ($)", "Realized PnL ($)", "ROI (%)"]
        st.dataframe(presentation_df[col_order], use_container_width=True)
        
        csv_data = trade_df.to_csv(index=False).encode('utf-8')
        st.download_button(label="📥 Download Complete Master Backup (.CSV)", data=csv_data, file_name="options_trade_history.csv", mime="text/csv")
        
        st.markdown("---")
        
        # MANAGEMENT PORTAL ENGINE BLOCK
        open_positions = trade_df[trade_df["Status"] == "Open"]
        st.markdown("### ⚙️ Order Management Engine (Close Working Positions)")
        if open_positions.empty:
            st.success("🟢 All logged trades are currently closed! No active exposure running.")
        else:
            selected_idx = st.selectbox(
                "Identify Working Open Contract to Close Out", 
                options=open_positions.index,
