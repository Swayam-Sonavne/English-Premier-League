"""
pages/1_Dashboard.py — Admin Page 1: Dashboard
Technical control center, dataset summary, live ML/DWM operational checks, and 9-lab coverage.
Academic Syllabus Lab 3 (Visualization) & Platform Overview.
"""
import streamlit as st

st.set_page_config(
    page_title="Dashboard — EPL Analytics & DWM",
    page_icon="🛠️",
    layout="wide",
)

# Role Access Guard
if st.session_state.get("auth_role") != "admin":
    st.warning("🔒 Administrator authentication required to view this technical DWM dashboard.")
    if st.button("🔑 Login as Administrator", key="db_auth_req_btn"):
        st.session_state["auth_role"] = "admin"
        st.rerun()
    st.stop()

from utils.admin_views import render_admin_dashboard, render_admin_sidebar

# Render Unified Admin Sidebar Navigation
render_admin_sidebar("Dashboard")

# Render Modern Admin Dashboard matching inspiration mockup
render_admin_dashboard()
