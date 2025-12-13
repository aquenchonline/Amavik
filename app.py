import streamlit as st
from streamlit_gsheets import GSheetsConnection
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import time
from datetime import date, timedelta, datetime

# ------------------------------------------------------------------
# 1. PAGE CONFIGURATION & STYLING
# ------------------------------------------------------------------
st.set_page_config(
    page_title="Amavik ERP", 
    layout="wide", 
    page_icon="🏭",
    initial_sidebar_state="expanded"
)

# ------------------------------------------------------------------
# 2. UI/UX STYLING (AdminUX Inspired - FORCED WHITE CARDS)
# ------------------------------------------------------------------
st.markdown("""
<style>
    /* IMPORT FONT */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* GENERAL APP SETTINGS */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* BACKGROUND COLORS */
    .stApp {
        background-color: #F3F6FD; /* Light Blue-Gray Background */
    }
    
    /* SIDEBAR STYLING */
    section[data-testid="stSidebar"] {
        background-color: #1e293b; /* Deep Slate Navy */
    }
    
    /* Sidebar Text Colors */
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3, 
    section[data-testid="stSidebar"] span, 
    section[data-testid="stSidebar"] p {
        color: #f1f5f9 !important;
    }

    /* NAV BUTTONS (Radio) */
    div[data-testid="stSidebar"] div.stRadio > div[role="radiogroup"] > label {
        background-color: transparent;
        border: none;
        padding: 12px 20px;
        margin-bottom: 4px;
        color: #94a3b8; /* Muted Text */
        transition: all 0.2s;
        border-radius: 6px;
        font-weight: 500;
        cursor: pointer;
    }

    div[data-testid="stSidebar"] div.stRadio > div[role="radiogroup"] > label:hover {
        background-color: rgba(255,255,255,0.05);
        color: #f8fafc;
    }

    div[data-testid="stSidebar"] div.stRadio > div[role="radiogroup"] > label[data-checked="true"] {
        background-color: #3b82f6 !important; /* AdminUX Blue */
        color: white !important;
        font-weight: 600;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }

    /* ============================================================ */
    /* 🚀 FORCE WHITE CARDS - THE FIX IS HERE                      */
    /* ============================================================ */
    
    /* 1. Target st.container(border=True) used in Packing/Production/Charts/Logs */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #ffffff !important;  /* Force Pure White */
        border: 1px solid #e2e8f0 !important;
        border-radius: 10px !important;
        box-shadow: 0 2px 4px 0 rgba(0,0,0,0.05) !important;
        padding: 16px !important;
        margin-bottom: 1rem;
    }

    /* Prevent double shadowing on nested elements */
    div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stVerticalBlockBorderWrapper"] {
        box-shadow: none !important;
        border: 1px solid #f1f5f9 !important;
        background-color: #f8fafc !important; 
    }

    /* 2. Target st.metric used in Ecommerce KPIs to make them White Cards */
    div[data-testid="stMetric"] {
        background-color: #ffffff !important; /* Force Pure White */
        border: 1px solid #e2e8f0 !important;
        border-radius: 10px !important;
        box-shadow: 0 2px 4px 0 rgba(0,0,0,0.05) !important;
        padding: 16px !important;
    }

    /* Force text color inside cards to be dark (readable on white) */
    div[data-testid="stVerticalBlockBorderWrapper"] *,
    div[data-testid="stMetric"] * {
        color: #1e293b; /* Dark Slate */
    }

    /* ============================================================ */

    /* BUTTONS */
    .stButton button {
        border-radius: 6px;
        font-weight: 500;
        height: 2.4em;
    }

    /* TABS */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
        padding-bottom: 10px;
    }

    .stTabs [data-baseweb="tab"] {
        height: 40px;
        white-space: pre-wrap;
        background-color: #ffffff; /* White Tabs */
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        padding: 4px 16px;
        color: #444;
        font-weight: 500;
        font-size: 0.95rem; 
    }

    .stTabs [aria-selected="true"] {
        background-color: #FF4B4B !important;
        color: white !important;
        border: 1px solid #FF4B4B;
        font-weight: 600;
        box-shadow: 0 2px 5px rgba(255, 75, 75, 0.3);
    }

    /* MOBILE ADJUSTMENTS */
    @media (max-width: 768px) {
        .stTabs [data-baseweb="tab-list"] {
            display: flex !important;
            flex-wrap: nowrap !important;   
            overflow-x: auto !important;    
            white-space: nowrap !important;
            gap: 5px !important;
            padding-bottom: 5px; 
            scrollbar-width: none; 
        }
        
        .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar { display: none; }

        .stTabs [data-baseweb="tab"] {
            flex: 0 0 auto !important;      
            width: 31% !important;          
            font-size: 0.7rem !important;
            padding: 4px 2px !important;
            height: 35px !important;
            min-width: auto !important;
            text-align: center;
        }

        /* 2 Cards per Row Logic */
        div[data-testid="column"] {
            width: 50% !important;
            flex: 0 0 50% !important;
            min-width: 50% !important;
        }

        p, .stMarkdown, div[data-testid="stMarkdownContainer"] p {
            font-size: 0.85rem !important;
        }
        
        div[data-testid="stMetricValue"] {
            font-size: 1.2rem !important;
        }
        
        .stButton button {
            font-size: 0.8rem;
            padding: 0 5px;
        }
        
        h1 { font-size: 1.5rem !important; }
        h2 { font-size: 1.3rem !important; }
        h3 { font-size: 1.1rem !important; }
    }
</style>
""", unsafe_allow_html=True)

SHEET_URL = "https://docs.google.com/spreadsheets/d/1S6xS6hcdKSPtzKxCL005GwvNWQNspNffNveI3P9zCgw/edit"

# ------------------------------------------------------------------
# 3. JAVASCRIPT HELPER
# ------------------------------------------------------------------
def inject_enter_key_navigation():
    js = """
    <script>
        var doc = window.parent.document;
        var inputs = doc.querySelectorAll('input, textarea');
        inputs.forEach(function(input, index) {
            input.addEventListener('keydown', function(e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    var next = inputs[index + 1];
                    if (next) { next.focus(); }
                }
            });
        });
    </script>
    """
    components.html(js, height=0, width=0)

# ------------------------------------------------------------------
# 4. USER AUTHENTICATION
# ------------------------------------------------------------------
USERS = {
    "Production": {"pass": "Amavik@80", "role": "Production", "access": ["Production"]},
    "Packing":    {"pass": "Amavik@97", "role": "Packing",    "access": ["Packing"]},
    "Store":      {"pass": "Amavik@17", "role": "Store",      "access": ["Store"]}, 
    "Ecommerce":  {"pass": "Amavik@12", "role": "Ecommerce",  "access": ["Ecommerce", "Order"]},
    "Amar":       {"pass": "Aquench@1933", "role": "Admin",   "access": ["Order", "Production", "Packing", "Store", "Ecommerce", "Configuration"]}
}

# ------------------------------------------------------------------
# 5. SESSION STATE
# ------------------------------------------------------------------
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["user"] = None
    st.session_state["role"] = None

if "edit_idx" not in st.session_state:
    st.session_state["edit_idx"] = None 

# Permission Sync
if st.session_state["logged_in"] and st.session_state["user"] in USERS:
    st.session_state["access"] = USERS[st.session_state["user"]]["access"]

def login():
    st.title("🔒 Amavik ERP")
    st.markdown("### Sign In")
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
    st.session_state["edit_idx"] = None
    st.rerun()

# ------------------------------------------------------------------
# 6. CONNECTION & HELPERS
# ------------------------------------------------------------------
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"🚨 Connection Error: {e}")
    st.stop()

def safe_int(val):
    try:
        num = pd.to_numeric(val, errors='coerce')
        return int(num) if pd.notna(num) else 0
    except:
        return 0

def safe_float(val):
    try:
        return float(pd.to_numeric(val, errors='coerce') or 0.0)
    except:
        return 0.0

def smart_format(val):
    try:
        num = float(val)
        if num.is_integer():
            return int(num)
        return round(num, 2)
    except:
        return 0

def filter_by_date(df, filter_option, date_col_name="Date"):
    if df.empty: return df
    df = df.copy() 
    if date_col_name not in df.columns: return df
    df["temp_date"] = pd.to_datetime(df[date_col_name], errors='coerce').dt.date
    today = date.today()
    mask = pd.Series([False] * len(df))
    if filter_option == "All": return df.drop(columns=["temp_date"], errors='ignore')
    elif filter_option == "Today": mask = df["temp_date"] == today
    elif filter_option == "Yesterday": mask = df["temp_date"] == (today - timedelta(days=1))
    elif filter_option == "Prev 7 Days": mask = (df["temp_date"] >= (today - timedelta(days=7))) & (df["temp_date"] < today)
    elif filter_option == "Prev 15 Days": mask = (df["temp_date"] >= (today - timedelta(days=15))) & (df["temp_date"] < today)
    elif filter_option == "Prev 30 Days": mask = (df["temp_date"] >= (today - timedelta(days=30))) & (df["temp_date"] < today)
    elif filter_option == "Prev All": mask = df["temp_date"] < today
    elif filter_option == "This Month": mask = (df["temp_date"] >= today.replace(day=1)) & (df["temp_date"] <= today)
    return df[mask].drop(columns=["temp_date"], errors='ignore')

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
        st.toast("✅ Saved!", icon="💾")
        st.session_state["edit_idx"] = None
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

def delete_task(original_data, index_to_delete, sheet_name):
    try:
        if index_to_delete in original_data.index:
            updated_data = original_data.drop(index_to_delete)
            final = updated_data.drop(columns=["_original_idx", "_dt_obj", "temp_date", "dt"], errors='ignore')
            conn.update(spreadsheet=SHEET_URL, worksheet=sheet_name, data=final)
            st.toast("🗑️ Task Deleted!", icon="✅")
            st.session_state["edit_idx"] = None
            st.cache_data.clear()
            time.sleep(1)
            st.rerun()
    except Exception as e:
        st.error(f"Error deleting: {e}")

# ------------------------------------------------------------------
# 7. COMPONENT LOGIC
# ------------------------------------------------------------------
def render_task_cards(df_display, date_col, role_name, data, worksheet_name):
    cols = st.columns(4)
    for i, (index, row) in enumerate(df_display.iterrows()):
        col = cols[i % 4]
        with col:
            prio = smart_format(row.get('Priority') if worksheet_name == "Production" else row.get('Order Priority')) or 999
            emoji_prio = "🔴" if prio == 1 else "🟡" if prio == 2 else "🟢"
            
            with st.container(border=True):
                c_head, c_del = st.columns([5, 1])
                with c_head:
                    st.caption(f"{emoji_prio} Priority {prio} | {row.get(date_col, '-')}")
                with c_del:
                    if st.session_state["role"] == "Admin":
                        if st.button("❌", key=f"del_{worksheet_name}_{index}", help="Delete"):
                            delete_task(data, index, worksheet_name)

                if worksheet_name == "Packing":
                    party_name = str(row.get('Party Name', '')).upper()
                    st.markdown(f"#### **{party_name}**")
                    st.markdown(f"**{row.get('Item Name', 'Item')}**")
                    
                    qty_val = smart_format(row.get('Qty'))
                    ready_val = smart_format(row.get('Ready Qty'))
                    st.caption(f"Qty: {qty_val} | Ready: {ready_val}")

                    details = []
                    if row.get('Logo'): details.append(str(row.get('Logo')))
                    if row.get('Bottom Print'): details.append(str(row.get('Bottom Print')))
                    if row.get('Box'): details.append(str(row.get('Box')))
                    
                    if details:
                        st.markdown(f"<div style='background-color:#f0f2f6; padding:4px 8px; border-radius:4px; font-size:0.8rem; color:#444; margin-bottom:8px;'>{' | '.join(details)}</div>", unsafe_allow_html=True)
                else: 
                    st.markdown(f"### **{row.get('Item Name', '')}**")
                    qty_val = smart_format(row.get('Quantity'))
                    ready_val = smart_format(row.get('Ready Qty'))
                    
                    c1, c2 = st.columns(2)
                    with c1: st.write(f"**Target:** {qty_val}")
                    with c2: st.write(f"**Ready:** {ready_val}")
                    
                    rem_key = "Notes"
                    if row.get(rem_key): st.info(f"{row[rem_key]}", icon="📝")

                btn_label = "✏️ Edit" if st.session_state["role"] == "Admin" else "✅ Update"
                if st.button(btn_label, key=f"btn_{worksheet_name}_{index}", use_container_width=True):
                    st.session_state["edit_idx"] = index
                    st.rerun()

def render_edit_form(edit_idx, data, worksheet_name, date_col):
    if edit_idx in data.index:
        row_data = data.loc[edit_idx]
        st.markdown(f"### ✏️ Editing: {row_data.get('Item Name', 'Task')}")
        
        col_qty = "Quantity" if worksheet_name == "Production" else "Qty"
        col_prio = "Priority" if worksheet_name == "Production" else "Order Priority"
        col_rem = "Notes" if worksheet_name == "Production" else "Remarks"

        if st.session_state["role"] == "Admin":
            with st.form(f"admin_{worksheet_name}_edit"):
                c1, c2, c3 = st.columns(3)
                with c1: new_date = st.date_input("Date", pd.to_datetime(row_data.get(date_col, date.today())).date())
                with c2: new_item = st.text_input("Item Name", row_data.get('Item Name', ''))
                with c3: new_qty = st.number_input("Target Qty", value=safe_float(row_data.get(col_qty)), step=0.01)
                
                c4, c5 = st.columns(2)
                with c4: new_prio = st.number_input("Priority", value=int(safe_float(row_data.get(col_prio)) or 1))
                with c5: new_rem = st.text_input("Notes/Remarks", row_data.get(col_rem, ''))

                new_party, new_box, new_logo, new_bot = "", "", "", ""
                if worksheet_name == "Packing":
                    new_party = st.text_input("Party Name", row_data.get('Party Name', ''))
                    new_box = st.text_input("Box", row_data.get('Box', ''))
                    new_logo = st.selectbox("Logo", ["W/O Logo", "Laser", "Pad"], index=["W/O Logo", "Laser", "Pad"].index(row_data.get('Logo', 'W/O Logo')) if row_data.get('Logo') in ["W/O Logo", "Laser", "Pad"] else 0)
                    new_bot = st.selectbox("Bottom", ["No", "Laser", "Pad"], index=["No", "Laser", "Pad"].index(row_data.get('Bottom Print', 'No')) if row_data.get('Bottom Print') in ["No", "Laser", "Pad"] else 0)

                st.markdown("---")
                c6, c7 = st.columns(2)
                with c6: new_ready = st.number_input("Ready Qty", value=safe_float(row_data.get('Ready Qty')), step=0.01)
                with c7: new_status = st.selectbox("Status", ["Pending", "Next Day", "Complete"], index=["Pending", "Next Day", "Complete"].index(row_data.get('Status', 'Pending')))

                if st.form_submit_button("💾 Save Changes"):
                    updated_row = pd.DataFrame([row_data])
                    updated_row.at[edit_idx, date_col] = str(new_date)
                    updated_row.at[edit_idx, "Item Name"] = new_item
                    updated_row.at[edit_idx, col_qty] = new_qty
                    updated_row.at[edit_idx, col_prio] = new_prio
                    updated_row.at[edit_idx, col_rem] = new_rem
                    updated_row.at[edit_idx, "Ready Qty"] = new_ready
                    updated_row.at[edit_idx, "Status"] = new_status
                    
                    if worksheet_name == "Packing":
                        updated_row.at[edit_idx, "Party Name"] = new_party
                        updated_row.at[edit_idx, "Box"] = new_box
                        updated_row.at[edit_idx, "Logo"] = new_logo
                        updated_row.at[edit_idx, "Bottom Print"] = new_bot

                    updated_row["_original_idx"] = edit_idx
                    save_smart_update(data, updated_row, worksheet_name)
        else:
            with st.form(f"user_{worksheet_name}_update"):
                c1, c2 = st.columns(2)
                with c1: new_ready = st.number_input("Ready Qty", value=safe_float(row_data.get('Ready Qty')), step=0.01)
                with c2: new_status = st.selectbox("Status", ["Pending", "Next Day", "Complete"], index=["Pending", "Next Day", "Complete"].index(row_data.get('Status', 'Pending')))
                
                if st.form_submit_button("✅ Update Status"):
                    updated_row = pd.DataFrame([row_data])
                    updated_row.at[edit_idx, "Ready Qty"] = new_ready
                    updated_row.at[edit_idx, "Status"] = new_status
                    updated_row["_original_idx"] = edit_idx
                    save_smart_update(data, updated_row, worksheet_name)
        
        if st.button("❌ Close Edit"):
            st.session_state["edit_idx"] = None
            st.rerun()

def render_add_task_form(data, worksheet_name):
    st.divider()
    with st.expander(f"➕ Assign New {worksheet_name} Task", expanded=False):
        with st.form(f"new_{worksheet_name}_task"):
            if worksheet_name == "Production":
                c1, c2, c3 = st.columns(3)
                with c1: n_date = st.date_input("Date")
                with c2: n_item = st.text_input("Item Name")
                with c3: n_qty = st.number_input("Quantity", min_value=1.0, step=0.01)
                c4, c5 = st.columns(2)
                with c4: n_prio = st.number_input("Priority", min_value=1, value=1)
                with c5: n_note = st.text_input("Notes")

                if st.form_submit_button("🚀 Assign Production Task"):
                    if not n_item: st.warning("Item Name Required")
                    else:
                        new_task = pd.DataFrame([{
                            "Date": str(n_date), "Item Name": n_item, "Quantity": n_qty, "Priority": n_prio, "Ready Qty": 0, "Status": "Pending", "Notes": n_note
                        }])
                        save_new_row(data, new_task, worksheet_name)
            else:
                c1, c2, c3 = st.columns(3)
                with c1: 
                    n_date = st.date_input("Order Date")
                    n_party = st.text_input("Party Name")
                    n_logo = st.selectbox("Logo", ["W/O Logo", "Laser", "Pad"])
                with c2:
                    n_item = st.text_input("Item Name")
                    n_qty = st.number_input("Order Qty", min_value=1.0, step=0.01)
                    n_bot = st.selectbox("Bottom Print", ["No", "Laser", "Pad"])
                with c3:
                    n_prio = st.number_input("Priority", min_value=1, value=1)
                    n_box = st.selectbox("Box", ["Loose", "Brown Box", "White Box", "Box"])
                    n_rem = st.text_input("Remarks")
                
                if st.form_submit_button("🚀 Assign Packing Task"):
                    if not n_item: st.warning("Item Name Required")
                    else:
                        new_task = pd.DataFrame([{
                            "Date": str(date.today()), "Order Date": str(n_date), "Order Priority": n_prio, "Item Name": n_item, "Party Name": n_party, "Qty": n_qty, "Logo": n_logo, "Bottom Print": n_bot, "Box": n_box, "Remarks": n_rem, "Ready Qty": 0, "Status": "Pending"
                        }])
                        save_new_row(data, new_task, worksheet_name)
        inject_enter_key_navigation()

# ------------------------------------------------------------------
# 7. MAIN LOGIC: MANAGE TAB
# ------------------------------------------------------------------
def manage_tab(tab_name, worksheet_name):
    # 🛑 INITIALIZE DATAFRAMES FIRST
    df_curr = pd.DataFrame()
    df_display = pd.DataFrame()

    try:
        data = conn.read(spreadsheet=SHEET_URL, worksheet=worksheet_name, ttl=0)
        if data is None or data.empty: data = pd.DataFrame()
    except:
        data = pd.DataFrame()

    if not data.empty:
        data['_original_idx'] = data.index

    # ===============================================================
    # A. ORDER TAB
    # ===============================================================
    if worksheet_name == "Order":
        c_title, c_ref = st.columns([6, 1])
        with c_title: st.subheader("📑 Orders & Dispatch")
        with c_ref:
            if st.button("🔄", key="ref_order"):
                st.cache_data.clear()
                st.rerun()

        # 🚀 FIX: Ensure required columns exist to prevent KeyError
        if "Item Name" not in data.columns: data["Item Name"] = ""
        if "Party Name" not in data.columns: data["Party Name"] = ""
        if "Qty" not in data.columns: data["Qty"] = 0
        if "Transaction Type" not in data.columns: data["Transaction Type"] = "Order Received"

        # 🚀 RENAMED TABS
        tab_log, tab_summ = st.tabs(["Order", "Summary"])
        
        with tab_log:
            with st.expander("➕ Add New Order / Dispatch", expanded=True):
                with st.form("order_entry_form"):
                    c1, c2, c3 = st.columns(3)
                    with c1: 
                        date_val = st.date_input("Date", value=date.today())
                        trans_type = st.selectbox("Transaction Type", ["Order Received", "Dispatch"])
                    with c2:
                        party = st.text_input("Party Name")
                        qty = st.number_input("Quantity", min_value=1.0, step=0.01)
                    with c3:
                        item = st.text_input("Item Name")
                        rem = st.text_input("Remarks")
                    if st.form_submit_button("✅ Submit Entry"):
                        if not party or not item: st.warning("Party Name and Item Name are required")
                        else:
                            new_order = pd.DataFrame([{"Date": str(date_val), "Transaction Type": trans_type, "Party Name": party, "Item Name": item, "Qty": qty, "Remarks": rem}])
                            save_new_row(data, new_order, worksheet_name)
                    inject_enter_key_navigation()

            st.divider()
            st.write("### 🗂️ Transaction History")
            if not data.empty:
                # Use float for decimals
                if "Qty" in data.columns: 
                    data["Qty"] = pd.to_numeric(data["Qty"], errors='coerce').fillna(0).astype(int)
                if "Date" in data.columns: data["Date"] = pd.to_datetime(data["Date"], errors='coerce')
                
                # Show rounded in editor
                edited_df = st.data_editor(
                    data, 
                    use_container_width=True, 
                    num_rows="fixed", 
                    key="order_editor", 
                    disabled=["_original_idx"], 
                    column_config={
                        "Date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"), 
                        "Qty": st.column_config.NumberColumn("Qty", format="%d"), 
                        "Transaction Type": st.column_config.SelectboxColumn("Type", options=["Order Received", "Dispatch"])
                    }
                )
                
                clean_view = data.drop(columns=["_original_idx"], errors='ignore')
                clean_edited = edited_df.drop(columns=["_original_idx"], errors='ignore')
                if not clean_view.equals(clean_edited):
                    if st.button("💾 Save Log Changes", key="save_ord_log"): save_smart_update(data, edited_df, worksheet_name)
            else: st.info("No records found.")

        with tab_summ:
            st.write("### 🔍 Pending Balance Analysis")
            c_view, c_search = st.columns([1, 2])
            with c_view:
                view_mode = st.radio("📊 View Mode", ["Party-wise Summary", "Item-wise Summary", "Matrix View (Item vs Party)"], horizontal=True, label_visibility="collapsed")
            with c_search:
                search_q = st.text_input("🔍 Search Filter", placeholder="Filter by Item or Party...", label_visibility="collapsed")

            if not data.empty:
                df_sum = data.copy()
                if search_q:
                    mask = (df_sum['Item Name'].astype(str).str.contains(search_q, case=False, na=False) | df_sum['Party Name'].astype(str).str.contains(search_q, case=False, na=False))
                    df_sum = df_sum[mask]

                if not df_sum.empty:
                    base_pivot = df_sum.pivot_table(index=['Party Name', 'Item Name'], columns='Transaction Type', values='Qty', aggfunc='sum', fill_value=0).reset_index()
                    if "Order Received" not in base_pivot.columns: base_pivot["Order Received"] = 0
                    if "Dispatch" not in base_pivot.columns: base_pivot["Dispatch"] = 0
                    base_pivot["Pending Balance"] = base_pivot["Order Received"] - base_pivot["Dispatch"]
                    
                    # Round for display
                    base_pivot = base_pivot.round(2)
                    
                    # Convert to Int for Display
                    cols_to_int = ["Order Received", "Dispatch", "Pending Balance"]
                    for c in cols_to_int:
                        base_pivot[c] = base_pivot[c].astype(int)

                    if view_mode == "Matrix View (Item vs Party)":
                        matrix = base_pivot.pivot_table(index="Item Name", columns="Party Name", values="Pending Balance", aggfunc="sum", fill_value=0, margins=True, margins_name="Total")
                        st.dataframe(matrix.style.highlight_between(left=1, right=1000000, color="#ffcdd2"), use_container_width=True)
                    elif view_mode == "Party-wise Summary":
                        st.dataframe(base_pivot.sort_values(by="Party Name").style.highlight_between(left=1, right=1000000, subset=["Pending Balance"], color="#ffcdd2"), use_container_width=True, column_config={"Pending Balance": st.column_config.NumberColumn("Pending", format="%d")})
                    else:
                        item_pivot = base_pivot.sort_values(by="Item Name")[["Item Name", "Party Name", "Order Received", "Dispatch", "Pending Balance"]]
                        st.dataframe(item_pivot.style.highlight_between(left=1, right=1000000, subset=["Pending Balance"], color="#ffcdd2"), use_container_width=True, column_config={"Pending Balance": st.column_config.NumberColumn("Pending", format="%d")})
                else: st.warning("No data matches your search.")
            else: st.info("No Order data available.")
        return 

    # ===============================================================
    # B. PRODUCTION & PACKING
    # ===============================================================
    if worksheet_name in ["Packing", "Production"]:
        st.subheader(f"📦 {worksheet_name} Tasks")
        
        if "Status" not in data.columns: data["Status"] = "Pending"
        data["Status"] = data["Status"].fillna("Pending").replace("", "Pending")
        
        if worksheet_name == "Production":
            date_col = "Date"
            prio_col = "Priority"
            if "Date" not in data.columns: data["Date"] = str(date.today())
            if "Priority" not in data.columns: data["Priority"] = 999
            if "Quantity" not in data.columns: data["Quantity"] = 0
            if "Item Name" not in data.columns: data["Item Name"] = ""
            if "Ready Qty" not in data.columns: data["Ready Qty"] = 0
            if "Notes" not in data.columns: data["Notes"] = ""
        else:
            date_col = "Order Date" if "Order Date" in data.columns else "Date"
            prio_col = "Order Priority"
            if "Order Priority" not in data.columns: data["Order Priority"] = 999
            if "Qty" not in data.columns: data["Qty"] = 0
            if "Party Name" not in data.columns: data["Party Name"] = ""
            if "Item Name" not in data.columns: data["Item Name"] = ""
            if "Ready Qty" not in data.columns: data["Ready Qty"] = 0

        # Safe date check
        if date_col in data.columns:
             data["_dt_obj"] = pd.to_datetime(data[date_col], errors='coerce').dt.date
        else:
             data["_dt_obj"] = date.today()

        data[prio_col] = pd.to_numeric(data[prio_col], errors='coerce').fillna(999)

        all_pending = data[data["Status"] != "Complete"].copy()
        today = date.today()
        all_pending = all_pending.sort_values(by=[prio_col, "_dt_obj"], ascending=[True, True])
        
        df_today_backlog = all_pending[all_pending["_dt_obj"] <= today].copy()
        df_future = all_pending[all_pending["_dt_obj"] > today].copy()
        
        if not df_today_backlog.empty:
            df_display = df_today_backlog
            st.success(f"📅 **Today's & Backlog Tasks** ({len(df_display)})")
        elif not df_future.empty:
            df_display = df_future
            st.info(f"🚀 Today done! **Upcoming Tasks** ({len(df_display)})")
        else:
            df_display = pd.DataFrame() 
            st.balloons()
            st.success("🎉 All tasks completed!")

        if st.session_state["edit_idx"] is not None:
            render_edit_form(st.session_state["edit_idx"], data, worksheet_name, date_col)
        elif not df_display.empty:
            render_task_cards(df_display, date_col, st.session_state["role"], data, worksheet_name)

        if st.session_state["role"] == "Admin" and st.session_state["edit_idx"] is None:
            render_add_task_form(data, worksheet_name)

        st.divider()
        with st.expander("✅ View Completed History"):
            mask_complete = data["Status"] == "Complete"
            data_hist = data[mask_complete].drop(columns=["_original_idx", "_dt_obj"], errors="ignore")
            # Force Int for History
            for c in ["Qty", "Quantity", "Ready Qty"]:
                if c in data_hist.columns: data_hist[c] = pd.to_numeric(data_hist[c], errors='coerce').fillna(0).astype(int)
            
            st.dataframe(data_hist, use_container_width=True)
        return

    # ===============================================================
    # C. STORE TAB LOGIC
    # ===============================================================
    if worksheet_name == "Store":
        st.subheader("📦 Store Management")

        if "Item Name" not in data.columns: data["Item Name"] = ""
        if "Qty" not in data.columns: data["Qty"] = 0
        if "Recvd From" not in data.columns: data["Recvd From"] = ""
        if "Type" not in data.columns: data["Type"] = ""
        if "Transaction Type" not in data.columns: data["Transaction Type"] = ""
        if "Invoice No." not in data.columns: data["Invoice No."] = ""

        tab_inv, tab_plan = st.tabs(["📊 Inventory Dashboard", "📅 Packing Planning"])

        with tab_inv:
            items_list = sorted(data["Item Name"].astype(str).unique())
            vendor_list = sorted(data["Recvd From"].astype(str).unique())
            type_list = sorted(data["Type"].astype(str).unique())

            c1, c2 = st.columns([1, 3])
            with c1: d_filter = st.selectbox("📅 Date Filter", ["All", "Today", "Yesterday", "Prev 7 Days", "This Month"], key="st_date")
            with c2: search_query = st.text_input("🔍 Universal Search (Item, Party, Type, Inv No.)", placeholder="Type at least 3 digits to search...")

            filtered_df = filter_by_date(data, d_filter, date_col_name="Date Of Entry")
            if search_query and len(search_query) >= 3:
                mask = (
                    filtered_df['Item Name'].astype(str).str.contains(search_query, case=False, na=False) |
                    filtered_df['Recvd From'].astype(str).str.contains(search_query, case=False, na=False) |
                    filtered_df['Type'].astype(str).str.contains(search_query, case=False, na=False) |
                    filtered_df['Transaction Type'].astype(str).str.contains(search_query, case=False, na=False) |
                    filtered_df['Invoice No.'].astype(str).str.contains(search_query, case=False, na=False)
                )
                filtered_df = filtered_df[mask]
                found_items = filtered_df['Item Name'].unique().tolist()
                if found_items: st.caption(f"💡 **Top Suggestions:** {', '.join(found_items[:5])}")
                else: st.warning("No matching items found.")

            st.divider()

            if not filtered_df.empty:
                with st.expander("📊 Live Stock Analysis (Based on Current Search)", expanded=True):
                    df_calc = filtered_df.copy()
                    df_calc["Qty"] = pd.to_numeric(df_calc["Qty"], errors="coerce").fillna(0)
                    stock_summary = []
                    unique_items = df_calc["Item Name"].unique()
                    for item in unique_items:
                        item_data = df_calc[df_calc["Item Name"] == item]
                        inward = item_data[item_data["Transaction Type"] == "Inward"]["Qty"].sum()
                        outward = item_data[item_data["Transaction Type"] == "Outward"]["Qty"].sum()
                        balance = inward - outward
                        last_entry = item_data.iloc[-1]
                        stock_summary.append({"Item Name": item, "Type": last_entry.get("Type",""), "Total Inward": inward, "Total Outward": outward, "Net Change": balance, "UOM": last_entry.get("UOM","")})
                    
                    df_sum_res = pd.DataFrame(stock_summary)
                    if not df_sum_res.empty:
                        # ALLOW DECIMALS IN STORE
                        df_sum_res = df_sum_res.round(2)
                        st.dataframe(df_sum_res.style.highlight_between(left=0.01, right=1000000, subset=["Net Change"], color="#ffcdd2"), use_container_width=True, column_config={"Net Change": st.column_config.NumberColumn("Net Balance")})

            if st.session_state["role"] == "Store":
                st.write("### 📋 Transaction Log")
                if filtered_df.empty: df_display = pd.DataFrame(columns=data.columns).drop(columns=["_original_idx"], errors="ignore")
                else: df_display = filtered_df.copy()

                if "Qty" in df_display.columns: df_display["Qty"] = pd.to_numeric(df_display["Qty"], errors='coerce').fillna(0)
                if "Date Of Entry" in df_display.columns: df_display["Date Of Entry"] = pd.to_datetime(df_display["Date Of Entry"], errors='coerce')

                # Removed format="%d" to allow decimals
                edited_df = st.data_editor(df_display, use_container_width=True, num_rows="fixed", key="store_editor", disabled=["_original_idx"], column_config={"Qty": st.column_config.NumberColumn("Qty"), "Date Of Entry": st.column_config.DateColumn("Date Of Entry", format="YYYY-MM-DD")})

                clean_view = df_display.drop(columns=["_original_idx"], errors='ignore')
                clean_edited = edited_df.drop(columns=["_original_idx"], errors='ignore')
                if not clean_view.equals(clean_edited):
                    if st.button("💾 Save Changes", key="save_store"): save_smart_update(data, edited_df, worksheet_name)

                st.divider()
                with st.expander("➕ Update Stock (Add New Entry)", expanded=True):
                    with st.form("store_form"):
                        c1, c2, c3 = st.columns(3)
                        with c1: date_ent = st.date_input("Date Of Entry", value=date.today())
                        with c2: trans_type = st.selectbox("Transaction Type", ["Inward", "Outward"])
                        with c3: qty = st.number_input("Quantity", min_value=1.0, step=0.01)
                        c4, c5, c6 = st.columns(3)
                        with c4: item_name = st.text_input("Item Name")
                        with c5: uom = st.selectbox("UOM", ["Pcs", "Boxes", "Kg", "Ltr", "Set", "Packet"])
                        with c6: i_type = st.selectbox("Type", ["Inner Box", "Outer Box", "Washer", "String", "Cap", "Bubble", "Bottle", "Other"])
                        c7, c8, c9 = st.columns(3)
                        with c7: recvd_from = st.text_input("Recvd From / Sent To")
                        with c8: vendor_brand = st.text_input("Vendor Name (Brand)")
                        with c9: invoice_no = st.text_input("Invoice No. (Inward Only)")

                        if st.form_submit_button("Submit Transaction"):
                            if not item_name: st.warning("⚠️ Item Name is required!")
                            else:
                                new_entry = pd.DataFrame([{"Date Of Entry": str(date_ent), "Recvd From": recvd_from, "Vendor Name(Brand)": vendor_brand, "Type": i_type, "Item Name": item_name, "Qty": qty, "UOM": uom, "Transaction Type": trans_type, "Invoice No.": invoice_no}])
                                save_new_row(data, new_entry, worksheet_name)
                    inject_enter_key_navigation()
            else:
                st.divider()
                st.info("🚫 **Restricted Area:** Detailed Transaction Logs and Data Entry are only visible to the Store Incharge.")
        
        with tab_plan:
            st.info("ℹ️ Showing Packing Orders for: **Last 7 Days & Next 5 Days**")
            try:
                packing_data = conn.read(spreadsheet=SHEET_URL, worksheet="Packing", ttl=0)
                if packing_data is None or packing_data.empty: packing_data = pd.DataFrame()
            except:
                packing_data = pd.DataFrame()

            if not packing_data.empty:
                d_col = "Order Date" if "Order Date" in packing_data.columns else "Date"
                packing_data["dt_obj"] = pd.to_datetime(packing_data[d_col], errors='coerce').dt.date
                today = date.today()
                mask_plan = (packing_data["dt_obj"] >= (today - timedelta(days=7))) & (packing_data["dt_obj"] <= (today + timedelta(days=5)))
                plan_df = packing_data[mask_plan].copy()
                
                if not plan_df.empty:
                    cols_to_show = []
                    if d_col in plan_df.columns: cols_to_show.append(d_col)
                    if "Party Name" in plan_df.columns: cols_to_show.append("Party Name")
                    if "Item Name" in plan_df.columns: cols_to_show.append("Item Name")
                    if "Qty" in plan_df.columns: cols_to_show.append("Qty")
                    
                    final_plan_view = plan_df[cols_to_show].copy()
                    final_plan_view["Inner Qty Required"] = "Calculate"
                    final_plan_view["Outer Box Required"] = "Calculate"
                    # Round qty in plan view
                    if "Qty" in final_plan_view.columns:
                        final_plan_view["Qty"] = pd.to_numeric(final_plan_view["Qty"], errors='coerce').fillna(0).astype(int)
                    
                    st.dataframe(final_plan_view, use_container_width=True, column_config={d_col: st.column_config.DateColumn("Order Date"), "Qty": st.column_config.NumberColumn("Order Qty", format="%d")})
                else:
                    st.info("No packing orders found in the selected date range.")
            else:
                st.info("Packing Sheet is empty.")

        return # End Store Logic

    # ===============================================================
    # D. ECOMMERCE DASHBOARD LOGIC
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

            # WRAP KPIS IN WHITE CARDS
            k1, k2, k3 = st.columns(3)
            def get_delta(curr, prev):
                if selected_period == "All Time": return None
                diff = curr - prev
                if prev == 0: return f"{diff}"
                pct = round((diff / prev) * 100, 1)
                return f"{diff} ({pct}%)"

            with k1:
                st.metric("Total Orders", c_ord, delta=get_delta(c_ord, p_ord))
            with k2:
                st.metric("Total Dispatched", c_dis, delta=get_delta(c_dis, p_dis))
            with k3:
                st.metric("Total Returns", c_ret, delta=get_delta(c_ret, p_ret), delta_color="inverse")

        st.divider()

        # CHART SECTION (WHITE CARD)
        with st.container(border=True):
            st.markdown("### 📈 Visual Trends")
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
                            daily_trend = df_viz_filtered.groupby(["Date", "Channel Name"])["Today's Order"].sum().reset_index()
                            fig_line = px.line(daily_trend, x="Date", y="Today's Order", color="Channel Name", title="Channel-wise Sales Trend", markers=True)
                            st.plotly_chart(fig_line, use_container_width=True)
                        else: st.info("No data for charts")
                    with p_col:
                        if not df_viz_filtered.empty and "Channel Name" in df_viz_filtered.columns:
                            channel_dist = df_viz_filtered.groupby("Channel Name")["Today's Order"].sum().reset_index()
                            fig_pie = px.pie(channel_dist, values="Today's Order", names="Channel Name", title="Channel Share", hole=0.4)
                            st.plotly_chart(fig_pie, use_container_width=True)

        st.divider()

        # LOGS SECTION (WHITE CARD)
        with st.container(border=True):
            st.write("### 📋 Detailed Logs")
            if df_curr.empty:
                display_df = pd.DataFrame(columns=data.columns).drop(columns=["dt"], errors="ignore") if not data.empty else pd.DataFrame()
            else:
                display_df = df_curr.drop(columns=["dt"], errors="ignore")

            is_editable = (st.session_state["role"] == "Ecommerce")
            if is_editable:
                cols_to_int_ecom = ["Today's Order", "Today's Dispatch", "Return"]
                for c in cols_to_int_ecom:
                    if c in display_df.columns:
                        display_df[c] = pd.to_numeric(display_df[c], errors='coerce').fillna(0).astype(int)

                edited_df = st.data_editor(display_df, use_container_width=True, num_rows="fixed", key="eco_editor", disabled=["_original_idx"], column_config={
                    "Today's Order": st.column_config.NumberColumn("Orders", format="%d"),
                    "Today's Dispatch": st.column_config.NumberColumn("Dispatch", format="%d"),
                    "Return": st.column_config.NumberColumn("Return", format="%d")
                })
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
                            channel = st.selectbox("Channel Name", ["Amazon", "Flipkart", "Meesho", "Ajio", "JioMart", "Myntra", "Aquench.in"])
                            orders = st.number_input("Today's Order", min_value=0)
                        with c2:
                            dispatch = st.number_input("Today's Dispatch", min_value=0)
                            ret = st.number_input("Return", min_value=0)
                        if st.form_submit_button("Add Record"):
                            new_row = pd.DataFrame([{"Date": str(date_val), "Channel Name": channel, "Today's Order": orders, "Today's Dispatch": dispatch, "Return": ret}])
                            save_new_row(data, new_row, worksheet_name)
                        
                        inject_enter_key_navigation()
            else:
                st.info("ℹ️ Read-Only View (Admin Access)")
                st.dataframe(display_df.drop(columns=["_original_idx"], errors='ignore'), use_container_width=True)
        return

# ------------------------------------------------------------------
# 8. APP ORCHESTRATION
# ------------------------------------------------------------------
if not st.session_state["logged_in"]:
    login()
else:
    with st.sidebar:
        st.write(f"👤 **{st.session_state['user']}**")
        st.caption(f"Role: {st.session_state['role']}")
        if st.button("Logout", use_container_width=True): logout()

    c1, c2 = st.columns([1, 1]) # Tight layout
    with c1:
        st.title("🏭 Amavik ERP")
    with c2:
        st.write("") 
        st.write("") 
        if st.button("🔄 Refresh Data", key="global_refresh"):
            st.cache_data.clear()
            st.rerun()

    preferred = ["Order", "Production", "Packing", "Store", "Ecommerce", "Configuration"]
    available_tabs = [t for t in preferred if t in st.session_state["access"]]
    
    if available_tabs:
        tabs = st.tabs(available_tabs)
        for tab, title in zip(tabs, available_tabs):
            with tab:
                if title == "Configuration":
                    st.header("⚙️ System Configuration")
                    st.info("Only Admin can access this area.")
                else:
                    manage_tab(title, title)
    else:
        st.error("No modules assigned to your role.")
