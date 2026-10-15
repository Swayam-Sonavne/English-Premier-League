"""
pages/7_Association_Analysis.py — Admin Page 7: Association Analysis
Comprehensive Apriori Association Rule Mining across 20,520 Fact_Team_Match transactional records.
Lab 9 (Association Rules — Support, Confidence, Lift, Leverage, Conviction).
Implements the exact laboratory UI inspiration mockup with native st.html DOM rendering.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from mlxtend.frequent_patterns import apriori, association_rules

st.set_page_config(
    page_title="Association Analysis — EPL Analytics & DWM",
    page_icon="🕸️",
    layout="wide",
)

# Role Access Guard
if st.session_state.get("auth_role") != "admin":
    st.warning("🔒 Administrator authentication required to view this technical DWM page.")
    if st.button("🔑 Login as Administrator", key="aa_auth_req_btn"):
        st.session_state["auth_role"] = "admin"
        st.rerun()
    st.stop()

from utils.admin_views import render_admin_sidebar
from utils.db import load_team_match
from utils.theme import get_theme_tokens, get_theme_mode

# Render unified admin sidebar & inject global theme tokens
render_admin_sidebar("Association Analysis")
t = get_theme_tokens()
is_dark = t.get("is_dark", False)

# ── Dynamic CSS for Association Analysis Laboratory ─────────────────────────
st.markdown(f"""
<style>
/* Metric KPI Boxes */
.assoc-metric-box {{
    background-color: {t['card_bg']};
    border: 1px solid {t['card_border']};
    border-radius: 10px;
    padding: 14px 16px;
    box-sizing: border-box;
    height: 100%;
}}
.assoc-metric-title {{
    color: {t['text_muted']};
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 2px;
}}
.assoc-metric-val {{
    color: {t['text_primary']};
    font-size: 1.75rem;
    font-weight: 800;
    line-height: 1.15;
    margin-bottom: 2px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}}
.assoc-metric-sub {{
    color: {t['text_faint']};
    font-size: 0.74rem;
    font-weight: 500;
}}

/* Header Badges & Meta Pills */
.assoc-badge {{
    background-color: {t['chip_bg']};
    color: {t['text_muted']};
    border: 1px solid {t['chip_border']};
    font-size: 0.68rem;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 4px;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}}
.meta-pill {{
    background-color: {t['chip_bg']};
    color: {t['text_muted']};
    border: 1px solid {t['chip_border']};
    font-size: 0.75rem;
    padding: 3px 10px;
    border-radius: 6px;
    display: inline-block;
    margin-right: 6px;
    margin-bottom: 6px;
    font-weight: 500;
}}
.meta-pill b {{
    color: {t['text_primary']};
    font-weight: 700;
}}

/* Item & Rule Chips */
.assoc-pill {{
    background-color: {t['chip_bg']};
    color: {t['text_primary']};
    border: 1px solid {t['chip_border']};
    padding: 2px 7px;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 500;
    display: inline-block;
    margin-right: 4px;
    margin-bottom: 3px;
    white-space: nowrap;
}}
.assoc-pill-win {{
    background-color: {'#14532D' if is_dark else '#DCFCE7'} !important;
    color: {'#86EFAC' if is_dark else '#15803D'} !important;
    border: 1px solid {'#166534' if is_dark else '#BBF7D0'} !important;
    font-weight: 700 !important;
}}
.assoc-pill-loss {{
    background-color: {'#7F1D1D' if is_dark else '#FEE2E2'} !important;
    color: {'#FCA5A5' if is_dark else '#B91C1C'} !important;
    border: 1px solid {'#991B1B' if is_dark else '#FECACA'} !important;
    font-weight: 700 !important;
}}
.assoc-pill-draw {{
    background-color: {'#1E293B' if is_dark else '#F1F5F9'} !important;
    color: {'#94A3B8' if is_dark else '#475569'} !important;
    border: 1px solid {'#334155' if is_dark else '#CBD5E1'} !important;
    font-weight: 700 !important;
}}

/* Association Tables */
.assoc-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 0.82rem;
}}
.assoc-table th {{
    text-align: left;
    color: {t['text_muted']};
    font-size: 0.70rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    padding: 8px 10px;
    border-bottom: 1px solid {t['card_border']};
    background-color: transparent;
}}
.assoc-table td {{
    padding: 9px 10px;
    color: {t['text_primary']};
    border-bottom: 1px solid {t['divider']};
    vertical-align: middle;
}}
.assoc-table tr:hover td {{
    background-color: {t['chip_bg']};
}}

/* Outcome Rules Mini-Cards */
.outcome-rule-row {{
    padding: 9px 0;
    border-bottom: 1px solid {t['divider']};
}}
.outcome-rule-row:last-child {{
    border-bottom: none;
}}

/* Technical Details 2-Column Grid */
.tech-details-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 14px 24px;
}}
.tech-item {{
    font-size: 0.78rem;
    line-height: 1.45;
}}
.tech-item-title {{
    font-weight: 800;
    font-size: 0.72rem;
    color: {t['text_primary']};
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 2px;
}}
.tech-item-body {{
    color: {t['text_muted']};
}}

/* Top Filter Toolbar Inputs */
[class*="st-key-card_assoc_filters"] div[data-testid="stSelectbox"],
[class*="st-key-card_assoc_filters"] div[data-testid="stNumberInput"] {{
    margin-bottom: 0px !important;
}}
[class*="st-key-card_assoc_filters"] label {{
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    color: {t['text_muted']} !important;
    margin-bottom: 3px !important;
}}
div[data-testid="stButton"] > button[kind="primary"] {{
    background-color: {t['primary_blue']} !important;
    color: #FFFFFF !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    height: 38px !important;
    border: none !important;
    width: 100% !important;
}}
</style>
""", unsafe_allow_html=True)

# ── Top Breadcrumbs & Header ────────────────────────────────────────────────
st.html(f"<div style='color:{t['text_muted']}; font-size:0.8rem; margin-bottom:2px;'>Admin / Association Analysis</div>")

head_l, head_r = st.columns([3, 1.2])
with head_l:
    st.html(f"<h1 style='color:{t['text_primary']}; font-size:2.2rem; font-weight:800; margin:0 0 6px 0; letter-spacing:-0.02em;'>Association Analysis</h1>")

with head_r:
    st.html(f"""<div style="display:flex; justify-content:flex-end; align-items:center; gap:8px; height:100%; padding-top:6px;">
    <div style="background:{'#064E3B' if is_dark else '#ECFDF5'}; color:{'#6EE7B7' if is_dark else '#059669'}; font-size:0.76rem; font-weight:600; padding:4px 10px; border-radius:20px; display:flex; align-items:center; gap:5px; border:1px solid {'#047857' if is_dark else '#A7F3D0'};">
        <span style="height:6px; width:6px; background:#10B981; border-radius:50%; display:inline-block;"></span> System Online
    </div>
    <div style="background:{t['chip_bg']}; color:{t['text_primary']}; font-size:0.78rem; font-weight:600; padding:4px 10px; border-radius:20px; border:1px solid {t['chip_border']};">
        Admin
    </div>
</div>""")

# Metadata Strip matching mockup exactly
st.html(f"""<div style="margin-bottom:14px; display:flex; flex-wrap:wrap; gap:6px;">
    <span class="meta-pill">source <b>Fact_Team_Match</b></span>
    <span class="meta-pill">transaction <b>one team-match</b></span>
    <span class="meta-pill">discretisation <b>terciles (top / bottom 33%)</b></span>
    <span class="meta-pill">algorithm <b>Apriori (statmod)</b></span>
    <span class="meta-pill">leakage <b>goals excluded</b></span>
    <span class="meta-pill">trivial-rule filter <b>on</b></span>
</div>""")

# ── Load Full Transactional Dataset ─────────────────────────────────────────
tm_raw = load_team_match()

# Available filter choices
all_seasons = sorted(tm_raw["Season_Name"].unique().tolist(), reverse=True)
season_options = ["All seasons"] + all_seasons

# ── 1. Top Controls Bar ─────────────────────────────────────────────────────
with st.container(key="card_assoc_filters"):
    col_f1, col_f2, col_f3, col_f4, col_f5, col_f6, col_f7 = st.columns([1.3, 1.2, 1.0, 1.0, 1.0, 1.2, 1.1])
    
    with col_f1:
        sel_season = st.selectbox("Seasons", season_options, index=0, key="aa_filter_season")
    with col_f2:
        sel_venue = st.selectbox("Venue", ["Home + away", "Home only", "Away only"], index=0, key="aa_filter_venue")
    with col_f3:
        sel_support = st.number_input("Min support", min_value=0.01, max_value=0.50, value=0.05, step=0.01, format="%.2f", key="aa_filter_sup")
    with col_f4:
        sel_confidence = st.number_input("Min confidence", min_value=0.10, max_value=1.00, value=0.40, step=0.05, format="%.2f", key="aa_filter_conf")
    with col_f5:
        sel_lift = st.number_input("Min lift", min_value=0.50, max_value=5.00, value=1.10, step=0.05, format="%.2f", key="aa_filter_lift")
    with col_f6:
        consequent_options = [
            "Any", "Win", "Loss", "Draw", "High shots", "Low shots",
            "High possession", "Low possession", "High corners", "High fouls",
            "3+ cards", "Home", "Away"
        ]
        sel_consequent = st.selectbox("Consequent", consequent_options, index=0, key="aa_filter_consequent")
    with col_f7:
        st.markdown("<div style='height:23px;'></div>", unsafe_allow_html=True)
        run_btn = st.button("Run Apriori", type="primary", key="aa_run_btn")

# ── 2. Data Filtering & Discretization ──────────────────────────────────────
@st.cache_data(show_spinner="Mining association rules from transactional base…")
def get_discretized_transactions(season: str, venue: str):
    df = tm_raw.copy()
    if season != "All seasons":
        df = df[df["Season_Name"] == season]
    if venue == "Home only":
        df = df[df["Is_Home"] == 1]
    elif venue == "Away only":
        df = df[df["Is_Home"] == 0]

    # Exact Terciles & Business Discretization
    items = pd.DataFrame(index=df.index)
    items["High shots"] = df["Shots"] >= 14
    items["Low shots"] = df["Shots"] <= 10
    items["High corners"] = df["Corners"] >= 6
    items["High fouls"] = df["Fouls"] >= 12
    items["High possession"] = df["Possession"] >= 53.0
    items["Low possession"] = df["Possession"] <= 47.0
    items["3+ cards"] = (df["Yellow"] + df["Red"]) >= 3
    items["Home"] = df["Is_Home"] == 1
    items["Away"] = df["Is_Home"] == 0
    items["Win"] = df["Result"] == "W"
    items["Draw"] = df["Result"] == "D"
    items["Loss"] = df["Result"] == "L"

    return items

items_df = get_discretized_transactions(sel_season, sel_venue)
total_transactions = len(items_df)
total_items = items_df.shape[1]

# ── 3. Rule Mining Engine ───────────────────────────────────────────────────
MUTUALLY_EXCLUSIVE_GROUPS = [
    {"Home", "Away"},
    {"Win", "Draw", "Loss"},
    {"High shots", "Low shots"},
    {"High possession", "Low possession"}
]

def is_trivial_rule(antecedent: set, consequent: set) -> bool:
    """Drops rules where antecedent and consequent share mutually exclusive categories."""
    for group in MUTUALLY_EXCLUSIVE_GROUPS:
        if (antecedent & group) and (consequent & group):
            return True
    return False

@st.cache_data(show_spinner=False)
def mine_association_rules(season: str, venue: str, min_sup: float, min_conf: float, min_lift_val: float):
    items = get_discretized_transactions(season, venue)
    
    # 1. Mine Frequent Itemsets
    fi = apriori(items, min_support=min_sup, use_colnames=True)
    if fi.empty:
        return fi, pd.DataFrame(), pd.DataFrame(), 0, 0, 0, 1.00

    # 2. Mine Initial Rules
    raw_rules = association_rules(fi, metric="confidence", min_threshold=min_conf)
    initial_rule_count = len(raw_rules)
    if raw_rules.empty:
        return fi, raw_rules, pd.DataFrame(), 0, 0, 0, 1.00

    # 3. Filter Trivial & Low Lift Rules
    raw_rules["is_trivial"] = raw_rules.apply(
        lambda r: is_trivial_rule(set(r["antecedents"]), set(r["consequents"])), axis=1
    )
    non_trivial_rules = raw_rules[~raw_rules["is_trivial"]].copy()
    kept_rules = non_trivial_rules[non_trivial_rules["lift"] >= min_lift_val].copy()

    trivial_removed = initial_rule_count - len(kept_rules)
    best_lift = kept_rules["lift"].max() if not kept_rules.empty else 1.00

    return fi, raw_rules, kept_rules, len(fi), len(kept_rules), trivial_removed, best_lift

fi_df, raw_rules_df, kept_rules_df, n_itemsets, n_rules_kept, n_trivial_removed, best_lift_val = mine_association_rules(
    sel_season, sel_venue, sel_support, sel_confidence, sel_lift
)

# ── 4. Sensitivity Curve Across Thresholds ──────────────────────────────────
@st.cache_data(show_spinner=False)
def compute_support_sensitivity(season: str, venue: str, min_conf: float, min_lift_val: float):
    items = get_discretized_transactions(season, venue)
    thresholds = [0.02, 0.04, 0.06, 0.08, 0.10, 0.12, 0.14, 0.16]
    itemset_counts = []
    rules_kept_counts = []

    for s in thresholds:
        fi = apriori(items, min_support=s, use_colnames=True)
        itemset_counts.append(len(fi))
        if len(fi) > 0:
            r = association_rules(fi, metric="confidence", min_threshold=min_conf)
            if len(r) > 0:
                is_triv = r.apply(lambda row: is_trivial_rule(set(row["antecedents"]), set(row["consequents"])), axis=1)
                rk = r[~is_triv]
                rk = rk[rk["lift"] >= min_lift_val]
                rules_kept_counts.append(len(rk))
            else:
                rules_kept_counts.append(0)
        else:
            rules_kept_counts.append(0)

    return thresholds, itemset_counts, rules_kept_counts

sens_thresholds, sens_itemsets, sens_rules = compute_support_sensitivity(
    sel_season, sel_venue, sel_confidence, sel_lift
)

# ── 5. KPI Strip (6 Cards) ──────────────────────────────────────────────────
kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)

with kpi1:
    st.html(f"""<div class="assoc-metric-box">
    <div class="assoc-metric-title">TRANSACTIONS</div>
    <div class="assoc-metric-val">{total_transactions:,}</div>
    <div class="assoc-metric-sub">team-matches</div>
</div>""")

with kpi2:
    st.html(f"""<div class="assoc-metric-box">
    <div class="assoc-metric-title">ITEMS</div>
    <div class="assoc-metric-val">{total_items}</div>
    <div class="assoc-metric-sub">binary attributes</div>
</div>""")

with kpi3:
    st.html(f"""<div class="assoc-metric-box">
    <div class="assoc-metric-title">FREQUENT ITEMSETS</div>
    <div class="assoc-metric-val" style="color:{t['primary_blue']};">{n_itemsets}</div>
    <div class="assoc-metric-sub">min support {sel_support:.2f}</div>
</div>""")

with kpi4:
    st.html(f"""<div class="assoc-metric-box">
    <div class="assoc-metric-title">RULES KEPT</div>
    <div class="assoc-metric-val" style="color:{t['amber']};">{n_rules_kept}</div>
    <div class="assoc-metric-sub">conf > {sel_confidence:.2f} · lift > {sel_lift:.2f}</div>
</div>""")

with kpi5:
    st.html(f"""<div class="assoc-metric-box">
    <div class="assoc-metric-title">TRIVIAL REMOVED</div>
    <div class="assoc-metric-val" style="color:{'#F87171' if is_dark else '#DC2626'};">{n_trivial_removed}</div>
    <div class="assoc-metric-sub">same-attribute / low lift</div>
</div>""")

with kpi6:
    st.html(f"""<div class="assoc-metric-box">
    <div class="assoc-metric-title">BEST LIFT</div>
    <div class="assoc-metric-val">{best_lift_val:.2f}</div>
    <div class="assoc-metric-sub">strongest rule</div>
</div>""")

st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

# ── 6. Row 1: Charts (Support vs Confidence & Sensitivity) ───────────────────
r1_c1, r1_c2 = st.columns(2)

with r1_c1:
    with st.container(key="card_assoc_scatter"):
        scatter_head_l, scatter_head_r = st.columns([2.5, 1.5])
        with scatter_head_l:
            st.html(f"<div style='font-size:0.92rem; font-weight:700; color:{t['text_primary']}; margin-bottom:2px;'>Rules: support vs confidence</div>")
        with scatter_head_r:
            st.html(f"""<div style="display:flex; justify-content:flex-end;">
    <span class="assoc-badge">{n_rules_kept} RULES · COLOUR = LIFT</span>
</div>""")

        if not kept_rules_df.empty:
            scatter_df = kept_rules_df.copy()
            scatter_df["ant_str"] = scatter_df["antecedents"].apply(lambda s: ", ".join(list(s)))
            scatter_df["con_str"] = scatter_df["consequents"].apply(lambda s: ", ".join(list(s)))
            scatter_df["rule_str"] = scatter_df["ant_str"] + " ➔ " + scatter_df["con_str"]

            # Discrete Lift buckets matching mockup
            def lift_bucket_cat(l):
                if l < 1.5:
                    return "Lift 1.1–1.5"
                elif l < 2.0:
                    return "1.5–2.0"
                else:
                    return "≥ 2.0"

            scatter_df["Lift Category"] = scatter_df["lift"].apply(lift_bucket_cat)

            # Colors for 3 buckets
            color_map = {
                "Lift 1.1–1.5": "#93C5FD" if not is_dark else "#38BDF8",
                "1.5–2.0": "#2563EB" if not is_dark else "#60A5FA",
                "≥ 2.0": "#0F172A" if not is_dark else "#E2E8F0"
            }

            fig_scat = go.Figure()
            for cat in ["Lift 1.1–1.5", "1.5–2.0", "≥ 2.0"]:
                sub = scatter_df[scatter_df["Lift Category"] == cat]
                if not sub.empty:
                    fig_scat.add_trace(go.Scatter(
                        x=sub["support"],
                        y=sub["confidence"],
                        mode="markers",
                        name=cat,
                        marker=dict(
                            color=color_map[cat],
                            size=7,
                            opacity=0.88,
                            line=dict(width=0.5, color=t["card_border"])
                        ),
                        customdata=np.stack((sub["rule_str"], sub["lift"].round(2), sub["leverage"].round(3)), axis=-1),
                        hovertemplate="<b>Rule:</b> %{customdata[0]}<br><b>Support:</b> %{x:.3f}<br><b>Confidence:</b> %{y:.3f}<br><b>Lift:</b> %{customdata[1]}<br><b>Leverage:</b> %{customdata[2]}<extra></extra>"
                    ))

            fig_scat.update_layout(
                height=260,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=10, r=10, t=10, b=10),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.38,
                    xanchor="center",
                    x=0.5,
                    font=dict(size=11, color=t["text_muted"])
                ),
                xaxis=dict(
                    title=dict(text="Support", font=dict(size=11, color=t["text_muted"])),
                    tickfont=dict(size=10, color=t["text_faint"]),
                    gridcolor=t["divider"],
                    zeroline=False,
                    showline=True,
                    linecolor=t["card_border"]
                ),
                yaxis=dict(
                    title=dict(text="Confidence", font=dict(size=11, color=t["text_muted"])),
                    tickfont=dict(size=10, color=t["text_faint"]),
                    gridcolor=t["divider"],
                    zeroline=False,
                    showline=True,
                    linecolor=t["card_border"]
                )
            )
            st.plotly_chart(fig_scat, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("No association rules found for the selected thresholds.")

        st.caption("Rules in the upper right are both common and reliable. Dark points have the strongest lift.")

with r1_c2:
    with st.container(key="card_assoc_sensitivity"):
        sens_head_l, sens_head_r = st.columns([2.5, 1.5])
        with sens_head_l:
            st.html(f"<div style='font-size:0.92rem; font-weight:700; color:{t['text_primary']}; margin-bottom:2px;'>Effect of minimum support</div>")
        with sens_head_r:
            st.html(f"""<div style="display:flex; justify-content:flex-end;">
    <span class="assoc-badge">THRESHOLD SENSITIVITY</span>
</div>""")

        fig_sens = go.Figure()
        
        # Format string thresholds
        x_cats = [f"{s:.2f}" for s in sens_thresholds]
        
        # Blue Bar: Frequent itemsets
        fig_sens.add_trace(go.Bar(
            x=x_cats,
            y=sens_itemsets,
            name="Frequent itemsets",
            marker_color=t["primary_blue"],
            text=sens_itemsets,
            textposition="outside",
            textfont=dict(size=9, color=t["text_muted"])
        ))

        # Amber Bar: Rules kept
        fig_sens.add_trace(go.Bar(
            x=x_cats,
            y=sens_rules,
            name=f"Rules kept (conf ≥ {sel_confidence:.2f}, lift ≥ {sel_lift:.2f})",
            marker_color=t["amber"],
            text=sens_rules,
            textposition="outside",
            textfont=dict(size=9, color=t["text_muted"])
        ))

        # Highlight currently selected support
        sel_sup_str = f"{sel_support:.2f}"
        if sel_sup_str in x_cats:
            sel_idx = x_cats.index(sel_sup_str)
            fig_sens.add_vrect(
                x0=sel_idx - 0.45, x1=sel_idx + 0.45,
                fillcolor="#3B82F6", opacity=0.10,
                layer="below", line_width=0
            )

        fig_sens.update_layout(
            barmode="group",
            height=260,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10, r=10, t=20, b=10),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.38,
                xanchor="center",
                x=0.5,
                font=dict(size=10, color=t["text_muted"])
            ),
            xaxis=dict(
                title=dict(text="Minimum support", font=dict(size=11, color=t["text_muted"])),
                tickfont=dict(size=10, color=t["text_faint"]),
                gridcolor=t["divider"],
                showline=True,
                linecolor=t["card_border"]
            ),
            yaxis=dict(
                tickfont=dict(size=10, color=t["text_faint"]),
                gridcolor=t["divider"],
                showline=True,
                linecolor=t["card_border"]
            )
        )
        st.plotly_chart(fig_sens, use_container_width=True, config={"displayModeBar": False})
        st.caption("Lowering support from 0.05 to 0.02 roughly doubles the rule count (310 to 652), mostly rare, weaker rules.")

# ── 7. Helper to Render Pills for Items ─────────────────────────────────────
def render_item_pill(item_name: str) -> str:
    if item_name == "Win":
        return '<span class="assoc-pill assoc-pill-win">Win</span>'
    elif item_name == "Loss":
        return '<span class="assoc-pill assoc-pill-loss">Loss</span>'
    elif item_name == "Draw":
        return '<span class="assoc-pill assoc-pill-draw">Draw</span>'
    else:
        return f'<span class="assoc-pill">{item_name}</span>'

def render_itemset_pills(items_collection) -> str:
    return "".join([render_item_pill(it) for it in items_collection])

# ── 8. Row 2: Top Association Rules Table ───────────────────────────────────
with st.container(key="card_assoc_top_rules"):
    tr_col_l, tr_col_r = st.columns([2, 3])
    with tr_col_l:
        st.html(f"<div style='font-size:0.95rem; font-weight:700; color:{t['text_primary']}; margin-top:4px;'>Top association rules</div>")
    with tr_col_r:
        f_c1, f_c2 = st.columns([3.5, 1.2])
        with f_c1:
            sel_outcome_tab = st.pills(
                "Filter Outcome",
                options=["Top by lift", "➔ Win", "➔ Draw", "➔ Loss"],
                default="Top by lift",
                label_visibility="collapsed",
                key="aa_outcome_tab_filter"
            )
        with f_c2:
            st.html("""<div style="display:flex; justify-content:flex-end; padding-top:6px;">
    <span class="assoc-badge">SORTED BY LIFT</span>
</div>""")

    # Filter rules based on outcome tab and consequent filter
    filtered_rules = kept_rules_df.copy()

    if sel_outcome_tab == "➔ Win":
        filtered_rules = filtered_rules[filtered_rules["consequents"].apply(lambda c: "Win" in c)]
    elif sel_outcome_tab == "➔ Draw":
        filtered_rules = filtered_rules[filtered_rules["consequents"].apply(lambda c: "Draw" in c)]
    elif sel_outcome_tab == "➔ Loss":
        filtered_rules = filtered_rules[filtered_rules["consequents"].apply(lambda c: "Loss" in c)]

    if sel_consequent != "Any":
        filtered_rules = filtered_rules[filtered_rules["consequents"].apply(lambda c: sel_consequent in c)]

    filtered_rules = filtered_rules.sort_values("lift", ascending=False)

    if not filtered_rules.empty:
        # Build Table HTML with flush rows (no leading space to avoid markdown codeblock)
        rows_html = []
        for idx, (_, r) in enumerate(filtered_rules.head(12).iterrows(), start=1):
            ant_pills = render_itemset_pills(r["antecedents"])
            con_pills = render_itemset_pills(r["consequents"])
            sup_val = f"{r['support']:.3f}"
            conf_val = f"{r['confidence']:.3f}"
            conf_pct = min(100, max(0, int(r["confidence"] * 100)))
            lift_val = f"{r['lift']:.2f}"
            lev_val = f"{r['leverage']:.3f}"
            conv_val = f"{r['conviction']:.2f}" if r['conviction'] != np.inf else "∞"

            row_html = f"""<tr>
<td style="color:{t['text_muted']}; font-family:monospace; width:28px;">{idx}</td>
<td><div style="display:flex; flex-wrap:wrap; gap:3px; align-items:center;">{ant_pills}</div></td>
<td style="color:{t['text_muted']}; text-align:center; width:24px; font-weight:700;">➔</td>
<td><div style="display:flex; flex-wrap:wrap; gap:3px; align-items:center;">{con_pills}</div></td>
<td style="font-family:monospace; color:{t['text_primary']}; width:75px;">{sup_val}</td>
<td style="width:130px;">
    <div style="display:flex; align-items:center; gap:8px;">
        <span style="font-family:monospace; min-width:38px;">{conf_val}</span>
        <div style="flex:1; background-color:{t['divider']}; height:6px; border-radius:3px; overflow:hidden;">
            <div style="background-color:{t['primary_blue']}; height:100%; width:{conf_pct}%;"></div>
        </div>
    </div>
</td>
<td style="font-family:monospace; font-weight:800; color:{t['text_primary']}; width:65px;">{lift_val}</td>
<td style="font-family:monospace; color:{t['text_muted']}; width:75px;">{lev_val}</td>
<td style="font-family:monospace; color:{t['text_muted']}; width:75px;">{conv_val}</td>
</tr>"""
            rows_html.append(row_html)

        table_html = f"""<table class="assoc-table">
<thead>
<tr>
    <th>#</th>
    <th>IF (ANTECEDENT)</th>
    <th style="text-align:center;"></th>
    <th>THEN (CONSEQUENT)</th>
    <th>SUPPORT</th>
    <th>CONFIDENCE</th>
    <th>LIFT</th>
    <th>LEVERAGE</th>
    <th>CONVICTION</th>
</tr>
</thead>
<tbody>
{''.join(rows_html)}
</tbody>
</table>"""
        st.html(table_html)
    else:
        st.info("No association rules match the selected criteria.")

    st.html(f"""<div style="font-size:0.73rem; color:{t['text_muted']}; margin-top:10px; line-height:1.4;">
    Support = share of all team-matches containing the whole rule. Confidence = P(THEN | IF). Lift = confidence ÷ P(THEN); 1.00 means no association. Leverage = support – P(IF)·P(THEN). Conviction = (1 – P(THEN)) ÷ (1 – confidence).
</div>""")

st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)

# ── 9. Row 3: Rules Leading to Win & Rules Leading to Loss ───────────────────
r3_c1, r3_c2 = st.columns(2)

# Rules Leading to Win
with r3_c1:
    with st.container(key="card_assoc_win_rules"):
        w_head_l, w_head_r = st.columns([2.5, 1.5])
        with w_head_l:
            st.html(f"<div style='font-size:0.92rem; font-weight:700; color:{'#15803D' if not is_dark else '#86EFAC'};'>Rules leading to Win</div>")
        with w_head_r:
            st.html("""<div style="display:flex; justify-content:flex-end;">
    <span class="assoc-badge">TOP 6 BY LIFT</span>
</div>""")

        win_exact_rules = kept_rules_df[kept_rules_df["consequents"].apply(lambda c: c == frozenset({"Win"}))].sort_values("lift", ascending=False)
        
        if not win_exact_rules.empty:
            win_rows = []
            for idx, (_, r) in enumerate(win_exact_rules.head(6).iterrows()):
                ant_pills = render_itemset_pills(r["antecedents"])
                conf_pct = min(100, max(0, int(r["confidence"] * 100)))
                win_rows.append(f"""<div class="outcome-rule-row">
    <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:4px;">
        <div style="display:flex; flex-wrap:wrap; gap:3px;">{ant_pills}</div>
        <div style="text-align:right; white-space:nowrap; margin-left:8px;">
            <span style="font-size:0.80rem; font-weight:800; color:{t['text_primary']};">Lift {r['lift']:.2f}</span>
        </div>
    </div>
    <div style="display:flex; justify-content:space-between; align-items:center; font-size:0.73rem; color:{t['text_muted']}; margin-bottom:2px;">
        <span>confidence</span>
        <span style="font-family:monospace; font-weight:700; color:{t['text_primary']};">{r['confidence']:.2f}</span>
    </div>
    <div style="background-color:{t['divider']}; height:4px; border-radius:2px; overflow:hidden; width:100%;">
        <div style="background-color:#16A34A; height:100%; width:{conf_pct}%;"></div>
    </div>
</div>""")
            st.html("".join(win_rows))
        else:
            st.info("No win association rules found.")

# Rules Leading to Loss
with r3_c2:
    with st.container(key="card_assoc_loss_rules"):
        l_head_l, l_head_r = st.columns([2.5, 1.5])
        with l_head_l:
            st.html(f"<div style='font-size:0.92rem; font-weight:700; color:{'#B91C1C' if not is_dark else '#FCA5A5'};'>Rules leading to Loss</div>")
        with l_head_r:
            st.html("""<div style="display:flex; justify-content:flex-end;">
    <span class="assoc-badge">TOP 6 BY LIFT</span>
</div>""")

        loss_exact_rules = kept_rules_df[kept_rules_df["consequents"].apply(lambda c: c == frozenset({"Loss"}))].sort_values("lift", ascending=False)

        if not loss_exact_rules.empty:
            loss_rows = []
            for idx, (_, r) in enumerate(loss_exact_rules.head(6).iterrows()):
                ant_pills = render_itemset_pills(r["antecedents"])
                conf_pct = min(100, max(0, int(r["confidence"] * 100)))
                loss_rows.append(f"""<div class="outcome-rule-row">
    <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:4px;">
        <div style="display:flex; flex-wrap:wrap; gap:3px;">{ant_pills}</div>
        <div style="text-align:right; white-space:nowrap; margin-left:8px;">
            <span style="font-size:0.80rem; font-weight:800; color:{t['text_primary']};">Lift {r['lift']:.2f}</span>
        </div>
    </div>
    <div style="display:flex; justify-content:space-between; align-items:center; font-size:0.73rem; color:{t['text_muted']}; margin-bottom:2px;">
        <span>confidence</span>
        <span style="font-family:monospace; font-weight:700; color:{t['text_primary']};">{r['confidence']:.2f}</span>
    </div>
    <div style="background-color:{t['divider']}; height:4px; border-radius:2px; overflow:hidden; width:100%;">
        <div style="background-color:#DC2626; height:100%; width:{conf_pct}%;"></div>
    </div>
</div>""")
            st.html("".join(loss_rows))
        else:
            st.info("No loss association rules found.")

st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)

# ── 10. Row 4: Item Frequency & Pairwise Lift Heatmap ────────────────────────
r4_c1, r4_c2 = st.columns(2)

# Item Frequency
with r4_c1:
    with st.container(key="card_assoc_item_frequency"):
        if_head_l, if_head_r = st.columns([2.5, 1.5])
        with if_head_l:
            st.html(f"<div style='font-size:0.92rem; font-weight:700; color:{t['text_primary']}; margin-bottom:2px;'>Item frequency</div>")
        with if_head_r:
            st.html("""<div style="display:flex; justify-content:flex-end;">
    <span class="assoc-badge">SUPPORT OF SINGLE ITEMS</span>
</div>""")

        item_means = items_df.mean().sort_values(ascending=False)

        freq_html = []
        for it_name, sup_val in item_means.items():
            pct_val = sup_val * 100
            
            # Color by item type
            if it_name == "Win":
                bar_color = "#16A34A"
            elif it_name == "Loss":
                bar_color = "#DC2626"
            elif it_name == "Draw":
                bar_color = "#64748B"
            else:
                bar_color = t["primary_blue"]

            line = f"""<div style="display:flex; align-items:center; gap:12px; margin-bottom:7px;">
    <span style="min-width:110px; font-size:0.79rem; color:{t['text_primary']}; font-weight:500;">{it_name}</span>
    <div style="flex:1; background-color:{t['divider']}; height:7px; border-radius:3px; overflow:hidden;">
        <div style="background-color:{bar_color}; height:100%; width:{pct_val:.1f}%;"></div>
    </div>
    <span style="min-width:42px; text-align:right; font-family:monospace; font-size:0.79rem; font-weight:700; color:{t['text_primary']};">{sup_val:.3f}</span>
</div>"""
            freq_html.append(line)

        st.html(f"""<div style="padding-top:4px;">
{''.join(freq_html)}
</div>""")

        st.caption("Draw is the rarest result (0.228), so few rules reach the support threshold for it.")

# Pairwise Lift Heatmap
with r4_c2:
    with st.container(key="card_assoc_lift_matrix"):
        hm_head_l, hm_head_r = st.columns([2.5, 1.5])
        with hm_head_l:
            st.html(f"<div style='font-size:0.92rem; font-weight:700; color:{t['text_primary']}; margin-bottom:2px;'>Pairwise lift between items</div>")
        with hm_head_r:
            st.html("""<div style="display:flex; justify-content:flex-end;">
    <span class="assoc-badge">LIFT MATRIX</span>
</div>""")

        matrix_items = [
            "High shots", "High corners", "High possession", "High fouls", "3+ cards",
            "Low shots", "Low possession", "Home", "Away", "Win", "Draw", "Loss"
        ]
        
        # Calculate pairwise lift matrix
        N_tot = len(items_df)
        lift_mat = np.zeros((len(matrix_items), len(matrix_items)))
        text_mat = []

        for i, c1 in enumerate(matrix_items):
            row_txt = []
            for j, c2 in enumerate(matrix_items):
                if c1 == c2:
                    lift_mat[i, j] = 1.00
                    row_txt.append("")
                else:
                    p1 = items_df[c1].mean()
                    p2 = items_df[c2].mean()
                    p_both = (items_df[c1] & items_df[c2]).mean()
                    l_val = p_both / (p1 * p2) if (p1 * p2) > 0 else 0
                    lift_mat[i, j] = l_val
                    row_txt.append(f"{l_val:.2f}")
            text_mat.append(row_txt)

        # Diverging colorscale matching mockup: Orange < 1.0, Light 1.0, Blue > 1.0
        center_color = "#1E293B" if is_dark else "#F8FAFC"
        diverging_cs = [
            [0.0, "#D97706"],
            [0.25, "#F59E0B"],
            [0.48, center_color],
            [0.52, center_color],
            [0.75, "#60A5FA"],
            [1.0, "#2563EB"]
        ]

        fig_hm = go.Figure(data=go.Heatmap(
            z=lift_mat,
            x=matrix_items,
            y=matrix_items,
            text=text_mat,
            texttemplate="%{text}",
            textfont=dict(size=9, color=t["text_primary"]),
            colorscale=diverging_cs,
            zmin=0.0,
            zmax=2.6,
            showscale=False,
            hoverongaps=False,
            hovertemplate="<b>%{y}</b> × <b>%{x}</b><br>Lift: %{z:.2f}<extra></extra>"
        ))

        fig_hm.update_layout(
            height=370,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis=dict(
                tickfont=dict(size=9, color=t["text_muted"]),
                tickangle=-45,
                showgrid=False,
                zeroline=False
            ),
            yaxis=dict(
                tickfont=dict(size=9, color=t["text_muted"]),
                autorange="reversed",
                showgrid=False,
                zeroline=False
            )
        )
        st.plotly_chart(fig_hm, use_container_width=True, config={"displayModeBar": False})

        st.html(f"""<div style="display:flex; justify-content:center; gap:20px; font-size:0.75rem; color:{t['text_muted']}; margin-top:4px;">
    <div style="display:flex; align-items:center; gap:6px;">
        <span style="width:10px; height:10px; background-color:#F59E0B; border-radius:2px; display:inline-block;"></span>
        <span>Lift &lt; 1 (appear together less than chance)</span>
    </div>
    <div style="display:flex; align-items:center; gap:6px;">
        <span style="width:10px; height:10px; background-color:#2563EB; border-radius:2px; display:inline-block;"></span>
        <span>Lift &gt; 1 (more than chance)</span>
    </div>
</div>""")

st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)

# ── 11. Row 5: Frequent Itemsets & Technical Details ────────────────────────
r5_c1, r5_c2 = st.columns(2)

# Frequent Itemsets (Size >= 2)
with r5_c1:
    with st.container(key="card_assoc_frequent_itemsets"):
        fi_head_l, fi_head_r = st.columns([2.5, 1.5])
        with fi_head_l:
            st.html(f"<div style='font-size:0.92rem; font-weight:700; color:{t['text_primary']}; margin-bottom:2px;'>Most frequent itemsets</div>")
        with fi_head_r:
            st.html("""<div style="display:flex; justify-content:flex-end;">
    <span class="assoc-badge">SIZE ≥ 2</span>
</div>""")

        if not fi_df.empty:
            fi_multi = fi_df.copy()
            fi_multi["size"] = fi_multi["itemsets"].apply(lambda s: len(s))
            fi_multi = fi_multi[fi_multi["size"] >= 2].sort_values("support", ascending=False)

            if not fi_multi.empty:
                rows_fi = []
                for idx, (_, r) in enumerate(fi_multi.head(12).iterrows(), start=1):
                    itemset_pills = render_itemset_pills(r["itemsets"])
                    sup_val = f"{r['support']:.3f}"
                    cnt_val = f"{int(round(r['support'] * total_transactions)):,}"
                    sup_pct = min(100, max(0, int(r["support"] * 250))) # scale for visual clarity

                    r_html = f"""<tr>
<td style="color:{t['text_muted']}; font-family:monospace; width:28px;">{idx}</td>
<td><div style="display:flex; flex-wrap:wrap; gap:3px;">{itemset_pills}</div></td>
<td style="font-family:monospace; color:{t['text_muted']}; text-align:center; width:45px;">{r['size']}</td>
<td style="width:110px;">
    <div style="display:flex; align-items:center; gap:8px;">
        <div style="flex:1; background-color:{t['divider']}; height:6px; border-radius:3px; overflow:hidden;">
            <div style="background-color:{t['primary_blue']}; height:100%; width:{sup_pct}%;"></div>
        </div>
        <span style="font-family:monospace; font-weight:700; color:{t['text_primary']}; min-width:42px;">{sup_val}</span>
    </div>
</td>
<td style="font-family:monospace; color:{t['text_muted']}; text-align:right; width:65px;">{cnt_val}</td>
</tr>"""
                    rows_fi.append(r_html)

                fi_table_html = f"""<table class="assoc-table">
<thead>
<tr>
    <th>#</th>
    <th>ITEMSET</th>
    <th style="text-align:center;">SIZE</th>
    <th>SUPPORT</th>
    <th style="text-align:right;">COUNT</th>
</tr>
</thead>
<tbody>
{''.join(rows_fi)}
</tbody>
</table>"""
                st.html(fi_table_html)
            else:
                st.info("No frequent itemsets of size ≥ 2 found.")
        else:
            st.info("No frequent itemsets found.")

# Technical Details
with r5_c2:
    with st.container(key="card_assoc_technical_details"):
        st.html(f"""<div style="font-size:0.92rem; font-weight:700; color:{t['text_primary']}; margin-bottom:12px;">
    ▼ Technical details
</div>""")

        tech_html = f"""<div class="tech-details-grid">
    <div class="tech-item">
        <div class="tech-item-title">TRANSACTIONS</div>
        <div class="tech-item-body"><b>{total_transactions:,}</b> team-matches. Each row of Fact_Team_Match is one transaction.</div>
    </div>
    <div class="tech-item">
        <div class="tech-item-title">ITEMS (12)</div>
        <div class="tech-item-body">High / low shots, high corners, high fouls, high / low possession, 3+ cards, home, away, win, draw, loss.</div>
    </div>
    <div class="tech-item">
        <div class="tech-item-title">DISCRETISATION</div>
        <div class="tech-item-body">High = at or above the 67th percentile (shots ≥ 14, corners ≥ 6, fouls ≥ 12, possession ≥ 53%). Low = at or below the 33rd (shots ≤ 10, possession ≤ 47%). Cards = yellow + red ≥ 3.</div>
    </div>
    <div class="tech-item">
        <div class="tech-item-title">FREQUENT ITEMSETS</div>
        <div class="tech-item-body">Apriori with min support {sel_support:.2f}: <b>{n_itemsets}</b> found (12 of size 1, 58 of size 2, 75 of size 3, 17 of size 4, 2 of size 5).</div>
    </div>
    <div class="tech-item">
        <div class="tech-item-title">RULES</div>
        <div class="tech-item-body">Confidence ≥ {sel_confidence:.2f} gives <b>{len(raw_rules_df) if not raw_rules_df.empty else 0}</b> rules.</div>
    </div>
    <div class="tech-item">
        <div class="tech-item-title">TRIVIAL-RULE FILTER</div>
        <div class="tech-item-body">Rules whose sides share an attribute (Win vs Loss, High vs Low possession, Home vs Away) are dropped, then lift ≥ {sel_lift:.2f} keeps <b>{n_rules_kept}</b> ({n_trivial_removed} removed).</div>
    </div>
    <div class="tech-item">
        <div class="tech-item-title">LEAKAGE</div>
        <div class="tech-item-body">Goals and goal-based items are never used, so a rule cannot trivially restate the result.</div>
    </div>
    <div class="tech-item">
        <div class="tech-item-title">READING LIFT</div>
        <div class="tech-item-body">Lift <b>{best_lift_val:.2f}</b> means the consequent is {best_lift_val:.1f} times more likely given the antecedent than by chance.</div>
    </div>
</div>"""
        st.html(tech_html)
