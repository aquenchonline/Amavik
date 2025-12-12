import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time

# ------------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------------
st.set_page_config(page_title="ERP System", layout="wide", page_icon="🔒")
SHEET_URL = "https://docs.google.com/spreadsheets/d/1S6xS6hcdKSPtzKxCL005GwvNWQNspNffNveI3P9zCgw/edit"

# ------------------------------------------------------------------
# AUTHENTICATION DATA (USER DB)
# ------------------------------------------------------------------
USERS = {
    "Production": {"pass": "Amavik@80", "role": "Production", "access": ["Production"]},
    "Packing":    {"pass": "Amavik@97", "role": "Packing",    "access": ["Packing"]},
    "Store":      {"pass": "Amavik@17", "role": "Store",      "access": ["Store"]},
    "Amar":       {"pass": "Aquench@1933", "role": "Admin",   "access": ["Production", "Packing", "Store", "Ecommerce", "Configuration"]}
}

# ------------------------------------------------------------------
# SESSION STATE MANAGEMENT (LOGIN)
# ------------------------------------------------------------------
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["user"] = None
    st.session_state["role"] = None

def login():
    st.title("🔒 ERP Login")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        username = st.text_input("User ID")
        password = st.text_input("Password", type="password")
        if st.button("Login", type="primary", use_container_width=True):
            if username in USERS and USERS[username]["pass"] == password:
                st.session_state["logged_in"] = True
                st.session_state["user"] = username
                st.session_state["role"] = USERS[username]["role"]
                st.session_state["access"] = USERS[username]["access"]
                st.rerun()
            else:
                st.error("❌ Invalid ID or Password")

def logout():
    st.session_state["logged_in"] = False
    st.session_state["user"] = None
    st.rerun()

# ------------------------------------------------------------------
# DATABASE CONNECTION
# ------------------------------------------------------------------
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"🚨 Connection Error: {e}")
    st.stop()

# ------------------------------------------------------------------
# CORE FUNCTION: MANAGE DATA (VIEW & EDIT)
# ------------------------------------------------------------------
def manage_tab(tab_name, worksheet_name):
    st.subheader(f"📂 {tab_name} Dashboard")

    # 1. READ DATA
    try:
        data = conn.read(spreadsheet=SHEET_URL, worksheet=worksheet_name, ttl=0)
        if data is None or data.empty:
            data = pd.DataFrame()
    except:
        data = pd.DataFrame()

    # Ensure "Ready Qty" column exists
    if "Ready Qty" not in data.columns:
        data["Ready Qty"] = 0

    # 2. EDITABLE TABLE (Logic for User vs Admin)
    st.write("### 📋 Data Overview")
    
    # Define which columns are editable
    all_columns = data.columns.tolist()
    
    if st.session_state["role"] == "Admin":
        # Admin can edit EVERYTHING
        disabled_cols = []
    else:
        # Standard Users can ONLY edit "Ready Qty"
        # We disable all columns EXCEPT "Ready Qty"
        disabled_cols = [col for col in all_columns if col != "Ready Qty"]

    # Show the Data Editor
    edited_df = st.data_editor(
        data,
        disabled=disabled_cols,  # Locks columns based on role
        use_container_width=True,
        num_rows="dynamic",      # Allows adding/deleting rows if Admin
        key=f"editor_{worksheet_name}"
    )

    # 3. SAVE BUTTON (For updates made in the table)
    # If data changed, show save button
    if not data.equals(edited_df):
        st.warning("⚠️ You have unsaved changes in the table above!")
        if st.button(f"💾 Save Changes to {tab_name}", key=f"save_{worksheet_name}"):
            try:
                conn.update(spreadsheet=SHEET_URL, worksheet=worksheet_name, data=edited_df)
                st.success("✅ Changes Saved!")
                st.cache_data.clear()
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Error saving: {e}")

    # 4. ADD NEW ENTRY FORM
    st.divider()
    with st.expander(f"➕ Add New Entry to {tab_name}"):
        with st.form(key=f"form_{worksheet_name}"):
            
            # === FORM FOR PACKING ===
            if worksheet_name == "Packing":
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
                    priority = st.number_input("Order Priority", min_value=1, step=1, key="p_prio")
                    box = st.selectbox("Box Type", ["Loose", "Brown Box", "White Box", "Box"], key="p_box")
                    remarks = st.text_input("Remarks", key="p_rem")
                
                # Ready Qty init
                ready_qty_init = st.number_input("Initial Ready Qty", value=0, key="p_ready")

                if st.form_submit_button("Submit Packing Data"):
                    if not item:
                        st.warning("Item Name Required")
                    else:
                        new_row = pd.DataFrame([{
                            "Date": str(date), "Order Date": str(order_date), "Order Priority": priority,
                            "Item Name": item, "Qty": qty, "Logo": logo, "Bottom Print": bottom, 
                            "Box": box, "Remarks": remarks, "Ready Qty": ready_qty_init
                        }])
                        save_new_entry(worksheet_name, data, new_row)

            # === FORM FOR ALL OTHERS ===
            else:
                c1, c2 = st.columns(2)
                with c1:
                    date = st.date_input("Date", key=f"d_{worksheet_name}")
                    item = st.text_input("Item Name", key=f"i_{worksheet_name}")
                with c2:
                    qty = st.number_input("Quantity", min_value=0, step=1, key=f"q_{worksheet_name}")
                    notes = st.text_input("Notes", key=f"n_{worksheet_name}")
                
                ready_qty_init = st.number_input("Initial Ready Qty", value=0, key=f"r_{worksheet_name}")

                if st.form_submit_button("Submit Entry"):
                    if not item:
                        st.warning("Item Name Required")
                    else:
                        new_row = pd.DataFrame([{
                            "Date": str(date), "Item": item, "Quantity": qty, 
                            "Notes": notes, "Ready Qty": ready_qty_init
                        }])
                        save_new_entry(worksheet_name, data, new_row)

def save_new_entry(sheet_name, old_df, new_row):
    try:
        updated_df = pd.concat([old_df, new_row], ignore_index=True)
        conn.update(spreadsheet=SHEET_URL, worksheet=sheet_name, data=updated_df)
        st.success("✅ Saved!")
        st.cache_data.clear()
        time.sleep(1)
        st.rerun()
    except Exception as e:
        st.error(f"Error: {e}")

# ------------------------------------------------------------------
# APP ORCHESTRATION
# ------------------------------------------------------------------

# 1. CHECK LOGIN STATUS
if not st.session_state["logged_in"]:
    login()
else:
    # 2. LOGGED IN HEADER
    with st.sidebar:
        st.write(f"👤 User: **{st.session_state['user']}**")
        if st.button("Logout"):
            logout()

    st.title("🏭 Mini ERP System")

    # 3. DETERMINE WHICH TABS TO SHOW
    user_access = st.session_state["access"]
    
    # Create the tab objects dynamically based on access
    # This is a bit tricky in Streamlit, so we use a simpler if/else logic
    
    # We create a list of tabs this user is allowed to see
    selected_tab = st.selectbox("Navigate to:", user_access)

    st.divider()

    # 4. RENDER SELECTED TAB
    if selected_tab == "Production":
        manage_tab("Production", "Production")
    
    elif selected_tab == "Packing":
        manage_tab("Packing", "Packing")
    
    elif selected_tab == "Store":
        manage_tab("Store", "Store")
        
    elif selected_tab == "Ecommerce":
        manage_tab("Ecommerce", "Ecommerce")
        
    elif selected_tab == "Configuration":
        st.header("⚙️ System Configuration")
        st.info("Only Amar (Admin) can see this.")
        st.write("Here you can add future settings, user management, or backup buttons.")
        st.text_input("Example Admin Setting", "Default Value")
