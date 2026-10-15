"""
utils/shell.py — Shared chrome for every signed-in page.

  render_shell(role, current)  theme CSS, sticky pill nav (replaces the sidebar), chart theming
  page_header(page)            editorial header: kicker, Anton title, one plain-English line
"""
import json
import os

import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

from utils.theme import PK, get_theme_mode, get_theme_tokens, inject_theme_css

STATIC = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")

USER_NAV = [("Dashboard", "Dashboard"), ("Clubs", "Clubs"), ("Players", "Players")]
ADMIN_NAV = [
    ("Overview", "Dashboard", "app.py"),
    ("Explorer", "EPL Explorer", "pages/2_EPL_Explorer.py"),
    ("Regression", "Performance Analysis", "pages/3_Performance_Analysis.py"),
    ("Classification", "Match Outcomes", "pages/4_Match_Outcomes.py"),
    ("Clustering", "Team Analytics", "pages/5_Team_Analytics.py"),
    ("Players", "Player Analytics", "pages/6_Player_Analytics.py"),
    ("Association", "Association Analysis", "pages/7_Association_Analysis.py"),
    ("OLAP", "OLAP Analysis", "pages/8_OLAP_Analysis.py"),
    ("Warehouse", "Data Warehouse", "pages/9_Data_Warehouse.py"),
]
# admin pages grouped so the top bar stays short; groups with several pages get a sub-row
ADMIN_GROUPS = [
    ("Overview", ["Dashboard"]),
    ("Explore", ["EPL Explorer", "OLAP Analysis"]),
    ("Mining", ["Match Outcomes", "Performance Analysis", "Team Analytics", "Association Analysis"]),
    ("Players", ["Player Analytics"]),
    ("Warehouse", ["Data Warehouse"]),
]

# kicker, title, plain-English line (written for readers who don't follow football)
PAGE_INFO = {
    "User:Dashboard": ("Overview", "The league in numbers",
                       "Pick a season on the right: the highlights, the table and the chart all follow it. The predictor estimates any fixture from that season."),
    "Clubs": ("Clubs", "Clubs",
              "One club, one season: where it finished, how it got there and its long-term trend. Add a rival to compare."),
    "Players": ("Players", "Players",
                "A player's season in numbers, how it built up match by match, and where it ranks among the league's scorers."),
    "Dashboard": ("Admin · overview", "Control room",
                  "What is in the warehouse, which models are ready, and where each course topic lives in the app."),
    "EPL Explorer": ("Admin · exploration", "EPL explorer",
                     "Filter the warehouse by season, club, player or stadium and watch every chart update."),
    "Performance Analysis": ("Admin · regression", "Performance analysis",
                             "Linear regression: how much shots, possession or fouls change the number of goals scored."),
    "Match Outcomes": ("Admin · classification", "Match outcomes",
                       "Three classifiers predict win, draw or loss. Compare their accuracy, confusion matrices and ROC curves."),
    "Team Analytics": ("Admin · clustering", "Team analytics",
                       "K-Means and hierarchical clustering group clubs with similar playing styles, without labels."),
    "Player Analytics": ("Admin · players", "Player analytics",
                         "Per-90 rates, percentiles and similar-player search across every season."),
    "Association Analysis": ("Admin · association rules", "Association analysis",
                             "Apriori finds match events that tend to occur together, and which combinations lead to a win."),
    "OLAP Analysis": ("Admin · OLAP", "OLAP analysis",
                      "Roll-up, drill-down, slice, dice and pivot the warehouse cube, with the SQL behind each step."),
    "Data Warehouse": ("Admin · design", "Data warehouse",
                       "The star schema: 3 fact tables and 8 dimension tables, with a dictionary of every column."),
}


# ── chart theming: every st.plotly_chart figure is re-coloured for the active mode ──
_OLD_ACC = {"#2563eb", "#3b82f6", "#1d4ed8", "#1e3a5f", "#6f42c1", "#1e40af", "#3a1b7a", "#9d7bff"}
_OLD_PK = {"#f59e0b", "#d97706", "#e8b84b", "#fbbf24"}
_OLD_CY = {"#60a5fa", "#93c5fd", "#38bdf8", "#13a8c8", "#3cd3ee"}
_OLD_INK = {"#0f172a", "#1e293b", "#0b1220", "#334155", "#111827"}
_OLD_MUTE = {"#64748b", "#94a3b8", "#475569", "#5b6578"}
_OLD_LINE = {"#f1f5f9", "#e2e8f0", "#e6eaf0", "#d5dbe6", "#cbd5e1"}


def _map_colour(c, t):
    if not isinstance(c, str):
        return c
    k = c.strip().lower()
    if k in _OLD_ACC:
        return t["primary_blue"]
    if k in _OLD_PK:
        return PK
    if k in _OLD_CY:
        return t["cyan"]
    if k in _OLD_INK:
        return t["text_primary"]
    if k in _OLD_MUTE:
        return t["text_muted"]
    if k in _OLD_LINE:
        return t["divider"]
    return c


def theme_figure(fig):
    if not isinstance(fig, go.Figure):
        return fig
    t = get_theme_tokens()
    m = lambda c: _map_colour(c, t)
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=t["text_muted"]),
        colorway=[t["primary_blue"], PK, t["cyan"], t["text_faint"], "#7C5CFF", "#FF8FBF", "#16A34A"],
        hoverlabel=dict(bgcolor=t["card_bg"], bordercolor=t["card_border"], font=dict(color=t["text_primary"], family="Inter")),
    )
    if fig.layout.title and fig.layout.title.text:
        fig.update_layout(title_font=dict(color=t["text_primary"], family="Inter", size=14))
    fig.update_layout(legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=t["text_muted"])))
    for ax in list(fig.select_xaxes()) + list(fig.select_yaxes()):
        ax.update(gridcolor=t["divider"], zerolinecolor=t["card_border"], linecolor=t["card_border"],
                  tickfont=dict(color=t["text_faint"]))
        if ax.title and ax.title.text:
            ax.title.font.color = t["text_muted"]
    for p in fig.select_polars():
        p.update(bgcolor="rgba(0,0,0,0)", radialaxis=dict(gridcolor=t["divider"], linecolor=t["card_border"]),
                 angularaxis=dict(gridcolor=t["divider"], linecolor=t["card_border"]))
    for a in fig.layout.annotations or []:
        if a.font and a.font.color:
            a.font.color = m(a.font.color)
        if a.bgcolor:
            a.bgcolor = "rgba(0,0,0,0)"
    for s in fig.layout.shapes or []:
        if s.line and s.line.color:
            s.line.color = m(s.line.color)
        if s.fillcolor:
            s.fillcolor = m(s.fillcolor)
    for tr in fig.data:
        for path in ("marker.color", "marker.line.color", "line.color", "textfont.color", "fillcolor", "insidetextfont.color"):
            try:
                node = tr
                for part in path.split(".")[:-1]:
                    node = getattr(node, part)
                leaf = path.split(".")[-1]
                val = getattr(node, leaf)
            except (AttributeError, ValueError):
                continue
            if isinstance(val, str):
                setattr(node, leaf, m(val))
            elif isinstance(val, (list, tuple)) and val and all(isinstance(v, str) for v in val):
                setattr(node, leaf, [m(v) for v in val])
        try:
            cs = tr.colorscale
            if cs and len(cs) and str(cs[-1][1]).lower() in ("rgb(8,48,107)", "#08306b"):
                tr.colorscale = [[0, t["chip_bg"]], [1, t["primary_blue"]]]
        except (AttributeError, ValueError):
            pass
    return fig


def _patch_plotly():
    if getattr(st, "_pldw_patched", False):
        return
    original = st.plotly_chart

    def plotly_chart(fig, *args, **kwargs):
        return original(theme_figure(fig), *args, **kwargs)

    st.plotly_chart = plotly_chart
    st._pldw_patched = True


# ── chrome ─────────────────────────────────────────────────────────────────────
NAV_CSS = """
<style>
/* top bar: one slim outlined panel, pinned to the window — logo left, outlined pill links, icon pills, theme switch */
.block-container{padding-top:84px!important}
.st-key-topbar [data-stale="true"]{display:none!important}
/* each part of the bar holds exactly one row of columns; anything after it is a leftover from the previous screen */
.st-key-topbar>*:not(:first-child),.st-key-navmid>*:not(:first-child),.st-key-navend>*:not(:first-child){display:none!important}
.st-key-topbar{position:fixed;top:10px;left:20px;right:20px;width:auto!important;z-index:1000;margin:0!important;
  padding:6px 8px 6px 18px!important;background:var(--bar)!important;border:1.5px solid var(--barline)!important;border-radius:16px;
  box-shadow:0 10px 30px rgba(9,8,13,.18);
  background-image:radial-gradient(circle at 7px 7px,var(--barfaint) 1.4px,transparent 2px),
    radial-gradient(circle at calc(100% - 7px) 7px,var(--barfaint) 1.4px,transparent 2px),
    radial-gradient(circle at 7px calc(100% - 7px),var(--barfaint) 1.4px,transparent 2px),
    radial-gradient(circle at calc(100% - 7px) calc(100% - 7px),var(--barfaint) 1.4px,transparent 2px)!important}
.st-key-topbar>[data-testid="stLayoutWrapper"]>[data-testid="stHorizontalBlock"]{align-items:center;flex-wrap:nowrap;gap:10px!important}
.st-key-topbar>[data-testid="stLayoutWrapper"]>[data-testid="stHorizontalBlock"]>[data-testid="stColumn"]:first-child{flex:0 0 auto!important;width:auto!important}
.st-key-topbar>[data-testid="stLayoutWrapper"]>[data-testid="stHorizontalBlock"]>[data-testid="stColumn"]:nth-child(2){flex:1 1 auto!important;width:auto!important}
.st-key-topbar>[data-testid="stLayoutWrapper"]>[data-testid="stHorizontalBlock"]>[data-testid="stColumn"]:last-child{flex:0 0 auto!important;width:auto!important}
.st-key-topbar [data-testid="stMarkdownContainer"],.st-key-topbar [data-testid="stMarkdownContainer"]>*,.st-key-topbar .stMarkdown{margin:0!important;padding:0!important;line-height:0}
.st-key-navmid,.st-key-navend{width:fit-content!important;padding:0!important;background:transparent!important}
.st-key-navmid{margin-left:auto}
.st-key-navend{margin-left:auto}
.st-key-navmid [data-testid="stHorizontalBlock"],.st-key-navend [data-testid="stHorizontalBlock"]{gap:8px!important;flex-wrap:nowrap;justify-content:flex-end}
.st-key-navmid [data-testid="stColumn"],.st-key-navend [data-testid="stColumn"]{width:auto!important;flex:0 0 auto!important;min-width:0!important}
/* logo */
.st-key-topbar .brand{display:inline-flex;align-items:center;gap:10px;white-space:nowrap;height:40px}
.st-key-topbar .brand img{width:30px;height:30px;display:block;flex:0 0 30px;animation:pl-spin 9s linear infinite}
.st-key-topbar .brand b{font-family:'Anton',sans-serif;font-weight:400;font-size:1.55rem;letter-spacing:.03em;color:var(--brand);
  line-height:1;text-transform:uppercase}
.st-key-topbar .brand small{font:700 .55rem 'Inter';letter-spacing:.18em;color:var(--pk);text-transform:uppercase;
  border:1.2px solid var(--pk);border-radius:20px;padding:3px 8px}
@keyframes pl-spin{to{transform:rotate(360deg)}}
/* outlined pill links with a dot; the active one gets the offset crescent and a badge */
.stMain .st-key-topbar div[data-testid="stButton"] button[kind]{position:relative;background:var(--pill)!important;color:var(--pillink)!important;
  border:1.2px solid var(--barline)!important;border-radius:30px!important;padding:0 18px!important;min-height:36px!important;height:36px!important;
  box-shadow:none!important;overflow:visible!important;transition:transform .15s,box-shadow .15s,padding .2s}
/* no dot: an arrow slides in on hover and stays on the current page */
.stMain .st-key-topbar div[data-testid="stButton"] button[kind]::before{content:'→';position:absolute;left:12px;top:50%;transform:translate(-6px,-50%);
  opacity:0;color:var(--pk);font:700 .8rem 'Inter';transition:opacity .2s,transform .2s}
.stMain .st-key-topbar div[data-testid="stButton"] button[kind]:hover::before,
.stMain .st-key-topbar div[data-testid="stButton"] button[kind="primary"]::before{opacity:1;transform:translate(0,-50%)}
.stMain .st-key-topbar div[data-testid="stButton"] button[kind]:hover,
.stMain .st-key-topbar div[data-testid="stButton"] button[kind="primary"]{padding:0 14px 0 30px!important}
.stMain .st-key-topbar div[data-testid="stButton"] button[kind] p{font:600 .64rem 'Inter'!important;letter-spacing:.14em;text-transform:uppercase;
  color:var(--pillink)!important;white-space:nowrap}
.stMain .st-key-topbar div[data-testid="stButton"] button[kind]:hover{box-shadow:-3px 0 0 0 var(--pk)!important}
.stMain .st-key-topbar div[data-testid="stButton"] button[kind="primary"]{box-shadow:-5px 0 0 0 var(--pk)!important;transform:translateX(3px)}
.stMain .st-key-topbar div[data-testid="stButton"] button[kind="primary"]::after{content:'';position:absolute;right:-4px;top:-5px;width:11px;height:11px;
  border-radius:50%;background:var(--pk);border:1.2px solid var(--barline)}
/* icon pills */
.stMain .st-key-navend div[data-testid="stButton"] button[kind],.stMain .st-key-navend [data-testid="stPopover"] button{width:44px!important;
  min-width:44px!important;padding:0!important;justify-content:center!important;transform:none!important}
.stMain .st-key-navend div[data-testid="stButton"] button[kind]::before,.stMain .st-key-navend div[data-testid="stButton"] button[kind]::after{display:none}
.stMain .st-key-navend div[data-testid="stButton"] button[kind]:hover{padding:0!important}
.stMain .st-key-navend div[data-testid="stButton"] button[kind] span,.stMain .st-key-navend [data-testid="stPopover"] button span{color:var(--pillink)!important;margin:0!important}
.stMain .st-key-navend [data-testid="stPopover"] button{min-height:36px!important;height:36px!important;border-radius:30px!important;
  background:var(--pill)!important;border:1.2px solid var(--barline)!important;box-shadow:none!important}
.stMain .st-key-navend [data-testid="stPopover"] button>div>div:last-child{display:none!important}
.stMain .st-key-navend div[data-testid="stButton"] button[kind]:hover,.stMain .st-key-navend [data-testid="stPopover"] button:hover{box-shadow:-3px 0 0 0 var(--pk)!important}
/* theme switch: a wide pill split light|dark with a yellow knob that sits on the active side */
.stMain .st-key-navend [class*="st-key-nav_theme_"] button[kind]{width:78px!important;min-width:78px!important;justify-content:flex-start!important;
  padding-left:14px!important;background:linear-gradient(90deg,var(--pill) 0 52%,#7D8B99 52% 100%)!important}
.stMain .st-key-navend [class*="st-key-nav_theme_"] button[kind]::after{display:block!important;content:'';position:absolute;top:50%;margin-top:-6px;
  width:12px;height:12px;border-radius:50%;background:#FFD400;border:1.2px solid var(--barline);right:12px;left:auto}
[data-testid="stPopoverBody"]{background:var(--card)!important;border:1.2px solid var(--barline)!important;border-radius:10px!important;min-width:210px}
[data-testid="stPopoverBody"] .so-q{font-size:.8rem;color:var(--ink);margin-bottom:4px}
[data-testid="stPopoverBody"] div[data-testid="stButton"] button{background:var(--pk)!important;border:0!important;border-radius:30px!important}
[data-testid="stPopoverBody"] div[data-testid="stButton"] button p{color:#fff!important;font-weight:600}

/* page header: title + description left, page controls right */
.st-key-pghead{margin-bottom:10px;padding-bottom:10px;border-bottom:1px solid var(--line)}
.st-key-pghead>[data-testid="stHorizontalBlock"]{align-items:flex-end}
.pg-head .k{font:600 .6rem 'Inter';letter-spacing:.3em;text-transform:uppercase;color:var(--pk);margin-bottom:4px}
.pg-head .t{font-family:'Anton',sans-serif;text-transform:uppercase;font-size:clamp(24px,2.3vw,34px);line-height:1;color:var(--ink)}
.pg-head p{margin:6px 0 0;max-width:620px;color:var(--mute);font-size:.8rem;line-height:1.45}
.st-key-pgctl [data-testid="stHorizontalBlock"]{justify-content:flex-end;gap:8px!important}
.sec{font:600 .68rem 'Inter';letter-spacing:.26em;text-transform:uppercase;color:var(--mute);margin:4vh 0 14px;display:flex;align-items:center;gap:12px}
.sec::after{content:'';flex:1;height:1px;background:var(--line)}

/* admin sub-nav */
.st-key-subnav{margin:-4px 0 10px}
.st-key-subnav [data-testid="stHorizontalBlock"]{gap:6px!important}
.st-key-subnav [data-testid="stColumn"]{width:auto!important;flex:0 0 auto!important;min-width:0!important}
.stMain .st-key-subnav div[data-testid="stButton"]>button[kind]{border-radius:30px!important;min-height:30px!important;height:30px!important;padding:4px 14px!important;
  background:transparent!important;border:1px solid var(--line)!important}
.stMain .st-key-subnav div[data-testid="stButton"]>button[kind] p{font:600 .62rem 'Inter'!important;letter-spacing:.14em;text-transform:uppercase;color:var(--mute)!important}
.stMain .st-key-subnav div[data-testid="stButton"]>button[kind="primary"]{background:var(--ink)!important;border-color:var(--ink)!important}
.stMain .st-key-subnav div[data-testid="stButton"]>button[kind="primary"] p{color:var(--bg)!important}
@media(max-width:1000px){.st-key-topbar .brand b,.st-key-topbar .brand small{display:none}}
</style>
"""


def _warm_up(role):
    """Load data and heavy libraries in the background once per server process, so page switches hit warm caches."""
    import threading
    flag = f"_pldw_warm_{role}"
    if getattr(st, flag, False):
        return
    setattr(st, flag, True)

    def run():
        try:
            from utils import db
            db.load_team_match(); db.load_player_perf(); db.load_fact_match()
            from utils import models
            models.get_classification_model("pre_match", "chronological", 4)
            if role == "admin":
                import utils.olap, utils.schema_diagrams  # noqa: F401
        except Exception:
            pass

    threading.Thread(target=run, daemon=True).start()


PAGE_TRANSITION_JS = r"""
(function(){
  if (window.__pgx) return; window.__pgx = 1;
  const D = document, B = D.body;
  let last = '', timer = null;
  // leaving: a page link was clicked
  D.addEventListener('click', e => {
    const b = e.target.closest && e.target.closest('.st-key-navmid button, .st-key-subnav button');
    if (!b || b.getAttribute('kind') === 'primary') return;
    B.classList.remove('pg-enter'); B.classList.add('pg-leave');
    clearTimeout(timer); timer = setTimeout(() => B.classList.remove('pg-leave'), 6000);  // safety net
  }, true);
  // entering: the page title changed, so the new page has rendered
  setInterval(() => {
    const t = D.querySelector('.pg-head .t');
    const txt = t ? t.textContent : '';
    if (txt && txt !== last) {
      if (last) {
        B.classList.remove('pg-leave'); B.classList.add('pg-enter');
        setTimeout(() => B.classList.remove('pg-enter'), 700);
      }
      last = txt;
    }
  }, 50);
})();
"""


def _page_transitions():
    """Inject the transition driver into the main page once (survives reruns)."""
    components.html("<script>const d=window.parent.document;if(!window.parent.__pgx){const s=d.createElement('script');"
                    f"s.textContent={json.dumps(PAGE_TRANSITION_JS)};d.head.appendChild(s);}}</script>", height=0)


def render_shell(role, current):
    """Top bar + page header. Returns the header's right-hand slot for the page's own controls."""
    _warm_up(role)
    inject_theme_css()
    st.markdown(NAV_CSS, unsafe_allow_html=True)
    if get_theme_mode() == "dark":
        st.markdown('<style>.stMain .st-key-navend [class*="st-key-nav_theme_"] button[kind]::after{left:12px!important;right:auto!important}'
                    '.stMain .st-key-navend [class*="st-key-nav_theme_"] button[kind]{justify-content:flex-end!important;padding:0 14px 0 0!important;'
                    'background:linear-gradient(90deg,#7D8B99 0 48%,var(--pill) 48% 100%)!important}</style>', unsafe_allow_html=True)
    _patch_plotly()
    dark = get_theme_mode() == "dark"
    targets = {b: f for _, b, f in ADMIN_NAV}
    labels = {b: a for a, b, _ in ADMIN_NAV}
    if role == "user":
        nav = [(label, page, page) for label, page in USER_NAV]
        group, sub = None, []
    else:
        group = next((g for g, pages in ADMIN_GROUPS if current in pages), "Overview")
        nav = [(g, pages[0], g) for g, pages in ADMIN_GROUPS]
        sub = next(pages for g, pages in ADMIN_GROUPS if g == group)
        sub = sub if len(sub) > 1 else []

    def go(page):
        if role == "user":
            st.session_state["user_subpage"] = page
            st.rerun()
        elif targets[page] == "app.py":
            st.session_state["auth_role"] = "admin"
            st.switch_page("app.py")
        else:
            st.switch_page(targets[page])

    with st.container(key="topbar"):
        c_brand, c_nav, c_end = st.columns([1.2, 2, 1], vertical_alignment="center")
        c_brand.markdown(
            '<div class="brand"><img src="/app/static/ball_front_sm.png" alt=""><b>EPL Analytics</b>'
            f'{"<small>Admin</small>" if role == "admin" else ""}</div>', unsafe_allow_html=True)
        with c_nav, st.container(key="navmid"):
            for col, (label, page, key) in zip(st.columns(len(nav)), nav):
                active = page == current if role == "user" else key == group
                if col.button(label, key=f"nav_{role}_{key}", type="primary" if active else "secondary") and not active:
                    go(page)
        with c_end, st.container(key="navend"):
            actions = st.columns(3 if role == "admin" else 2)
            if role == "admin" and actions[0].button("", icon=":material/visibility:", key="nav_to_user",
                                                     help="Open the user view", type="secondary"):
                st.session_state.update(auth_role="user", user_subpage="Dashboard")
                st.switch_page("app.py")
            if actions[-1].button("", icon=":material/dark_mode:" if dark else ":material/light_mode:", key=f"nav_theme_{role}",
                                  help="Switch to light theme" if dark else "Switch to dark theme", type="secondary"):
                st.session_state["theme_mode"] = "light" if dark else "dark"
                st.rerun()
            # two-step sign out: the icon opens a small panel with the confirm button
            with actions[-2].popover("", icon=":material/logout:", help="Sign out"):
                st.markdown('<div class="so-q">Sign out of EPL Analytics?</div>', unsafe_allow_html=True)
                if st.button("Sign out", key=f"nav_out_{role}", type="primary", use_container_width=True):
                    st.session_state["auth_role"] = None
                    st.switch_page("app.py")

    if sub:
        with st.container(key="subnav"):
            scols = st.columns([1] * len(sub) + [max(1, 8 - len(sub))])
            for col, page in zip(scols, sub):
                if col.button(labels[page], key=f"sub_{page}", type="primary" if page == current else "secondary") and page != current:
                    go(page)

    slot = page_header(current, role)
    _page_transitions()
    return slot


def page_header(page, role="admin"):
    key = f"User:{page}" if role == "user" and f"User:{page}" in PAGE_INFO else page
    kicker, title, line = PAGE_INFO.get(key, ("", page, ""))
    with st.container(key="pghead"):
        left, right = st.columns([1.1, 1], vertical_alignment="bottom")
        left.markdown(f'<div class="pg-head"><div class="k">{kicker}</div><div class="t">{title}</div><p>{line}</p></div>',
                      unsafe_allow_html=True)
        slot = right.container(key="pgctl")
    return slot


def section(label):
    st.markdown(f'<div class="sec">{label}</div>', unsafe_allow_html=True)
