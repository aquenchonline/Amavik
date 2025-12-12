import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time
from datetime import date, timedelta

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
# HELPER: DATE FILTER LOGIC
# ------------------------------------------------------------------
def filter_by_date(df, filter_option):
    if df.empty:
        return df
    
    df["temp_date"] = pd.to_datetime(df["Date"], errors='coerce').dt.date
    today = date.today()
    
    if filter_option == "All":
        return df.drop(columns=["temp_date"])
    
    mask = pd.Series([False] * len(df))
    
    if filter_option == "Today":
        mask = df["temp_date"] == today
    elif filter_option == "Yesterday":
        mask = df["temp_date"] == (today - timedelta(days=1))
    elif filter_option == "Prev 7 Days":
        mask = (df["temp_date"] >= (today - timedelta(days=7))) & (df["temp_date"] < today)
    elif filter_option == "Prev 15 Days":
        mask = (df["temp_date"] >= (today - timedelta(days=15))) & (df["temp_date"] < today)
    elif filter_option == "Prev 30 Days":
        mask = (df["temp_date"] >= (today - timedelta(days=30))) & (df["temp_date"] < today)
    elif filter_option == "Prev All":
        mask = df["temp_date"] < today
    elif filter_option == "Next 7 Days":
        mask = (df["temp_date"] > today) & (df["temp_date"] <= (today + timedelta(days=7)))
    elif filter_option == "Next 15 Days":
        mask = (df["temp_date"] > today) & (df["temp_date"] <= (today + timedelta(days=15)))
    elif filter_option == "Next 30 Days":
        mask = (df["temp_date"] > today) & (df["temp_date"] <= (today + timedelta(days=30)))

    return df[mask].drop(columns=["temp_date"])

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

    # Ensure Essential Columns
    if "Ready Qty" not in data.columns:
        data["Ready Qty"] = 0
    if "Status" not in data.columns:
        data["Status"] = "Pending"
    
    # --- ADD PARTY NAME HANDLING FOR PACKING ---
    if worksheet_name == "Packing":
        if "Party Name" not in data.columns:
            data["Party Name"] = "" 
        
        # Reorder columns for Packing
        desired_order = ["Date", "Order Date", "Order Priority", "Item Name", "Party Name", "Qty", "Logo", "Bottom Print", "Box", "Remarks", "Ready Qty", "Status"]
        current_cols = data.columns.tolist()
        final_order = [c for c in desired_order if c in current_cols] + [c for c in current_cols if c not in desired_order]
        data = data[final_order]

    data["Status"] = data["Status"].fillna("Pending").replace("", "Pending")

    # --- ADD TRACKING ID FOR SAFE EDITING ---
    if not data.empty:
        data['_original_idx'] = data.index

    # -----------------------------------------------------------
    # 2. ADVANCED FILTERS (Date + Item + Party)
    # -----------------------------------------------------------
    
    # Get unique values for filters from the ACTUAL data
    unique_items = sorted(data["Item Name"].astype(str).unique().tolist()) if "Item Name" in data.columns else []
    
    # Check if Party Name exists and has data
    unique_parties = []
    if "Party Name" in data.columns:
        unique_parties = sorted(data["Party Name"].astype(str).unique().tolist())

    # Create Filter UI Layout
    c1, c2, c3 = st.columns(3)
    
    with c1:
        date_filter = st.selectbox(
            "📅 Date Range", 
            ["All", "Today", "Yesterday", "Prev 7 Days", "Prev 15 Days", "Prev 30 Days", "Prev All", 
             "Next 7 Days", "Next 15 Days", "Next 30 Days"],
            index=0,
            key=f"filter_date_{worksheet_name}"
        )
    
    with c2:
        item_filter = st.multiselect(
            "📦 Item Name",
            options=unique_items,
            placeholder="All Items",
            key=f"filter_item_{worksheet_name}"
        )
        
    with c3:
        if unique_parties:
            party_filter = st.multiselect(
                "busts_in_silhouette: Party Name",
                options=unique_parties,
                placeholder="All Parties",
                key=f"filter_party_{worksheet_name}"
            )
        else:
            party_filter = []

    # --- APPLY FILTERS ---
    
    # 1. Date Filter
    filtered_data = filter_by_date(data, date_filter)

    # 2. Item Filter
    if item_filter:
        filtered_data = filtered_data[filtered_data["Item Name"].isin(item_filter)]

    # 3. Party Filter
    if party_filter and "Party Name" in filtered_data.columns:
        filtered_data = filtered_data[filtered_data["Party Name"].isin(party_filter)]

    # -----------------------------------------------------------
    # 3. SPLIT ACTIVE / COMPLETED
    # -----------------------------------------------------------
    if not filtered_data.empty:
        active_mask = filtered_data["Status"] != "Complete"
        df_active_view = filtered_data[active_mask].copy()
        df_completed_view = filtered_data[~active_mask].copy()
    else:
        df_active_view = pd.DataFrame()
        df_completed_view = pd.DataFrame()

    # 4. ACTIVE TASKS TABLE
    st.write("### 🚀 Active Tasks")
    
    all_columns = [c for c in data.columns if c != "_original_idx"]
    
    if st.session_state["role"] == "Admin":
        disabled_cols = ["_original_idx"]
    else:
        disabled_cols = [c for c in all_columns if c not in ["Ready Qty", "Status"]]
        disabled_cols.append("_original_idx")

    column_config = {
        "Status": st.column_config.SelectboxColumn("Status", options=["Pending", "Next Day", "Complete"], required=True),
        "_original_idx": None 
    }

    # EDITOR
    edited_active_df = st.data_editor(
        df_active_view,
        disabled=disabled_cols,
        column_config=column_config,
        use_container_width=True,
        num_rows="dynamic" if st.session_state["role"] == "Admin" else "fixed",
        key=f"active_{worksheet_name}"
    )

    # 5. SAVE LOGIC
    df_active_clean = df_active_view.drop(columns=["_original_idx"], errors='ignore')
    df_edited_clean = edited_active_df.drop(columns=["_original_idx"], errors='ignore')

    if not df_active_clean.equals(df_edited_clean):
        st.warning("⚠️ Changes detected.")
        if st.button(f"💾 Save Changes to {tab_name}", key=f"save_{worksheet_name}"):
            try:
                # Update Rows
                for i, row in edited_active_df.iterrows():
                    idx = row.get("_original_idx")
                    
                    if pd.notna(idx) and idx in data.index:
                        for col in all_columns:
                            if col in row:
                                data.at[idx, col] = row[col]
                    
                    elif pd.isna(idx):
                        new_row_data = {col: row[col] for col in all_columns if col in row}
                        data = pd.concat([data, pd.DataFrame([new_row_data])], ignore_index=True)

                # Handle Deletions (Admin)
                if st.session_state["role"] == "Admin":
                    original_ids = df_active_view["_original_idx"].dropna()
                    current_ids = edited_active_df["_original_idx"].dropna()
                    deleted_ids = original_ids[~original_ids.isin(current_ids)]
                    if not deleted_ids.empty:
                        data = data.drop(deleted_ids)

                # Save
                final_upload = data.drop(columns=["_original_idx"], errors='ignore')
                conn.update(spreadsheet=SHEET_URL, worksheet=worksheet_name, data=final_upload)
                st.success("✅ Database Updated!")
                st.cache_data.clear()
                time.sleep(1)
                st.rerun()

            except Exception as e:
                st.error(f"Error saving: {e}")

    # 6. COMPLETED TASKS (History)
    st.divider()
    with st.expander("✅ Completed History (Click to View)", expanded=False):
        if st.session_state["role"] == "Admin":
             edited_history_df = st.data_editor(
                df_completed_view,
                column_config=column_config,
                use_container_width=True,
                key=f"hist_{worksheet_name}"
            )
             hist_clean = df_completed_view.drop(columns=["_original_idx"], errors='ignore')
             hist_edited_clean = edited_history_df.drop(columns=["_original_idx"], errors='ignore')

             if not hist_clean.equals(hist_edited_clean):
                 if st.button(f"💾 Update History for {tab_name}"):
                     for i, row in edited_history_df.iterrows():
                        idx = row.get("_original_idx")
                        if pd.notna(idx) and idx in data.index:
                             for col in all_columns:
                                if col in row:
                                    data.at[idx, col] = row[col]
                     
                     final_upload = data.drop(columns=["_original_idx"], errors='ignore')
                     conn.update(spreadsheet=SHEET_URL, worksheet=worksheet_name, data=final_upload)
                     st.cache_data.clear()
                     st.rerun()
        else:
            st.dataframe(df_completed_view.drop(columns=["_original_idx"], errors='ignore'), use_container_width=True)

    # 7. ADD NEW ENTRY FORM
    restricted_roles = ["Production", "Packing"]
    if st.session_state["role"] not in restricted_roles:
        st.divider()
        with st.expander(f"➕ Add New Entry to {tab_name}"):
            with st.form(key=f"form_{worksheet_name}"):
                
                # PACKING FORM
                if worksheet_name == "Packing":
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        date_val = st.date_input("Date", key="p_date")
                        item = st.text_input("Item Name", key="p_item")
                        party = st.text_input("Party Name", key="p_party")
                    with c2:
                        order_date = st.date_input("Order Date (Manual)", key="p_odate")
                        qty = st.number_input("Qty", min_value=0, step=1, key="p_qty")
                        logo = st.selectbox("Logo", ["W/O Logo", "Laser", "Pad"], key="p_logo")
                    with c3:
                        priority = st.number_input("Order Priority", min_value=1, step=1, key="p_prio")
                        bottom = st.selectbox("Bottom Print", ["No", "Laser", "Pad"], key="p_bot")
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
                            clean_data = data.drop(columns=["_original_idx"], errors='ignore')
                            new_row = pd.DataFrame([{
                                "Date": str(date_val), "Order Date": str(order_date), "Order Priority": priority,
                                "Item Name": item, "Party Name": party, "Qty": qty, "Logo": logo, "Bottom Print": bottom, 
                                "Box": box, "Remarks": remarks, "Ready Qty": ready_qty_init, "Status": status_init
                            }])
                            save_new_entry(worksheet_name, clean_data, new_row)

                # STANDARD FORM
                else:
                    c1, c2 = st.columns(2)
                    with c1:
                        date_val = st.date_input("Date", key=f"d_{worksheet_name}")
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
                            clean_data = data.drop(columns=["_original_idx"], errors='ignore')
                            new_row = pd.DataFrame([{
                                "Date": str(date_val), "Item": item, "Quantity": qty, 
                                "Notes": notes, "Ready Qty": ready_qty_init, "Status": status_init
                            }])
                            save_new_entry(worksheet_name, clean_data, new_row)
    else:
        st.info(f"ℹ️ {st.session_state['role']} Users: View, Update Ready Qty & Status only.")

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
