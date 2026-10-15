"""
utils/theme.py — Universal Dark / Light Theme Engine for EPL Analytics & DWM Platform
Provides token-based theme management, dynamic CSS variable injection, and Plotly theme styling.
"""
import streamlit as st

# ── EXACT TOKEN DEFINITIONS ──────────────────────────────────────────────────
THEME_TOKENS = {
    "dark": {
        "page_bg": "#0A0F1C",             # Page background
        "sidebar_bg": "#060A14",          # Sidebar
        "card_bg": "#111A2E",             # Card / input / KPI strip
        "chip_bg": "#17223A",             # Chip and tag fill, table highlight
        "card_border": "#25314A",         # Card border
        "divider": "#1E2940",             # Dividers, bar tracks, chart grid lines
        "chip_border": "#2B3957",         # Chip border
        "input_border": "#34425F",        # Input border, "Level" segment
        "text_primary": "#E6ECF7",        # Primary text
        "text_muted": "#94A3B8",          # Muted text (labels, captions)
        "text_faint": "#64748B",          # Faint text (axis ticks, chart rings)
        "primary_blue": "#3B82F6",        # Primary blue (selected nav, buttons, Player A)
        "amber": "#F59E0B",               # Amber (Player B, assists)
        "online_dot": "#16A34A",          # Online status dot
        "form_played": "#2B4A86",         # "played" cells in season form strip
        "form_goal": "#F59E0B",           # Goals
        "form_assist": "#3B82F6",         # Assists
        "form_both": "#8B5CF6",           # Goal + assist
        "form_dnp": "#17223A",            # Not in squad / empty
        "zscore_pos": "#3B82F6",          # Positive z-score
        "zscore_neg": "#8A94A6",          # Negative z-score
        "white": "#FFFFFF",
        "is_dark": True,
    },
    "light": {
        "page_bg": "#EEF2F8",             # Page background
        "sidebar_bg": "#0B1220",          # Sidebar
        "card_bg": "#FFFFFF",             # Card / input / KPI strip
        "chip_bg": "#F4F7FC",             # Chip and tag fill, table highlight
        "card_border": "#D5DBE6",         # Card border
        "divider": "#E6EAF0",             # Dividers, bar tracks, chart grid lines
        "chip_border": "#DDE3EE",         # Chip border
        "input_border": "#C5CDDB",        # Input border, "Level" segment
        "text_primary": "#0B1220",        # Primary text
        "text_muted": "#5B6578",          # Muted text (labels, captions)
        "text_faint": "#9AA4B2",          # Faint text (axis ticks, chart rings)
        "primary_blue": "#2563EB",        # Primary blue (selected nav, buttons, Player A)
        "amber": "#D97706",               # Amber (Player B, assists)
        "online_dot": "#16A34A",          # Online status dot
        "form_played": "#BFD0F7",         # "played" cells in season form strip
        "form_goal": "#D97706",           # Goals
        "form_assist": "#2563EB",         # Assists
        "form_both": "#7C3AED",           # Goal + assist
        "form_dnp": "#F1F5F9",            # Not in squad / empty
        "zscore_pos": "#2563EB",          # Positive z-score
        "zscore_neg": "#64748B",          # Negative z-score
        "white": "#FFFFFF",
        "is_dark": False,
    }
}


def init_theme():
    """Initialise theme in session state if not already set."""
    if "theme_mode" not in st.session_state:
        st.session_state["theme_mode"] = "light"


def get_theme_mode() -> str:
    """Return 'light' or 'dark'."""
    init_theme()
    return st.session_state.get("theme_mode", "light")


def get_theme_tokens() -> dict:
    """Return the active token dictionary for python calculations & inline templates."""
    mode = get_theme_mode()
    return THEME_TOKENS.get(mode, THEME_TOKENS["light"])


def toggle_theme():
    """Toggle between light and dark mode and trigger rerun."""
    init_theme()
    st.session_state["theme_mode"] = "dark" if st.session_state["theme_mode"] == "light" else "light"
    st.rerun()


def render_theme_toggle_button(key="sb_theme_toggle"):
    """Render a sleek sidebar toggle button for light/dark mode."""
    mode = get_theme_mode()
    btn_label = "🌙 Dark Mode" if mode == "light" else "☀️ Light Mode"
    if st.button(btn_label, use_container_width=True, key=key, type="secondary"):
        toggle_theme()


def inject_theme_css():
    """
    Injects comprehensive CSS rules based on the active theme tokens.
    Uses the exact 3-step surface ladder (page -> card -> chip).
    """
    t = get_theme_tokens()
    is_dark = t["is_dark"]

    st.markdown(f"""
    <style>
    /* Global App Background & Typography */
    html, body, .stApp {{
        background-color: {t['page_bg']} !important;
        color: {t['text_primary']} !important;
        transition: background-color 0.2s ease, color 0.2s ease;
    }}

    /* Global Headings & Text */
    h1, h2, h3, h4, h5, h6 {{
        color: {t['text_primary']} !important;
    }}
    p, span, label, div {{
        color: inherit;
    }}
    .stCaption, [data-testid="stCaptionContainer"] {{
        color: {t['text_muted']} !important;
    }}
    hr {{
        border-color: {t['divider']} !important;
    }}

    /* Universal Cards Across All Pages (3-Step Surface Ladder) */
    .admin-card, .pa-card, .ta-card, .mo-card, .pe-card, .exp-card, .explorer-card,
    .olap-card, .dw-card, .stat-card, .highlight-card, .player-hero-card,
    div[data-testid="stExpander"], [class*="st-key-card_"] {{
        background-color: {t['card_bg']} !important;
        border: 1px solid {t['card_border']} !important;
        border-radius: 12px !important;
        box-shadow: { '0 4px 16px rgba(0,0,0,0.5)' if is_dark else '0 1px 3px rgba(0,0,0,0.03)' } !important;
        color: {t['text_primary']} !important;
    }}

    [class*="st-key-card_"] {{
        padding: 16px 18px !important;
        margin-bottom: 16px !important;
        box-sizing: border-box !important;
    }}
    [class*="st-key-card_"] p {{
        margin-bottom: 2px !important;
    }}
    [class*="st-key-card_"] .stCaption, [class*="st-key-card_"] [data-testid="stCaptionContainer"] {{
        margin-bottom: 8px !important;
    }}

    /* Metric Boxes & KPI Strips */
    .ta-metric-box, .mo-metric-box, .pa-metric-box, .pe-metric-box, .kpi-metric-box,
    div[data-testid="metric-container"] {{
        background-color: {t['card_bg']} !important;
        border: 1px solid {t['card_border']} !important;
        border-radius: 12px !important;
        color: {t['text_primary']} !important;
    }}

    /* KPI / Metric Values & Titles */
    .ta-metric-title, .mo-metric-title, .pa-metric-title, .pe-metric-title, .kpi-title,
    .stat-card-title, .highlight-label {{
        color: {t['text_muted']} !important;
    }}
    .ta-metric-val, .mo-metric-val, .pa-metric-val, .pe-metric-val, .kpi-val,
    .stat-card-value, .highlight-value {{
        color: {t['text_primary']} !important;
    }}
    .ta-metric-sub, .mo-metric-sub, .pa-metric-sub, .pe-metric-sub, .kpi-sub,
    .highlight-sub {{
        color: {t['text_faint']} !important;
    }}
    .kpi-icon-wrap {{
        background-color: {t['chip_bg']} !important;
        border: 1px solid {t['chip_border']} !important;
    }}

    /* Meta Pills & Badges (Chip Level in 3-Step Ladder) */
    .meta-pill {{
        background-color: {t['chip_bg']} !important;
        color: {t['text_muted']} !important;
        border: 1px solid {t['chip_border']} !important;
    }}
    .meta-pill b {{
        color: {t['text_primary']} !important;
    }}
    .ta-badge, .pa-badge, .mo-badge, .pe-badge {{
        background-color: {t['chip_bg']} !important;
        color: {t['text_muted']} !important;
        border: 1px solid {t['chip_border']} !important;
    }}
    .rank-pill {{
        background-color: {t['chip_bg']} !important;
        border: 1px solid {t['chip_border']} !important;
        color: {t['text_muted']} !important;
    }}
    .rank-pill b {{
        color: {t['text_primary']} !important;
    }}

    /* Segmented Controls */
    .mo-tab-wrap, .ta-seg-ctrl {{
        background-color: {t['chip_bg']} !important;
        border: 1px solid {t['input_border']} !important;
    }}
    .mo-tab-btn, .ta-seg-btn {{
        color: {t['text_muted']} !important;
    }}
    .mo-tab-btn.active, .ta-seg-btn.active {{
        background-color: {t['primary_blue']} !important;
        color: {t['white']} !important;
    }}

    /* Tables */
    .pa-table, .ta-table, .mo-table, .pe-table, .exp-table, .custom-table {{
        width: 100% !important;
        border-collapse: collapse !important;
    }}
    .pa-table th, .ta-table th, .mo-table th, .pe-table th, .exp-table th, .custom-table th {{
        color: {t['text_muted']} !important;
        border-bottom: 1px solid {t['card_border']} !important;
        background-color: transparent !important;
    }}
    .pa-table td, .ta-table td, .mo-table td, .pe-table td, .exp-table td, .custom-table td {{
        color: {t['text_primary']} !important;
        border-bottom: 1px solid {t['divider']} !important;
    }}
    .pa-table tr:hover td, .ta-table tr:hover td, .mo-table tr:hover td, .pe-table tr:hover td {{
        background-color: { 'rgba(255,255,255,0.03)' if is_dark else 'rgba(0,0,0,0.01)' } !important;
    }}

    /* Streamlit Interactive DataFrames */
    div[data-testid="stDataFrame"], [data-testid="stTable"] {{
        background-color: {t['card_bg']} !important;
        border: 1px solid {t['card_border']} !important;
        border-radius: 8px !important;
    }}

    /* Form & Input Controls */
    div[data-baseweb="select"] > div {{
        background-color: {t['card_bg']} !important;
        border-color: {t['input_border']} !important;
        color: {t['text_primary']} !important;
    }}
    div[data-baseweb="select"] span {{
        color: {t['text_primary']} !important;
    }}
    span[data-baseweb="tag"] {{
        background-color: {t['chip_bg']} !important;
        border: 1px solid {t['chip_border']} !important;
        color: {t['text_primary']} !important;
    }}
    div[data-baseweb="input"] > div {{
        background-color: {t['card_bg']} !important;
        border-color: {t['input_border']} !important;
        color: {t['text_primary']} !important;
    }}
    div[data-baseweb="input"] input {{
        color: {t['text_primary']} !important;
    }}
    div[data-baseweb="popover"], ul[role="listbox"] {{
        background-color: {t['card_bg']} !important;
        border: 1px solid {t['card_border']} !important;
        color: {t['text_primary']} !important;
    }}
    li[role="option"] {{
        background-color: {t['card_bg']} !important;
        color: {t['text_primary']} !important;
    }}
    li[role="option"]:hover {{
        background-color: {t['chip_bg']} !important;
    }}

    /* Primary Action Buttons */
    div[data-testid="stButton"] > button[kind="primary"] {{
        background-color: {t['primary_blue']} !important;
        color: {t['white']} !important;
        font-weight: 600 !important;
        border: none !important;
        border-radius: 8px !important;
    }}
    div[data-testid="stButton"] > button[kind="primary"]:hover {{
        background-color: { '#2563EB' if is_dark else '#1D4ED8' } !important;
    }}

    /* Tabs Styling */
    button[data-baseweb="tab"] {{
        color: {t['text_muted']} !important;
    }}
    button[data-baseweb="tab"][aria-selected="true"] {{
        color: {t['primary_blue']} !important;
        font-weight: 600 !important;
    }}
    div[data-baseweb="tab-highlight"] {{
        background-color: {t['primary_blue']} !important;
    }}
    div[data-baseweb="tab-border"] {{
        background-color: {t['card_border']} !important;
    }}

    /* Checkbox & Radio Labels */
    .stCheckbox label span, .stRadio label span {{
        color: {t['text_primary']} !important;
    }}

    /* Streamlit Code & Pre Blocks */
    pre, code {{
        background-color: {t['chip_bg']} !important;
        color: {t['primary_blue']} !important;
        border: 1px solid {t['card_border']} !important;
    }}

    /* Alerts */
    div[data-testid="stAlert"] {{
        background-color: {t['card_bg']} !important;
        border: 1px solid {t['card_border']} !important;
        color: {t['text_primary']} !important;
    }}

    /* Sidebar Background */
    [data-testid="stSidebar"] {{
        background-color: {t['sidebar_bg']} !important;
    }}
    </style>
    """, unsafe_allow_html=True)


def get_plotly_theme_layout() -> dict:
    """Return standard Plotly layout overrides for dark/light mode."""
    t = get_theme_tokens()
    return {
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": dict(color=t["text_muted"], family="sans-serif"),
        "grid_color": t["divider"],
        "legend_bg": "rgba(17, 26, 46, 0.9)" if t["is_dark"] else "rgba(255, 255, 255, 0.9)",
        "tokens": t,
        "is_dark": t["is_dark"],
    }
