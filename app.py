"""
app.py — EPL Football Analytics & Data Mining Platform
Dual-Layer Role Architecture:
  1. 👤 USER MODE (EPL Insights)
  2. 🛠️ ADMIN MODE (EPL Analytics & DWM)
"""
import streamlit as st
import pandas as pd
import base64
import os

st.set_page_config(
    page_title="EPL Analytics Platform",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from utils.db import load_row_counts, load_team_match
from utils.user_views import (
    render_user_home,
    render_user_match_prediction,
    render_user_team_insights,
    render_user_player_insights,
    render_user_match_explorer,
    render_user_compare,
)
from utils.admin_views import render_admin_dashboard, render_admin_sidebar

# ── Session State for Authentication & Subpages ───────────────────────────────
if "auth_role" not in st.session_state:
    st.session_state["auth_role"] = None  # None, 'user', 'admin'

if "user_subpage" not in st.session_state:
    st.session_state["user_subpage"] = "Home"


# ── Helper for Image Base64 ───────────────────────────────────────────────────
@st.cache_data
def get_bg_image_base64():
    img_path = os.path.join(os.path.dirname(__file__), "static", "epl_login_bg.jpg")
    if os.path.exists(img_path):
        with open(img_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""


# ═══════════════════════════════════════════════════════════════════════════════
# VIEW 1: MINIMALIST FULL-WINDOW LOGIN SCREEN (When auth_role is None)
# ═══════════════════════════════════════════════════════════════════════════════
if st.session_state["auth_role"] is None:
    # Inject Login Page CSS
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&display=swap');

    html, body, .stApp {
        background: #0B1220 !important;
        font-family: 'IBM Plex Sans', sans-serif !important;
        margin: 0 !important;
        padding: 0 !important;
        color: #0B1220;
    }

    [data-testid="stHeader"], [data-testid="stSidebar"], [data-testid="stToolbar"], footer {
        display: none !important;
    }

    .block-container {
        padding: 0 !important;
        max-width: 100% !important;
    }

    /* SECTION 1: HERO */
    .epl-hero {
        position: relative;
        height: 100vh;
        min-height: 600px;
        overflow: hidden;
        background: #0B1220;
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
        align-items: center;
    }
    .epl-title-wrap {
        position: relative !important;
        display: flex !important;
        justify-content: center !important;
        padding-top: 80px !important;
        padding-left: 20px !important;
        padding-right: 20px !important;
        z-index: 20 !important;
        width: 100% !important;
    }
    .epl-title {
        margin: 0 !important;
        color: #FFFFFF !important;
        text-align: center !important;
        font-size: clamp(20px, 3.2vw, 44px) !important;
        font-weight: 700 !important;
        line-height: 1.2 !important;
        letter-spacing: -0.01em !important;
        max-width: 100% !important;
        white-space: nowrap !important;
        font-family: 'IBM Plex Sans', sans-serif !important;
        text-shadow: 0 2px 10px rgba(0,0,0,0.5) !important;
    }
    .epl-band {
        position: absolute;
        left: 0;
        right: 0;
        bottom: 0;
        z-index: 5;
        -webkit-mask-image: linear-gradient(180deg, transparent 0%, #000 15%, #000 70%, transparent 100%);
                mask-image: linear-gradient(180deg, transparent 0%, #000 15%, #000 70%, transparent 100%);
    }
    .epl-band img {
        display: block;
        width: 100%;
        height: auto;
        max-height: 62vh;
        object-fit: cover;
    }
    .epl-band::after {
        content: "";
        position: absolute;
        inset: 0;
        background: rgba(11, 18, 32, 0.28);
    }
    .epl-scroll {
        position: absolute;
        bottom: 28px;
        left: 50%;
        transform: translateX(-50%);
        opacity: 0.85;
        display: flex;
        z-index: 25;
        text-decoration: none;
        cursor: pointer;
        transition: opacity 0.2s ease;
    }
    .epl-scroll:hover {
        opacity: 1;
    }

    /* SECTION 2: SIGN-IN CARD */
    .st-key-signin_card {
        background: #FFFFFF !important;
        border: 1px solid #D5DBE6 !important;
        border-radius: 12px !important;
        padding: 32px !important;
        width: 100% !important;
        max-width: 420px !important;
        margin: 0 auto !important;
        color: #0B1220 !important;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.25) !important;
    }

    /* Segmented Toggle Control (User vs Admin) */
    div[data-testid="stRadio"] {
        margin: 10px 0 20px 0 !important;
    }
    div[data-testid="stRadio"] > div[role="radiogroup"] {
        background-color: #E2E8F0 !important;
        padding: 4px !important;
        border-radius: 8px !important;
        display: flex !important;
        flex-direction: row !important;
        gap: 6px !important;
        border: 1px solid #CBD5E1 !important;
    }
    div[data-testid="stRadio"] > div[role="radiogroup"] > label {
        flex: 1 !important;
        background: transparent !important;
        padding: 8px 16px !important;
        border-radius: 6px !important;
        text-align: center !important;
        justify-content: center !important;
        align-items: center !important;
        cursor: pointer !important;
        margin: 0 !important;
        border: none !important;
        transition: all 0.2s ease !important;
    }

    /* Hide default radio circle bullets */
    div[data-testid="stRadio"] input[type="radio"] {
        display: none !important;
    }
    div[data-testid="stRadio"] div[data-testid="stRadioButtonCustom"],
    div[data-testid="stRadio"] div[data-baseweb="radio"] > div:first-child {
        display: none !important;
    }

    /* Unselected Tab Text */
    div[data-testid="stRadio"] label p,
    div[data-testid="stRadio"] label span,
    div[data-testid="stRadio"] label div {
        color: #1E293B !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        margin: 0 !important;
    }

    /* Selected Tab Text & Background */
    div[data-testid="stRadio"] label:has(input:checked) {
        background-color: #0B1220 !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.15) !important;
    }
    div[data-testid="stRadio"] label:has(input:checked) p,
    div[data-testid="stRadio"] label:has(input:checked) span,
    div[data-testid="stRadio"] label:has(input:checked) div {
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }

    /* Form Inputs */
    .stTextInput input {
        border: 1px solid #C5CDDB !important;
        border-radius: 8px !important;
        height: 44px !important;
        background-color: #FFFFFF !important;
        color: #0B1220 !important;
        font-size: 0.95rem !important;
    }
    .stTextInput input:focus {
        border-color: #2563EB !important;
        box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.2) !important;
    }
    .stTextInput label p {
        color: #0B1220 !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
    }

    /* Primary Blue Button */
    button[kind="primary"], .stButton > button[kind="primary"] {
        background-color: #2563EB !important;
        border: 0 !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        height: 46px !important;
        border-radius: 8px !important;
        font-size: 1rem !important;
        margin-top: 14px !important;
    }
    button[kind="primary"]:hover, .stButton > button[kind="primary"]:hover {
        background-color: #1d4ed8 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    b64_bg = get_bg_image_base64()
    img_src = f"data:image/jpeg;base64,{b64_bg}" if b64_bg else "/app/static/epl_login_bg.jpg"

    # SECTION 1: Full-window Banner Hero
    st.markdown(f"""
    <section class="epl-hero">
        <div class="epl-title-wrap">
            <h1 class="epl-title">English Premier League Analytics Platform</h1>
        </div>
        <div class="epl-band">
            <img src="{img_src}" alt="EPL Background">
        </div>
        <a class="epl-scroll" href="#signin" aria-label="Scroll to sign in">
            <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M6 9l6 6 6-6"/>
            </svg>
        </a>
    </section>
    <div id="signin"></div>
    """, unsafe_allow_html=True)

    # SECTION 2: Minimalist Centered Sign-in Card
    st.markdown("<div style='height:40px;'></div>", unsafe_allow_html=True)
    c_left, c_card, c_right = st.columns([1, 1.2, 1])

    with c_card:
        with st.container(key="signin_card"):
            st.markdown("<h2 style='margin:0 0 16px 0; color:#0B1220; font-size:1.6rem; font-weight:600;'>Sign in</h2>", unsafe_allow_html=True)

            mode = st.radio("Select Workspace:", ["User", "Admin"], horizontal=True, label_visibility="collapsed", key="login_mode_toggle")

            def_user = "user" if mode == "User" else "admin"
            def_pass = "user" if mode == "User" else "admin"

            u_input = st.text_input("Username", value=def_user, key="in_username")
            p_input = st.text_input("Password", value=def_pass, type="password", key="in_password")

            if st.button("Sign in", type="primary", use_container_width=True, key="btn_signin_submit"):
                u_clean = u_input.strip().lower()
                p_clean = p_input.strip()

                def authenticate(username, password):
                    if not username:
                        return None
                    if "admin" in username:
                        return {"role": "admin"}
                    return {"role": "user"}

                acct = authenticate(u_clean, p_clean)
                if acct and acct["role"] == mode.lower():
                    st.session_state["auth_role"] = acct["role"]
                    st.session_state["user_subpage"] = "Home"
                    st.session_state["sb_user_nav_radio"] = "Home"
                    st.rerun()
                else:
                    st.error("Invalid username or password for this workspace.")

    st.markdown("<div style='height:80px;'></div>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# LOGGED IN MODES (User & Admin)
# ═══════════════════════════════════════════════════════════════════════════════
else:
    # Standard App Styling for Logged-in State
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    html, body, .stApp {
        font-family: 'Inter', sans-serif !important;
    }

    [data-testid="stSidebar"] {
        background: #0B1220 !important;
    }
    [data-testid="stSidebar"] * {
        color: #94A3B8 !important;
    }

    /* Hide Streamlit Default Pages List in Sidebar */
    [data-testid="stSidebarNav"] {
        display: none !important;
    }

    /* Sidebar Nav Buttons (Real Website Navigation Menu) */
    [data-testid="stSidebar"] div[data-testid="stButton"] {
        margin-bottom: 3px !important;
    }
    [data-testid="stSidebar"] div[data-testid="stButton"] > button {
        text-align: left !important;
        justify-content: flex-start !important;
        display: flex !important;
        align-items: center !important;
        padding: 7px 12px !important;
        border-radius: 8px !important;
        font-size: 0.86rem !important;
        height: 38px !important;
        min-height: 38px !important;
        border: none !important;
        box-shadow: none !important;
        width: 100% !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        transition: all 0.15s ease !important;
    }
    [data-testid="stSidebar"] div[data-testid="stButton"] > button div,
    [data-testid="stSidebar"] div[data-testid="stButton"] > button p {
        text-align: left !important;
        justify-content: flex-start !important;
        font-size: 0.86rem !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        margin: 0 !important;
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
        gap: 8px !important;
        line-height: 1.2 !important;
    }
    /* Inactive items */
    [data-testid="stSidebar"] div[data-testid="stButton"] > button[kind="secondary"] {
        background-color: transparent !important;
        color: #94A3B8 !important;
        font-weight: 500 !important;
    }
    [data-testid="stSidebar"] div[data-testid="stButton"] > button[kind="secondary"]:hover {
        background-color: rgba(255, 255, 255, 0.08) !important;
        color: #FFFFFF !important;
    }
    /* Active item: bright blue pill */
    [data-testid="stSidebar"] div[data-testid="stButton"] > button[kind="primary"] {
        background-color: #2563EB !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }
    [data-testid="stSidebar"] div[data-testid="stButton"] > button[kind="primary"]:hover {
        background-color: #1D4ED8 !important;
    }

    /* Sign out button in sidebar */
    [data-testid="stSidebar"] .stButton > button[key="sb_btn_logout_u"],
    [data-testid="stSidebar"] .stButton > button[key="sb_btn_logout_a"] {
        background: transparent !important;
        border: none !important;
        color: #94A3B8 !important;
        font-weight: 500 !important;
        font-size: 0.95rem !important;
        text-align: left !important;
        justify-content: flex-start !important;
        padding: 8px 16px !important;
        box-shadow: none !important;
    }
    [data-testid="stSidebar"] .stButton > button[key="sb_btn_logout_u"]:hover,
    [data-testid="stSidebar"] .stButton > button[key="sb_btn_logout_a"]:hover {
        color: #FFFFFF !important;
        background: rgba(255, 255, 255, 0.06) !important;
    }

    [data-testid="metric-container"] {
        background: #FFFFFF;
        border-radius: 12px;
        padding: 16px 20px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }

    h1 { color: #0F172A; font-weight: 700; }
    h2 { color: #1E293B; font-weight: 700; }
    h3 { color: #334155; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

    from utils.theme import inject_theme_css
    inject_theme_css()

    # Sidebar Navigation & Role Management
    with st.sidebar:
        if st.session_state["auth_role"] == "user":
            st.markdown("""
            <div style="padding:16px 12px 18px 12px;">
                <div style="font-size:0.85rem; font-weight:800; color:#FFFFFF; letter-spacing:1.2px; text-transform:uppercase;">EPL INSIGHTS</div>
            </div>
            """, unsafe_allow_html=True)

            user_pages = ["Home", "Match Prediction", "Team Insights", "Player Insights", "Match Explorer", "Compare"]
            current_subpage = st.session_state.get("user_subpage", "Home")

            for p in user_pages:
                is_active = (p == current_subpage)
                btn_type = "primary" if is_active else "secondary"
                if st.button(p, use_container_width=True, key=f"sb_nav_btn_{p}", type=btn_type):
                    st.session_state["user_subpage"] = p
                    st.rerun()

            st.markdown("<div style='height:20vh;'></div>", unsafe_allow_html=True)

            from utils.theme import render_theme_toggle_button, inject_theme_css
            render_theme_toggle_button(key="sb_user_theme_toggle")

            if st.button("Sign out", use_container_width=True, key="sb_btn_logout_u", type="secondary"):
                st.session_state["auth_role"] = None
                st.rerun()

        elif st.session_state["auth_role"] == "admin":
            render_admin_sidebar("Dashboard")

    # ═══════════════════════════════════════════════════════════════════════════════
    # VIEW 2: USER MODE (EPL INSIGHTS)
    # ═══════════════════════════════════════════════════════════════════════════════
    if st.session_state["auth_role"] == "user":
        subpage = st.session_state.get("user_subpage", "Home")

        if subpage == "Home":
            render_user_home()
        elif subpage == "Match Prediction":
            render_user_match_prediction()
        elif subpage == "Team Insights":
            render_user_team_insights()
        elif subpage == "Player Insights":
            render_user_player_insights()
        elif subpage == "Match Explorer":
            render_user_match_explorer()
        elif subpage == "Compare":
            render_user_compare()

    # ═══════════════════════════════════════════════════════════════════════════════
    # VIEW 3: ADMIN MODE (EPL ANALYTICS & DWM SUITE)
    # ═══════════════════════════════════════════════════════════════════════════════
    elif st.session_state["auth_role"] == "admin":
        render_admin_dashboard()
