import streamlit as st
from streamlit_gsheets import GSheetsConnection
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
from datetime import date, timedelta, datetime
import math
import numpy as np

# ------------------------------------------------------------------
# 1. PAGE CONFIGURATION
# ------------------------------------------------------------------
st.set_page_config(
    page_title="Amavik ERP", 
    layout="wide", 
    page_icon="🏭",
    initial_sidebar_state="collapsed" # Collapsed for login view
)

# ------------------------------------------------------------------
# 2. UI/UX STYLING (GXON Analytics + AdminUX Theme)
# ------------------------------------------------------------------
st.markdown("""
<style>
    /* IMPORT FONTS */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

    /* GLOBAL RESET & FONTS */
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
        color: #2a3547;
    }

    /* APP BACKGROUND */
    .stApp {
        background-color: #F4F7FE; /* GXON Light Dashboard BG */
    }

    /* ======================================= */
    /* LOGIN PAGE SPECIFIC STYLES              */
    /* ======================================= */
    .login-header {
        font-size: 2rem;
        font-weight: 700;
        color: #111C43;
        margin-bottom: 0.5rem;
    }
    .login-sub {
        color: #7C8FAC;
        font-size: 1rem;
        margin-bottom: 2rem;
    }

    /* ======================================= */
    /* SIDEBAR STYLING (Light/Dark/Orange/Blue) */
    /* ======================================= */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #EAEFF4;
    }
    
    /* Sidebar Text */
    section[data-testid="stSidebar"] * {
        color: #111C43 !important; /* Dark Navy Text */
    }

    /* NAV BUTTONS */
    div[data-testid="stSidebar"] div.stRadio > div[role="radiogroup"] > label {
        background-color: #F8F9FA;
        border: 1px solid #EFF3F8;
        padding: 12px 20px;
        margin-bottom: 6px;
        color: #5A6A85 !important;
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.2s ease-in-out;
    }

    /* HOVER: Deep Blue */
    div[data-testid="stSidebar"] div.stRadio > div[role="radiogroup"] > label:hover {
        background-color: #111C43 !important;
        color: #FFFFFF !important;
        border-color: #111C43;
    }

    /* ACTIVE: Orange */
    div[data-testid="stSidebar"] div.stRadio > div[role="radiogroup"] > label[data-checked="true"] {
        background-color: #FF8C00 !important; /* Orange */
        color: white !important;
        border-color: #FF8C00;
        font-weight: 600;
        box-shadow: 0 4px 10px rgba(255, 140, 0, 0.25);
    }
    
    /* Hide Radio Circles */
    div[data-testid="stSidebar"] div.stRadio div[role="radiogroup"] label div:first-child {
        display: none !important;
    }

    /* ======================================= */
    /* CARDS (White, Soft Shadow, Rounded)     */
    /* ======================================= */
    /* Applies to st.container(border=True) */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF !important;
        border: none !important;
        border-radius: 12px !important;
        /* Exact shadow from reference */
        box-shadow: 0px 9px 20px rgba(46, 35, 94, 0.07) !important;
        padding: 24px !important;
        margin-bottom: 20px;
    }

    /* Prevent double shadow on nested cards */
    div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stVerticalBlockBorderWrapper"] {
        box-shadow: none !important;
        background-color: #F9F9FC !important;
        border: 1px solid #EFF3F8 !important;
    }

    /* METRICS */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        padding: 10px;
        border-radius: 10px;
    }
    div[data-testid="stMetricLabel"] { font-size: 0.85rem; color: #7C8FAC; }
    div[data-testid="stMetricValue"] { font-size: 1.8rem; color: #2A3547; font-weight: 700; }

    /* ======================================= */
    /* TABLES & SEARCH BAR                     */
    /* ======================================= */
    
    /* Custom Search Bar */
    .stTextInput input {
        border-radius: 50px !important;
        border: 1px solid #DFE5EF;
        padding: 8px 20px;
        font-size: 0.9rem;
        background-color: #fff;
    }
    .stTextInput input:focus {
        border-color: #5D87FF;
        box-shadow: 0 0 0 3px rgba(93, 135, 255, 0.1);
    }
    
    /* PAGINATION BUTTONS */
    .pagination-btn button {
        background-color: #ffffff !important;
        color: #5A6A85 !important;
        border: 1px solid #DFE5EF !important;
        border-radius: 6px !important;
        height: 2em !important;
        font-size: 0.8rem !important;
        padding: 0px 10px !important;
        box-shadow: none !important;
    }
    .pagination-btn button:hover {
        background-color: #F4F7FE !important;
        border-color: #5D87FF !important;
        color: #5D87FF !important;
    }

    /* ======================================= */
    /* COMPONENTS                              */
    /* ======================================= */

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
        border-bottom: 1px solid #EAEFF4;
        padding-bottom: 0px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        background-color: transparent;
        border: none;
        color: #5A6A85;
        font-weight: 600;
        font-size: 0.95rem;
        border-bottom: 3px solid transparent;
        border-radius: 0;
        padding: 0 5px;
    }
    
    .stTabs [aria-selected="true"] {
        color: #5D87FF !important;
        border-bottom: 3px solid #5D87FF !important;
        background-color: transparent !important;
        box-shadow: none !important;
    }

    /* Buttons */
    .stButton button {
        background-color: #5D87FF;
        color: white;
        border-radius: 8px;
        font-weight: 600;
        border: none;
        height: 2.6em;
        box-shadow: 0 4px 14px 0 rgba(93, 135, 255, 0.39);
        transition: 0.2s;
    }
    .stButton button:hover {
        background-color: #4570EA;
        color: white;
    }

    /* Headings */
    h1, h2, h3, h4 { color: #2A3547 !important; font-weight: 700; }
    
    /* MOBILE OPTIMIZATIONS */
    @media (max-width: 768px) {
        div[data-testid="column"] {
            width: 50% !important;
            flex: 0 0 50% !important;
            min-width: 50% !important;
        }
        /* FIXED SLIDING TABS WITH SPACING */
        .stTabs [data-baseweb="tab-list"] {
            display: flex !important;
            flex-wrap: nowrap !important;
            overflow-x: auto !important;
            white-space: nowrap !important;
            gap: 20px !important;  
            padding-bottom: 5px; 
            padding-left: 5px;
            scrollbar-width: none; 
            -ms-overflow-style: none;
        }
        .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar { display: none; }
        
        .stTabs [data-baseweb="tab"] {
            flex: 0 0 auto !important;
            width: auto !important;
            font-size: 0.8rem;
            padding: 5px 15px;
        }
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

if st.session_state["logged_in"] and st.session_state["user"] in USERS:
    st.session_state["access"] = USERS[st.session_state["user"]]["access"]

def login():
    # Split Layout for Login (Image Left | Form Right)
    c1, c2 = st.columns([1.5, 1])
    
    with c1:
        # Placeholder for a professional ERP/Analytics image
        st.image("https://img.freepik.com/free-vector/data-extraction-concept-illustration_114360-4876.jpg", use_container_width=True)
    
    with c2:
        st.markdown("<div style='margin-top: 50px;'></div>", unsafe_allow_html=True)
        st.markdown('<p class="login-header">Welcome to Amavik ERP</p>', unsafe_allow_html=True)
        st.markdown('<p class="login-sub">Please sign-in to your account to continue</p>', unsafe_allow_html=True)
        
        username = st.text_input("User ID", placeholder="Enter your ID")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        
        st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
        
        if st.button("Sign In", type="primary", use_container_width=True):
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
    except: return 0

def safe_float(val):
    try:
        return float(pd.to_numeric(val, errors='coerce') or 0.0)
    except: return 0.0

# 🧠 SMART FORMATTING: Int if whole, else 1 decimal
def smart_format(val):
    try:
        num = float(val)
        if num.is_integer():
            return int(num)
        return round(num, 1) # Max 1 decimal
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
    except Exception as e: st.error(f"Error saving data: {e}")

def save_new_row(original_data, new_row_df, sheet_name):
    try:
        original_clean = original_data.drop(columns=["_original_idx"], errors='ignore')
        updated = pd.concat([original_clean, new_row_df], ignore_index=True)
        conn.update(spreadsheet=SHEET_URL, worksheet=sheet_name, data=updated)
        st.toast("✅ Entry Added!", icon="➕")
        st.cache_data.clear()
        time.sleep(1)
        st.rerun()
    except Exception as e: st.error(f"Error adding row: {e}")

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
    except Exception as e: st.error(f"Error deleting: {e}")

# ------------------------------------------------------------------
# 7. VISUALIZATION & TABLE HELPERS (NEW GRAPH LIBRARY)
# ------------------------------------------------------------------
def create_spline_chart(df, x_col, y_col, color_col=None):
    """Creates a Modern Spline Area Chart using Plotly GO"""
    fig = go.Figure()
    
    # Modern Color Palette
    colors = ['#5D87FF', '#49BEFF', '#FFB624', '#FF4B4B']
    
    if color_col:
        unique_groups = df[color_col].unique()
        for i, group in enumerate(unique_groups):
            group_df = df[df[color_col] == group]
            fig.add_trace(go.Scatter(
                x=group_df[x_col], 
                y=group_df[y_col],
                mode='lines+markers',
                name=group,
                line=dict(width=3, shape='spline', color=colors[i % len(colors)]),
                fill='tozeroy',
                # Create a semi-transparent color for the fill
                fillcolor=f"rgba{tuple(list(int(colors[i%len(colors)][1:][j:j+2], 16) for j in (0, 2, 4)) + [0.1])}"
            ))
    else:
        fig.add_trace(go.Scatter(
            x=df[x_col], 
            y=df[y_col],
            mode='lines+markers',
            line=dict(width=3, shape='spline', color='#5D87FF'),
            fill='tozeroy',
            fillcolor='rgba(93, 135, 255, 0.1)'
        ))

    fig.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family="Plus Jakarta Sans", size=12, color="#2A3547"),
        margin=dict(l=20, r=20, t=20, b=40),
        xaxis=dict(showgrid=False, zeroline=False),
        yaxis=dict(showgrid=True, gridcolor='#EAEFF4', zeroline=False),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5)
    )
    return fig

def create_donut_chart(df, values, names):
    """Creates a Modern Donut Chart"""
    fig = px.pie(df, values=values, names=names, hole=0.7)
    fig.update_traces(textposition='outside', textinfo='percent+label', marker=dict(colors=['#5D87FF', '#49BEFF', '#FFB624', '#13DEB9']))
    fig.update_layout(
        showlegend=True,
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family="Plus Jakarta Sans", size=12, color="#2A3547"),
        margin=dict(l=20, r=20, t=20, b=50),
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5)
    )
    return fig

def color_status(val):
    """Pandas Styler function for Status Pills."""
    if not isinstance(val, str): return ''
    val = val.lower()
    if 'complete' in val or 'confirmed' in val:
        return 'background-color: #E6FFFA; color: #13DEB9; font-weight: 600; padding: 4px 10px; border-radius: 20px;'
    elif 'pending' in val:
        return 'background-color: #FEF5E5; color: #FFAE1F; font-weight: 600; padding: 4px 10px; border-radius: 20px;'
    elif 'ship' in val or 'dispatch' in val:
        return 'background-color: #EBF3FE; color: #5D87FF; font-weight: 600; padding: 4px 10px; border-radius: 20px;'
    return ''

def render_styled_table(df, key_prefix, editable=False, decimal_format=None):
    """
    Renders a dataframe with Pagination (10 rows/page) and Search.
    decimal_format: String like "%.1f" to force decimals (used for Store)
    """
    if df.empty:
        st.info("No data available.")
        return None

    # --- 1. SEARCH & FILTER ---
    c_title, c_search = st.columns([3, 1])
    with c_title: st.markdown("##### 📋 Entries")
    with c_search: 
        search_query = st.text_input("Search", placeholder="Search...", key=f"search_{key_prefix}", label_visibility="collapsed")

    df_filtered = df.copy()
    if search_query:
        mask = df_filtered.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
        df_filtered = df_filtered[mask]
        # Reset pagination on search
        if f"page_{key_prefix}" in st.session_state:
             st.session_state[f"page_{key_prefix}"] = 0

    if df_filtered.empty:
        st.warning("No matching records found.")
        return None

    # --- 2. PAGINATION LOGIC ---
    ITEMS_PER_PAGE = 10
    total_rows = len(df_filtered)
    total_pages = max(1, math.ceil(total_rows / ITEMS_PER_PAGE))
    
    if f"page_{key_prefix}" not in st.session_state:
        st.session_state[f"page_{key_prefix}"] = 0
    
    if st.session_state[f"page_{key_prefix}"] >= total_pages:
        st.session_state[f"page_{key_prefix}"] = max(0, total_pages - 1)
        
    current_page = st.session_state[f"page_{key_prefix}"]
    
    start_idx = current_page * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    df_page = df_filtered.iloc[start_idx:end_idx]

    # --- 3. COLUMN CONFIGURATION ---
    st_config = {}
    status_col = next((c for c in df_page.columns if "Status" in c), None)
    
    date_cols = [c for c in df_page.columns if "Date" in c]
    for dc in date_cols:
        st_config[dc] = st.column_config.DateColumn(dc, format="YYYY-MM-DD")
    
    if decimal_format:
        num_cols = df_page.select_dtypes(include=['float', 'int']).columns
        for nc in num_cols:
             st_config[nc] = st.column_config.NumberColumn(nc, format=decimal_format)

    # --- 4. RENDER TABLE ---
    result = None
    if not editable:
        styled_df = df_page.style.map(color_status, subset=[status_col] if status_col else [])
        st.dataframe(
            styled_df,
            use_container_width=True,
            column_config=st_config,
            hide_index=True 
        )
    else:
        if status_col:
            st_config[status_col] = st.column_config.SelectboxColumn(
                "Status",
                options=["Pending", "Complete", "Next Day", "Shipped", "Confirmed"],
                required=True,
                width="medium"
            )
        
        result = st.data_editor(
            df_page,
            use_container_width=True,
            column_config=st_config,
            num_rows="fixed",
            key=f"editor_{key_prefix}_{current_page}",
            hide_index=True,
            disabled=["_original_idx"]
        )

    # --- 5. PAGINATION CONTROLS (Arrows) ---
    st.markdown("---")
    c_info, c_prev, c_page, c_next = st.columns([6, 1, 2, 1])
    
    with c_info:
        st.caption(f"Showing {start_idx + 1} to {min(end_idx, total_rows)} of {total_rows} entries")
    
    with c_prev:
        if st.button("◀", key=f"prev_{key_prefix}", disabled=(current_page == 0)):
            st.session_state[f"page_{key_prefix}"] -= 1
            st.rerun()
            
    with c_page:
        st.markdown(f"<div style='text-align:center; padding-top:5px; font-weight:500; color:#5A6A85;'>Page {current_page + 1} of {total_pages}</div>", unsafe_allow_html=True)
        
    with c_next:
        if st.button("▶", key=f"next_{key_prefix}", disabled=(current_page >= total_pages - 1)):
            st.session_state[f"page_{key_prefix}"] += 1
            st.rerun()

    # CSS for circular arrow buttons
    st.markdown("""
    <script>
        var buttons = window.parent.document.querySelectorAll('button[kind="secondary"]');
        buttons.forEach(btn => {
            if(btn.innerText === "◀" || btn.innerText === "▶") {
                btn.classList.add("pagination-btn");
            }
        });
    </script>
    """, unsafe_allow_html=True)

    return result

# ------------------------------------------------------------------
# 8. COMPONENT LOGIC
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
                # NO DELETE BUTTON

                if worksheet_name == "Packing":
                    party_name = str(row.get('Party Name', '')).upper()
                    st.markdown(f"<h4 style='margin:0; padding:0; color:#111C43;'>{party_name}</h4>", unsafe_allow_html=True)
                    st.markdown(f"<p style='color:#5A6A85; font-size:0.9rem; margin-top:2px;'>{row.get('Item Name', 'Item')}</p>", unsafe_allow_html=True)
                    
                    qty_val = smart_format(row.get('Qty'))
                    ready_val = smart_format(row.get('Ready Qty'))
                    st.markdown(f"<div style='display:flex; justify-content:space-between; margin-top:10px;'><div><small>Target</small><h5>{qty_val}</h5></div><div><small>Ready</small><h5>{ready_val}</h5></div></div>", unsafe_allow_html=True)

                    details = []
                    if row.get('Logo'): details.append(str(row.get('Logo')))
                    if row.get('Bottom Print'): details.append(str(row.get('Bottom Print')))
                    if row.get('Box'): details.append(str(row.get('Box')))
                    
                    if details:
                        st.markdown(f"<div style='background-color:#F4F7FE; padding:6px 10px; border-radius:6px; font-size:0.75rem; color:#5D87FF; font-weight:600; text-align:center; margin-top:10px;'>{' | '.join(details)}</div>", unsafe_allow_html=True)
                else: 
                    st.markdown(f"#### {row.get('Item Name', '')}")
                    qty_val = smart_format(row.get('Quantity'))
                    ready_val = smart_format(row.get('Ready Qty'))
                    st.markdown(f"<div style='display:flex; justify-content:space-between; margin-top:10px;'><div><small>Target</small><h5>{qty_val}</h5></div><div><small>Ready</small><h5>{ready_val}</h5></div></div>", unsafe_allow_html=True)
                    
                    rem_key = "Notes"
                    if row.get(rem_key): st.info(f"{row[rem_key]}")

                btn_label = "✏️ Edit" if st.session_state["role"] == "Admin" else "✅ Update"
                if st.button(btn_label, key=f"btn_{worksheet_name}_{index}", use_container_width=True):
                    st.session_state["edit_idx"] = index
                    st.rerun()

def render_edit_form(edit_idx, data, worksheet_name, date_col):
    if edit_idx in data.index:
        row_data = data.loc[edit_idx]
        with st.container(border=True):
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
                        new_logo = st.selectbox("Logo", ["W/O Logo", "Laser", "Pad"], index=0)
                        new_bot = st.selectbox("Bottom", ["No", "Laser", "Pad"], index=0)

                    st.divider()
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
                if st.form_submit_button("🚀 Assign"):
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
                
                if st.form_submit_button("🚀 Assign"):
                    if not n_item: st.warning("Item Name Required")
                    else:
                        new_task = pd.DataFrame([{
                            "Date": str(date.today()), "Order Date": str(n_date), "Order Priority": n_prio, "Item Name": n_item, "Party Name": n_party, "Qty": n_qty, "Logo": n_logo, "Bottom Print": n_bot, "Box": n_box, "Remarks": n_rem, "Ready Qty": 0, "Status": "Pending"
                        }])
                        save_new_row(data, new_task, worksheet_name)
        inject_enter_key_navigation()

# ------------------------------------------------------------------
# 9. MAIN LOGIC: MANAGE TAB
# ------------------------------------------------------------------
def manage_tab(tab_name, worksheet_name):
    df_curr, df_display = pd.DataFrame(), pd.DataFrame()
    try:
        data = conn.read(spreadsheet=SHEET_URL, worksheet=worksheet_name, ttl=0)
        if data is None or data.empty: data = pd.DataFrame()
    except: data = pd.DataFrame()

    if not data.empty: data['_original_idx'] = data.index

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

        if "Item Name" not in data.columns: data["Item Name"] = ""
        if "Party Name" not in data.columns: data["Party Name"] = ""
        if "Qty" not in data.columns: data["Qty"] = 0
        if "Transaction Type" not in data.columns: data["Transaction Type"] = "Order Received"

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
                    if st.form_submit_button("✅ Submit"):
                        if not party or not item: st.warning("Party Name and Item Name are required")
                        else:
                            new_order = pd.DataFrame([{"Date": str(date_val), "Transaction Type": trans_type, "Party Name": party, "Item Name": item, "Qty": qty, "Remarks": rem}])
                            save_new_row(data, new_order, worksheet_name)
                    inject_enter_key_navigation()

            if not data.empty:
                # Apply smart formatting
                for col in data.select_dtypes(include=['float', 'int']).columns:
                     data[col] = data[col].apply(smart_format)
                     
                if "Date" in data.columns: data["Date"] = pd.to_datetime(data["Date"], errors='coerce')
                
                edited = render_styled_table(data, "order", editable=True)
                if edited is not None:
                    clean_view = data.drop(columns=["_original_idx"], errors='ignore')
                    clean_edited = edited.drop(columns=["_original_idx"], errors='ignore')
                    if not clean_view.equals(clean_edited):
                        if st.button("💾 Save Log Changes", key="save_ord_log"): save_smart_update(data, edited, worksheet_name)
            else: st.info("No records found.")

        with tab_summ:
            c_view, c_search = st.columns([1, 2])
            with c_view:
                view_mode = st.radio("📊 View Mode", ["Party-wise Summary", "Item-wise Summary", "Matrix View"], horizontal=True, label_visibility="collapsed")
            with c_search:
                search_q = st.text_input("🔍 Search Filter", placeholder="Filter...", label_visibility="collapsed")

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
                    
                    for c in ["Order Received", "Dispatch", "Pending Balance"]: 
                        base_pivot[c] = base_pivot[c].apply(smart_format)

                    if view_mode == "Matrix View":
                        matrix = base_pivot.pivot_table(index="Item Name", columns="Party Name", values="Pending Balance", aggfunc="sum", fill_value=0, margins=True, margins_name="Total")
                        st.dataframe(matrix.style.highlight_between(left=1, right=1000000, color="#ffcdd2"), use_container_width=True)
                    elif view_mode == "Party-wise Summary":
                        render_styled_table(base_pivot.sort_values(by="Party Name"), "summ_party")
                    else:
                        render_styled_table(base_pivot.sort_values(by="Item Name"), "summ_item")
                else: st.warning("No data matches your search.")
            else: st.info("No Order data available.")
        return 

    # ===============================================================
    # B. PRODUCTION & PACKING (4 TABS REDESIGN)
    # ===============================================================
    if worksheet_name in ["Packing", "Production"]:
        c_head, c_btn = st.columns([6, 1])
        with c_head: st.subheader(f"📦 {worksheet_name} Dashboard")
        with c_btn:
            if st.button("🔄", key=f"ref_{worksheet_name}"):
                st.cache_data.clear()
                st.rerun()

        # Init Data
        if "Status" not in data.columns: data["Status"] = "Pending"
        data["Status"] = data["Status"].fillna("Pending").replace("", "Pending")
        
        if worksheet_name == "Production":
            date_col, prio_col = "Date", "Priority"
            for c in ["Date", "Priority", "Quantity", "Item Name", "Ready Qty", "Notes"]:
                if c not in data.columns: data[c] = ""
        else:
            date_col, prio_col = "Order Date", "Order Priority"
            for c in ["Order Date", "Order Priority", "Qty", "Party Name", "Item Name", "Ready Qty"]:
                if c not in data.columns: data[c] = ""
        
        if date_col in data.columns: data["_dt_obj"] = pd.to_datetime(data[date_col], errors='coerce').dt.date
        else: data["_dt_obj"] = date.today()
        
        # Smart Format Numbers
        data[prio_col] = pd.to_numeric(data[prio_col], errors='coerce').fillna(999)
        qty_key = "Quantity" if worksheet_name == "Production" else "Qty"
        if qty_key in data.columns: data[qty_key] = data[qty_key].apply(smart_format)
        if "Ready Qty" in data.columns: data["Ready Qty"] = data["Ready Qty"].apply(smart_format)

        # IF EDITING, SHOW FORM ONLY
        if st.session_state["edit_idx"] is not None:
            render_edit_form(st.session_state["edit_idx"], data, worksheet_name, date_col)
            return

        # ROLE BASED TABS
        if st.session_state["role"] == "Admin":
            tabs = st.tabs(["➕ Create Task", "📌 Pending (Cards)", "📅 Upcoming", "🗂️ All Tasks"])
            t_create, t_pending, t_upcoming, t_all = tabs[0], tabs[1], tabs[2], tabs[3]
        else:
            tabs = st.tabs(["📌 Pending (Cards)", "📅 Upcoming"])
            t_create, t_all = None, None
            t_pending, t_upcoming = tabs[0], tabs[1]

        # 1. CREATE TASK
        if t_create:
            with t_create:
                render_add_task_form(data, worksheet_name)

        # 2. PENDING (CARDS)
        with t_pending:
            all_pending = data[data["Status"] != "Complete"].copy().sort_values(by=[prio_col, "_dt_obj"], ascending=[True, True])
            
            backlog = all_pending[all_pending["_dt_obj"] < date.today()]
            today_tasks = all_pending[all_pending["_dt_obj"] == date.today()]
            future_pending = all_pending[all_pending["_dt_obj"] > date.today()]

            if not backlog.empty:
                st.markdown("#### 🔴 Backlog (Previous Days)")
                render_task_cards(backlog, date_col, st.session_state["role"], data, worksheet_name)
                st.markdown("---")
            
            if not today_tasks.empty:
                st.markdown("#### 🟢 Today's Tasks")
                render_task_cards(today_tasks, date_col, st.session_state["role"], data, worksheet_name)
                st.markdown("---")
            
            if not future_pending.empty:
                st.markdown("#### 🔵 Upcoming Pending")
                render_task_cards(future_pending, date_col, st.session_state["role"], data, worksheet_name)
            
            if all_pending.empty:
                st.success("🎉 No pending tasks! All clear.")

        # 3. UPCOMING (TABLE)
        with t_upcoming:
            upcoming_data = data[(data["_dt_obj"] > date.today()) & (data["Status"] != "Complete")].copy()
            render_styled_table(upcoming_data.drop(columns=["_original_idx", "_dt_obj"], errors='ignore'), f"upcoming_{worksheet_name}")

        # 4. ALL TASKS (TABLE)
        if t_all:
            with t_all:
                render_styled_table(data.drop(columns=["_original_idx", "_dt_obj"], errors='ignore'), f"all_{worksheet_name}")

        return

    # ===============================================================
    # C. STORE TAB LOGIC
    # ===============================================================
    if worksheet_name == "Store":
        st.subheader("📦 Store Management")
        for c in ["Item Name", "Qty", "Recvd From", "Type", "Transaction Type", "Invoice No."]:
            if c not in data.columns: data[c] = ""
        
        tab_inv, tab_plan = st.tabs(["📊 Inventory Dashboard", "📅 Packing Planning"])
        
        with tab_inv:
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
                    
                    # Explicit Numeric Conversion
                    df_calc["Qty"] = pd.to_numeric(df_calc["Qty"], errors="coerce").fillna(0).astype(float)
                    
                    stock_summary = df_calc.groupby("Item Name").apply(lambda x: pd.Series({
                        "Type": x["Type"].iloc[0] if not x["Type"].empty else "", 
                        "Inward": x[x["Transaction Type"] == "Inward"]["Qty"].sum(), 
                        "Outward": x[x["Transaction Type"] == "Outward"]["Qty"].sum()
                    })).reset_index()
                    
                    stock_summary["Balance"] = stock_summary["Inward"] - stock_summary["Outward"]
                    render_styled_table(stock_summary.round(1), "stock", decimal_format="%.1f")

            if st.session_state["role"] == "Store":
                st.write("### 📋 Transaction Log")
                if filtered_df.empty: df_display = pd.DataFrame(columns=data.columns).drop(columns=["_original_idx"], errors="ignore")
                else: df_display = filtered_df.copy()
                
                if "Qty" in df_display.columns: df_display["Qty"] = pd.to_numeric(df_display["Qty"], errors='coerce').fillna(0).astype(float).round(1)
                if "Date Of Entry" in df_display.columns: df_display["Date Of Entry"] = pd.to_datetime(df_display["Date Of Entry"], errors='coerce')
                
                edited_df = render_styled_table(df_display, "store_log", editable=True, decimal_format="%.1f")
                if edited_df is not None:
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
            else: st.info("🚫 Restricted")
        
        with tab_plan:
            st.info("ℹ️ Packing Planning")
            try: packing_data = conn.read(spreadsheet=SHEET_URL, worksheet="Packing", ttl=0)
            except: packing_data = pd.DataFrame()
            if not packing_data.empty:
                d_col = "Order Date" if "Order Date" in packing_data.columns else "Date"
                packing_data["dt_obj"] = pd.to_datetime(packing_data[d_col], errors='coerce').dt.date
                mask_plan = (packing_data["dt_obj"] >= (date.today() - timedelta(days=7))) & (packing_data["dt_obj"] <= (date.today() + timedelta(days=5)))
                plan_df = packing_data[mask_plan].copy()
                
                # Deduplicate Party Name logic
                cols = []
                for c in [d_col, "Party Name", "Item Name", "Qty"]:
                    if c in plan_df.columns: cols.append(c)
                
                # Remove duplicates from list if any
                cols_to_show = list(dict.fromkeys(cols))
                
                final_plan = plan_df[cols_to_show].copy()
                if "Qty" in final_plan.columns: 
                    final_plan["Qty"] = pd.to_numeric(final_plan["Qty"], errors='coerce').fillna(0).astype(float).round(1)
                
                render_styled_table(final_plan, "plan", decimal_format="%.1f")
            else: st.info("Empty")
        return

    # ===============================================================
    # D. ECOMMERCE DASHBOARD LOGIC
    # ===============================================================
    if worksheet_name == "Ecommerce":
        st.subheader("📊 Performance Overview")
        df_curr = pd.DataFrame()
        unique_channels = ["All Channels"]
        if "Channel Name" in data.columns:
            channels_list = sorted(data["Channel Name"].astype(str).unique().tolist())
            unique_channels.extend(channels_list)

        c_ch, c_date = st.columns(2)
        with c_ch: selected_channel = st.selectbox("Select Channel", unique_channels, index=0)
        with c_date: selected_period = st.selectbox("Compare Period", ["Today", "Yesterday", "Last 7 Days", "Last 30 Days", "This Month", "All Time"], index=0)

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

            with st.container(border=True):
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
                            fig_line = create_spline_chart(df_viz_filtered, "Date", "Today's Order", "Channel Name")
                            st.plotly_chart(fig_line, use_container_width=True)
                        else: st.info("No data for charts")
                    with p_col:
                        if not df_viz_filtered.empty and "Channel Name" in df_viz_filtered.columns:
                            channel_dist = df_viz_filtered.groupby("Channel Name")["Today's Order"].sum().reset_index()
                            fig_pie = create_donut_chart(channel_dist, "Today's Order", "Channel Name")
                            st.plotly_chart(fig_pie, use_container_width=True)

        st.divider()

        with st.container(border=True):
            st.write("### 📋 Detailed Logs")
            if df_curr.empty:
                display_df = pd.DataFrame(columns=data.columns).drop(columns=["dt"], errors="ignore") if not data.empty else pd.DataFrame()
            else:
                display_df = df_curr.drop(columns=["dt"], errors="ignore")

            is_editable = (st.session_state["role"] == "Ecommerce")
            if is_editable:
                for c in ["Today's Order", "Today's Dispatch", "Return"]:
                    if c in display_df.columns:
                        display_df[c] = pd.to_numeric(display_df[c], errors='coerce').apply(smart_format)

                edited_df = render_styled_table(display_df, "eco_log", editable=True)
                if edited_df is not None:
                    clean_view = display_df.drop(columns=["_original_idx"], errors='ignore')
                    clean_edited = edited_df.drop(columns=["_original_idx"], errors='ignore')
                    if not clean_view.equals(clean_edited):
                        if st.button("💾 Save Table Changes"): save_smart_update(data, edited_df, worksheet_name)
                
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
                render_styled_table(display_df.drop(columns=["_original_idx"], errors='ignore'), "eco_read")
        return

# ------------------------------------------------------------------
# 9. APP ORCHESTRATION
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
