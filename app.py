import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.figure_factory as ff
import json
import os
import re
from typing import Dict, List, Tuple, Any

def parse_markdown_table(text: str) -> pd.DataFrame:
    """Parses a markdown table from the text and returns it as a DataFrame."""
    lines = text.strip().split("\n")
    table_lines = []
    in_table = False
    
    for line in lines:
        if "|" in line:
            # Check if it is a separator line like |---|---|
            if re.match(r"^\s*\|?[\s\-\|:]+\|?\s*$", line):
                in_table = True
                continue
            table_lines.append(line)
            
    if len(table_lines) < 2:
        return None
        
    # Parse headers
    headers = [col.strip() for col in table_lines[0].split("|") if col.strip()]
    rows = []
    
    for line in table_lines[1:]:
        cols = [col.strip() for col in line.split("|")]
        if line.startswith("|"):
            cols = cols[1:]
        if line.endswith("|"):
            cols = cols[:-1]
        cols = [c.strip() for c in cols]
        
        if len(cols) == len(headers):
            rows.append(cols)
            
    if not rows:
        return None
        
    df_parsed = pd.DataFrame(rows, columns=headers)
    
    # Try converting numerical columns
    for col in df_parsed.columns:
        cleaned_col = df_parsed[col].str.replace("$", "", regex=False).str.replace(",", "", regex=False).str.replace("%", "", regex=False).str.strip()
        try:
            numeric_vals = pd.to_numeric(cleaned_col)
            if not numeric_vals.isna().all():
                df_parsed[col] = numeric_vals
        except:
            pass
            
    return df_parsed

# Scikit-learn imports for model analysis
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.tree import DecisionTreeRegressor, DecisionTreeClassifier
from sklearn.metrics import mean_absolute_error, r2_score, accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

import tools.adk_tools as adk_tools
from tools.google_sheets_tools import read_sheet_to_df, write_df_to_sheet
import tools.google_sheets_tools as gs_tools

# Set page config
st.set_page_config(
    page_title="InsightPilot",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject JavaScript to force-expand the sidebar by clearing local/session storage collapsed states
st.components.v1.html(
    """
    <script>
        try {
            var parentWindow = window.parent;
            parentWindow.localStorage.setItem("streamlitSidebarCollapsed", "false");
            parentWindow.sessionStorage.setItem("streamlitSidebarCollapsed", "false");
        } catch (e) {
            console.error("Failed to force expand sidebar:", e);
        }
    </script>
    """,
    height=0,
    width=0
)

# Theme Toggle State
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

def toggle_theme():
    st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"

IS_DARK = st.session_state.theme == "dark"

# Theme Colors (Premium zinc/coral theme matching screenshot)
if IS_DARK:
    bg_color = "#09090b"
    bg_subtle = "#0c0c0f"
    card_color = "#18181b"
    card_hover = "#27272a"
    border_color = "#27272a"
    border_subtle = "#1e1e24"
    text_color = "#ffffff"
    text_muted = "#a1a1aa"
    accent_color = "#ff6b4a"
    accent_hover = "#ff856b"
    shadow = "none"
else:
    bg_color = "#f4f5f7"  # Premium off-white from screenshot
    bg_subtle = "#ffffff" # White sidebar
    card_color = "#ffffff" # White cards from screenshot
    card_hover = "#fafafa"
    border_color = "rgba(0, 0, 0, 0.04)"
    border_subtle = "rgba(0, 0, 0, 0.02)"
    text_color = "#1f2937"  # Charcoal text from screenshot
    text_muted = "#6b7280"  # Subdued gray text
    accent_color = "#e25c38"  # Coral orange from screenshot
    accent_hover = "#c84d2d"
    shadow = "0 10px 30px rgba(0,0,0,0.02), 0 1px 8px rgba(0,0,0,0.03)"

# Global Custom CSS
css = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=JetBrains+Mono:wght@400;500&display=swap');
    
    html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"], .main, .block-container, section[data-testid="stMain"] {{
        background-color: {bg_color} !important;
        color: {text_color} !important;
        font-family: 'DM Sans', -apple-system, sans-serif !important;
    }}
    
    .block-container {{
        padding: 1.5rem 2.5rem 2rem !important;
        max-width: 1360px !important;
    }}
    
    header[data-testid="stHeader"] {{
        background-color: rgba(0,0,0,0) !important;
        border-bottom: none !important;
        z-index: 999990 !important;
    }}
    
    footer, [data-testid="stToolbar"],
    [data-testid="stDecoration"], [data-testid="stStatusWidget"], .stDeployButton {{
        display: none !important;
    }}
    
    /* Hide the native sidebar completely */
    [data-testid="stSidebar"] {{
        display: none !important;
        visibility: hidden !important;
        width: 0px !important;
    }}
    
    /* Reset main content margins to span full screen width */
    section[data-testid="stMain"] {{
        margin-left: 0px !important;
        width: 100% !important;
    }}
    
    /* Hide all collapse/expand toggle controls completely */
    button[data-testid="stSidebarCollapseButton"] {{
        display: none !important;
    }}
    div[data-testid="stSidebarCollapsedControl"] {{
        display: none !important;
    }}
    
    /* Ensure Streamlit elements respect custom color contrast */
    [data-testid="stMarkdownContainer"] p, 
    [data-testid="stMarkdownContainer"] li, 
    [data-testid="stMarkdownContainer"] span, 
    [data-testid="stMarkdownContainer"] b, 
    [data-testid="stMarkdownContainer"] strong,
    [data-testid="stMarkdownContainer"] label,
    div[data-testid="stSubheader"] h3,
    div[data-testid="stSubheader"] h4,
    div[data-testid="stSubheader"] h5 {{
        color: {text_color} !important;
    }}
    
    /* Enforce contrast inside the sidebar */
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] div,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {{
        color: {text_color} !important;
    }}
    
    /* Sidebar Container Card */
    .sidebar-container-card {{
        background: {bg_subtle};
        border: 1px solid {border_color};
        border-radius: 24px !important;
        padding: 1.5rem 1.4rem;
        box-shadow: {shadow};
        margin-bottom: 1.5rem;
    }}
    
    /* Metric Cards (Rounder corners & soft shadows matching screenshot) */
    .metric-card {{
        background: {card_color};
        border: 1px solid {border_color};
        border-radius: 20px !important;
        padding: 1.25rem 1.4rem;
        box-shadow: {shadow};
        margin-bottom: 1rem;
        transition: transform 0.2s ease, background-color 0.2s ease;
    }}
    .metric-card:hover {{
        background: {card_hover};
        transform: translateY(-2px);
    }}
    .metric-label {{
        font-size: 0.78rem;
        color: {text_muted} !important;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}
    .metric-value {{
        font-size: 1.75rem;
        font-weight: 700;
        color: {text_color} !important;
        letter-spacing: -0.03em;
        margin-top: 0.2rem;
    }}
    
    /* Chart Container (Rounded corners matching screenshot) */
    .chart-wrap {{
        background: {card_color};
        border: 1px solid {border_color};
        border-radius: 20px !important;
        padding: 1.2rem;
        box-shadow: {shadow};
        margin-top: 1rem;
    }}
    
    /* Chat bubbles (More rounded corners) */
    .chat-bubble {{
        padding: 0.85rem 1.1rem;
        border-radius: 18px;
        margin-bottom: 0.8rem;
        border: 1px solid {border_color};
        font-size: 0.9rem;
        line-height: 1.5;
        color: {text_color} !important;
    }}
    .user-chat {{
        background: {bg_color};
        align-self: flex-end;
        margin-left: 20%;
        border-bottom-right-radius: 4px;
    }}
    .assistant-chat {{
        background: {card_color};
        align-self: flex-start;
        margin-right: 20%;
        border-bottom-left-radius: 4px;
        box-shadow: {shadow};
    }}
    .thought-bubble {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        color: {text_muted} !important;
        background: {bg_color};
        border-left: 3px solid {accent_color};
        padding: 0.5rem 0.8rem;
        margin-bottom: 0.8rem;
        border-radius: 0 8px 8px 0;
        white-space: pre-wrap;
    }}
    
    /* Custom Button Styling - Coral Orange like the screenshot */
    button[kind="primary"], .stButton button, button[data-testid="baseButton-secondary"] {{
        background-color: {accent_color} !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 24px !important;
        padding: 0.55rem 1.6rem !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        box-shadow: 0 4px 12px rgba(226, 92, 56, 0.15) !important;
        transition: background-color 0.2s ease, transform 0.1s ease !important;
    }}
    button[kind="primary"]:hover, .stButton button:hover, button[data-testid="baseButton-secondary"]:hover {{
        background-color: {accent_hover} !important;
        transform: translateY(-1px) !important;
    }}
    
    /* Pill Tabs styling (Active accent highlight) */
    button[data-baseweb="tab"] {{
        background: transparent !important;
        color: {text_muted} !important;
        font-size: 0.88rem !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.35rem !important;
        border: 1px solid transparent !important;
        border-radius: 12px !important;
        transition: background-color 0.2s, color 0.2s !important;
    }}
    button[data-baseweb="tab"][aria-selected="true"] {{
        color: #ffffff !important;
        background: {accent_color} !important;
        box-shadow: 0 4px 10px rgba(226, 92, 56, 0.12) !important;
    }}
    [data-baseweb="tab-highlight"], [data-baseweb="tab-border"] {{
        display: none !important;
    }}
    [data-baseweb="tab-list"] {{
        gap: 6px !important;
        background: {bg_color} !important;
        border: 1px solid {border_color} !important;
        border-radius: 16px !important;
        padding: 4px;
        margin-bottom: 1.5rem;
    }}
</style>
"""
st.markdown(css, unsafe_allow_html=True)

PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans, sans-serif", color="#fafafa" if IS_DARK else "#09090b", size=11),
    margin=dict(l=40, r=20, t=30, b=40),
    xaxis=dict(
        gridcolor="rgba(255,255,255,0.06)" if IS_DARK else "rgba(0,0,0,0.06)",
        zerolinecolor="rgba(255,255,255,0.06)" if IS_DARK else "rgba(0,0,0,0.06)",
        tickfont=dict(size=10, color="#a1a1aa" if IS_DARK else "#71717a"),
    ),
    yaxis=dict(
        gridcolor="rgba(255,255,255,0.06)" if IS_DARK else "rgba(0,0,0,0.06)",
        zerolinecolor="rgba(255,255,255,0.06)" if IS_DARK else "rgba(0,0,0,0.06)",
        tickfont=dict(size=10, color="#a1a1aa" if IS_DARK else "#71717a"),
    ),
)

# Initialize Session State
if "datasets" not in st.session_state:
    st.session_state.datasets = {}
    
# Preload default Sales CSV if present
if "default_loaded" not in st.session_state:
    if os.path.exists("Sales_Data.csv"):
        try:
            df_default = pd.read_csv("Sales_Data.csv")
            st.session_state.datasets["Sales_Data.csv (Default)"] = df_default
            st.session_state.active_name = "Sales_Data.csv (Default)"
            st.session_state.active_names = ["Sales_Data.csv (Default)"]
            adk_tools._active_df = df_default
            adk_tools._active_datasets = {"Sales_Data.csv (Default)": df_default}
        except Exception:
            st.session_state.active_name = None
            st.session_state.active_names = []
            adk_tools._active_datasets = {}
    else:
        st.session_state.active_name = None
        st.session_state.active_names = []
        adk_tools._active_datasets = {}
    st.session_state.default_loaded = True

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "google_sheet_sync_status" not in st.session_state:
    st.session_state.google_sheet_sync_status = "Not Connected"
if "show_bi_visuals" not in st.session_state:
    st.session_state.show_bi_visuals = False
if "show_chat_visuals" not in st.session_state:
    st.session_state.show_chat_visuals = False

# Brand Header matching the screenshot
head_left, head_middle, head_right = st.columns([7, 3, 2])
with head_left:
    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 0.5rem;">
        <div style="width: 44px; height: 44px; background-color: #111827; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #ffffff; font-weight: 700; font-size: 1.1rem; box-shadow: {shadow};">IP</div>
        <div>
            <div style="font-size: 1.35rem; font-weight: 700; color: {text_color}; line-height: 1.2;">InsightPilot</div>
            <div style="font-size: 0.8rem; color: {text_muted}; font-weight: 500;">Business Analytics Dashboard</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
with head_middle:
    # Live date badge matching the screenshot (Saturday, June 27)
    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 10px; margin-left: auto;">
        <div style="width: 44px; height: 44px; border-radius: 50%; border: 1px solid {border_color}; background-color: {card_color}; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 1.1rem; color: {text_color}; box-shadow: {shadow};">27</div>
        <div>
            <div style="font-size: 0.85rem; font-weight: 600; color: {text_color}; line-height: 1.2;">Sat, June</div>
            <div style="font-size: 0.75rem; color: {text_muted}; font-weight: 500;">Live Workspace Sync</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
with head_right:
    theme_label = "☀️ Light Theme" if IS_DARK else "🌙 Dark Theme"
    st.button(theme_label, on_click=toggle_theme, use_container_width=True)

st.markdown("<hr style='margin: 0.75rem 0 1.25rem; opacity: 0.08;'/>", unsafe_allow_html=True)

# ==========================================================
# IN-PAGE DATA CONNECTOR & MULTI-FILE UPLOAD (EXPANDER CARD)
# ==========================================================
with st.expander("🔌 Connect & Manage Workspace Datasets", expanded=True):
    col_conn1, col_conn2 = st.columns([5, 7])
    
    with col_conn1:
        st.markdown("##### 📂 Load Datasets by File Path")
        st.caption("Paste absolute file paths (CSV, Excel, or JSON). Separate multiple paths with a comma or newline.")
        
        path_input = st.text_area(
            "File Paths",
            placeholder="e.g.\nX:\\agy-cli-projects\\Sales_Data.csv\nX:\\agy-cli-projects\\data\\Candy_Products.csv",
            height=110,
            key="file_path_input",
            label_visibility="collapsed"
        )
        
        load_col, clear_col = st.columns([3, 1])
        with load_col:
            load_btn = st.button("📥 Load Files", use_container_width=True, key="load_paths_btn")
        with clear_col:
            clear_btn = st.button("🗑️ Clear All", use_container_width=True, key="clear_datasets_btn")
        
        if load_btn and path_input.strip():
            raw_paths = [p.strip().strip('"').strip("'") for p in path_input.replace("\n", ",").split(",") if p.strip()]
            loaded_any = False
            for raw_path in raw_paths:
                try:
                    ext = os.path.splitext(raw_path)[1].lower()
                    if ext in [".xlsx", ".xls"]:
                        df_loaded = pd.read_excel(raw_path)
                    elif ext == ".json":
                        df_loaded = pd.read_json(raw_path)
                    else:
                        df_loaded = pd.read_csv(raw_path)
                    df_loaded.columns = df_loaded.columns.str.strip()
                    fname = os.path.basename(raw_path)
                    st.session_state.datasets[fname] = df_loaded
                    if "active_names" not in st.session_state:
                        st.session_state.active_names = []
                    if fname not in st.session_state.active_names:
                        st.session_state.active_names.append(fname)
                    loaded_any = True
                    st.success(f"✅ Loaded: {os.path.basename(raw_path)} ({df_loaded.shape[0]} rows)")
                except Exception as e:
                    st.error(f"❌ {os.path.basename(raw_path)}: {e}")
            
            if loaded_any:
                st.session_state.active_name = ", ".join(st.session_state.active_names)
                adk_tools._active_datasets = {name: st.session_state.datasets[name] for name in st.session_state.active_names}
                adk_tools._active_df = adk_tools.consolidate_datasets()
                if "runner" in st.session_state:
                    del st.session_state.runner
                st.rerun()
        
        if clear_btn:
            st.session_state.datasets = {}
            st.session_state.active_names = []
            st.session_state.active_name = None
            st.session_state.processed_files = []
            adk_tools._active_datasets = {}
            adk_tools._active_df = None
            if "runner" in st.session_state:
                del st.session_state.runner
            adk_tools.load_sales_data()
            st.session_state.datasets["Sales_Data.csv (Default)"] = adk_tools._active_df
            st.session_state.active_names = ["Sales_Data.csv (Default)"]
            st.session_state.active_name = "Sales_Data.csv (Default)"
            st.rerun()
        
        # Always sync session state datasets to adk_tools on every page run
        active_names_now = st.session_state.get("active_names", [])
        if active_names_now:
            adk_tools._active_datasets = {
                name: st.session_state.datasets[name]
                for name in active_names_now
                if name in st.session_state.datasets
            }
            adk_tools._active_df = adk_tools.consolidate_datasets()
        
        # Connection & Sync Details
        st.markdown("##### ℹ️ Active Datasets")
        if st.session_state.get("active_names"):
            for dname in st.session_state.active_names:
                df_info = st.session_state.datasets.get(dname)
                shape_str = f"{df_info.shape[0]} rows × {df_info.shape[1]} cols" if df_info is not None else "unknown"
                st.markdown(
                    f"<div style='padding:6px 10px; border-radius:6px; background:rgba(255,140,60,0.1); "
                    f"border:1px solid rgba(255,140,60,0.35); margin-bottom:5px; font-size:0.82rem;'>"
                    f"📄 <b>{dname}</b> — {shape_str}</div>",
                    unsafe_allow_html=True
                )
        else:
            st.caption("No datasets loaded. Use the path input above or upload a file.")
        
    with col_conn2:
        st.markdown("##### 📁 Upload Datasets (Optional)")
        st.caption("Alternatively, upload files directly here.")
        uploaded_files = st.file_uploader(
            "Upload CSV or Excel files (Multi-file allowed)",
            type=["csv", "xlsx"],
            accept_multiple_files=True,
            key="csv_xlsx_uploader"
        )
        
        st.markdown("##### 🔌 Connect Google Sheet (Optional)")
        conn_type_gs = st.radio(
            "Sheet Connection",
            ["Skip", "Connect Google Sheet"],
            key="conn_type_radio",
            label_visibility="collapsed",
            horizontal=True
        )
        
        if conn_type_gs == "Connect Google Sheet":
            spreadsheet_id = st.text_input("Spreadsheet ID or URL", key="sheet_id_input_direct")
            sheet_name_input = st.text_input("Sheet Name", value="Sheet1", key="sheet_name_val_direct")
            creds_file = st.file_uploader("Upload SA JSON", type=["json"], key="sa_json_file_direct")
            creds_text = st.text_area("Or Paste SA JSON content", height=60, key="sa_json_text_direct")
            creds_dict = None
            if creds_file:
                try:
                    creds_dict = json.load(creds_file)
                except Exception as e:
                    st.error(f"Invalid JSON file: {e}")
            elif creds_text.strip():
                try:
                    creds_dict = json.loads(creds_text)
                except Exception as e:
                    st.error(f"Invalid JSON text: {e}")
            gs_tools.g_creds_dict = creds_dict
            
            if st.button("📥 Load from Google Sheet", use_container_width=True, key="load_g_sheet_btn"):
                if not spreadsheet_id.strip():
                    st.error("Please enter a Spreadsheet ID or URL.")
                else:
                    with st.spinner("Fetching data from Google Sheet..."):
                        try:
                            df = read_sheet_to_df(spreadsheet_id.strip(), sheet_name_input, creds_dict)
                            if not df.empty:
                                sheet_key = f"Google Sheet: {sheet_name_input}"
                                st.session_state.datasets[sheet_key] = df
                                if "active_names" not in st.session_state:
                                    st.session_state.active_names = []
                                if sheet_key not in st.session_state.active_names:
                                    st.session_state.active_names.append(sheet_key)
                                st.session_state.active_name = ", ".join(st.session_state.active_names)
                                adk_tools._active_datasets = {name: st.session_state.datasets[name] for name in st.session_state.active_names}
                                adk_tools._active_df = adk_tools.consolidate_datasets()
                                st.session_state.google_sheet_sync_status = f"Connected to sheet: {sheet_name_input}"
                                st.success("Loaded sheet data successfully!")
                                st.rerun()
                            else:
                                st.warning("Loaded sheet is empty.")
                        except Exception as e:
                            st.error(f"Failed to load: {e}")
        else:
            spreadsheet_id = ""
            sheet_name_input = "Sheet1"
            creds_dict = None
        
        # Handle file uploads
        if uploaded_files:
            current_uploaded_names = [f.name for f in uploaded_files]
            if "processed_files" not in st.session_state:
                st.session_state.processed_files = []
            if set(current_uploaded_names) != set(st.session_state.processed_files):
                newly_added = []
                for file in uploaded_files:
                    if file.name not in st.session_state.processed_files:
                        try:
                            if file.name.endswith(".xlsx"):
                                df = pd.read_excel(file)
                            else:
                                df = pd.read_csv(file)
                            df.columns = df.columns.str.strip()
                            st.session_state.datasets[file.name] = df
                            newly_added.append(file.name)
                        except Exception as e:
                            st.error(f"Error loading {file.name}: {e}")
                st.session_state.processed_files = current_uploaded_names
                if newly_added:
                    if "active_names" not in st.session_state:
                        st.session_state.active_names = []
                    for name in newly_added:
                        if name not in st.session_state.active_names:
                            st.session_state.active_names.append(name)
                    st.session_state.active_name = ", ".join(st.session_state.active_names)
                    adk_tools._active_datasets = {name: st.session_state.datasets[name] for name in st.session_state.active_names}
                    adk_tools._active_df = adk_tools.consolidate_datasets()
                    st.session_state.processed_files = []

# ==========================================================
# DATASET PREVIEW WINDOW
# ==========================================================
if st.session_state.get("datasets"):
    with st.expander("🔍 Dataset Preview", expanded=False):
        dataset_names = list(st.session_state.datasets.keys())
        if len(dataset_names) == 1:
            preview_tabs = [dataset_names[0]]
        else:
            preview_tabs = dataset_names

        tabs = st.tabs([f"📄 {n}" for n in preview_tabs])
        for tab, dname in zip(tabs, preview_tabs):
            with tab:
                dpreview = st.session_state.datasets.get(dname)
                if dpreview is not None and not dpreview.empty:
                    rows, cols = dpreview.shape
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Rows", f"{rows:,}")
                    c2.metric("Columns", cols)
                    c3.metric("Memory", f"{dpreview.memory_usage(deep=True).sum() / 1024:.1f} KB")

                    view_mode = st.radio(
                        "View",
                        ["Head (first 10)", "Tail (last 10)", "Statistics"],
                        horizontal=True,
                        key=f"preview_mode_{dname}"
                    )
                    if view_mode == "Head (first 10)":
                        st.dataframe(dpreview.head(10), use_container_width=True, height=280)
                    elif view_mode == "Tail (last 10)":
                        st.dataframe(dpreview.tail(10), use_container_width=True, height=280)
                    else:
                        st.dataframe(dpreview.describe(include="all").T, use_container_width=True, height=280)

                    st.markdown(
                        f"<div style='font-size:0.78rem; color:{text_muted}; margin-top:4px;'>"
                        f"Columns: {', '.join(dpreview.columns.tolist())}</div>",
                        unsafe_allow_html=True
                    )
                else:
                    st.info(f"No data available for {dname}.")

# Helper for metric card HTML
def metric_card(label, value):
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
    </div>
    """, unsafe_allow_html=True)

# Dynamic metrics and BI calculation
def generate_dynamic_analysis(df: pd.DataFrame):
    required_cols = ["Order Date", "Ship Date", "Sales", "Units", "Gross Profit", "Cost"]
    is_sales_data = all(col in df.columns for col in required_cols)
    
    if is_sales_data:
        from agents.kpi_agent import KPIAgent
        from agents.insight_agent import InsightAgent
        from agents.recommendation_agent import RecommendationAgent
        
        # Clean dataframe to format correct numeric inputs
        df_cleaned = df.copy()
        df_cleaned.drop_duplicates(inplace=True)
        df_cleaned["Order Date"] = pd.to_datetime(df_cleaned["Order Date"], dayfirst=True, errors="coerce")
        df_cleaned["Ship Date"] = pd.to_datetime(df_cleaned["Ship Date"], dayfirst=True, errors="coerce")
        numeric_cols = ["Sales", "Units", "Gross Profit", "Cost"]
        for col in numeric_cols:
            df_cleaned[col] = pd.to_numeric(df_cleaned[col], errors="coerce")
        df_cleaned.dropna(subset=numeric_cols, inplace=True)
        
        kpis = KPIAgent().calculate_kpis(df_cleaned)
        insights = InsightAgent().generate_insights(df_cleaned)
        recs = RecommendationAgent().generate_recommendations(df_cleaned)
        
        formatted_kpis = {
            "Total Sales": f"${kpis['Total Sales']:,.2f}",
            "Total Profit": f"${kpis['Total Profit']:,.2f}",
            "Profit Margin": f"{kpis['Profit Margin (%)']:.2f}%",
            "Units Sold": f"{kpis['Total Units']:,}",
            "Total Orders": f"{kpis['Total Orders']:,}",
            "Avg Order Value": f"${kpis['Average Order Value']:,.2f}"
        }
        return formatted_kpis, insights, recs, True
    else:
        num_cols = df.select_dtypes(include=['number']).columns.tolist()
        cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        kpis = {
            "Total Rows": f"{len(df):,}",
            "Total Columns": f"{len(df.columns)}"
        }
        for col in num_cols[:4]:
            col_sum = df[col].sum()
            col_mean = df[col].mean()
            if col_sum > 100000:
                kpis[f"Total {col}"] = f"{col_sum:,.2f}"
            else:
                kpis[f"Avg {col}"] = f"{col_mean:,.2f}"
                
        insights = {}
        if cat_cols and num_cols:
            cat = cat_cols[0]
            num = num_cols[0]
            grouped = df.groupby(cat)[num].sum().sort_values(ascending=False)
            if not grouped.empty:
                insights[f"Top {cat} by {num}"] = f"{grouped.index[0]} ({grouped.iloc[0]:,.2f})"
                insights[f"Lowest {cat} by {num}"] = f"{grouped.index[-1]} ({grouped.iloc[-1]:,.2f})"
        else:
            insights["Info"] = "Upload a dataset containing both category and numeric columns to calculate deep insights."
            
        recs = []
        if cat_cols and num_cols:
            cat = cat_cols[0]
            num = num_cols[0]
            grouped = df.groupby(cat)[num].sum().sort_values(ascending=False)
            if len(grouped) >= 2:
                recs.append(f"Target investments and scaling in the high-performing category '{grouped.index[0]}' for optimal {num}.")
                recs.append(f"Perform operational review on category '{grouped.index[-1]}' which represents the weakest {num} generation.")
        else:
            recs.append("Add categorical and numeric fields to get automatic strategic recommendations.")
            
        return kpis, insights, recs, False

# Main app layout using Tabs
if adk_tools._active_df is not None:
    df = adk_tools._active_df
    
    # Render main tabs
    tab_bi, tab_ml = st.tabs(["💬 BI Chat & Insights", "🤖 Model Analysis & Prediction"])
    
    # ==========================================================
    # TAB 1: BI CHAT & INSIGHTS
    # ==========================================================
    with tab_bi:
        # Core Metrics Summary top row
        kpi_metrics, insights_data, recommendations_data, is_standard_sales = generate_dynamic_analysis(df)
        
        st.markdown("### 📈 Core Metrics Summary")
        kpi_cols = st.columns(len(kpi_metrics))
        for col_idx, (label, val) in enumerate(kpi_metrics.items()):
            with kpi_cols[col_idx]:
                metric_card(label, val)
                
        st.markdown("<hr style='margin: 1.5rem 0; opacity: 0.1;'/>", unsafe_allow_html=True)
        
        # Split layout inside Tab 1
        chat_col, analysis_col = st.columns([7, 5])
        
        # Left Chat Pane
        with chat_col:
            # Welcoming header matching the screenshot
            st.markdown(f"""
            <div style="margin-bottom: 1.5rem; margin-top: 0.5rem;">
                <div style="font-size: 1.95rem; font-weight: 700; color: {text_color}; line-height: 1.15;">Hey, Need help? 👋</div>
                <div style="font-size: 1.95rem; font-weight: 300; color: {text_muted}; line-height: 1.15;">Just ask me anything!</div>
            </div>
            """, unsafe_allow_html=True)
            
            chat_container = st.container(height=380)
            with chat_container:
                for message in st.session_state.chat_history:
                    role = message["role"]
                    content = message["content"]
                    thoughts = message.get("thoughts", "")
                    
                    if role == "user":
                        st.markdown(f'<div class="chat-bubble user-chat">👤 <b>You:</b><br/>{content}</div>', unsafe_allow_html=True)
                    else:
                        if thoughts:
                            st.markdown(f'<div class="thought-bubble">💡 <b>Agent thoughts/actions:</b><br/>{thoughts}</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="chat-bubble assistant-chat">🤖 <b>Agent:</b><br/>{content}</div>', unsafe_allow_html=True)
                        
            user_input = st.chat_input("Ask a business analytics question...")
            
            if user_input:
                st.session_state.chat_history.append({"role": "user", "content": user_input})
                
                with st.spinner("InsightPilot is analyzing..."):
                    # Load environment variables
                    if os.path.exists(".env"):
                        with open(".env") as f:
                            for line in f:
                                if line.startswith("GOOGLE_API_KEY="):
                                    os.environ["GOOGLE_API_KEY"] = line.strip().split("=", 1)[1]
                                    
                    from google.genai.types import Content, Part
                    from google.adk.runners import InMemoryRunner
                    from adk_root import root_agent
                    
                    # Always re-sync the consolidated multi-dataset from session state
                    active_names = st.session_state.get("active_names", [])
                    if active_names:
                        adk_tools._active_datasets = {
                            name: st.session_state.datasets[name]
                            for name in active_names
                            if name in st.session_state.datasets
                        }
                        adk_tools._active_df = adk_tools.consolidate_datasets()
                    else:
                        adk_tools._active_df = df

                    new_message = Content(role="user", parts=[Part.from_text(text=user_input)])
                    thoughts_list = []
                    text_response_list = []

                    # Model fallback chain: try each in order, fall back on 429
                    MODEL_CHAIN = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-flash-8b"]
                    
                    last_err = None
                    for model_name in MODEL_CHAIN:
                        try:
                            root_agent.model = model_name
                            # Recreate runner when model changes
                            if st.session_state.get("_last_model") != model_name:
                                if "runner" in st.session_state:
                                    del st.session_state.runner
                                st.session_state._last_model = model_name
                            if "runner" not in st.session_state:
                                st.session_state.runner = InMemoryRunner(agent=root_agent)
                                st.session_state.runner.auto_create_session = True

                            events = st.session_state.runner.run(
                                user_id="streamlit_user",
                                session_id="session_1",
                                new_message=new_message
                            )
                            
                            for event in events:
                                if not event.content or not event.content.parts:
                                    continue
                                for part in event.content.parts:
                                    if part.text:
                                        text_response_list.append(part.text)
                                    elif part.function_call:
                                        thoughts_list.append(f"🔧 Calling tool: `{part.function_call.name}`")
                                    elif part.function_response:
                                        resp_str = str(part.function_response.response)
                                        resp_short = resp_str[:200] + "..." if len(resp_str) > 200 else resp_str
                                        thoughts_list.append(f"✅ Tool result: {resp_short}")
                            
                            last_err = None
                            break  # Success — stop trying other models
                            
                        except Exception as e:
                            last_err = e
                            err_str = str(e)
                            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                                thoughts_list.append(f"⚠️ {model_name} rate limited, trying next model...")
                                # Reset runner so next model gets a fresh one
                                if "runner" in st.session_state:
                                    del st.session_state.runner
                                continue
                            else:
                                break  # Non-quota error — don't retry
                    
                    response_text = "".join(text_response_list).strip()
                    thoughts_text = "\n".join(thoughts_list)
                    
                    if last_err:
                        err_msg = str(last_err)
                        if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                            response_text = (
                                "⚠️ **API Rate Limit**: All Gemini free-tier models are currently rate-limited. "
                                "Please wait 1–2 minutes and try again. "
                                "To avoid this, consider adding a paid API key at [Google AI Studio](https://aistudio.google.com)."
                            )
                        else:
                            response_text = f"❌ Agent error: {err_msg[:300]}"
                    elif not response_text:
                        response_text = "⚠️ No response generated. Please try rephrasing your question."
                    
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": response_text,
                        "thoughts": thoughts_text
                    })
                st.rerun()

        # Right Analysis and Visuals Pane
        with analysis_col:
            st.markdown("### 🔍 Active Analysis Results")
            
            st.markdown("##### 📌 Insights")
            for key, value in insights_data.items():
                st.markdown(f"**{key}**: {value}")
                
            st.markdown("---")
            
            st.markdown("##### 🎯 Strategic Recommendations")
            for rec in recommendations_data:
                st.markdown(f"• {rec}")
                
            st.markdown("---")
            
            # Two Visuals Buttons
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                bi_vis_label = "Hide BI Visuals 📊" if st.session_state.show_bi_visuals else "Build BI Visuals 📊"
                if st.button(bi_vis_label, use_container_width=True):
                    st.session_state.show_bi_visuals = not st.session_state.show_bi_visuals
                    st.session_state.show_chat_visuals = False  # Close other
                    st.rerun()
            with col_btn2:
                chat_vis_label = "Hide Chat Visuals 💬" if st.session_state.show_chat_visuals else "Build Chat Visuals 💬"
                if st.button(chat_vis_label, use_container_width=True):
                    st.session_state.show_chat_visuals = not st.session_state.show_chat_visuals
                    st.session_state.show_bi_visuals = False  # Close other
                    st.rerun()
                    
            # 1. BI VISUALS RENDERING
            if st.session_state.show_bi_visuals:
                st.markdown("<div class='chart-wrap'>", unsafe_allow_html=True)
                st.markdown("### 📊 Interactive BI Visualizations")
                if is_standard_sales:
                    v_tab1, v_tab2, v_tab3 = st.tabs(["Sales by Region", "Profit by Region", "Monthly Sales Trend"])
                    with v_tab1:
                        region_sales = df.groupby("Region")["Sales"].sum().reset_index()
                        fig = px.bar(region_sales, x="Region", y="Sales", color="Region",
                                     title="Total Sales by Region",
                                     color_discrete_sequence=px.colors.qualitative.Prism)
                        fig.update_layout(PLOT_LAYOUT)
                        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                    with v_tab2:
                        region_profit = df.groupby("Region")["Gross Profit"].sum().reset_index()
                        fig = px.bar(region_profit, x="Region", y="Gross Profit", color="Region",
                                     title="Total Profit by Region",
                                     color_discrete_sequence=px.colors.qualitative.Prism)
                        fig.update_layout(PLOT_LAYOUT)
                        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                    with v_tab3:
                        df_temp = df.copy()
                        df_temp["Order Date"] = pd.to_datetime(df_temp["Order Date"], errors="coerce")
                        df_temp["Month"] = df_temp["Order Date"].dt.to_period("M").astype(str)
                        monthly_sales = df_temp.groupby("Month")["Sales"].sum().reset_index()
                        fig = px.line(monthly_sales, x="Month", y="Sales", markers=True,
                                      title="Monthly Revenue Trendline",
                                      line_shape="spline")
                        fig.update_layout(PLOT_LAYOUT)
                        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                else:
                    cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
                    num_cols = df.select_dtypes(include=['number']).columns.tolist()
                    date_cols = []
                    for col in df.columns:
                        if 'date' in col.lower() or 'time' in col.lower() or pd.api.types.is_datetime64_any_dtype(df[col]):
                            date_cols.append(col)
                    if num_cols:
                        st.markdown("##### Custom Dataset Graph Config")
                        c_sel1, c_sel2, c_sel3 = st.columns(3)
                        with c_sel1:
                            x_ax = st.selectbox("X Axis (Category/Date)", cat_cols + date_cols + num_cols if cat_cols or date_cols else num_cols, key="custom_x_axis")
                        with c_sel2:
                            y_ax = st.selectbox("Y Axis (Metric)", num_cols, key="custom_y_axis")
                        with c_sel3:
                            c_type = st.selectbox("Chart Type", ["Bar", "Line", "Scatter", "Histogram"], key="custom_c_type")
                        with st.spinner("Generating chart..."):
                            if c_type == "Bar":
                                grouped_df = df.groupby(x_ax)[y_ax].sum().reset_index()
                                grouped_df = grouped_df.sort_values(by=y_ax, ascending=False).head(15)
                                fig = px.bar(grouped_df, x=x_ax, y=y_ax, color=x_ax,
                                             title=f"{y_ax} by {x_ax} (Top 15)",
                                             color_discrete_sequence=px.colors.qualitative.Prism)
                            elif c_type == "Line":
                                sorted_df = df.sort_values(by=x_ax)
                                fig = px.line(sorted_df, x=x_ax, y=y_ax, markers=True,
                                              title=f"{y_ax} over {x_ax}")
                            elif c_type == "Scatter":
                                fig = px.scatter(df, x=x_ax, y=y_ax, color=x_ax if x_ax in cat_cols else None,
                                                 title=f"{y_ax} vs {x_ax}")
                            else:
                                fig = px.histogram(df, x=y_ax, title=f"Distribution of {y_ax}")
                            fig.update_layout(PLOT_LAYOUT)
                            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                    else:
                        st.warning("No numeric columns found to construct charts.")
                st.markdown("</div>", unsafe_allow_html=True)
                
            # 2. CHAT VISUALS RENDERING
            if st.session_state.show_chat_visuals:
                st.markdown("<div class='chart-wrap'>", unsafe_allow_html=True)
                st.markdown("### 💬 Chat Output Visualizer")
                
                # Retrieve last assistant message
                assistant_msgs = [m for m in st.session_state.chat_history if m["role"] == "assistant"]
                if not assistant_msgs:
                    st.warning("No agent response history found. Chat with the agent first!")
                else:
                    last_msg = assistant_msgs[-1]["content"]
                    # Try to parse markdown table
                    chat_df = parse_markdown_table(last_msg)
                    if chat_df is not None and not chat_df.empty:
                        st.markdown("##### Extracted Tabular Data")
                        # Display matrix/table format
                        st.dataframe(chat_df, use_container_width=True)
                        
                        chat_cols = chat_df.columns.tolist()
                        chat_num_cols = chat_df.select_dtypes(include=['number']).columns.tolist()
                        chat_cat_cols = chat_df.select_dtypes(include=['object', 'category']).columns.tolist()
                        
                        if chat_cols:
                            st.markdown("##### Visual Representation Config")
                            col_cx, col_cy, col_ct = st.columns(3)
                            with col_cx:
                                cx_ax = st.selectbox("X Axis Column", chat_cat_cols + chat_num_cols if chat_cat_cols else chat_cols, key="chat_x_axis")
                            with col_cy:
                                cy_ax = st.selectbox("Y Axis Column", chat_num_cols if chat_num_cols else chat_cols, key="chat_y_axis")
                            with col_ct:
                                ct_type = st.selectbox("Visualization Format", ["Bar Chart", "Line Plot", "Scatter Plot", "Pie Chart"], key="chat_c_type")
                                
                            with st.spinner("Building chat visuals..."):
                                try:
                                    if ct_type == "Bar Chart":
                                        fig = px.bar(chat_df, x=cx_ax, y=cy_ax, color=cx_ax,
                                                     title=f"{cy_ax} by {cx_ax} (From Chat Response)",
                                                     color_discrete_sequence=px.colors.qualitative.Prism)
                                    elif ct_type == "Line Plot":
                                        fig = px.line(chat_df, x=cx_ax, y=cy_ax, markers=True,
                                                      title=f"{cy_ax} over {cx_ax} (From Chat Response)")
                                    elif ct_type == "Scatter Plot":
                                        fig = px.scatter(chat_df, x=cx_ax, y=cy_ax, color=cx_ax if cx_ax in chat_cat_cols else None,
                                                         title=f"{cy_ax} vs {cx_ax} (From Chat Response)")
                                    else: # Pie Chart
                                        fig = px.pie(chat_df, names=cx_ax, values=cy_ax,
                                                     title=f"Distribution of {cy_ax} by {cx_ax} (From Chat Response)",
                                                     color_discrete_sequence=px.colors.qualitative.Prism)
                                        
                                    fig.update_layout(PLOT_LAYOUT)
                                    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                                except Exception as ve:
                                    st.error(f"Failed to render visualization: {ve}")
                        else:
                            st.warning("Extracted table columns could not be read.")
                    else:
                        st.info("No structured markdown table was found in the last agent response.")
                        st.info("💡 **Tip**: Ask the agent to calculate product profit margins or compare performance categories to generate tabular outputs!")
                st.markdown("</div>", unsafe_allow_html=True)

                
    # ==========================================================
    # TAB 2: MODEL ANALYSIS & PREDICTION
    # ==========================================================
    with tab_ml:
        st.markdown("### 🤖 ML Model Analysis Workspace")
        st.markdown("Create predictive models directly on your active dataset. Preprocess data, fit models, and compare metrics dynamically.")
        
        # Identify columns
        all_cols = df.columns.tolist()
        num_cols = df.select_dtypes(include=['number']).columns.tolist()
        cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # Setup form
        with st.form("ml_config_form"):
            st.markdown("##### ⚙️ Step 1: Configure Target & Predictors")
            col_t, col_f = st.columns([4, 8])
            with col_t:
                target_col = st.selectbox("Select Target Variable (Y)", all_cols)
            with col_f:
                # Default features: everything except target
                default_feats = [col for col in all_cols if col != target_col]
                feature_cols = st.multiselect("Select Feature Variables (X)", all_cols, default=default_feats)
                
            st.markdown("##### 📊 Step 2: Training Split & Task Configuration")
            col_split, col_task = st.columns(2)
            with col_split:
                test_size = st.slider("Test Split Size (%)", min_value=10, max_value=50, value=20, step=5) / 100.0
            with col_task:
                # Auto detect task type
                is_target_numeric = target_col in num_cols
                unique_vals = df[target_col].nunique()
                
                if is_target_numeric and unique_vals > 10:
                    task_default = "Regression"
                else:
                    task_default = "Classification"
                    
                task_type = st.selectbox("ML Task Type", ["Regression", "Classification"], index=0 if task_default == "Regression" else 1)
                
            train_model_btn = st.form_submit_button("🚂 Fit & Compare Models")
            
        if train_model_btn:
            if not feature_cols:
                st.error("Please select at least one predictor feature.")
            elif target_col in feature_cols:
                st.error("Target variable cannot be included in predictor features.")
            else:
                with st.spinner("Preparing data and training models..."):
                    try:
                        # Prepare data
                        ml_df = df[[target_col] + feature_cols].dropna()
                        X = ml_df[feature_cols]
                        y = ml_df[target_col]
                        
                        # Identify numeric and categorical features
                        num_feats = X.select_dtypes(include=['number']).columns.tolist()
                        cat_feats = X.select_dtypes(include=['object', 'category']).columns.tolist()
                        
                        # Create preprocessing pipelines
                        num_transformer = Pipeline(steps=[
                            ('imputer', SimpleImputer(strategy='median')),
                            ('scaler', StandardScaler())
                        ])
                        
                        cat_transformer = Pipeline(steps=[
                            ('imputer', SimpleImputer(strategy='most_frequent')),
                            ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
                        ])
                        
                        preprocessor = ColumnTransformer(
                            transformers=[
                                ('num', num_transformer, num_feats),
                                ('cat', cat_transformer, cat_feats)
                            ]
                        )
                        
                        # Train Test Split (Strict Ordering: split before pipeline fitting)
                        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42)
                        
                        if task_type == "Regression":
                            # Preprocess target if needed (none required for regression y)
                            model1 = Pipeline(steps=[('preprocessor', preprocessor),
                                                     ('regressor', LinearRegression())])
                            model2 = Pipeline(steps=[('preprocessor', preprocessor),
                                                     ('regressor', DecisionTreeRegressor(max_depth=5, random_state=42))])
                            
                            model1.fit(X_train, y_train)
                            model2.fit(X_train, y_train)
                            
                            y_pred1 = model1.predict(X_test)
                            y_pred2 = model2.predict(X_test)
                            
                            # Metrics
                            mae1 = mean_absolute_error(y_test, y_pred1)
                            rmse1 = np.sqrt(mean_absolute_error(y_test, y_pred1))
                            r2_1 = r2_score(y_test, y_pred1)
                            
                            mae2 = mean_absolute_error(y_test, y_pred2)
                            rmse2 = np.sqrt(mean_absolute_error(y_test, y_pred2))
                            r2_2 = r2_score(y_test, y_pred2)
                            
                            # Comparison display
                            st.markdown("### 📊 Regression Model Comparison")
                            
                            metrics_df = pd.DataFrame({
                                "Metric": ["Mean Absolute Error (MAE)", "Root Mean Squared Error (RMSE)", "R-Squared (R²)"],
                                "Model 1: Linear Regression": [f"{mae1:,.4f}", f"{rmse1:,.4f}", f"{r2_1:.4f}"],
                                "Model 2: Decision Tree": [f"{mae2:,.4f}", f"{rmse2:,.4f}", f"{r2_2:.4f}"]
                            })
                            st.table(metrics_df)
                            
                            # Decision Recommendation
                            best_model = "Linear Regression" if r2_1 > r2_2 else "Decision Tree"
                            st.markdown(f"""
                            > **Recommendation**: **{best_model}** shows superior predictive performance (higher $R^2$). 
                            > Linear models are highly interpretable for linear trends, whereas Decision Trees excel at capturing non-linear relationships.
                            """)
                            
                            # Visualization
                            st.markdown("<div class='chart-wrap'>", unsafe_allow_html=True)
                            st.markdown("##### Actual vs. Predicted Target Values")
                            vis_df = pd.DataFrame({
                                "Actual": y_test,
                                "Linear Regression": y_pred1,
                                "Decision Tree": y_pred2
                            }).reset_index(drop=True)
                            
                            fig = px.scatter(vis_df, x="Actual", y=["Linear Regression", "Decision Tree"],
                                             opacity=0.6, title="Predictions vs. Ground Truth")
                            fig.add_shape(
                                type="line", line=dict(dash="dash", color="white" if IS_DARK else "black"),
                                x0=y_test.min(), y0=y_test.min(), x1=y_test.max(), y1=y_test.max()
                            )
                            fig.update_layout(PLOT_LAYOUT)
                            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                            st.markdown("</div>", unsafe_allow_html=True)
                            
                        else:  # Classification
                            # Fit Label encoder or use raw labels
                            model1 = Pipeline(steps=[('preprocessor', preprocessor),
                                                     ('classifier', LogisticRegression(max_iter=1000, random_state=42))])
                            model2 = Pipeline(steps=[('preprocessor', preprocessor),
                                                     ('classifier', DecisionTreeClassifier(max_depth=5, random_state=42))])
                            
                            model1.fit(X_train, y_train)
                            model2.fit(X_train, y_train)
                            
                            y_pred1 = model1.predict(X_test)
                            y_pred2 = model2.predict(X_test)
                            
                            # Metrics (handle multi-class averaging)
                            avg_method = "weighted" if len(np.unique(y)) > 2 else "binary"
                            acc1 = accuracy_score(y_test, y_pred1)
                            prec1 = precision_score(y_test, y_pred1, average=avg_method, zero_division=0)
                            rec1 = recall_score(y_test, y_pred1, average=avg_method, zero_division=0)
                            f1_1 = f1_score(y_test, y_pred1, average=avg_method, zero_division=0)
                            
                            acc2 = accuracy_score(y_test, y_pred2)
                            prec2 = precision_score(y_test, y_pred2, average=avg_method, zero_division=0)
                            rec2 = recall_score(y_test, y_pred2, average=avg_method, zero_division=0)
                            f1_2 = f1_score(y_test, y_pred2, average=avg_method, zero_division=0)
                            
                            # Comparison display
                            st.markdown("### 📊 Classification Model Comparison")
                            
                            metrics_df = pd.DataFrame({
                                "Metric": ["Accuracy", f"Precision ({avg_method})", f"Recall ({avg_method})", f"F1-Score ({avg_method})"],
                                "Model 1: Logistic Regression": [f"{acc1:.4%}", f"{prec1:.4%}", f"{rec1:.4%}", f"{f1_1:.4%}"],
                                "Model 2: Decision Tree": [f"{acc2:.4%}", f"{prec2:.4%}", f"{rec2:.4%}", f"{f1_2:.4%}"]
                            })
                            st.table(metrics_df)
                            
                            # Decision Recommendation
                            best_model = "Logistic Regression" if f1_1 > f1_2 else "Decision Tree"
                            st.markdown(f"""
                            > **Recommendation**: **{best_model}** yielded a higher F1-score. 
                            > Consider Logistic Regression for robust baseline classification and class probability estimation, or Decision Tree for hierarchical decision logic.
                            """)
                            
                            # Confusion Matrix for Model 1
                            st.markdown("<div class='chart-wrap'>", unsafe_allow_html=True)
                            st.markdown("##### Confusion Matrix: Model 1 (Logistic Regression)")
                            
                            labels = sorted(list(np.unique(y_test)))
                            cm = confusion_matrix(y_test, y_pred1, labels=labels)
                            
                            # Heatmap
                            fig = ff.create_annotated_heatmap(
                                z=cm, x=[f"Predicted {l}" for l in labels], y=[f"Actual {l}" for l in labels],
                                colorscale="Purples" if IS_DARK else "Blues", showscale=True
                            )
                            fig.update_layout(PLOT_LAYOUT)
                            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                            st.markdown("</div>", unsafe_allow_html=True)
                            
                    except Exception as e:
                        st.error(f"Error during training: {str(e)}")
                        
else:
    st.markdown("""
    <div style="text-align: center; padding: 5rem 2rem;">
        <h2 style="font-size: 2.2rem; font-weight: 700; margin-bottom: 1rem;">Welcome to InsightPilot 🚀</h2>
        <p style="font-size: 1.1rem; color: #a1a1aa; max-width: 600px; margin: 0 auto 2rem;">
            Upload CSV/Excel file(s) or connect your Google Sheet using the sidebar panel to load and explore your business metrics.
        </p>
    </div>
    """, unsafe_allow_html=True)
