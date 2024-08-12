import streamlit as st
from deta import Deta
import pytz
from datetime import datetime
import pandas as pd

# Initialize Deta Base with your project key
deta = Deta(st.secrets['key'])
db = deta.Base("trade_tracker")

def calculate_sl(instrument, ltp):
    # Define time zone
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)

    # Extract current time
    current_time = now.strftime('%H:%M')
    
    # Define stop-loss multipliers
    if current_time < '11:30':
        if instrument == 'BANKNIFTY':
            sl = ltp * 1.31
        elif instrument == 'NIFTY':
            sl = ltp * 1.39
        else:
            return "Invalid instrument"
    else:
        if instrument == 'BANKNIFTY':
            sl = ltp * 1.8
        elif instrument == 'NIFTY':
            sl = ltp * 1.6
        else:
            return "Invalid instrument"
    
    # Handle additional trade rule
    if 'additional_trade' in instrument.lower():
        sl = ltp * 1.43

    return sl

# Function to fetch unique times from the database
def fetch_unique_times():
    items = db.fetch().items
    unique_times = pd.Series([item['time'][:16] for item in items]).unique()
    return unique_times

# Function to fetch instruments by selected time
def fetch_instruments_by_time(selected_time):
    items = db.fetch().items
    filtered_items = [item for item in items if item['time'][:16] == selected_time]
    return filtered_items

# Function to fetch current SL based on name and instrument type
def fetch_current_sl(name, instrument_type):
    items = db.fetch().items
    for item in items:
        if item['name'] == name and item['instrument_type'] == instrument_type:
            return item['sl']
    return None

# Function to update SL in Deta Base
def update_sl(key, new_sl):
    db.update({"sl": new_sl}, key)

tab1, tab2 = st.tabs(['Trade Bot','Additional Trade'])

with tab1:

    # Streamlit UI
    st.title('Trade Bot Dashboard')

    # 1. Select Time
    unique_times = fetch_unique_times()
    selected_time = st.selectbox("Select Time", unique_times)

    if selected_time:
        # 2. Select Instrument
        instruments = fetch_instruments_by_time(selected_time)
        instrument_options = [f"{item['name']} {item['strike']}" for item in instruments]
        selected_instrument = st.selectbox("Select Instrument", instrument_options)

        if selected_instrument:
            # Find the selected instrument items
            selected_items = [item for item in instruments if f"{item['name']} {item['strike']}" == selected_instrument]
            
            if selected_items:
                st.write("Selected Items Details:")
                for item in selected_items:
                    st.json(item)

                col1, col2 = st.columns(2)
                col3, col4 = st.columns(2)

                # Entry Prices
                with col1:
                    entry_price_call = st.number_input("Entry Price for Call (CE)", value=0.0, format="%.2f")

                with col2:
                    entry_price_put = st.number_input("Entry Price for Put (PE)", value=0.0, format="%.2f")

                # Calculate and display new SL for selected items
                new_sl_call = None
                new_sl_put = None

                if entry_price_call > 0:
                    new_sl_call = calculate_sl(selected_items[0]['name'], entry_price_call)
                    with col3:
                        st.write(f"Calculated SL for Call (CE): {new_sl_call:.2f}")

                if entry_price_put > 0:
                    new_sl_put = calculate_sl(selected_items[0]['name'], entry_price_put)
                    with col4:
                        st.write(f"Calculated SL for Put (PE): {new_sl_put:.2f}")

                # Update SL button
                if st.button("Update SL"):
                    if new_sl_call is not None:
                        for item in selected_items:
                            if item['instrument_type'] == "CE":
                                update_sl(item['key'], new_sl_call)
                    if new_sl_put is not None:
                        for item in selected_items:
                            if item['instrument_type'] == "PE":
                                update_sl(item['key'], new_sl_put)
                    
                    st.success("SL updated successfully!")
                
with tab2:
    st.title('Additional Trade')

    entry = st.number_input('Entry Price')

    if entry:

        st.write(f'SL : {entry*1.43}')
