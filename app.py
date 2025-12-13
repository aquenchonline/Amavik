import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
import time
from datetime import date, timedelta, datetime

# ------------------------------------------------------------------
# 1. PAGE CONFIGURATION
# ------------------------------------------------------------------
st.set_page_config(
    page_title="ERP System", 
    layout="wide", 
    page_icon="🏭",
    initial_sidebar_state="expanded"
)

SHEET_URL = "https://docs.google.com/spreadsheets/d/1S6xS6hcdKSPtzKxCL005GwvNWQNspNffNveI3P9zCgw/edit"

# ------------------------------------------------------------------
# 2. USER AUTHENTICATION DATABASE
# ------------------------------------------------------------------
USERS = {
    "Production": {"pass": "Amavik@80", "role": "Production", "access": ["Production"]},
    "Packing":    {"pass": "Amavik@97", "role": "Packing",    "access": ["Packing"]},
    "Store":      {"pass": "Amavik@17", "role": "Store",      "access": ["Store"]},
    "Ecommerce":  {"pass": "Amavik@12", "role": "Ecommerce",  "access": ["Ecommerce"]},
    "Amar":       {"pass": "Aquench@1933", "role": "Admin",   "access": ["Production", "Packing", "Store", "Ecommerce", "Configuration"]}
}

# ------------------------------------------------------------------
# 3. SESSION STATE (LOGIN SYSTEM)
# ------------------------------------------------------------------
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["user"] = None
    st.session_state["role"] = None

def login():
    st.title("🔒 ERP Secure Login")
    st.markdown("Please sign in to access the system.")
    
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
# 4. DATABASE CONNECTION
# ------------------------------------------------------------------
try:
    # This looks for [connections.gsheets] in secrets.toml
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"🚨 Connection Error: {e}")
    st.stop()

# ------------------------------------------------------------------
# 5. HELPER FUNCTIONS
# ------------------------------------------------------------------
def filter_by_date(df, filter_option):
    """Filters a dataframe based on the 'Date' column."""
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
    elif filter_option == "This Month": mask = (df["temp_date"] >= today.replace(day=1)) & (df["temp_date"] <= today)
    
    return df[mask].drop(columns=["temp_date"])

def save_smart_update(original_data, edited_subset, sheet_name):
    """Updates existing rows and adds new rows without overwriting hidden data."""
    try:
        all_cols = [c for c in original_data.columns if c != "_original_idx"]
        
        # Update logic
        for i, row in edited_subset.iterrows():
            idx = row.get("_original_idx")
            
            # Existing row update
            if pd.notna(idx) and idx in original_data.index:
                for col in all_cols:
                    if col in row: original_data.at[idx, col] = row[col]
            
            # New row added via table (Admin feature)
            elif pd.isna(idx):
                new_data = {col: row[col] for col in all_cols if col in row}
                original_data = pd.concat([original_data, pd.DataFrame([new_data])], ignore_index=True)
        
        # Clean and Upload
        final = original_data.drop(columns=["_original_idx"], errors='ignore')
        conn.update(spreadsheet=SHEET_URL, worksheet=sheet_name, data=final)
        
        st.toast("✅ Saved Successfully!", icon="💾")
        st.cache_data.clear()
        time.sleep(1)
        st.rerun()
    except Exception as e:
        st.error(f"Error saving data: {e}")

def save_new_row(original_data, new_row_df, sheet_name):
    """Appends a new row to the sheet."""
    try:
        original_clean = original_data.drop(columns=["_original_idx"], errors='ignore')
        updated = pd.concat([original_clean, new_row_df], ignore_index=True)
        conn.update(spreadsheet=SHEET_URL, worksheet=sheet_name, data=updated)
        
        st.toast("✅ Entry Added!", icon="➕")
        st.cache_data.clear()
        time.sleep(1)
        st.rerun()
    except Exception as e:
        st.error(f"Error adding row: {e}")

# ------------------------------------------------------------------
# 6. MAIN LOGIC: MANAGE TAB
# ------------------------------------------------------------------
def manage_tab(tab_name, worksheet_name):
    # READ DATA (ttl=0 ensures fresh data every reload)
    try:
        data = conn.read(spreadsheet=SHEET_URL, worksheet=worksheet_name, ttl=0)
        if data is None or data.empty: data = pd.DataFrame()
    except:
        data = pd.DataFrame()

    # Create Index for safe tracking
    if not data.empty:
        data['_original_idx'] = data.index

    # ===============================================================
    # A. ECOMMERCE DASHBOARD LOGIC
    # ===============================================================
    if worksheet_name == "Ecommerce":
        # Initialize container for current view to prevent crashes
        df_curr = pd.DataFrame()

        st.markdown("## 📊 Ecommerce Performance Center")
        
        # --- FILTERS ---
        col_ch, col_date = st.columns([1, 1])
        
        unique_channels = ["All Channels"]
        if "Channel Name" in data.columns:
            channels_list = sorted(data["Channel Name"].astype(str).unique().tolist())
            unique_channels.extend(channels_list)

        with col_ch:
            selected_channel = st.selectbox("Select Channel", unique_channels, index=0)

        with col_date:
            selected_period = st.selectbox(
                "Compare Period", 
                ["Today", "Yesterday", "Last 7 Days", "Last 15 Days", "Last 30 Days", "This Month", "All Time"],
                index=0
            )

        # --- KPI CALCULATION ---
        if not data.empty:
            df_calc = data.copy()
            df_calc["dt"] = pd.to_datetime(df_calc["Date"], errors='coerce').dt.date
            
            # 1. Filter Channel
            if selected_channel != "All Channels":
                df_calc = df_calc[df_calc["Channel Name"] == selected_channel]

            today = date.today()
            
            # 2. Determine Date Ranges
            if selected_period == "Today":
                curr_start, curr_end = today, today
                prev_start, prev_end = today - timedelta(days=1), today - timedelta(days=1)
            elif selected_period == "Yesterday":
                curr_start, curr_end = today - timedelta(days=1), today - timedelta(days=1)
                prev_start, prev_end = today - timedelta(days=2), today - timedelta(days=2)
            elif selected_period == "Last 7 Days":
                curr_start, curr_end = today - timedelta(days=6), today
                prev_start, prev_end = today - timedelta(days=13), today - timedelta(days=7)
            elif selected_period == "Last 15 Days":
                curr_start, curr_end = today - timedelta(days=14), today
                prev_start, prev_end = today - timedelta(days=29), today - timedelta(days=15)
            elif selected_period == "Last 30 Days":
                curr_start, curr_end = today - timedelta(days=29), today
                prev_start, prev_end = today - timedelta(days=59), today - timedelta(days=30)
            elif selected_period == "This Month":
                curr_start, curr_end = today.replace(day=1), today
                prev_month_end = curr_start - timedelta(days=1)
                prev_month_start = prev_month_end.replace(day=1)
                prev_start, prev_end = prev_month_start, prev_month_start + (curr_end - curr_start)
            else:
                curr_start, curr_end = date.min, date.max
                prev_start, prev_end = date.min, date.min

            # 3. Apply Ranges
            mask_curr = (df_calc["dt"] >= curr_start) & (df_calc["dt"] <= curr_end)
            df_curr = df_calc[mask_curr]
            
            mask_prev = (df_calc["dt"] >= prev_start) & (df_calc["dt"] <= prev_end)
            df_prev = df_calc[mask_prev]

            # 4. Sum Values
            def sum_cols(df):
                o = pd.to_numeric(df["Today's Order"], errors='coerce').sum()
                d = pd.to_numeric(df["Today's Dispatch"], errors='coerce').sum()
                r = pd.to_numeric(df["Return"], errors='coerce').sum()
                return int(o), int(d), int(r)

            c_ord, c_dis, c_ret = sum_cols(df_curr)
            p_ord, p_dis, p_ret = sum_cols(df_prev)

            # 5. Display KPI Cards
            k1, k2, k3 = st.columns(3)
            
            def get_delta(curr, prev):
                if selected_period == "All Time": return None
                diff = curr - prev
                if prev == 0: return f"{diff}"
                pct = round((diff / prev) * 100, 1)
                return f"{diff} ({pct}%)"

            with k1: st.metric(label="Total Orders", value=c_ord, delta=get_delta(c_ord, p_ord))
            with k2: st.metric(label="Total Dispatched", value=c_dis, delta=get_delta(c_dis, p_dis))
            with k3: st.metric(label="Total Returns", value=c_ret, delta=get_delta(c_ret, p_ret), delta_color="inverse")

        st.divider()

        # --- CHARTS SECTION ---
        st.subheader("📈 Visual Trends")
        if not data.empty:
            df_viz = data.copy()
            df_viz["Date"] = pd.to_datetime(df_viz["Date"], errors='coerce')
            df_viz["Today's Order"] = pd.to_numeric(df_viz["Today's Order"], errors='coerce').fillna(0)

            # Range Selector
            today = date.today()
            default_start = today - timedelta(days=10)
            
            c_range, _ = st.columns([1, 2])
            with c_range:
                date_range = st.date_input("Chart Date Range", value=(default_start, today), key="viz_range")

            if isinstance(date_range, tuple) and len(date_range) == 2:
                start_d, end_d = date_range
                mask_viz = (df_viz["Date"].dt.date >= start_d) & (df_viz["Date"].dt.date <= end_d)
                df_viz_filtered = df_viz[mask_viz]

                g_col, p_col = st.columns([2, 1])

                # Line Chart
                with g_col:
                    if not df_viz_filtered.empty:
                        daily_trend = df_viz_filtered.groupby("Date")["Today's Order"].sum().reset_index()
                        fig_line = px.line(daily_trend, x="Date", y="Today's Order", title="Order Trend", markers=True)
                        fig_line.update_traces(line_color='#FF4B4B', line_width=3)
                        st.plotly_chart(fig_line, use_container_width=True)
                    else:
                        st.info("No data for charts")

                # Pie Chart
                with p_col:
                    if not df_viz_filtered.empty and "Channel Name" in df_viz_filtered.columns:
                        channel_dist = df_viz_filtered.groupby("Channel Name")["Today's Order"].sum().reset_index()
                        fig_pie = px.pie(channel_dist, values="Today's Order", names="Channel Name", title="Channel Share", hole=0.4)
                        st.plotly_chart(fig_pie, use_container_width=True)

        st.divider()

        # --- DATA TABLE & EDITING ---
        st.write("### 📋 Detailed Logs")
        
        # Determine what to show in table (Reuse KPI filter logic)
        if df_curr.empty:
            if not data.empty:
                display_df = pd.DataFrame(columns=data.columns).drop(columns=["dt"], errors="ignore")
            else:
                display_df = pd.DataFrame()
        else:
            display_df = df_curr.drop(columns=["dt"], errors="ignore")

        is_editable = (st.session_state["role"] == "Ecommerce")

        if is_editable:
            # Edit Mode
            edited_df = st.data_editor(
                display_df,
                use_container_width=True,
                num_rows="fixed",
                key="eco_editor",
                disabled=["_original_idx"]
            )
            
            # Save Table Changes
            clean_view = display_df.drop(columns=["_original_idx"], errors='ignore')
            clean_edited = edited_df.drop(columns=["_original_idx"], errors='ignore')
            
            if not clean_view.equals(clean_edited):
                if st.button("💾 Save Table Changes"):
                    save_smart_update(data, edited_df, worksheet_name)

            st.divider()
            
            # Add New Entry Form
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
            # Read Only
            st.info("ℹ️ Read-Only View (Admin Access)")
            st.dataframe(display_df.drop(columns=["_original_idx"], errors='ignore'), use_container_width=True)

        return # End Ecommerce logic

    # ===============================================================
    # B. STANDARD LOGIC (Production, Packing, Store)
    # ===============================================================
    st.subheader(f"📂 {tab_name} Dashboard")

    # Ensure Standard Columns
    if "Ready Qty" not in data.columns: data["Ready Qty"] = 0
    if "Status" not in data.columns: data["Status"] = "Pending"
    
    # Special Sorting for Packing
    if worksheet_name == "Packing":
        if "Party Name" not in data.columns: data["Party Name"] = ""
        desired_order = ["Date", "Order Date", "Order Priority", "Item Name", "Party Name", "Qty", "Logo", "Bottom Print", "Box", "Remarks", "Ready Qty", "Status"]
        current_cols = data.columns.tolist()
        final_order = [c for c in desired_order if c in current_cols] + [c for c in current_cols if c not in desired_order]
        data = data[final_order]

    data["Status"] = data["Status"].fillna("Pending").replace("", "Pending")

    # --- FILTERS ---
    unique_items = sorted(data["Item Name"].astype(str).unique().tolist()) if "Item Name" in data.columns else []
    unique_parties = sorted(data["Party Name"].astype(str).unique().tolist()) if "Party Name" in data.columns else []

    c1, c2, c3 = st.columns(3)
    with c1:
        date_filter = st.selectbox("📅 Date Range", ["All", "Today", "Yesterday", "Prev 7 Days", "Prev 15 Days", "Prev 30 Days", "Prev All"], index=0, key=f"d_{worksheet_name}")
    with c2:
        item_filter = st.multiselect("📦 Item Name", options=unique_items, key=f"i_{worksheet_name}")
    with c3:
        party_filter = st.multiselect("busts_in_silhouette: Party Name", options=unique_parties, key=f"p_{worksheet_name}") if unique_parties else []

    # Apply Filters
    filtered_data = filter_by_date(data, date_filter)
    if item_filter: filtered_data = filtered_data[filtered_data["Item Name"].isin(item_filter)]
    if party_filter and "Party Name" in filtered_data.columns: filtered_data = filtered_data[filtered_data["Party Name"].isin(party_filter)]

    # --- SPLIT VIEW (Active vs Complete) ---
    if not filtered_data.empty:
        active_mask = filtered_data["Status"] != "Complete"
        df_active = filtered_data[active_mask].copy()
        df_comp = filtered_data[~active_mask].copy()
    else:
        df_active, df_comp = pd.DataFrame(), pd.DataFrame()

    # --- PERMISSIONS ---
    all_columns = [c for c in data.columns if c != "_original_idx"]
    if st.session_state["role"] == "Admin":
        disabled_cols = ["_original_idx"]
    else:
        # Standard users only edit specific status columns
        disabled_cols = [c for c in all_columns if c not in ["Ready Qty", "Status"]] + ["_original_idx"]

    # --- ACTIVE TASKS TABLE ---
    st.write("### 🚀 Active Tasks")
    edited_active = st.data_editor(
        df_active,
        disabled=disabled_cols,
        column_config={
            "Status": st.column_config.SelectboxColumn("Status", options=["Pending", "Next Day", "Complete"], required=True), 
            "_original_idx": None
        },
        use_container_width=True,
        num_rows="dynamic" if st.session_state["role"] == "Admin" else "fixed",
        key=f"act_{worksheet_name}"
    )

    # Save Check
    clean_active = df_active.drop(columns=["_original_idx"], errors='ignore')
    clean_edited = edited_active.drop(columns=["_original_idx"], errors='ignore')

    if not clean_active.equals(clean_edited):
        if st.button(f"💾 Save {tab_name} Changes", key=f"sv_{worksheet_name}"):
            save_smart_update(data, edited_active, worksheet_name)

    # --- COMPLETED HISTORY ---
    st.divider()
    with st.expander("✅ Completed History (Read Only)"):
        st.dataframe(df_comp.drop(columns=["_original_idx"], errors='ignore'), use_container_width=True)

    # --- ADD ENTRY FORM ---
    # Logic: Show form only if User is Admin OR (User is Store/Production/Packing/etc depending on logic)
    # Your rule: Packing/Production CANNOT add entries. Only Store/Admin can.
    can_add_entry = st.session_state["role"] not in ["Production", "Packing"]
    
    if can_add_entry:
        st.divider()
        with st.expander(f"➕ Add New Entry"):
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
                
                else: # Production / Store
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
# 7. APP ORCHESTRATION
# ------------------------------------------------------------------
if not st.session_state["logged_in"]:
    login()
else:
    with st.sidebar:
        st.write(f"👤 **{st.session_state['user']}**")
        st.caption(f"Role: {st.session_state['role']}")
        if st.button("Logout", use_container_width=True): logout()

    st.title("🏭 ERP System")
    
    # Navigation
    sel = st.selectbox("Navigate to:", st.session_state["access"])
    st.divider()

    if sel == "Configuration":
        st.header("⚙️ Configuration")
        st.info("Admin Area: Add future settings here.")
    else:
        manage_tab(sel, sel)
