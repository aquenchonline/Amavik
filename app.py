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
    # 👇 NEW USER ADDED
    "Ecommerce":  {"pass": "Amavik@12", "role": "Ecommerce",  "access": ["Ecommerce"]},
    "Amar":       {"pass": "Aquench@1933", "role": "Admin",   "access": ["Production", "Packing", "Store", "Ecommerce", "Configuration"]}
}

# ------------------------------------------------------------------
# SESSION STATE MANAGEMENT
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
# CONNECTION
# ------------------------------------------------------------------
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"🚨 Connection Error: {e}")
    st.stop()

# ------------------------------------------------------------------
# HELPER: DATE FILTER
# ------------------------------------------------------------------
def filter_by_date(df, filter_option):
    if df.empty: return df
    df["temp_date"] = pd.to_datetime(df["Date"], errors='coerce').dt.date
    today = date.today()
    mask = pd.Series([False] * len(df))
    
    if filter_option == "All": return df.drop(columns=["temp_date"])
    elif filter_option == "Today": mask = df["temp_date"] == today
    elif filter_option == "Yesterday": mask = df["temp_date"] == (today - timedelta(days=1))
    elif filter_option == "Prev 7 Days": mask = (df["temp_date"] >= (today - timedelta(days=7))) & (df["temp_date"] < today)
    elif filter_option == "Prev 15 Days": mask = (df["temp_date"] >= (today - timedelta(days=15))) & (df["temp_date"] < today)
    elif filter_option == "Prev 30 Days": mask = (df["temp_date"] >= (today - timedelta(days=30))) & (df["temp_date"] < today)
    elif filter_option == "Prev All": mask = df["temp_date"] < today
    elif filter_option == "Next 7 Days": mask = (df["temp_date"] > today) & (df["temp_date"] <= (today + timedelta(days=7)))
    elif filter_option == "Next 15 Days": mask = (df["temp_date"] > today) & (df["temp_date"] <= (today + timedelta(days=15)))
    elif filter_option == "Next 30 Days": mask = (df["temp_date"] > today) & (df["temp_date"] <= (today + timedelta(days=30)))
    
    return df[mask].drop(columns=["temp_date"])

# ------------------------------------------------------------------
# CORE FUNCTION: MANAGE DATA
# ------------------------------------------------------------------
def manage_tab(tab_name, worksheet_name):
    st.subheader(f"📂 {tab_name} Dashboard")

    # 1. READ DATA
    try:
        data = conn.read(spreadsheet=SHEET_URL, worksheet=worksheet_name, ttl=0)
        if data is None or data.empty: data = pd.DataFrame()
    except:
        data = pd.DataFrame()

    # --- ADD TRACKING ID ---
    if not data.empty:
        data['_original_idx'] = data.index

    # ===============================================================
    # SPECIAL LOGIC FOR ECOMMERCE TAB
    # ===============================================================
    if worksheet_name == "Ecommerce":
        # 1. KPI CALCULATIONS (Today vs Yesterday)
        st.write("### 📊 Performance Overview")
        
        # Helper to get numeric sums for a specific date
        def get_daily_sums(df, target_date):
            if df.empty: return 0, 0, 0
            # Filter rows for date
            df_temp = df.copy()
            df_temp["dt"] = pd.to_datetime(df_temp["Date"], errors='coerce').dt.date
            day_data = df_temp[df_temp["dt"] == target_date]
            
            # Sum columns safely
            orders = pd.to_numeric(day_data["Today's Order"], errors='coerce').sum()
            dispatch = pd.to_numeric(day_data["Today's Dispatch"], errors='coerce').sum()
            returns = pd.to_numeric(day_data["Return"], errors='coerce').sum()
            return orders, dispatch, returns

        today = date.today()
        yesterday = today - timedelta(days=1)

        t_ord, t_dis, t_ret = get_daily_sums(data, today)
        y_ord, y_dis, y_ret = get_daily_sums(data, yesterday)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Today's Orders", f"{int(t_ord)}", delta=f"{int(t_ord - y_ord)} vs Yest")
        with col2:
            st.metric("Dispatched Today", f"{int(t_dis)}", delta=f"{int(t_dis - y_dis)} vs Yest")
        with col3:
            # For returns, positive delta is usually "bad", but st.metric makes positive green by default.
            # We invert the color logic: delta_color="inverse" means Red for Up, Green for Down
            st.metric("Today's Returns", f"{int(t_ret)}", delta=f"{int(t_ret - y_ret)} vs Yest", delta_color="inverse")

        st.divider()

        # 2. DATA TABLE & PERMISSIONS
        # Logic: Only "Ecommerce" role can edit. Admin is View Only.
        is_editable = (st.session_state["role"] == "Ecommerce")
        
        st.write("### 📋 Data Log")
        
        # Date Filter
        d_filter = st.selectbox("📅 Filter View", ["All", "Today", "Yesterday", "Prev 7 Days"], index=1, key="eco_filter")
        filtered_view = filter_by_date(data, d_filter)

        if is_editable:
            # Editable Table for Ecommerce User
            edited_df = st.data_editor(
                filtered_view,
                use_container_width=True,
                num_rows="fixed",
                key="eco_editor",
                disabled=["_original_idx"]
            )
            
            # Save Button
            clean_view = filtered_view.drop(columns=["_original_idx"], errors='ignore')
            clean_edited = edited_df.drop(columns=["_original_idx"], errors='ignore')
            
            if not clean_view.equals(clean_edited):
                if st.button("💾 Save Changes"):
                    save_smart_update(data, edited_df, worksheet_name)

            # Add Entry Form (Only for Ecommerce User)
            st.divider()
            with st.expander("➕ Add New Ecommerce Entry"):
                with st.form("eco_form"):
                    c1, c2 = st.columns(2)
                    with c1:
                        date_val = st.date_input("Date")
                        channel = st.text_input("Channel Name")
                        orders = st.number_input("Today's Order", min_value=0)
                    with c2:
                        dispatch = st.number_input("Today's Dispatch", min_value=0)
                        ret = st.number_input("Return", min_value=0)
                    
                    if st.form_submit_button("Add Record"):
                        if not channel:
                            st.warning("Channel Name Required")
                        else:
                            new_row = pd.DataFrame([{
                                "Date": str(date_val), "Channel Name": channel, 
                                "Today's Order": orders, "Today's Dispatch": dispatch, "Return": ret
                            }])
                            save_new_row(data, new_row, worksheet_name)

        else:
            # Read-Only View for Admin
            st.info("ℹ️ Read-Only View (Admin Access)")
            st.dataframe(filtered_view.drop(columns=["_original_idx"], errors='ignore'), use_container_width=True)

        return # End Ecommerce logic here

    # ===============================================================
    # STANDARD LOGIC FOR PRODUCTION / PACKING / STORE
    # ===============================================================
    
    # Ensure Columns
    if "Ready Qty" not in data.columns: data["Ready Qty"] = 0
    if "Status" not in data.columns: data["Status"] = "Pending"
    
    # Special columns for Packing
    if worksheet_name == "Packing":
        if "Party Name" not in data.columns: data["Party Name"] = ""
        desired_order = ["Date", "Order Date", "Order Priority", "Item Name", "Party Name", "Qty", "Logo", "Bottom Print", "Box", "Remarks", "Ready Qty", "Status"]
        current_cols = data.columns.tolist()
        final_order = [c for c in desired_order if c in current_cols] + [c for c in current_cols if c not in desired_order]
        data = data[final_order]

    data["Status"] = data["Status"].fillna("Pending").replace("", "Pending")

    # FILTERS
    unique_items = sorted(data["Item Name"].astype(str).unique().tolist()) if "Item Name" in data.columns else []
    unique_parties = sorted(data["Party Name"].astype(str).unique().tolist()) if "Party Name" in data.columns else []

    c1, c2, c3 = st.columns(3)
    with c1:
        date_filter = st.selectbox("📅 Date Range", ["All", "Today", "Yesterday", "Prev 7 Days", "Prev 15 Days", "Prev 30 Days", "Prev All"], index=0, key=f"d_{worksheet_name}")
    with c2:
        item_filter = st.multiselect("📦 Item Name", options=unique_items, key=f"i_{worksheet_name}")
    with c3:
        party_filter = st.multiselect("busts_in_silhouette: Party Name", options=unique_parties, key=f"p_{worksheet_name}") if unique_parties else []

    filtered_data = filter_by_date(data, date_filter)
    if item_filter: filtered_data = filtered_data[filtered_data["Item Name"].isin(item_filter)]
    if party_filter and "Party Name" in filtered_data.columns: filtered_data = filtered_data[filtered_data["Party Name"].isin(party_filter)]

    # SPLIT VIEW
    if not filtered_data.empty:
        active_mask = filtered_data["Status"] != "Complete"
        df_active = filtered_data[active_mask].copy()
        df_comp = filtered_data[~active_mask].copy()
    else:
        df_active, df_comp = pd.DataFrame(), pd.DataFrame()

    # PERMISSIONS
    all_columns = [c for c in data.columns if c != "_original_idx"]
    if st.session_state["role"] == "Admin":
        disabled_cols = ["_original_idx"]
    else:
        disabled_cols = [c for c in all_columns if c not in ["Ready Qty", "Status"]] + ["_original_idx"]

    # EDITABLE TABLE
    st.write("### 🚀 Active Tasks")
    edited_active = st.data_editor(
        df_active,
        disabled=disabled_cols,
        column_config={"Status": st.column_config.SelectboxColumn("Status", options=["Pending", "Next Day", "Complete"], required=True), "_original_idx": None},
        use_container_width=True,
        num_rows="dynamic" if st.session_state["role"] == "Admin" else "fixed",
        key=f"act_{worksheet_name}"
    )

    # SAVE LOGIC
    clean_active = df_active.drop(columns=["_original_idx"], errors='ignore')
    clean_edited = edited_active.drop(columns=["_original_idx"], errors='ignore')

    if not clean_active.equals(clean_edited):
        if st.button(f"💾 Save {tab_name}", key=f"sv_{worksheet_name}"):
            save_smart_update(data, edited_active, worksheet_name)

    # HISTORY
    st.divider()
    with st.expander("✅ Completed History"):
        st.dataframe(df_comp.drop(columns=["_original_idx"], errors='ignore'), use_container_width=True)

    # ADD ENTRY FORM
    if st.session_state["role"] not in ["Production", "Packing"]:
        st.divider()
        with st.expander(f"➕ Add Entry"):
            with st.form(f"fm_{worksheet_name}"):
                if worksheet_name == "Packing":
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        d = st.date_input("Date")
                        i = st.text_input("Item")
                        p = st.text_input("Party")
                    with c2:
                        od = st.date_input("Order Date")
                        q = st.number_input("Qty", min_value=0)
                        l = st.selectbox("Logo", ["W/O Logo", "Laser", "Pad"])
                    with c3:
                        pr = st.number_input("Priority", min_value=1)
                        b = st.selectbox("Bottom", ["No", "Laser", "Pad"])
                        bx = st.selectbox("Box", ["Loose", "Brown Box", "White Box", "Box"])
                    rem = st.text_input("Remarks")
                    c4, c5 = st.columns(2)
                    with c4: rq = st.number_input("Ready Qty", value=0)
                    with c5: stt = st.selectbox("Status", ["Pending", "Next Day", "Complete"])
                    
                    if st.form_submit_button("Submit"):
                        if not i: st.warning("Item Required")
                        else:
                            nr = pd.DataFrame([{"Date": str(d), "Order Date": str(od), "Order Priority": pr, "Item Name": i, "Party Name": p, "Qty": q, "Logo": l, "Bottom Print": b, "Box": bx, "Remarks": rem, "Ready Qty": rq, "Status": stt}])
                            save_new_row(data, nr, worksheet_name)
                else:
                    c1, c2 = st.columns(2)
                    with c1:
                        d = st.date_input("Date")
                        i = st.text_input("Item")
                    with c2:
                        q = st.number_input("Qty", min_value=0)
                        n = st.text_input("Notes")
                    c3, c4 = st.columns(2)
                    with c3: rq = st.number_input("Ready Qty", value=0)
                    with c4: stt = st.selectbox("Status", ["Pending", "Next Day", "Complete"])

                    if st.form_submit_button("Submit"):
                        if not i: st.warning("Item Required")
                        else:
                            nr = pd.DataFrame([{"Date": str(d), "Item": i, "Quantity": q, "Notes": n, "Ready Qty": rq, "Status": stt}])
                            save_new_row(data, nr, worksheet_name)

# ------------------------------------------------------------------
# SAVING HELPERS
# ------------------------------------------------------------------
def save_smart_update(original_data, edited_subset, sheet_name):
    try:
        all_cols = [c for c in original_data.columns if c != "_original_idx"]
        for i, row in edited_subset.iterrows():
            idx = row.get("_original_idx")
            if pd.notna(idx) and idx in original_data.index:
                for col in all_cols:
                    if col in row: original_data.at[idx, col] = row[col]
            elif pd.isna(idx):
                # New row added via table
                new_data = {col: row[col] for col in all_cols if col in row}
                original_data = pd.concat([original_data, pd.DataFrame([new_data])], ignore_index=True)
        
        final = original_data.drop(columns=["_original_idx"], errors='ignore')
        conn.update(spreadsheet=SHEET_URL, worksheet=sheet_name, data=final)
        st.success("✅ Saved!")
        st.cache_data.clear()
        time.sleep(1)
        st.rerun()
    except Exception as e:
        st.error(f"Error: {e}")

def save_new_row(original_data, new_row_df, sheet_name):
    try:
        original_clean = original_data.drop(columns=["_original_idx"], errors='ignore')
        updated = pd.concat([original_clean, new_row_df], ignore_index=True)
        conn.update(spreadsheet=SHEET_URL, worksheet=sheet_name, data=updated)
        st.success("✅ Added!")
        st.cache_data.clear()
        time.sleep(1)
        st.rerun()
    except Exception as e:
        st.error(f"Error: {e}")

# ------------------------------------------------------------------
# MAIN APP
# ------------------------------------------------------------------
if not st.session_state["logged_in"]:
    login()
else:
    with st.sidebar:
        st.write(f"👤 **{st.session_state['user']}** ({st.session_state['role']})")
        if st.button("Logout"): logout()

    st.title("🏭 ERP System")
    
    sel = st.selectbox("Navigate to:", st.session_state["access"])
    st.divider()

    if sel == "Configuration":
        st.header("⚙️ Configuration")
        st.info("Admin Area")
    else:
        manage_tab(sel, sel)
