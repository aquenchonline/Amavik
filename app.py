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
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"🚨 Connection Error: {e}")
    st.stop()

# ------------------------------------------------------------------
# 5. HELPER FUNCTIONS
# ------------------------------------------------------------------
def filter_by_date(df, filter_option, date_col_name="Date"):
    if df.empty: return df
    df = df.copy() # Work on a copy
    # Coerce date column
    df["temp_date"] = pd.to_datetime(df[date_col_name], errors='coerce').dt.date
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
    try:
        all_cols = [c for c in original_data.columns if c != "_original_idx"]
        for i, row in edited_subset.iterrows():
            idx = row.get("_original_idx")
            if pd.notna(idx) and idx in original_data.index:
                for col in all_cols:
                    if col in row: original_data.at[idx, col] = row[col]
            elif pd.isna(idx):
                new_data = {col: row[col] for col in all_cols if col in row}
                original_data = pd.concat([original_data, pd.DataFrame([new_data])], ignore_index=True)
        
        final = original_data.drop(columns=["_original_idx"], errors='ignore')
        conn.update(spreadsheet=SHEET_URL, worksheet=sheet_name, data=final)
        st.toast("✅ Saved Successfully!", icon="💾")
        st.cache_data.clear()
        time.sleep(1)
        st.rerun()
    except Exception as e:
        st.error(f"Error saving data: {e}")

def save_new_row(original_data, new_row_df, sheet_name):
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
    try:
        data = conn.read(spreadsheet=SHEET_URL, worksheet=worksheet_name, ttl=0)
        if data is None or data.empty: data = pd.DataFrame()
    except:
        data = pd.DataFrame()

    if not data.empty:
        data['_original_idx'] = data.index

    # ===============================================================
    # A. STORE TAB LOGIC (INVENTORY SYSTEM)
    # ===============================================================
    if worksheet_name == "Store":
        df_display = pd.DataFrame()

        # Header & Refresh
        c_title, c_ref = st.columns([8, 1])
        with c_title: st.subheader("📦 Store Inventory Management")
        with c_ref:
            if st.button("🔄", key="ref_store"):
                st.cache_data.clear()
                st.rerun()

        # Live Stock Levels
        if not data.empty and "Item Name" in data.columns and "Qty" in data.columns:
            with st.expander("📊 View Live Stock Levels (Calculated)", expanded=True):
                df_calc = data.copy()
                df_calc["Qty"] = pd.to_numeric(df_calc["Qty"], errors="coerce").fillna(0)
                
                stock_summary = []
                unique_items = df_calc["Item Name"].unique()
                
                for item in unique_items:
                    item_data = df_calc[df_calc["Item Name"] == item]
                    inward = item_data[item_data["Transaction Type"] == "Inward"]["Qty"].sum()
                    outward = item_data[item_data["Transaction Type"] == "Outward"]["Qty"].sum()
                    balance = inward - outward
                    
                    last_entry = item_data.iloc[-1]
                    uom = last_entry["UOM"] if "UOM" in last_entry else ""
                    i_type = last_entry["Type"] if "Type" in last_entry else ""
                    
                    stock_summary.append({
                        "Item Name": item,
                        "Type": i_type,
                        "Total Inward": inward,
                        "Total Outward": outward,
                        "Available Balance": balance,
                        "UOM": uom
                    })
                
                df_stock = pd.DataFrame(stock_summary)
                if not df_stock.empty:
                    st.dataframe(
                        df_stock.style.highlight_between(left=0, right=0, subset=["Available Balance"], color="#ffcdd2"),
                        use_container_width=True,
                        column_config={
                            "Available Balance": st.column_config.NumberColumn("Current Stock", format="%d"),
                            "Total Inward": st.column_config.NumberColumn("Total In", format="%d"),
                            "Total Outward": st.column_config.NumberColumn("Total Out", format="%d"),
                        }
                    )
                else:
                    st.info("No stock data found.")

        st.divider()

        # Filters
        c1, c2, c3, c4 = st.columns(4)
        with c1: d_filter = st.selectbox("📅 Date Filter", ["All", "Today", "Yesterday", "Prev 7 Days", "This Month"], key="st_date")
        with c2: items_list = sorted(data["Item Name"].astype(str).unique()) if "Item Name" in data.columns else []
        i_filter = st.multiselect("📦 Item Search", items_list, key="st_item")
        with c3: vendor_list = sorted(data["Recvd From"].astype(str).unique()) if "Recvd From" in data.columns else []
        v_filter = st.multiselect("busts_in_silhouette: Recvd From", vendor_list, key="st_vendor")
        with c4: trans_filter = st.selectbox("arrows_counterclockwise: Transaction", ["All", "Inward", "Outward"], key="st_trans")

        # Apply Filters
        filtered_df = filter_by_date(data, d_filter, date_col_name="Date Of Entry")
        if i_filter: filtered_df = filtered_df[filtered_df["Item Name"].isin(i_filter)]
        if v_filter: filtered_df = filtered_df[filtered_df["Recvd From"].isin(v_filter)]
        if trans_filter != "All": filtered_df = filtered_df[filtered_df["Transaction Type"] == trans_filter]

        st.write("### 📋 Transaction Log")
        
        # --- FIX: ENSURE DATA TYPES BEFORE EDITOR ---
        if filtered_df.empty:
            df_display = pd.DataFrame(columns=data.columns).drop(columns=["_original_idx"], errors="ignore")
        else:
            df_display = filtered_df.copy() # Copy to avoid warnings

        # 1. Force Qty to Number
        if "Qty" in df_display.columns:
            df_display["Qty"] = pd.to_numeric(df_display["Qty"], errors='coerce').fillna(0)
        
        # 2. Force Date to Date Object
        if "Date Of Entry" in df_display.columns:
            df_display["Date Of Entry"] = pd.to_datetime(df_display["Date Of Entry"], errors='coerce')

        disabled_cols = ["_original_idx"]

        edited_df = st.data_editor(
            df_display,
            use_container_width=True,
            num_rows="fixed",
            key="store_editor",
            disabled=disabled_cols if st.session_state["role"] == "Admin" else ["_original_idx"],
            column_config={
                "Qty": st.column_config.NumberColumn("Qty", format="%d"),
                "Date Of Entry": st.column_config.DateColumn("Date Of Entry", format="YYYY-MM-DD")
            }
        )

        clean_view = df_display.drop(columns=["_original_idx"], errors='ignore')
        clean_edited = edited_df.drop(columns=["_original_idx"], errors='ignore')
        
        if not clean_view.equals(clean_edited):
            if st.button("💾 Save Changes", key="save_store"):
                save_smart_update(data, edited_df, worksheet_name)

        st.divider()
        with st.expander("➕ Update Stock (Add New Entry)", expanded=True):
            with st.form("store_form"):
                c1, c2, c3 = st.columns(3)
                with c1: date_ent = st.date_input("Date Of Entry", value=date.today())
                with c2: trans_type = st.selectbox("Transaction Type", ["Inward", "Outward"])
                with c3: qty = st.number_input("Quantity", min_value=1, step=1)
                c4, c5, c6 = st.columns(3)
                with c4: item_name = st.text_input("Item Name")
                with c5: uom = st.selectbox("UOM", ["Pcs", "Boxes", "Kg", "Ltr", "Set", "Packet"])
                with c6: i_type = st.selectbox("Type", ["Inner Box", "Outer Box", "Washer", "String", "Cap", "Bubble", "Bottle", "Other"])
                c7, c8, c9 = st.columns(3)
                with c7: recvd_from = st.text_input("Recvd From / Sent To")
                with c8: vendor_brand = st.text_input("Vendor Name (Brand)")
                with c9: invoice_no = st.text_input("Invoice No. (Inward Only)")

                if st.form_submit_button("Submit Transaction"):
                    if not item_name:
                        st.warning("⚠️ Item Name is required!")
                    else:
                        new_entry = pd.DataFrame([{
                            "Date Of Entry": str(date_ent),
                            "Recvd From": recvd_from,
                            "Vendor Name(Brand)": vendor_brand,
                            "Type": i_type,
                            "Item Name": item_name,
                            "Qty": qty,
                            "UOM": uom,
                            "Transaction Type": trans_type,
                            "Invoice No.": invoice_no
                        }])
                        save_new_row(data, new_entry, worksheet_name)
        
        return 

    # ===============================================================
    # B. ECOMMERCE DASHBOARD LOGIC
    # ===============================================================
    if worksheet_name == "Ecommerce":
        df_curr = pd.DataFrame()
        c_head, c_ch, c_date, c_ref = st.columns([2, 1, 1, 0.5])
        with c_head: st.subheader("📊 Performance Overview")
        with c_ref:
            st.write("")
            st.write("")
            if st.button("🔄", key="ref_eco"):
                st.cache_data.clear()
                st.rerun()
        
        unique_channels = ["All Channels"]
        if "Channel Name" in data.columns:
            channels_list = sorted(data["Channel Name"].astype(str).unique().tolist())
            unique_channels.extend(channels_list)

        with c_ch: selected_channel = st.selectbox("Select Channel", unique_channels, index=0)
        with c_date: selected_period = st.selectbox("Compare Period", ["Today", "Yesterday", "Last 7 Days", "Last 15 Days", "Last 30 Days", "This Month", "All Time"], index=0)

        if not data.empty:
            df_calc = data.copy()
            df_calc["dt"] = pd.to_datetime(df_calc["Date"], errors='coerce').dt.date
            
            if selected_channel != "All Channels": df_calc = df_calc[df_calc["Channel Name"] == selected_channel]

            today = date.today()
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

            mask_curr = (df_calc["dt"] >= curr_start) & (df_calc["dt"] <= curr_end)
            df_curr = df_calc[mask_curr]
            mask_prev = (df_calc["dt"] >= prev_start) & (df_calc["dt"] <= prev_end)
            df_prev = df_calc[mask_prev]

            def sum_cols(df):
                o = pd.to_numeric(df["Today's Order"], errors='coerce').sum()
                d = pd.to_numeric(df["Today's Dispatch"], errors='coerce').sum()
                r = pd.to_numeric(df["Return"], errors='coerce').sum()
                return int(o), int(d), int(r)

            c_ord, c_dis, c_ret = sum_cols(df_curr)
            p_ord, p_dis, p_ret = sum_cols(df_prev)

            k1, k2, k3 = st.columns(3)
            def get_delta(curr, prev):
                if selected_period == "All Time": return None
                diff = curr - prev
                if prev == 0: return f"{diff}"
                pct = round((diff / prev) * 100, 1)
                return f"{diff} ({pct}%)"

            with k1: st.metric("Total Orders", c_ord, delta=get_delta(c_ord, p_ord))
            with k2: st.metric("Total Dispatched", c_dis, delta=get_delta(c_dis, p_dis))
            with k3: st.metric("Total Returns", c_ret, delta=get_delta(c_ret, p_ret), delta_color="inverse")

        st.divider()

        st.subheader("📈 Visual Trends")
        if not data.empty:
            df_viz = data.copy()
            df_viz["Date"] = pd.to_datetime(df_viz["Date"], errors='coerce')
            df_viz["Today's Order"] = pd.to_numeric(df_viz["Today's Order"], errors='coerce').fillna(0)
            today = date.today()
            default_start = today - timedelta(days=10)
            c_range, _ = st.columns([1, 2])
            with c_range: date_range = st.date_input("Chart Date Range", value=(default_start, today), key="viz_range")

            if isinstance(date_range, tuple) and len(date_range) == 2:
                start_d, end_d = date_range
                mask_viz = (df_viz["Date"].dt.date >= start_d) & (df_viz["Date"].dt.date <= end_d)
                df_viz_filtered = df_viz[mask_viz]
                g_col, p_col = st.columns([2, 1])
                with g_col:
                    if not df_viz_filtered.empty:
                        daily_trend = df_viz_filtered.groupby("Date")["Today's Order"].sum().reset_index()
                        fig_line = px.line(daily_trend, x="Date", y="Today's Order", title="Order Trend", markers=True)
                        fig_line.update_traces(line_color='#FF4B4B', line_width=3)
                        st.plotly_chart(fig_line, use_container_width=True)
                    else: st.info("No data for charts")
                with p_col:
                    if not df_viz_filtered.empty and "Channel Name" in df_viz_filtered.columns:
                        channel_dist = df_viz_filtered.groupby("Channel Name")["Today's Order"].sum().reset_index()
                        fig_pie = px.pie(channel_dist, values="Today's Order", names="Channel Name", title="Channel Share", hole=0.4)
                        st.plotly_chart(fig_pie, use_container_width=True)

        st.divider()

        st.write("### 📋 Detailed Logs")
        if df_curr.empty:
            display_df = pd.DataFrame(columns=data.columns).drop(columns=["dt"], errors="ignore") if not data.empty else pd.DataFrame()
        else:
            display_df = df_curr.drop(columns=["dt"], errors="ignore")

        is_editable = (st.session_state["role"] == "Ecommerce")
        if is_editable:
            edited_df = st.data_editor(display_df, use_container_width=True, num_rows="fixed", key="eco_editor", disabled=["_original_idx"])
            clean_view = display_df.drop(columns=["_original_idx"], errors='ignore')
            clean_edited = edited_df.drop(columns=["_original_idx"], errors='ignore')
            if not clean_view.equals(clean_edited):
                if st.button("💾 Save Table Changes"): save_smart_update(data, edited_df, worksheet_name)
            
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
                        if not channel: st.warning("Channel Name Required")
                        else:
                            new_row = pd.DataFrame([{"Date": str(date_val), "Channel Name": channel, "Today's Order": orders, "Today's Dispatch": dispatch, "Return": ret}])
                            save_new_row(data, new_row, worksheet_name)
        else:
            st.info("ℹ️ Read-Only View (Admin Access)")
            st.dataframe(display_df.drop(columns=["_original_idx"], errors='ignore'), use_container_width=True)
        return

    # ===============================================================
    # C. STANDARD LOGIC (Production, Packing)
    # ===============================================================
    
    # Header & Refresh
    c_title, c_ref = st.columns([8, 1])
    with c_title: st.subheader(f"📂 {tab_name} Dashboard")
    with c_ref:
        if st.button("🔄", key=f"ref_{worksheet_name}"):
            st.cache_data.clear()
            st.rerun()

    if "Ready Qty" not in data.columns: data["Ready Qty"] = 0
    if "Status" not in data.columns: data["Status"] = "Pending"
    
    if worksheet_name == "Packing":
        if "Party Name" not in data.columns: data["Party Name"] = ""
        desired_order = ["Date", "Order Date", "Order Priority", "Item Name", "Party Name", "Qty", "Logo", "Bottom Print", "Box", "Remarks", "Ready Qty", "Status"]
        current_cols = data.columns.tolist()
        final_order = [c for c in desired_order if c in current_cols] + [c for c in current_cols if c not in desired_order]
        data = data[final_order]

    data["Status"] = data["Status"].fillna("Pending").replace("", "Pending")

    # Filters
    unique_items = sorted(data["Item Name"].astype(str).unique().tolist()) if "Item Name" in data.columns else []
    unique_parties = sorted(data["Party Name"].astype(str).unique().tolist()) if "Party Name" in data.columns else []

    c1, c2, c3 = st.columns(3)
    with c1: date_filter = st.selectbox("📅 Date Range", ["All", "Today", "Yesterday", "Prev 7 Days", "Prev 15 Days", "Prev 30 Days", "Prev All"], index=0, key=f"d_{worksheet_name}")
    with c2: item_filter = st.multiselect("📦 Item Name", options=unique_items, key=f"i_{worksheet_name}")
    with c3: party_filter = st.multiselect("busts_in_silhouette: Party Name", options=unique_parties, key=f"p_{worksheet_name}") if unique_parties else []

    filtered_data = filter_by_date(data, date_filter)
    if item_filter: filtered_data = filtered_data[filtered_data["Item Name"].isin(item_filter)]
    if party_filter and "Party Name" in filtered_data.columns: filtered_data = filtered_data[filtered_data["Party Name"].isin(party_filter)]

    if not filtered_data.empty:
        active_mask = filtered_data["Status"] != "Complete"
        df_active = filtered_data[active_mask].copy()
        df_comp = filtered_data[~active_mask].copy()
    else:
        df_active, df_comp = pd.DataFrame(), pd.DataFrame()

    all_columns = [c for c in data.columns if c != "_original_idx"]
    if st.session_state["role"] == "Admin": disabled_cols = ["_original_idx"]
    else: disabled_cols = [c for c in all_columns if c not in ["Ready Qty", "Status"]] + ["_original_idx"]

    st.write("### 🚀 Active Tasks")
    edited_active = st.data_editor(
        df_active,
        disabled=disabled_cols,
        column_config={"Status": st.column_config.SelectboxColumn("Status", options=["Pending", "Next Day", "Complete"], required=True), "_original_idx": None},
        use_container_width=True,
        num_rows="dynamic" if st.session_state["role"] == "Admin" else "fixed",
        key=f"act_{worksheet_name}"
    )

    clean_active = df_active.drop(columns=["_original_idx"], errors='ignore')
    clean_edited = edited_active.drop(columns=["_original_idx"], errors='ignore')

    if not clean_active.equals(clean_edited):
        if st.button(f"💾 Save {tab_name} Changes", key=f"sv_{worksheet_name}"):
            save_smart_update(data, edited_active, worksheet_name)

    st.divider()
    with st.expander("✅ Completed History (Read Only)"):
        st.dataframe(df_comp.drop(columns=["_original_idx"], errors='ignore'), use_container_width=True)

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
    sel = st.selectbox("Navigate to:", st.session_state["access"])
    st.divider()

    if sel == "Configuration":
        st.header("⚙️ Configuration")
        st.info("Admin Area: Add future settings here.")
    else:
        manage_tab(sel, sel)
