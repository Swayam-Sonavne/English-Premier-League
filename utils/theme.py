"""
utils/theme.py — Light / dark theme engine in the landing page's editorial style.

Colours are exposed twice: as Python tokens (for Plotly and inline templates) and as CSS
variables (--bg, --card, --chip, --ink, --mute, --faint, --line, --acc, --pk, --cy) that the
page stylesheets reference, so one switch re-themes everything.
"""
import streamlit as st

PK = "#FF3E8E"  # pink accent, shared by both modes

THEME_TOKENS = {
    "dark": {
        "page_bg": "#09080D",
        "sidebar_bg": "#09080D",
        "card_bg": "#131119",
        "chip_bg": "#1C1924",
        "card_border": "#26232F",
        "divider": "#211E29",
        "chip_border": "#2E2A38",
        "input_border": "#363243",
        "grid_line": "rgba(255,255,255,0.05)",
        "text_primary": "#F3F2F6",
        "text_muted": "#A9A6B4",
        "text_faint": "#6E6B7A",
        "primary_blue": "#9D7BFF",        # main accent (kept name for existing pages)
        "amber": PK,                      # secondary accent
        "cyan": "#3CD3EE",
        "online_dot": "#22C55E",
        "form_played": "#3A2E5C",
        "form_goal": PK,
        "form_assist": "#9D7BFF",
        "form_both": "#3CD3EE",
        "form_dnp": "#1C1924",
        "zscore_pos": "#9D7BFF",
        "zscore_neg": "#6E6B7A",
        "white": "#FFFFFF",
        "is_dark": True,
    },
    "light": {
        "page_bg": "#F3F2F6",
        "sidebar_bg": "#09080D",
        "card_bg": "#FFFFFF",
        "chip_bg": "#ECEBF1",
        "card_border": "#E3E1E9",
        "divider": "#ECEAF0",
        "chip_border": "#DEDBE6",
        "input_border": "#D3D0DC",
        "grid_line": "rgba(9,8,13,0.06)",
        "text_primary": "#09080D",
        "text_muted": "#5F5C6B",
        "text_faint": "#9B98A6",
        "primary_blue": "#3A1B7A",
        "amber": PK,
        "cyan": "#13A8C8",
        "online_dot": "#16A34A",
        "form_played": "#D9D1EE",
        "form_goal": PK,
        "form_assist": "#3A1B7A",
        "form_both": "#13A8C8",
        "form_dnp": "#ECEBF1",
        "zscore_pos": "#3A1B7A",
        "zscore_neg": "#9B98A6",
        "white": "#FFFFFF",
        "is_dark": False,
    },
}


def init_theme():
    if "theme_mode" not in st.session_state:
        st.session_state["theme_mode"] = "light"


def get_theme_mode() -> str:
    init_theme()
    return st.session_state.get("theme_mode", "light")


def get_theme_tokens() -> dict:
    return THEME_TOKENS.get(get_theme_mode(), THEME_TOKENS["light"])


def toggle_theme():
    init_theme()
    st.session_state["theme_mode"] = "dark" if st.session_state["theme_mode"] == "light" else "light"
    st.rerun()


def render_theme_toggle_button(key="sb_theme_toggle"):
    """Kept for older call sites; the top bar now owns the toggle."""
    mode = get_theme_mode()
    if st.button("Dark mode" if mode == "light" else "Light mode", use_container_width=True, key=key, type="secondary"):
        toggle_theme()


def inject_theme_css():
    t = get_theme_tokens()
    dark = t["is_dark"]
    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Anton&family=Inter:wght@400;500;600;700&display=swap');
:root, .stApp {{
  --bg:{t['page_bg']}; --card:{t['card_bg']}; --chip:{t['chip_bg']}; --ink:{t['text_primary']};
  --mute:{t['text_muted']}; --faint:{t['text_faint']}; --line:{t['card_border']}; --gl:{t['grid_line']};
  --acc:{t['primary_blue']}; --pk:{PK}; --cy:{t['cyan']}; --nav:{'#1A1722' if dark else '#09080D'};
  --bar:{'#E2E5EA' if dark else '#0F0E14'}; --barline:{'#09080D' if dark else 'rgba(255,255,255,.24)'};
  --brand:{'#5E6B7A' if dark else '#B7C0CC'}; --pill:{'#FFFFFF' if dark else '#1C1A24'}; --pillink:{'#09080D' if dark else '#F3F2F6'};
  --barfaint:{'#9B98A6' if dark else '#4A4757'};
}}
/* reruns: never show the previous screen's leftovers (Streamlit keeps them faded until replaced) */
[data-stale="true"] {{ opacity:0 !important; transition:opacity .2s ease .3s !important; pointer-events:none !important; }}
[data-stale="false"] {{ transition:opacity .2s ease !important; }}
.st-key-topbar [data-stale="true"], .st-key-pghead [data-stale="true"] {{ display:none !important; }}
.stElementContainer:has(iframe[height="0"]) {{ display:none !important; }}
/* page change: current content settles back while the next page loads, then the new page glides in */
body.pg-leave .stMain .stElementContainer:not(.st-key-topbar *):not(.st-key-subnav *) {{
  opacity:.25 !important; transform:translateY(-6px) scale(.995); transition:opacity .25s ease, transform .25s ease !important; }}
body.pg-enter .stMain .stElementContainer:not(.st-key-topbar *):not(.st-key-subnav *) {{
  animation:pg-in .5s cubic-bezier(.2,.8,.2,1) both; }}
body.pg-enter .stMain .stElementContainer:not(.st-key-topbar *):nth-child(n+3) {{ animation-delay:.05s; }}
body.pg-enter .stMain .stElementContainer:not(.st-key-topbar *):nth-child(n+5) {{ animation-delay:.1s; }}
@keyframes pg-in {{ from {{ opacity:0; transform:translateY(14px); }} to {{ opacity:1; transform:none; }} }}
@media (prefers-reduced-motion: reduce) {{
  body.pg-leave .stMain .stElementContainer, body.pg-enter .stMain .stElementContainer {{ animation:none !important; transform:none !important; }} }}
html, body, .stApp {{ background:var(--bg) !important; color:var(--ink) !important; font-family:'Inter',sans-serif !important; }}
[data-testid="stAppViewContainer"], [data-testid="stMain"], .stMain, [data-testid="stHeader"] {{ background:transparent !important; }}
[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="stSidebarNav"] {{ display:none !important; }}

/* vertical grid lines, as on the landing page */
.stApp::before {{ content:''; position:fixed; inset:0; pointer-events:none; z-index:0;
  background-image:repeating-linear-gradient(90deg,transparent 0,transparent calc(100%/7 - 1px),var(--gl) calc(100%/7 - 1px),var(--gl) calc(100%/7)); }}
[data-testid="stAppViewContainer"] {{ position:relative; z-index:1; }}
.block-container {{ padding-top:.6rem !important; padding-bottom:.6rem !important; max-width:1440px !important; }}
.stMain [data-testid="stVerticalBlock"] {{ gap:.55rem; }}
.stMain [data-testid="stHorizontalBlock"] {{ gap:.6rem; }}
[class*="st-key-card_"] {{ padding:12px 14px !important; margin:0 !important; gap:.4rem !important; height:100%; }}
div[data-baseweb="select"] > div {{ min-height:34px !important; }}
.stMain [data-testid="stPlotlyChart"] {{ margin:0 !important; }}

/* typography */
.stMain h1, .stMain h2, .stMain h3 {{ font-family:'Anton',sans-serif !important; font-weight:400 !important; text-transform:uppercase;
  letter-spacing:.01em !important; color:var(--ink) !important; line-height:1.02 !important; }}
.stMain h1 {{ font-size:clamp(30px,3.4vw,48px) !important; }}
.stMain h2 {{ font-size:1.55rem !important; }}
.stMain h3 {{ font-size:1.2rem !important; }}
.stMain h4, .stMain h5, .stMain h6 {{ color:var(--ink) !important; font-family:'Inter',sans-serif !important; }}
.stMain p, .stMain li, .stMain label, .stMain span, .stMain td, .stMain th {{ color:inherit; }}
.stMain [data-testid="stMarkdownContainer"] {{ color:var(--ink); }}
.stCaption, [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {{ color:var(--mute) !important; }}
hr {{ border-color:var(--line) !important; }}
a {{ color:var(--acc); }}

/* cards: flat, thin rule, square-ish corners */
.admin-card, .pa-card, .ta-card, .mo-card, .pe-card, .exp-card, .explorer-card, .olap-card, .dw-card, .stat-card,
.highlight-card, .player-hero-card, div[data-testid="stExpander"], [class*="st-key-card_"],
.ta-metric-box, .mo-metric-box, .pa-metric-box, .pe-metric-box, .kpi-metric-box, div[data-testid="stMetric"], div[data-testid="metric-container"] {{
  background:var(--card) !important; border:1px solid var(--line) !important; border-radius:6px !important;
  box-shadow:none !important; color:var(--ink) !important; }}
div[data-testid="stMetric"] {{ padding:14px 16px !important; }}
[data-testid="stMetricValue"], [data-testid="stMetricValue"] * {{ font-family:'Anton',sans-serif !important; color:var(--ink) !important; font-weight:400 !important; }}
[data-testid="stMetricValue"] {{ font-size:clamp(1.3rem,2vw,1.8rem) !important; }}
[data-testid="stMetricLabel"] p {{ color:var(--mute) !important; text-transform:uppercase; letter-spacing:.12em; font-size:.7rem !important; }}
.ta-metric-title, .mo-metric-title, .pa-metric-title, .pe-metric-title, .kpi-title, .stat-card-title, .highlight-label {{
  color:var(--mute) !important; text-transform:uppercase; letter-spacing:.12em; font-size:.7rem !important; }}
.ta-metric-val, .mo-metric-val, .pa-metric-val, .pe-metric-val, .kpi-val, .kpi-value, .stat-card-value, .highlight-value {{
  color:var(--ink) !important; font-family:'Anton',sans-serif !important; font-weight:400 !important; letter-spacing:.01em; }}
.ta-metric-sub, .mo-metric-sub, .pa-metric-sub, .pe-metric-sub, .kpi-sub, .highlight-sub {{ color:var(--faint) !important; }}
.kpi-icon-wrap, .meta-pill, .ta-badge, .pa-badge, .mo-badge, .pe-badge, .rank-pill {{
  background:var(--chip) !important; border:1px solid var(--line) !important; color:var(--mute) !important; }}
.meta-pill b, .rank-pill b {{ color:var(--ink) !important; }}
.mo-tab-wrap, .ta-seg-ctrl {{ background:var(--chip) !important; border:1px solid var(--line) !important; }}
.mo-tab-btn, .ta-seg-btn {{ color:var(--mute) !important; }}
.mo-tab-btn.active, .ta-seg-btn.active {{ background:var(--ink) !important; color:var(--bg) !important; }}

/* tables */
.pa-table th, .ta-table th, .mo-table th, .pe-table th, .exp-table th, .custom-table th, .status-table th {{
  color:var(--mute) !important; border-bottom:1px solid var(--line) !important; background:transparent !important;
  text-transform:uppercase; letter-spacing:.1em; font-size:.68rem !important; }}
.pa-table td, .ta-table td, .mo-table td, .pe-table td, .exp-table td, .custom-table td, .status-table td {{
  color:var(--ink) !important; border-bottom:1px solid var(--line) !important; }}
.pa-table tr:hover td, .ta-table tr:hover td, .mo-table tr:hover td, .pe-table tr:hover td {{ background:var(--chip) !important; }}
div[data-testid="stDataFrame"], [data-testid="stTable"] {{ border:1px solid var(--line) !important; border-radius:6px !important; }}
{'div[data-testid="stDataFrame"] canvas, div[data-testid="stDataFrame"] [class*="dvn-"] {filter:invert(.9) hue-rotate(180deg);}' if dark else ''}

/* inputs */
div[data-baseweb="select"] > div, div[data-baseweb="input"], div[data-baseweb="input"] > div, div[data-baseweb="textarea"],
div[data-baseweb="base-input"], .stNumberInput input, .stDateInput input {{
  background:var(--card) !important; border-color:var(--line) !important; color:var(--ink) !important; border-radius:4px !important; }}
div[data-baseweb="select"] span, div[data-baseweb="input"] input, textarea {{ color:var(--ink) !important; }}
span[data-baseweb="tag"] {{ background:var(--chip) !important; border:1px solid var(--line) !important; color:var(--ink) !important; }}
div[data-baseweb="popover"], ul[role="listbox"], li[role="option"] {{ background:var(--card) !important; color:var(--ink) !important; }}
li[role="option"]:hover {{ background:var(--chip) !important; }}
[data-testid="stWidgetLabel"] p, .stMain label p {{ color:var(--mute) !important; font-size:.78rem !important; font-weight:600 !important; }}
.stCheckbox label span, .stRadio label span, .stRadio label p, .stCheckbox label p {{ color:var(--ink) !important; }}
div[data-baseweb="slider"] div[role="slider"] {{ background:var(--pk) !important; }}

/* buttons */
.stMain div[data-testid="stButton"] > button, .stMain div[data-testid="stDownloadButton"] > button, .stMain div[data-testid="stFormSubmitButton"] > button {{
  border-radius:3px !important; font-weight:600 !important; letter-spacing:.04em; }}
.stMain div[data-testid="stButton"] > button[kind="primary"], .stMain div[data-testid="stFormSubmitButton"] > button {{
  background:var(--pk) !important; color:#fff !important; border:0 !important; }}
.stMain div[data-testid="stButton"] > button[kind="primary"]:hover {{ background:#E52A78 !important; }}
.stMain div[data-testid="stButton"] > button[kind="secondary"] {{ background:var(--card) !important; color:var(--ink) !important; border:1px solid var(--line) !important; }}
.stMain div[data-testid="stButton"] > button[kind="secondary"]:hover {{ border-color:var(--ink) !important; }}

/* tabs */
button[data-baseweb="tab"] p {{ color:var(--mute) !important; font-weight:600; letter-spacing:.06em; text-transform:uppercase; font-size:.78rem !important; }}
button[data-baseweb="tab"][aria-selected="true"] p {{ color:var(--ink) !important; }}
div[data-baseweb="tab-highlight"] {{ background:var(--pk) !important; }}
div[data-baseweb="tab-border"] {{ background:var(--line) !important; }}

pre, code {{ background:var(--chip) !important; color:var(--acc) !important; border:1px solid var(--line) !important; }}
div[data-testid="stAlert"] {{ background:var(--card) !important; border:1px solid var(--line) !important; border-left:3px solid var(--acc) !important; color:var(--ink) !important; border-radius:4px !important; }}
div[data-testid="stAlert"] p {{ color:var(--ink) !important; }}
div[data-testid="stAlert"] > div, div[data-testid="stAlertContainer"] {{ background:transparent !important; color:var(--ink) !important; }}
div[data-testid="stExpander"] summary p {{ color:var(--ink) !important; font-weight:600; }}
</style>
""", unsafe_allow_html=True)


def get_plotly_theme_layout() -> dict:
    t = get_theme_tokens()
    return {
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": dict(color=t["text_muted"], family="Inter, sans-serif"),
        "grid_color": t["divider"],
        "legend_bg": "rgba(0,0,0,0)",
        "tokens": t,
        "is_dark": t["is_dark"],
    }
