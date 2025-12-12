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

    # Ensure Essential Columns Exist
    if "Ready Qty" not in data.columns:
        data["Ready Qty"] = 0
    
    if "Status" not in data.columns:
        data["Status"] = "Pending"

    # Fill empty status with "Pending" for logic consistency
    data["Status"] = data["Status"].fillna("Pending")
    data["Status"] = data["Status"].replace("", "Pending")

    # -----------------------------------------------------------
    # SPLIT DATA: ACTIVE vs COMPLETED
    # -----------------------------------------------------------
    # Active: Pending, Next Day, or anything NOT "Complete"
    active_mask = data["Status"] != "Complete"
    df_active = data[active_mask].copy()
    
    # Completed: Only "Complete"
    df_completed = data[~active_mask].copy()

    # -----------------------------------------------------------
    # VIEW 1: ACTIVE TASKS (EDITABLE)
    # -----------------------------------------------------------
    st.write("### 🚀 Active Tasks (Pending / Next Day)")

    all_columns = data.columns.tolist()
    
    # Permission Logic
    if st.session_state["role"] == "Admin":
        disabled_cols = [] # Admin edits everything
    else:
        # Standard Users can ONLY edit "Ready Qty" and "Status"
        # We disable all columns EXCEPT those two
        disabled_cols = [col for col in all_columns if col not in ["Ready Qty", "Status"]]

    # Configure the Status Column as a Dropdown
    column_config = {
        "Status": st.column_config.SelectboxColumn(
            "Status",
            options=["Pending", "Next Day", "Complete"],
            default="Pending",
            required=True,
        )
    }

    edited_active_df = st.data_editor(
        df_active,
        disabled=disabled_cols,
        column_config=column_config,
        use_container_width=True,
        num_rows="dynamic" if st.session_state["role"] == "Admin" else "fixed",
        key=f"editor_{worksheet_name}"
    )

    # SAVE BUTTON LOGIC
    # We compare the edited active rows with the original active rows
    if not df_active.equals(edited_active_df):
        st.warning("⚠️ Changes detected! Click Save to update.")
        if st.button(f"💾 Save Changes to {tab_name}", key=f"save_{worksheet_name}"):
            try:
                # RECOMBINE: Edited Active Rows + Original Completed Rows
                # This ensures we don't lose the hidden completed data
                final_df = pd.concat([edited_active_df, df_completed], ignore_index=True)
                
                conn.update(spreadsheet=SHEET_URL, worksheet=worksheet_name, data=final_df)
                st.success("✅ Saved! If you marked items as 'Complete', they will move to the table below.")
                st.cache_data.clear()
                time.sleep(1.5)
                st.rerun()
            except Exception as e:
                st.error(f"Error saving: {e}")

    # -----------------------------------------------------------
    # VIEW 2: COMPLETED TASKS (READ ONLY for Standard, Editable for Admin)
    # -----------------------------------------------------------
    st.divider()
    with st.expander("✅ Completed History (Click to View)", expanded=False):
        st.write("These items are marked as **Complete**.")
        
        # Admin can edit history if needed (to revert status), others just view
        if st.session_state["role"] == "Admin":
            edited_completed_df = st.data_editor(
                df_completed,
                column_config=column_config,
                use_container_width=True,
                key=f"history_{worksheet_name}"
            )
            # Save button for history table
            if not df_completed.equals(edited_completed_df):
                if st.button(f"💾 Update History for {tab_name}"):
                    final_df = pd.concat([df_active, edited_completed_df], ignore_index=True)
                    conn.update(spreadsheet=SHEET_URL, worksheet=worksheet_name, data=final_df)
                    st.cache_data.clear()
                    st.rerun()
        else:
            # Standard users just see a static table
            st.dataframe(df_completed, use_container_width=True)

    # -----------------------------------------------------------
    # ADD NEW ENTRY FORM (UNCHANGED)
    # -----------------------------------------------------------
    restricted_roles = ["Production", "Packing"]
    
    if st.session_state["role"] not in restricted_roles:
        
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
                    
                    c4, c5 = st.columns(2)
                    with c4:
                        ready_qty_init = st.number_input("Initial Ready Qty", value=0, key="p_ready")
                    with c5:
                        status_init = st.selectbox("Initial Status", ["Pending", "Next Day", "Complete"], key="p_stat")

                    if st.form_submit_button("Submit Packing Data"):
                        if not item:
                            st.warning("Item Name Required")
                        else:
                            new_row = pd.DataFrame([{
                                "Date": str(date), "Order Date": str(order_date), "Order Priority": priority,
                                "Item Name": item, "Qty": qty, "Logo": logo, "Bottom Print": bottom, 
                                "Box": box, "Remarks": remarks, "Ready Qty": ready_qty_init, "Status": status_init
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
                    
                    c3, c4 = st.columns(2)
                    with c3:
                        ready_qty_init = st.number_input("Initial Ready Qty", value=0, key=f"r_{worksheet_name}")
                    with c4:
                        status_init = st.selectbox("Initial Status", ["Pending", "Next Day", "Complete"], key=f"s_{worksheet_name}")

                    if st.form_submit_button("Submit Entry"):
                        if not item:
                            st.warning("Item Name Required")
                        else:
                            new_row = pd.DataFrame([{
                                "Date": str(date), "Item": item, "Quantity": qty, 
                                "Notes": notes, "Ready Qty": ready_qty_init, "Status": status_init
                            }])
                            save_new_entry(worksheet_name, data, new_row)
    else:
        st.info(f"ℹ️ {st.session_state['role']} Users can View and Update 'Ready Qty' & 'Status'. New entries restricted.")

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

if not st.session_state["logged_in"]:
    login()
else:
    with st.sidebar:
        st.write(f"👤 User: **{st.session_state['user']}**")
        if st.button("Logout"):
            logout()

    st.title("🏭 Mini ERP System")

    user_access = st.session_state["access"]
    selected_tab = st.selectbox("Navigate to:", user_access)
    st.divider()

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
        st.text_input("Example Admin Setting", "Default Value")
