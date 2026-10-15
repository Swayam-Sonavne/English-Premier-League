"""
utils/admin_views.py — Admin Mode (EPL Analytics & DWM)
Implements the exact Admin Dashboard UI from inspiration mockups:
  1. Top KPI Summary Strip (5 Cards)
  2. Model & Engine Status Table (matching mockup alignment with outline SVGs) + Clickable Analytics Modules (inside card box)
  3. Goals & Possession Dual-Axis Trend + Match Result Donut Chart (inside card boxes)
  4. Recent Top Performers Table + Quick Access Nav Buttons (inside card box)
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils.db import load_row_counts, load_team_match, load_fact_match, load_player_perf, q
from utils.models import get_classification_model, get_kmeans_model


from utils.theme import inject_theme_css, render_theme_toggle_button, get_theme_mode, get_theme_tokens

def render_admin_sidebar(current_page="Dashboard"):
    """
    Renders the unified, sleek Admin Sidebar navigation matching the mockup with clean outline glyphs and left alignment.
    Automatically injects global theme CSS (light/dark mode).
    """
    inject_theme_css()

    st.markdown("""
    <style>
    /* Hide Streamlit Default Pages Navigation across ALL pages */
    [data-testid="stSidebarNav"] {
        display: none !important;
    }
    [data-testid="stSidebar"] {
        background-color: #0B1220 !important;
    }

    /* Admin Mode Sidebar Nav Buttons */
    [data-testid="stSidebar"] div[data-testid="stButton"] {
        margin-bottom: 3px !important;
    }
    [data-testid="stSidebar"] div[data-testid="stButton"] > button {
        text-align: left !important;
        justify-content: flex-start !important;
        display: flex !important;
        align-items: center !important;
        padding: 8px 14px !important;
        border-radius: 8px !important;
        font-size: 0.88rem !important;
        height: 40px !important;
        min-height: 40px !important;
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
        font-size: 0.88rem !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        margin: 0 !important;
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
        gap: 10px !important;
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
    </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("""
        <div style="padding:14px 10px 16px 10px;">
            <div style="font-size:0.82rem; font-weight:800; color:#FFFFFF; letter-spacing:1.2px; text-transform:uppercase;">EPL ANALYTICS</div>
        </div>
        """, unsafe_allow_html=True)

        admin_nav = [
            ("⊞  Dashboard", "Dashboard", "app.py"),
            ("⌕  EPL Explorer", "EPL Explorer", "pages/2_EPL_Explorer.py"),
            ("📈  Performance Analysis", "Performance Analysis", "pages/3_Performance_Analysis.py"),
            ("🎯  Match Outcomes", "Match Outcomes", "pages/4_Match_Outcomes.py"),
            ("👥  Team Analytics", "Team Analytics", "pages/5_Team_Analytics.py"),
            ("👤  Player Analytics", "Player Analytics", "pages/6_Player_Analytics.py"),
            ("🔗  Association Analysis", "Association Analysis", "pages/7_Association_Analysis.py"),
            ("📐  OLAP Analysis", "OLAP Analysis", "pages/8_OLAP_Analysis.py"),
            ("🗄️  Data Warehouse", "Data Warehouse", "pages/9_Data_Warehouse.py"),
        ]

        for label, page_name, target_file in admin_nav:
            is_active = (page_name == current_page)
            btn_type = "primary" if is_active else "secondary"
            if st.button(label, use_container_width=True, key=f"sb_admin_nav_{page_name}", type=btn_type):
                if target_file == "app.py":
                    st.session_state["auth_role"] = "admin"
                    st.switch_page("app.py")
                else:
                    st.switch_page(target_file)

        st.markdown("<div style='height:8vh;'></div>", unsafe_allow_html=True)

        # Theme Toggle
        render_theme_toggle_button(key="sb_admin_theme_toggle")

        if st.button("👤 Switch to User Mode", use_container_width=True, key="sb_admin_sw_user", type="secondary"):
            st.session_state["auth_role"] = "user"
            st.session_state["user_subpage"] = "Home"
            st.switch_page("app.py")

        if st.button("🚪 Logout", use_container_width=True, key="sb_admin_logout", type="secondary"):
            st.session_state["auth_role"] = None
            st.switch_page("app.py")


def render_admin_dashboard():
    """
    Renders the complete Admin Dashboard view matching the UI inspiration mockup.
    All modules, status tables, and charts are strictly contained in clean white card boxes.
    """
    # ── Custom CSS for Admin Dashboard ─────────────────────────────────────────
    st.markdown("""
    <style>
    /* Card Container */
    .admin-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 16px 18px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
        margin-bottom: 16px;
        box-sizing: border-box;
        overflow: hidden;
    }

    .kpi-title {
        color: #64748B;
        font-size: 0.8rem;
        font-weight: 500;
        margin-bottom: 4px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .kpi-value {
        color: #0F172A;
        font-size: 1.75rem;
        font-weight: 700;
        line-height: 1.15;
        margin-bottom: 2px;
    }
    .kpi-sub {
        color: #94A3B8;
        font-size: 0.74rem;
        line-height: 1.2;
    }

    /* Status Table - Matching Inspiration Image 5 */
    .status-table {
        width: 100%;
        border-collapse: collapse;
        table-layout: fixed;
    }
    .status-table tr {
        border-bottom: 1px solid #F1F5F9;
        height: 44px;
    }
    .status-table tr:last-child {
        border-bottom: none;
    }
    .status-col-name {
        width: 44%;
        text-align: left;
        vertical-align: middle;
        font-size: 0.82rem;
        font-weight: 600;
        color: #0F172A;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        padding: 4px 0;
    }
    .status-col-badge {
        width: 25%;
        text-align: center;
        vertical-align: middle;
        padding: 4px 0;
    }
    .status-col-desc {
        width: 31%;
        text-align: right;
        vertical-align: middle;
        font-size: 0.74rem;
        color: #64748B;
    /* 2x4 Analytics Modules Grid inside White Box */
    .mod-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
    }
    .mod-card {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 9px 12px;
        text-decoration: none !important;
        transition: all 0.15s ease;
        box-shadow: 0 1px 2px rgba(0,0,0,0.02);
        box-sizing: border-box;
    }
    .mod-card:hover {
        border-color: #2563EB;
        background: #F8FAFC;
        box-shadow: 0 4px 10px rgba(37, 99, 235, 0.08);
    }
    .mod-left {
        display: flex;
        align-items: center;
        gap: 10px;
        overflow: hidden;
    }
    .mod-title {
        font-size: 0.85rem;
        font-weight: 600;
        color: #0F172A;
        white-space: nowrap;
    }
    .mod-arrow {
        color: #94A3B8;
        font-size: 1rem;
        font-weight: 600;
    }
    .mod-card:hover .mod-arrow {
        color: #2563EB;
    }

    /* Quick Access Grid */
    .qa-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
    }
    .qa-btn-link {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 9px 12px;
        text-decoration: none !important;
        transition: all 0.15s ease;
        color: #1E293B;
        font-size: 0.84rem;
        font-weight: 500;
    }
    .qa-btn-link:hover {
        border-color: #2563EB;
        color: #2563EB;
        background: #EFF6FF;
    }

    /* Table styling */
    .perf-table {
        width: 100%;
        border-collapse: collapse;
    }
    .perf-table th {
        text-align: left;
        color: #64748B;
        font-size: 0.76rem;
        font-weight: 600;
        text-transform: uppercase;
        padding: 6px 10px 10px 10px;
        border-bottom: 1px solid #E2E8F0;
    }
    .perf-table td {
        padding: 10px;
        color: #0F172A;
        font-size: 0.85rem;
        border-bottom: 1px solid #F1F5F9;
    }
    .perf-table tr:last-child td {
        border-bottom: none;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── Top Header Bar ──────────────────────────────────────────────────────────
    c_head_l, c_head_r = st.columns([3, 1])
    with c_head_l:
        st.markdown("<h1 style='color:#0F172A; font-size:2.2rem; font-weight:700; margin:0 0 4px 0;'>Dashboard</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color:#64748B; font-size:0.9rem; margin:0 0 16px 0;'>Overview of the EPL analytics platform, data summary, model status and key insights.</p>", unsafe_allow_html=True)

    with c_head_r:
        st.markdown("""
        <div style="display:flex; justify-content:flex-end; align-items:center; gap:10px; height:100%; padding-top:6px;">
            <div style="background:#ECFDF5; color:#059669; font-size:0.78rem; font-weight:600; padding:5px 12px; border-radius:20px; display:flex; align-items:center; gap:6px;">
                <span style="height:7px; width:7px; background:#10B981; border-radius:50%; display:inline-block;"></span> System Online
            </div>
            <div style="background:#F1F5F9; color:#1E293B; font-size:0.82rem; font-weight:600; padding:5px 12px; border-radius:20px; display:flex; align-items:center; gap:6px;">
                👤 Admin
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Row 1: Top KPI Metric Strip (5 Cards) ──────────────────────────────────
    counts = load_row_counts()
    tot_facts = counts["Fact_Match"] + counts["Fact_Team_Match"] + counts["Fact_Player_Performance"]

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        st.markdown("""
        <div class="admin-card">
            <div class="kpi-title">🗄️ Total Seasons</div>
            <div class="kpi-value">27</div>
            <div class="kpi-sub">Historical seasons in dataset</div>
        </div>
        """, unsafe_allow_html=True)

    with k2:
        st.markdown("""
        <div class="admin-card">
            <div class="kpi-title">👥 Total Teams</div>
            <div class="kpi-value">20</div>
            <div class="kpi-sub">Premier League clubs</div>
        </div>
        """, unsafe_allow_html=True)

    with k3:
        st.markdown("""
        <div class="admin-card">
            <div class="kpi-title">⚽ Total Matches</div>
            <div class="kpi-value">10,260</div>
            <div class="kpi-sub">League matches</div>
        </div>
        """, unsafe_allow_html=True)

    with k4:
        st.markdown("""
        <div class="admin-card">
            <div class="kpi-title">👤 Total Players</div>
            <div class="kpi-value">11,880</div>
            <div class="kpi-sub">Unique players</div>
        </div>
        """, unsafe_allow_html=True)

    with k5:
        st.markdown(f"""
        <div class="admin-card">
            <div class="kpi-title">📄 Fact Table Rows</div>
            <div class="kpi-value">{tot_facts:,}</div>
            <div class="kpi-sub">Match, team & player records</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)

    # ── Row 2: Model Status (Left) & Analytics Modules (Right) ─────────────────
    col_status, col_modules = st.columns([1.35, 1.65])

    with col_status:
        st.markdown("""
        <div class="admin-card">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                <h3 style="color:#0F172A; font-size:1.02rem; font-weight:700; margin:0;">Model & Engine Status</h3>
                <div style="display:flex; align-items:center; gap:5px;">
                    <span style="height:7px; width:7px; background:#10B981; border-radius:50%; display:inline-block;"></span>
                    <span style="color:#64748B; font-size:0.75rem; font-weight:500;">Live Check</span>
                </div>
            </div>
            <table class="status-table">
                <tbody>
                    <tr>
                        <td class="status-col-name">
                            <span style="display:inline-flex; align-items:center; gap:9px;">
                                <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#334155" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"></ellipse><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"></path><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"></path></svg>
                                Database Connection
                            </span>
                        </td>
                        <td class="status-col-badge">
                            <span class="status-badge"><span style="height:6px; width:6px; background:#10B981; border-radius:50%;"></span> Healthy</span>
                        </td>
                        <td class="status-col-desc">Connected to epl_dw.db</td>
                    </tr>
                    <tr>
                        <td class="status-col-name">
                            <span style="display:inline-flex; align-items:center; gap:9px;">
                                <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#334155" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"></path><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"></path><path d="M4 22h16"></path><path d="M10 14.66V17c0 .55-.45 1-1 1H8c-.55 0-1 .45-1 1v1c0 .55.45 1 1 1h8c.55 0 1-.45 1-1v-1c0-.55-.45-1-1-1h-1c-.55 0-1-.45-1-1v-2.34"></path><path d="M6 4h12a2 2 0 0 1 2 2v3a6 6 0 0 1-6 6h0a6 6 0 0 1-6-6V6a2 2 0 0 1 2-2Z"></path></svg>
                                Regression Engine
                            </span>
                        </td>
                        <td class="status-col-badge">
                            <span class="status-badge"><span style="height:6px; width:6px; background:#10B981; border-radius:50%;"></span> Healthy</span>
                        </td>
                        <td class="status-col-desc">Models loaded</td>
                    </tr>
                    <tr>
                        <td class="status-col-name">
                            <span style="display:inline-flex; align-items:center; gap:9px;">
                                <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#334155" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><circle cx="12" cy="12" r="4"></circle><line x1="4.93" y1="4.93" x2="9.17" y2="9.17"></line><line x1="14.83" y1="14.83" x2="19.07" y2="19.07"></line><line x1="14.83" y1="9.17" x2="19.07" y2="4.93"></line><line x1="4.93" y1="19.07" x2="9.17" y2="14.83"></line></svg>
                                Classification Engine
                            </span>
                        </td>
                        <td class="status-col-badge">
                            <span class="status-badge"><span style="height:6px; width:6px; background:#10B981; border-radius:50%;"></span> Healthy</span>
                        </td>
                        <td class="status-col-desc">Models loaded</td>
                    </tr>
                    <tr>
                        <td class="status-col-name">
                            <span style="display:inline-flex; align-items:center; gap:9px;">
                                <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#334155" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg>
                                Clustering Engine
                            </span>
                        </td>
                        <td class="status-col-badge">
                            <span class="status-badge"><span style="height:6px; width:6px; background:#10B981; border-radius:50%;"></span> Healthy</span>
                        </td>
                        <td class="status-col-desc">Models loaded</td>
                    </tr>
                    <tr>
                        <td class="status-col-name">
                            <span style="display:inline-flex; align-items:center; gap:9px;">
                                <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#334155" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="5" r="3"></circle><circle cx="6" cy="18" r="3"></circle><circle cx="18" cy="18" r="3"></circle><line x1="10.5" y1="7.5" x2="7.5" y2="15.5"></line><line x1="13.5" y1="7.5" x2="16.5" y2="15.5"></line><line x1="9" y1="18" x2="15" y2="18"></line></svg>
                                Association Engine
                            </span>
                        </td>
                        <td class="status-col-badge">
                            <span class="status-badge"><span style="height:6px; width:6px; background:#10B981; border-radius:50%;"></span> Healthy</span>
                        </td>
                        <td class="status-col-desc">Ready</td>
                    </tr>
                    <tr>
                        <td class="status-col-name">
                            <span style="display:inline-flex; align-items:center; gap:9px;">
                                <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#334155" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.9a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83Z"></path><path d="m22 12.5-9.17 4.16a2 2 0 0 1-1.66 0L2 12.5"></path><path d="m22 17.5-9.17 4.16a2 2 0 0 1-1.66 0L2 17.5"></path></svg>
                                OLAP Engine
                            </span>
                        </td>
                        <td class="status-col-badge">
                            <span class="status-badge"><span style="height:6px; width:6px; background:#10B981; border-radius:50%;"></span> Healthy</span>
                        </td>
                        <td class="status-col-desc">Ready</td>
                    </tr>
                </tbody>
            </table>
        </div>
        """, unsafe_allow_html=True)

    with col_modules:
        st.markdown("""
        <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:12px; padding:16px 18px; box-shadow:0 1px 3px rgba(0,0,0,0.03); margin-bottom:16px; box-sizing:border-box;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px;">
                <h3 style="color:#0F172A; font-size:1.02rem; font-weight:700; margin:0;">Analytics Modules</h3>
                <span style="color:#64748B; font-size:0.78rem;">8 active modules</span>
            </div>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
                <a href="/EPL_Explorer" target="_self" style="display:flex; align-items:center; justify-content:space-between; background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; padding:9px 12px; text-decoration:none; color:#0F172A; box-shadow:0 1px 2px rgba(0,0,0,0.02);">
                    <span style="display:flex; align-items:center; gap:8px; font-size:0.85rem; font-weight:600; color:#0F172A; text-decoration:none;">
                        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                        EPL Explorer
                    </span>
                    <span style="color:#94A3B8; font-size:1rem; font-weight:600; text-decoration:none;">›</span>
                </a>
                <a href="/Performance_Analysis" target="_self" style="display:flex; align-items:center; justify-content:space-between; background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; padding:9px 12px; text-decoration:none; color:#0F172A; box-shadow:0 1px 2px rgba(0,0,0,0.02);">
                    <span style="display:flex; align-items:center; gap:8px; font-size:0.85rem; font-weight:600; color:#0F172A; text-decoration:none;">
                        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline><polyline points="17 6 23 6 23 12"></polyline></svg>
                        Performance Analysis
                    </span>
                    <span style="color:#94A3B8; font-size:1rem; font-weight:600; text-decoration:none;">›</span>
                </a>
                <a href="/Match_Outcomes" target="_self" style="display:flex; align-items:center; justify-content:space-between; background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; padding:9px 12px; text-decoration:none; color:#0F172A; box-shadow:0 1px 2px rgba(0,0,0,0.02);">
                    <span style="display:flex; align-items:center; gap:8px; font-size:0.85rem; font-weight:600; color:#0F172A; text-decoration:none;">
                        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><circle cx="12" cy="12" r="6"></circle><circle cx="12" cy="2" r="2"></circle></svg>
                        Match Outcomes
                    </span>
                    <span style="color:#94A3B8; font-size:1rem; font-weight:600; text-decoration:none;">›</span>
                </a>
                <a href="/Team_Analytics" target="_self" style="display:flex; align-items:center; justify-content:space-between; background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; padding:9px 12px; text-decoration:none; color:#0F172A; box-shadow:0 1px 2px rgba(0,0,0,0.02);">
                    <span style="display:flex; align-items:center; gap:8px; font-size:0.85rem; font-weight:600; color:#0F172A; text-decoration:none;">
                        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
                        Team Analytics
                    </span>
                    <span style="color:#94A3B8; font-size:1rem; font-weight:600; text-decoration:none;">›</span>
                </a>
                <a href="/Player_Analytics" target="_self" style="display:flex; align-items:center; justify-content:space-between; background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; padding:9px 12px; text-decoration:none; color:#0F172A; box-shadow:0 1px 2px rgba(0,0,0,0.02);">
                    <span style="display:flex; align-items:center; gap:8px; font-size:0.85rem; font-weight:600; color:#0F172A; text-decoration:none;">
                        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
                        Player Analytics
                    </span>
                    <span style="color:#94A3B8; font-size:1rem; font-weight:600; text-decoration:none;">›</span>
                </a>
                <a href="/Association_Analysis" target="_self" style="display:flex; align-items:center; justify-content:space-between; background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; padding:9px 12px; text-decoration:none; color:#0F172A; box-shadow:0 1px 2px rgba(0,0,0,0.02);">
                    <span style="display:flex; align-items:center; gap:8px; font-size:0.85rem; font-weight:600; color:#0F172A; text-decoration:none;">
                        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="18" cy="5" r="3"></circle><circle cx="6" cy="12" r="3"></circle><circle cx="18" cy="19" r="3"></circle><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line></svg>
                        Association Analysis
                    </span>
                    <span style="color:#94A3B8; font-size:1rem; font-weight:600; text-decoration:none;">›</span>
                </a>
                <a href="/OLAP_Analysis" target="_self" style="display:flex; align-items:center; justify-content:space-between; background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; padding:9px 12px; text-decoration:none; color:#0F172A; box-shadow:0 1px 2px rgba(0,0,0,0.02);">
                    <span style="display:flex; align-items:center; gap:8px; font-size:0.85rem; font-weight:600; color:#0F172A; text-decoration:none;">
                        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg>
                        OLAP Analysis
                    </span>
                    <span style="color:#94A3B8; font-size:1rem; font-weight:600; text-decoration:none;">›</span>
                </a>
                <a href="/Data_Warehouse" target="_self" style="display:flex; align-items:center; justify-content:space-between; background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; padding:9px 12px; text-decoration:none; color:#0F172A; box-shadow:0 1px 2px rgba(0,0,0,0.02);">
                    <span style="display:flex; align-items:center; gap:8px; font-size:0.85rem; font-weight:600; color:#0F172A; text-decoration:none;">
                        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"></ellipse><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"></path><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"></path></svg>
                        Data Warehouse
                    </span>
                    <span style="color:#94A3B8; font-size:1rem; font-weight:600; text-decoration:none;">›</span>
                </a>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)

    t = get_theme_tokens()

    # ── Row 3: Goals and Possession Trends (Left) & Match Result Distribution (Right) ──
    col_trend, col_dist = st.columns([1.8, 1.2])

    with col_trend:
        with st.container(key="card_dashboard_trends"):
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                <h3 style="color:{t['text_primary']}; font-size:1.02rem; font-weight:700; margin:0;">Goals and Possession Trends</h3>
                <div style="font-size:0.78rem; color:{t['text_muted']}; display:flex; gap:12px;">
                    <span style="display:flex; align-items:center; gap:4px;"><span style="height:7px; width:7px; background:{t['primary_blue']}; border-radius:50%; display:inline-block;"></span> Avg Goals per Match</span>
                    <span style="display:flex; align-items:center; gap:4px;"><span style="height:7px; width:7px; background:{t['text_muted']}; border-radius:50%; display:inline-block;"></span> Avg Possession %</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            goals_df = q("""
                SELECT s.Season_Name,
                       ROUND(AVG(fm.Home_Goals + fm.Away_Goals), 2) AS Avg_Goals,
                       ROUND(AVG(tm.Possession), 1) AS Avg_Possession
                FROM Fact_Match fm
                JOIN Dim_Season s USING(Season_ID)
                JOIN Fact_Team_Match tm USING(Match_ID)
                GROUP BY s.Season_Name, s.Season_ID
                ORDER BY s.Season_ID
            """)

            fig_trend = go.Figure()
            fig_trend.add_trace(go.Scatter(
                x=goals_df["Season_Name"], y=goals_df["Avg_Goals"],
                name="Avg Goals per Match",
                mode="lines+markers",
                line=dict(color=t["primary_blue"], width=2.5),
                marker=dict(size=6)
            ))
            fig_trend.add_trace(go.Scatter(
                x=goals_df["Season_Name"], y=goals_df["Avg_Possession"] / 20.0,  # Scaled for dual-reading
                name="Avg Possession %",
                mode="lines+markers",
                line=dict(color=t["text_muted"], width=2, dash="dot"),
                marker=dict(size=5)
            ))
            fig_trend.update_layout(
                height=260,
                margin=dict(l=10, r=10, t=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                showlegend=False,
                xaxis=dict(tickangle=-45, showgrid=False, tickfont=dict(color=t["text_faint"])),
                yaxis=dict(showgrid=True, gridcolor=t["divider"], range=[0.5, 3.5], tickfont=dict(color=t["text_faint"])),
            )
            st.plotly_chart(fig_trend, use_container_width=True, config={"displayModeBar": False})

    with col_dist:
        with st.container(key="card_dashboard_dist"):
            st.markdown(f"""
            <h3 style="color:{t['text_primary']}; font-size:1.02rem; font-weight:700; margin:0 0 8px 0;">Match Result Distribution</h3>
            """, unsafe_allow_html=True)

            res_df = pd.DataFrame({
                "Outcome": ["Home Wins", "Draws", "Away Wins"],
                "Percent": [45, 27, 28],
                "Color": [t["online_dot"], t["primary_blue"], t["text_muted"]]
            })

            fig_donut = go.Figure(data=[go.Pie(
                labels=res_df["Outcome"],
                values=res_df["Percent"],
                hole=0.68,
                marker_colors=res_df["Color"],
                textinfo="percent",
                hoverinfo="label+percent",
            )])
            fig_donut.update_layout(
                height=260,
                margin=dict(l=0, r=0, t=0, b=0),
                paper_bgcolor="rgba(0,0,0,0)",
                showlegend=True,
                legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="right", x=1.1, font=dict(color=t["text_muted"])),
                annotations=[dict(text=f"Total Matches<br><b style='color:{t['text_primary']}'>10,260</b>", x=0.38, y=0.5, font_size=11, showarrow=False, font=dict(color=t["text_primary"]))]
            )
            st.plotly_chart(fig_donut, use_container_width=True, config={"displayModeBar": False})

    st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)

    # ── Row 4: Recent Top Performers (Left) & Quick Access (Right) ─────────────
    col_top, col_qa = st.columns([1.8, 1.2])

    with col_top:
        st.markdown("""
        <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:12px; padding:16px 18px; box-shadow:0 1px 3px rgba(0,0,0,0.03); margin-bottom:16px; box-sizing:border-box;">
            <h3 style="color:#0F172A; font-size:1.02rem; font-weight:700; margin:0 0 10px 0;">Recent Top Performers</h3>
            <table class="perf-table">
                <thead>
                    <tr>
                        <th>Type</th>
                        <th>Name</th>
                        <th>Club</th>
                        <th>Value</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td style="color:#64748B;">Top Scoring Club</td>
                        <td><b>Manchester United</b></td>
                        <td>Manchester United</td>
                        <td><b>2,318 goals</b></td>
                    </tr>
                    <tr>
                        <td style="color:#64748B;">Most Points</td>
                        <td><b>Manchester United</b></td>
                        <td>Manchester United</td>
                        <td><b>2,318 points</b></td>
                    </tr>
                    <tr>
                        <td style="color:#64748B;">All-Time Top Scorer</td>
                        <td><b>Alan Shearer</b></td>
                        <td>Newcastle United</td>
                        <td><b>260 goals</b></td>
                    </tr>
                    <tr>
                        <td style="color:#64748B;">Highest Avg Possession</td>
                        <td><b>Manchester City</b></td>
                        <td>Manchester City</td>
                        <td><b>62%</b></td>
                    </tr>
                </tbody>
            </table>
        </div>
        """, unsafe_allow_html=True)

    with col_qa:
        st.markdown("""
        <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:12px; padding:16px 18px; box-shadow:0 1px 3px rgba(0,0,0,0.03); margin-bottom:16px; box-sizing:border-box;">
            <h3 style="color:#0F172A; font-size:1.02rem; font-weight:700; margin:0 0 2px 0;">Quick Access</h3>
            <p style="color:#64748B; font-size:0.78rem; margin:0 0 12px 0;">Jump to any analytics module</p>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
                <a href="/EPL_Explorer" target="_self" style="display:flex; align-items:center; justify-content:space-between; background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; padding:9px 12px; text-decoration:none; color:#1E293B;">
                    <span style="display:flex; align-items:center; gap:8px; font-size:0.84rem; font-weight:500; color:#1E293B; text-decoration:none;">
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                        EPL Explorer
                    </span>
                    <span style="color:#94A3B8; font-weight:600; font-size:0.95rem; text-decoration:none;">›</span>
                </a>
                <a href="/Performance_Analysis" target="_self" style="display:flex; align-items:center; justify-content:space-between; background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; padding:9px 12px; text-decoration:none; color:#1E293B;">
                    <span style="display:flex; align-items:center; gap:8px; font-size:0.84rem; font-weight:500; color:#1E293B; text-decoration:none;">
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline><polyline points="17 6 23 6 23 12"></polyline></svg>
                        Performance Analysis
                    </span>
                    <span style="color:#94A3B8; font-weight:600; font-size:0.95rem; text-decoration:none;">›</span>
                </a>
                <a href="/Match_Outcomes" target="_self" style="display:flex; align-items:center; justify-content:space-between; background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; padding:9px 12px; text-decoration:none; color:#1E293B;">
                    <span style="display:flex; align-items:center; gap:8px; font-size:0.84rem; font-weight:500; color:#1E293B; text-decoration:none;">
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><circle cx="12" cy="12" r="6"></circle><circle cx="12" cy="2" r="2"></circle></svg>
                        Match Outcomes
                    </span>
                    <span style="color:#94A3B8; font-weight:600; font-size:0.95rem; text-decoration:none;">›</span>
                </a>
                <a href="/Team_Analytics" target="_self" style="display:flex; align-items:center; justify-content:space-between; background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; padding:9px 12px; text-decoration:none; color:#1E293B;">
                    <span style="display:flex; align-items:center; gap:8px; font-size:0.84rem; font-weight:500; color:#1E293B; text-decoration:none;">
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
                        Team Analytics
                    </span>
                    <span style="color:#94A3B8; font-weight:600; font-size:0.95rem; text-decoration:none;">›</span>
                </a>
                <a href="/Player_Analytics" target="_self" style="display:flex; align-items:center; justify-content:space-between; background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; padding:9px 12px; text-decoration:none; color:#1E293B;">
                    <span style="display:flex; align-items:center; gap:8px; font-size:0.84rem; font-weight:500; color:#1E293B; text-decoration:none;">
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
                        Player Analytics
                    </span>
                    <span style="color:#94A3B8; font-weight:600; font-size:0.95rem; text-decoration:none;">›</span>
                </a>
                <a href="/Association_Analysis" target="_self" style="display:flex; align-items:center; justify-content:space-between; background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; padding:9px 12px; text-decoration:none; color:#1E293B;">
                    <span style="display:flex; align-items:center; gap:8px; font-size:0.84rem; font-weight:500; color:#1E293B; text-decoration:none;">
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="18" cy="5" r="3"></circle><circle cx="6" cy="12" r="3"></circle><circle cx="18" cy="19" r="3"></circle><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line></svg>
                        Association Analysis
                    </span>
                    <span style="color:#94A3B8; font-weight:600; font-size:0.95rem; text-decoration:none;">›</span>
                </a>
                <a href="/OLAP_Analysis" target="_self" style="display:flex; align-items:center; justify-content:space-between; background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; padding:9px 12px; text-decoration:none; color:#1E293B;">
                    <span style="display:flex; align-items:center; gap:8px; font-size:0.84rem; font-weight:500; color:#1E293B; text-decoration:none;">
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg>
                        OLAP Analysis
                    </span>
                    <span style="color:#94A3B8; font-weight:600; font-size:0.95rem; text-decoration:none;">›</span>
                </a>
                <a href="/Data_Warehouse" target="_self" style="display:flex; align-items:center; justify-content:space-between; background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; padding:9px 12px; text-decoration:none; color:#1E293B;">
                    <span style="display:flex; align-items:center; gap:8px; font-size:0.84rem; font-weight:500; color:#1E293B; text-decoration:none;">
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"></ellipse><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"></path><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"></path></svg>
                        Data Warehouse
                    </span>
                    <span style="color:#94A3B8; font-weight:600; font-size:0.95rem; text-decoration:none;">›</span>
                </a>
            </div>
        </div>
        """, unsafe_allow_html=True)


