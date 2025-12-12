import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# ------------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------------
st.set_page_config(page_title="ERP System", layout="wide")
SHEET_URL = "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID_HERE/edit"

st.title("🏭 Mini ERP System")
st.markdown("Manage Production, Packing, Store, and Ecommerce data.")

# Connect to Google Sheets
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"Connection Error: {e}")
    st.stop()

# ------------------------------------------------------------------
# REUSABLE FUNCTION TO HANDLE DATA
# ------------------------------------------------------------------
def manage_tab(tab_name, worksheet_name):
    """
    Reads and writes data for a specific worksheet.
    """
    st.header(f"{tab_name} Department")

    # 1. READ DATA
    try:
        data = conn.read(spreadsheet=SHEET_URL, worksheet=worksheet_name)
        # Handle empty sheet
        if data.empty:
            data = pd.DataFrame(columns=["Date", "Item", "Quantity", "Notes"])
    except Exception:
        # If sheet doesn't exist or has error, init empty
        data = pd.DataFrame(columns=["Date", "Item", "Quantity", "Notes"])

    # Show Data Table
    st.dataframe(data, use_container_width=True)

    # 2. WRITE DATA (FORM)
    with st.expander(f"➕ Add Entry to {tab_name}"):
        with st.form(key=f"form_{worksheet_name}"):
            # unique key is needed for each form so they don't mix up
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
                    # Create new row
                    new_data = pd.DataFrame([{
                        "Date": str(date),
                        "Item": item,
                        "Quantity": qty,
                        "Notes": notes
                    }])
                    
                    # Append and Update
                    updated_df = pd.concat([data, new_data], ignore_index=True)
                    conn.update(spreadsheet=SHEET_URL, worksheet=worksheet_name, data=updated_df)
                    
                    st.success(f"✅ Added to {tab_name}!")
                    st.rerun()

# ------------------------------------------------------------------
# MAIN APP LAYOUT (TABS)
# ------------------------------------------------------------------

# Create the visual tabs
t1, t2, t3, t4 = st.tabs(["🔨 Production", "📦 Packing", "wf Store", "🛒 Ecommerce"])

# Run the function for each tab
with t1:
    manage_tab("Production", "Production") # (Display Name, Sheet Tab Name)

with t2:
    manage_tab("Packing", "Packing")

with t3:
    manage_tab("Store", "Store")

with t4:
    manage_tab("Ecommerce", "Ecommerce")
