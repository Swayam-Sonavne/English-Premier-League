"""
app.py — EPL Football Analytics & Data Mining Platform
Dual-Layer Role Architecture:
  1. 👤 USER MODE (EPL Insights)
  2. 🛠️ ADMIN MODE (EPL Analytics & DWM)
"""
import streamlit as st

st.set_page_config(
    page_title="EPL Analytics Platform",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Session State for Authentication & Subpages ───────────────────────────────
if "auth_role" not in st.session_state:
    st.session_state["auth_role"] = None  # None, 'user', 'admin'

if "user_subpage" not in st.session_state:
    st.session_state["user_subpage"] = "Dashboard"


# ═══════════════════════════════════════════════════════════════════════════════
# VIEW 1: SCROLL-STORY LANDING PAGE WITH SIGN IN / SIGN UP (When auth_role is None)
# ═══════════════════════════════════════════════════════════════════════════════
if st.session_state["auth_role"] is None:
    from utils.landing import render_landing
    render_landing()


# ═══════════════════════════════════════════════════════════════════════════════
# SIGNED-IN MODES: shared shell (top nav, header, theme) + the page body
# ═══════════════════════════════════════════════════════════════════════════════
else:
    from utils.shell import render_shell

    if st.session_state["auth_role"] == "user":
        from utils.user_views import render_user_clubs, render_user_dashboard, render_user_players

        subpage = st.session_state.get("user_subpage", "Dashboard")
        if subpage not in ("Dashboard", "Clubs", "Players"):
            subpage = st.session_state["user_subpage"] = "Dashboard"
        slot = render_shell("user", subpage)
        {"Dashboard": render_user_dashboard, "Clubs": render_user_clubs, "Players": render_user_players}[subpage](slot)

    elif st.session_state["auth_role"] == "admin":
        from utils.admin_views import render_admin_dashboard, render_admin_sidebar

        render_admin_sidebar("Dashboard")
        render_admin_dashboard()
