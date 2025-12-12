import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# ------------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------------
st.set_page_config(page_title="ERP System", layout="wide")
SHEET_URL = "https://docs.google.com/spreadsheets/d/1S6xS6hcdKSPtzKxCL005GwvNWQNspNffNveI3P9zCgw/edit"

st.title("🏭 Mini ERP System")

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
    st.header(f"{tab_name} Department")

    # -----------------------------------------------------------
    # A. READ DATA
    # -----------------------------------------------------------
    # We use ttl=0 to ensure we always get fresh data
    try:
        data = conn.read(spreadsheet=SHEET_URL, worksheet=worksheet_name, ttl=0)
        if data is None or data.empty:
             # Default empty structure if sheet is blank
             data = pd.DataFrame() 
    except Exception:
        data = pd.DataFrame()

    # Display Data
    st.dataframe(data, use_container_width=True)

    # -----------------------------------------------------------
    # B. WRITE DATA (The Form)
    # -----------------------------------------------------------
    with st.expander(f"➕ Add Entry to {tab_name}"):
        with st.form(key=f"form_{worksheet_name}"):
            
            # === SPECIAL LOGIC FOR PACKING TAB ===
            if worksheet_name == "Packing":
                # Layout: 3 Columns for better fit
                c1, c2, c3 = st.columns(3)
                
                with c1:
                    date = st.date_input("Date", key="p_date")
                    item = st.text_input("Item Name", key="p_item")
                    logo = st.selectbox("Logo", ["W/O Logo", "Laser", "Pad"], key="p_logo")
                
                with c2:
                    order_date = st.date_input("Order Date (Manual)", key="p_odate")
                    qty = st.number_input("Qty", min_value=0, step=1, key="p_qty")
                    bottom = st.selectbox("Bottom Print", ["No", "Laser", "Pad"], key="p_bot")

                with c3:
                    priority = st.selectbox("Order Priority", ["High", "Medium", "Low"], key="p_prio")
                    box = st.selectbox("Box Type", ["Loose", "Brown Box", "White Box", "Box"], key="p_box")
                    remarks = st.text_input("Remarks", key="p_rem")

                submit = st.form_submit_button("Submit Packing Data")

                if submit:
                    if not item:
                        st.warning("⚠️ Item Name is required")
                    else:
                        # Packing Specific Data Structure
                        new_data = pd.DataFrame([{
                            "Date": str(date),
                            "Order Date": str(order_date),
                            "Order Priority": priority,
                            "Item Name": item,
                            "Qty": qty,
                            "Logo": logo,
                            "Bottom Print": bottom,
                            "Box": box,
                            "Remarks": remarks
                        }])
                        save_data(worksheet_name, data, new_data)

            # === STANDARD LOGIC FOR ALL OTHER TABS ===
            else:
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
                        # Standard Data Structure
                        new_data = pd.DataFrame([{
                            "Date": str(date),
                            "Item": item,
                            "Quantity": qty,
                            "Notes": notes
                        }])
                        save_data(worksheet_name, data, new_data)

# Helper function to save data and refresh
def save_data(sheet_name, old_df, new_row_df):
    try:
        updated_df = pd.concat([old_df, new_row_df], ignore_index=True)
        conn.update(spreadsheet=SHEET_URL, worksheet=sheet_name, data=updated_df)
        st.success("✅ Saved successfully!")
        st.cache_data.clear()
        import time
        time.sleep(1)
        st.rerun()
    except Exception as e:
        st.error(f"Error saving data: {e}")

# ------------------------------------------------------------------
# 3. MAIN APP LAYOUT (TABS)
# ------------------------------------------------------------------

t1, t2, t3, t4 = st.tabs(["🔨 Production", "📦 Packing", "jg Store", "🛒 Ecommerce"])

with t1:
    manage_tab("Production", "Production") 

with t2:
    manage_tab("Packing", "Packing") # This triggers the special form

with t3:
    manage_tab("Store", "Store")

with t4:
    manage_tab("Ecommerce", "Ecommerce")
