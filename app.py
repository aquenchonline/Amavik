import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# ------------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------------
st.set_page_config(page_title="ERP System", layout="wide")

# 👇 YOUR SPECIFIC SHEET URL IS NOW HARDCODED HERE
SHEET_URL = "https://docs.google.com/spreadsheets/d/1S6xS6hcdKSPtzKxCL005GwvNWQNspNffNveI3P9zCgw/edit"

st.title("🏭 Amavik ERP")
st.markdown("Manage Production, Packing, Store, and Ecommerce data.")

# ------------------------------------------------------------------
# 1. ESTABLISH CONNECTION
# ------------------------------------------------------------------
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"🚨 Connection Error: {e}")
    st.stop()

# ------------------------------------------------------------------
# 2. REUSABLE FUNCTION TO HANDLE DATA
# ------------------------------------------------------------------
def manage_tab(tab_name, worksheet_name):
    """
    Reads and writes data for a specific worksheet.
    """
    st.header(f"{tab_name} Department")

    # READ DATA
    try:
        data = conn.read(spreadsheet=SHEET_URL, worksheet=worksheet_name)
        # Check if data is empty or None
        if data is None or data.empty:
            data = pd.DataFrame(columns=["Date", "Item", "Quantity", "Notes"])
    except Exception:
        # If the sheet is brand new or has errors, start with empty structure
        data = pd.DataFrame(columns=["Date", "Item", "Quantity", "Notes"])

    # Show Data Table
    st.dataframe(data, use_container_width=True)

    # WRITE DATA (FORM)
    with st.expander(f"➕ Add Entry to {tab_name}"):
        # We need a unique key for every form so Streamlit doesn't get confused
        with st.form(key=f"form_{worksheet_name}"):
            col1, col2 = st.columns(2)
            with col1:
                date = st.date_input("Date", key=f"date_{worksheet_name}")
                item = st.text_input("Item Name", key=f"item_{worksheet_name}")
            with col2:
                qty = st.number_input("Quantity", min_value=0, step=1, key=f"qty_{worksheet_name}")
                notes = st.text_input("Notes/Status", key=f"note_{worksheet_name}")
            
            submit = st.form_submit_button("Submit Entry")

            if submit:
                if not item:
                    st.warning("⚠️ Item Name is required")
                else:
                    try:
                        # Create new row
                        new_data = pd.DataFrame([{
                            "Date": str(date),
                            "Item": item,
                            "Quantity": qty,
                            "Notes": notes
                        }])
                        
                        # Append new row to existing data
                        updated_df = pd.concat([data, new_data], ignore_index=True)
                        
                        # Update Google Sheet
                        conn.update(spreadsheet=SHEET_URL, worksheet=worksheet_name, data=updated_df)
                        
                        st.success(f"✅ Added to {tab_name}!")
                        
                        # Wait 1 second then reload to show new data
                        import time
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error saving data: {e}")

# ------------------------------------------------------------------
# 3. MAIN APP LAYOUT (TABS)
# ------------------------------------------------------------------

# Create the visual tabs
t1, t2, t3, t4 = st.tabs(["🔨 Production", "📦 Packing", "jg Store", "🛒 Ecommerce"])

# Run the function for each tab
# Ensure your Google Sheet has tabs named exactly: "Production", "Packing", "Store", "Ecommerce"
with t1:
    manage_tab("Production", "Production") 

with t2:
    manage_tab("Packing", "Packing")

with t3:
    manage_tab("Store", "Store")

with t4:
    manage_tab("Ecommerce", "Ecommerce")
