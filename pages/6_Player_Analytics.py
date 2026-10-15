"""
pages/6_Player_Analytics.py — Admin Page 6: Player Analytics & Player Comparison
Matches the UI Inspiration Mockup for Player Analytics / Comparison (Labs 2 & 3):
  - Toggle between 'Single player' and 'Multiple players' modes
  - Full exact token palette support for both Dark Mode and Light Mode:
      * Page background: #0A0F1C (Dark) / #EEF2F8 (Light)
      * Sidebar: #060A14 (Dark) / #0B1220 (Light)
      * Card / Input / KPI strip: #111A2E (Dark) / #FFFFFF (Light)
      * Chip and tag fill: #17223A (Dark) / #EEF2F8 / #F4F7FC (Light)
      * Card border: #25314A (Dark) / var(--line) (Light)
      * Dividers / grid lines: #1E2940 (Dark) / #E6EAF0 (Light)
      * Chip border: #2B3957 (Dark) / var(--line) (Light)
      * Input border: #34425F (Dark) / var(--line) (Light)
      * Primary text: #E6ECF7 (Dark) / #0B1220 (Light)
      * Muted text: #94A3B8 (Dark) / #5B6578 (Light)
      * Faint text: #64748B (Dark) / #9AA4B2 (Light)
      * Primary blue: var(--acc) (Dark) / #2563EB (Light)
      * Amber: var(--pk) (Dark) / #D97706 (Light)
      * Online status dot: #16A34A
      * Form played cells: #2B4A86 (Dark) / #BFD0F7 (Light)
      * Z-score shading: 8-43% scaled opacity
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy import stats
from scipy.spatial.distance import cdist, cosine

st.set_page_config(
    page_title="Player Analytics — Analytics & DWM",
    page_icon="⚽",
    layout="wide",
)

# Role Access Guard
if st.session_state.get("auth_role") != "admin":
    st.warning("🔒 Administrator authentication required to view this technical DWM page.")
    if st.button("🔑 Login as Administrator", key="pa_auth_req_btn"):
        st.session_state["auth_role"] = "admin"
        st.rerun()
    st.stop()

from utils.admin_views import render_admin_sidebar
from utils.db import q, load_dim_season, load_dim_team, load_dim_position
from utils.theme import get_theme_tokens, get_plotly_theme_layout

# Render Admin Sidebar (which also injects global CSS)
render_admin_sidebar("Player Analytics")

# Active Theme Tokens
t = get_theme_tokens()
is_dark = t["is_dark"]
c_page_bg = t["page_bg"]
c_card_bg = t["card_bg"]
c_chip_bg = t["chip_bg"]
c_card_border = t["card_border"]
c_chip_border = t["chip_border"]
c_divider = t["divider"]
c_input_border = t["input_border"]
c_text_primary = t["text_primary"]
c_text_muted = t["text_muted"]
c_text_faint = t["text_faint"]
c_primary_blue = t["primary_blue"]
c_amber = t["amber"]
c_form_played = t["form_played"]
c_form_dnp = t["form_dnp"]
c_white = t["white"]

# ── Global Component Styles ──────────────────────────────────────────────────
st.markdown(f"""
<style>
/* Card Container */
.pa-card, [class*="st-key-card_"] {{
    background: {c_card_bg};
    border: 1px solid {c_card_border};
    border-radius: 12px;
    padding: 16px 18px;
    box-shadow: { '0 4px 16px rgba(0, 0, 0, 0.45)' if is_dark else '0 1px 3px rgba(0, 0, 0, 0.03)' };
    margin-bottom: 16px;
    box-sizing: border-box;
}}

/* Hero Player Card */
.player-hero-card {{
    background: {c_card_bg};
    border: 1px solid {c_card_border};
    border-radius: 12px;
    padding: 16px 20px;
    box-shadow: { '0 4px 16px rgba(0, 0, 0, 0.45)' if is_dark else '0 1px 3px rgba(0, 0, 0, 0.03)' };
    margin-bottom: 16px;
    box-sizing: border-box;
}}

/* Meta Pill (Chip Ladder) */
.meta-pill {{
    background: {c_chip_bg};
    border: 1px solid {c_chip_border};
    color: {c_text_muted};
    font-size: 0.75rem;
    padding: 3px 10px;
    border-radius: 6px;
    display: inline-block;
    margin-right: 6px;
    margin-bottom: 6px;
    font-weight: 500;
}}
.meta-pill b {{
    color: {c_text_primary};
    font-weight: 700;
}}

/* Tables */
.pa-table {{
    width: 100%;
    border-collapse: collapse;
}}
.pa-table th {{
    text-align: left;
    color: {c_text_muted};
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    padding: 8px 10px;
    border-bottom: 1px solid {c_card_border};
    background-color: transparent;
}}
.pa-table td {{
    padding: 8px 10px;
    color: {c_text_primary};
    font-size: 0.82rem;
    border-bottom: 1px solid {c_divider};
}}
.pa-table tr:last-child td {{
    border-bottom: none;
}}

/* Primary Button */
div[data-testid="stButton"] > button[kind="primary"] {{
    background-color: {c_primary_blue} !important;
    color: {c_white} !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    height: 38px !important;
    border: none !important;
}}

/* Small Card Header Badge */
.pa-badge {{
    background: {c_chip_bg};
    border: 1px solid {c_chip_border};
    color: {c_text_muted};
    font-size: 0.7rem;
    font-weight: 700;
    padding: 2px 7px;
    border-radius: 4px;
    text-transform: uppercase;
}}

/* Top Rank Pill in Hero */
.rank-pill {{
    background: {c_chip_bg};
    border: 1px solid {c_chip_border};
    padding: 3px 8px;
    border-radius: 6px;
    font-size: 0.72rem;
    color: {c_text_muted};
    font-weight: 500;
}}
.rank-pill b {{
    color: {c_text_primary};
    font-weight: 700;
}}
</style>
""", unsafe_allow_html=True)

# ── Load Reference Data ──────────────────────────────────────────────────────
dim_seasons = load_dim_season()
all_seasons = sorted(dim_seasons["Season_Name"].tolist(), reverse=True)

@st.cache_data(show_spinner=False)
def get_all_season_players(season_name: str) -> pd.DataFrame:
    return q(f"""
        SELECT
            p.Player_ID,
            p.Player_Name,
            t.Team_Name,
            pos.Position_Name,
            COUNT(fp.Match_ID)      AS Apps,
            SUM(fp.Minutes)         AS Minutes,
            SUM(fp.Goals)           AS Goals,
            SUM(fp.Assists)         AS Assists,
            SUM(fp.Shots)           AS Shots,
            SUM(fp.Yellow)          AS Yellow,
            SUM(fp.Red)             AS Red
        FROM Fact_Player_Performance fp
        JOIN Dim_Player p       USING(Player_ID)
        JOIN Dim_Team t         USING(Team_ID)
        JOIN Dim_Position pos   ON p.Position_ID = pos.Position_ID
        JOIN Dim_Season s       USING(Season_ID)
        WHERE s.Season_Name = '{season_name}'
        GROUP BY p.Player_ID, p.Player_Name, t.Team_Name, pos.Position_Name
        ORDER BY Goals DESC, Shots DESC
    """)

def make_initials(name):
    parts = name.split()
    return (parts[0][0] + parts[-1][0]).upper() if len(parts) >= 2 else name[:2].upper()

# ── Top Breadcrumbs & Header Bar ─────────────────────────────────────────────
default_mode = st.session_state.get("pa_mode_state", "Single player")

c_head_l, c_head_r = st.columns([3, 1.2])
with c_head_l:
    sub_title = "Single player" if default_mode == "Single player" else "Compare"

with c_head_r:
    st.markdown(f"""
    <div style="display:flex; justify-content:flex-end; align-items:center; gap:8px; height:100%; padding-top:6px;">
        <span class="pa-badge">LABS 2 · 3</span>
        <div style="background:{c_chip_bg}; border:1px solid {c_chip_border}; color:{c_text_muted}; font-size:0.76rem; font-weight:600; padding:4px 10px; border-radius:20px; display:flex; align-items:center; gap:5px;">
            <span style="height:6px; width:6px; background:#16A34A; border-radius:50%; display:inline-block;"></span> System Online
        </div>
        <div style="background:{c_chip_bg}; border:1px solid {c_chip_border}; color:{c_text_muted}; font-size:0.78rem; font-weight:600; padding:4px 10px; border-radius:20px;">
            Admin
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── 1. Top Control Panel Container ──────────────────────────────────────────
with st.container(key="card_player_analytics_controls"):
    all_p_df_temp = get_all_season_players(all_seasons[0])
    player_labels_temp = [f"{r['Player_Name']} · {r['Team_Name']} · {r['Position_Name']}" for _, r in all_p_df_temp.iterrows()]
    def_single = next((p for p in player_labels_temp if "Ali Murphy" in p), player_labels_temp[0])

    # Layout depends on mode
    cp_cols = st.columns([1.1, 1.4, 2.5, 1.3, 0.9])

    with cp_cols[0]:
        st.markdown(f"<div style='font-size:0.78rem; font-weight:600; color:{c_text_muted}; margin-bottom:6px;'>Season</div>", unsafe_allow_html=True)
        sel_season = st.selectbox("Season", all_seasons, index=0, label_visibility="collapsed", key="pa_season_sel")

    with cp_cols[1]:
        st.markdown(f"<div style='font-size:0.78rem; font-weight:600; color:{c_text_muted}; margin-bottom:6px;'>Analysis mode</div>", unsafe_allow_html=True)
        sel_mode = st.radio("Analysis mode", ["Single player", "Multiple players"], index=0, horizontal=True, label_visibility="collapsed", key="pa_mode_radio")
        st.session_state["pa_mode_state"] = sel_mode

    all_p_df = get_all_season_players(sel_season)
    player_labels = [f"{r['Player_Name']} · {r['Team_Name']} · {r['Position_Name']}" for _, r in all_p_df.iterrows()]

    if sel_mode == "Single player":
        with cp_cols[2]:
            st.markdown(f"<div style='font-size:0.78rem; font-weight:600; color:{c_text_muted}; margin-bottom:6px;'>Player</div>", unsafe_allow_html=True)
            def_idx = player_labels.index(def_single) if def_single in player_labels else 0
            sel_single_player = st.selectbox("Player", player_labels, index=def_idx, label_visibility="collapsed", key="pa_single_p")

        with cp_cols[3]:
            st.markdown(f"<div style='font-size:0.78rem; font-weight:600; color:{c_text_muted}; margin-bottom:6px;'>Benchmark against</div>", unsafe_allow_html=True)
            p_name_picked = sel_single_player.split(" · ")[0]
            p_row_picked = all_p_df[all_p_df["Player_Name"] == p_name_picked].iloc[0]
            pos_picked = p_row_picked["Position_Name"]
            n_pos_peers = len(all_p_df[all_p_df["Position_Name"] == pos_picked])
            sel_benchmark = st.selectbox("Benchmark against", [f"Same position ({n_pos_peers})", "All players (440)"], index=0, label_visibility="collapsed", key="pa_single_bench")

        with cp_cols[4]:
            st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)
            btn_action = st.button("Analyse", type="primary", key="pa_single_act_btn")

    else:
        with cp_cols[2]:
            st.markdown(f"<div style='font-size:0.78rem; font-weight:600; color:{c_text_muted}; margin-bottom:6px;'>Players - 2 of 4 selected</div>", unsafe_allow_html=True)
            multi_labels = [f"{r['Player_Name']} ({r['Team_Name']})" for _, r in all_p_df.iterrows()]
            def_p1 = next((p for p in multi_labels if "Ali Murphy" in p), multi_labels[0])
            def_p2 = next((p for p in multi_labels if "Theo Taylor" in p), multi_labels[1] if len(multi_labels)>1 else multi_labels[0])
            sel_multi_players = st.multiselect("Select players", multi_labels, default=[def_p1, def_p2], max_selections=4, label_visibility="collapsed", key="pa_multi_select")

        with cp_cols[3]:
            st.markdown(f"<div style='font-size:0.78rem; font-weight:600; color:{c_text_muted}; margin-bottom:6px;'>Target Position</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='padding-top:8px; font-size:0.84rem; color:{c_text_muted}; font-weight:600;'>Auto-aligned</div>", unsafe_allow_html=True)

        with cp_cols[4]:
            st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)
            btn_action = st.button("Compare", type="primary", key="pa_multi_act_btn")


# ═════════════════════════════════════════════════════════════════════════════
# MODE 1: SINGLE PLAYER ANALYSIS
# ═════════════════════════════════════════════════════════════════════════════
if sel_mode == "Single player":
    single_p_name = sel_single_player.split(" · ")[0]
    p_row = all_p_df[all_p_df["Player_Name"] == single_p_name].iloc[0]
    pos_name = p_row["Position_Name"]
    team_name = p_row["Team_Name"]

    # Peer group
    if "Same position" in sel_benchmark:
        peer_df = all_p_df[all_p_df["Position_Name"] == pos_name].copy().reset_index(drop=True)
        peer_label = f"{len(peer_df)} {pos_name.lower()}s"
    else:
        peer_df = all_p_df.copy().reset_index(drop=True)
        peer_label = "440 players"

    peer_count = len(peer_df)

    # Compute rates on peer group
    peer_df["G90"] = np.where(peer_df["Minutes"] > 0, peer_df["Goals"] / peer_df["Minutes"] * 90, 0.0)
    peer_df["A90"] = np.where(peer_df["Minutes"] > 0, peer_df["Assists"] / peer_df["Minutes"] * 90, 0.0)
    peer_df["S90"] = np.where(peer_df["Minutes"] > 0, peer_df["Shots"] / peer_df["Minutes"] * 90, 0.0)
    peer_df["Conv"] = np.where(peer_df["Shots"] > 0, peer_df["Goals"] / peer_df["Shots"] * 100, 0.0)
    peer_df["Y90"] = np.where(peer_df["Minutes"] > 0, peer_df["Yellow"] / peer_df["Minutes"] * 90, 0.0)

    # Percentiles
    for col in ["G90", "A90", "S90", "Conv", "Minutes"]:
        peer_df[f"{col}_pctile"] = peer_df[col].rank(pct=True) * 100
    peer_df["Discipline_pctile"] = 100 - (peer_df["Y90"].rank(pct=True) * 100)

    # Ranks (1 = highest, except Yellow where 1 = lowest)
    peer_df["Goals_rank"] = peer_df["Goals"].rank(ascending=False, method="min").astype(int)
    peer_df["Assists_rank"] = peer_df["Assists"].rank(ascending=False, method="min").astype(int)
    peer_df["Shots_rank"] = peer_df["Shots"].rank(ascending=False, method="min").astype(int)
    peer_df["G90_rank"] = peer_df["G90"].rank(ascending=False, method="min").astype(int)
    peer_df["A90_rank"] = peer_df["A90"].rank(ascending=False, method="min").astype(int)
    peer_df["S90_rank"] = peer_df["S90"].rank(ascending=False, method="min").astype(int)
    peer_df["Conv_rank"] = peer_df["Conv"].rank(ascending=False, method="min").astype(int)
    peer_df["Minutes_rank"] = peer_df["Minutes"].rank(ascending=False, method="min").astype(int)
    peer_df["Yellow_rank"] = peer_df["Yellow"].rank(ascending=True, method="min").astype(int)

    p_stats = peer_df[peer_df["Player_Name"] == single_p_name].iloc[0]

    # Metadata Strip
    st.markdown(f"""
    <div style="margin-bottom:14px;">
        <span class="meta-pill">source <b>Fact_Player_Performance</b></span>
        <span class="meta-pill">grain <b>player × match</b></span>
        <span class="meta-pill">season <b>{sel_season}</b></span>
        <span class="meta-pill">benchmark <b>{peer_label}</b></span>
        <span class="meta-pill">rows used <b>{int(p_stats['Apps'])}</b></span>
    </div>
    """, unsafe_allow_html=True)

    # ── Player Profile Hero Card ─────────────────────────────────────────────
    st.markdown(f"""<div class="player-hero-card" style="border-top:3px solid {t['primary_blue']};">
<div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
    <div style="display:flex; align-items:center; gap:12px;">
        <div style="width:44px; height:44px; border-radius:50%; background:{t['primary_blue']}; color:{t['white']}; display:flex; align-items:center; justify-content:center; font-weight:700; font-size:1.1rem;">
            {make_initials(single_p_name)}
        </div>
        <div>
            <div style="color:{t['text_primary']}; font-size:1.25rem; font-weight:700;">{single_p_name}</div>
            <div style="color:{t['text_muted']}; font-size:0.78rem;">{team_name} · {pos_name} · {sel_season}</div>
        </div>
    </div>
    <div style="display:flex; gap:6px; flex-wrap:wrap;">
        <span class="rank-pill">Goals <b>#{p_stats['Goals_rank']} of {peer_count}</b></span>
        <span class="rank-pill">Assists <b>#{p_stats['Assists_rank']} of {peer_count}</b></span>
        <span class="rank-pill">Goals / 90 <b>#{p_stats['G90_rank']} of {peer_count}</b></span>
        <span class="rank-pill">Shots <b>#{p_stats['Shots_rank']} of {peer_count}</b></span>
        <span class="rank-pill">Conversion <b>#{p_stats['Conv_rank']} of {peer_count}</b></span>
    </div>
</div>
<div style="display:grid; grid-template-columns:repeat(6, 1fr); gap:8px; margin-top:16px; border-top:1px solid {t['divider']}; padding-top:12px;">
    <div>
        <div style="color:{t['text_muted']}; font-size:0.68rem; font-weight:700; text-transform:uppercase;">APPEARANCES</div>
        <div style="color:{t['text_primary']}; font-size:1.4rem; font-weight:700;">{int(p_stats['Apps'])}</div>
        <div style="color:{t['text_faint']}; font-size:0.72rem;">38 team matches</div>
    </div>
    <div>
        <div style="color:{t['text_muted']}; font-size:0.68rem; font-weight:700; text-transform:uppercase;">MINUTES</div>
        <div style="color:{t['text_primary']}; font-size:1.4rem; font-weight:700;">{int(p_stats['Minutes']):,}</div>
        <div style="color:{t['text_faint']}; font-size:0.72rem;">{p_stats['Minutes']/p_stats['Apps']:.1f} per app</div>
    </div>
    <div>
        <div style="color:{t['text_muted']}; font-size:0.68rem; font-weight:700; text-transform:uppercase;">GOALS</div>
        <div style="color:{t['primary_blue']}; font-size:1.4rem; font-weight:700;">{int(p_stats['Goals'])}</div>
        <div style="color:{t['text_faint']}; font-size:0.72rem;">{p_stats['G90']:.2f} per 90</div>
    </div>
    <div>
        <div style="color:{t['text_muted']}; font-size:0.68rem; font-weight:700; text-transform:uppercase;">ASSISTS</div>
        <div style="color:{t['amber']}; font-size:1.4rem; font-weight:700;">{int(p_stats['Assists'])}</div>
        <div style="color:{t['text_faint']}; font-size:0.72rem;">{p_stats['A90']:.2f} per 90</div>
    </div>
    <div>
        <div style="color:{t['text_muted']}; font-size:0.68rem; font-weight:700; text-transform:uppercase;">SHOTS</div>
        <div style="color:{t['text_primary']}; font-size:1.4rem; font-weight:700;">{int(p_stats['Shots'])}</div>
        <div style="color:{t['text_faint']}; font-size:0.72rem;">{p_stats['S90']:.2f} per 90</div>
    </div>
    <div>
        <div style="color:{t['text_muted']}; font-size:0.68rem; font-weight:700; text-transform:uppercase;">CONVERSION</div>
        <div style="color:{t['text_primary']}; font-size:1.4rem; font-weight:700;">{p_stats['Conv']:.1f}%</div>
        <div style="color:{t['text_faint']}; font-size:0.72rem;">peer mean {peer_df['Conv'].mean():.1f}%</div>
    </div>
</div>
</div>""", unsafe_allow_html=True)

    # ── Row 1: Profile vs Peers & Rates with Uncertainty ─────────────────────
    s_r1_l, s_r1_r = st.columns([1.0, 1.1])

    with s_r1_l:
        with st.container(key="card_profile_vs_peers"):
            st.markdown(f"""<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
    <h3 style="color:{t['text_primary']}; font-size:1.02rem; font-weight:700; margin:0;">Profile vs peers</h3>
    <span class="pa-badge">PERCENTILE 0–100</span>
</div>
""", unsafe_allow_html=True)

            radar_axes = ["Goals / 90", "Assists / 90", "Shots / 90", "Conversion", "Minutes", "Discipline"]
            val_pct = [
                int(round(p_stats["G90_pctile"])),
                int(round(p_stats["A90_pctile"])),
                int(round(p_stats["S90_pctile"])),
                int(round(p_stats["Conv_pctile"])),
                int(round(p_stats["Minutes_pctile"])),
                int(round(p_stats["Discipline_pctile"])),
            ]
            median_pct = [50, 50, 50, 50, 50, 50]

            fig_rad = go.Figure()
            fig_rad.add_trace(go.Scatterpolar(
                r=val_pct + [val_pct[0]],
                theta=radar_axes + [radar_axes[0]],
                fill="toself",
                fillcolor="rgba(59, 130, 246, 0.18)" if is_dark else "rgba(37, 99, 235, 0.14)",
                line=dict(color=t["primary_blue"], width=2.5),
                name=single_p_name,
                hoverinfo="theta+r"
            ))
            fig_rad.add_trace(go.Scatterpolar(
                r=median_pct + [median_pct[0]],
                theta=radar_axes + [radar_axes[0]],
                mode="lines",
                line=dict(color=t["text_faint"], dash="dash", width=1.5),
                name="Peer median (50)",
                hoverinfo="theta+r"
            ))

            fig_rad.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, 100], tickvals=[25, 50, 75, 100], tickfont=dict(size=8, color=t["text_faint"]), gridcolor=t["divider"]),
                    angularaxis=dict(tickfont=dict(size=9.5, color=t["text_primary"], weight=600), gridcolor=t["divider"]),
                    bgcolor="rgba(0,0,0,0)"
                ),
                height=265,
                margin=dict(l=20, r=20, t=15, b=15),
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.12, xanchor="center", x=0.5, font=dict(size=9, color=t["text_muted"])),
                paper_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_rad, use_container_width=True, config={"displayModeBar": False})
            st.markdown(f"""<div style="font-size:0.72rem; color:{t['text_faint']}; margin-top:8px;">
Each axis is the percentile among {peer_count} {pos_name.lower()}s. Discipline is inverted: fewer yellow cards per 90 scores higher.
</div>""", unsafe_allow_html=True)

    # Right: Rates with Uncertainty
    with s_r1_r:
        with st.container(key="card_rates_with_uncertainty"):
            st.markdown(f"""<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
    <h3 style="color:{t['text_primary']}; font-size:1.02rem; font-weight:700; margin:0;">Rates with uncertainty</h3>
    <span class="pa-badge">95% INTERVAL</span>
</div>
""", unsafe_allow_html=True)

            t_exp = max(p_stats["Minutes"] / 90.0, 0.1)

            def get_rate_interval(k, t, peer_mean):
                k = int(k)
                r_pt = k / t
                r_low = (0.5 * stats.chi2.ppf(0.025, 2 * k) / t) if k > 0 else 0.0
                r_high = 0.5 * stats.chi2.ppf(0.975, 2 * (k + 1)) / t
                return r_pt, r_low, r_high, peer_mean

            u_metrics = [
                ("Goals / 90", p_stats["Goals"], t_exp, peer_df["G90"].mean()),
                ("Assists / 90", p_stats["Assists"], t_exp, peer_df["A90"].mean()),
                ("Shots / 90", p_stats["Shots"], t_exp, peer_df["S90"].mean()),
                ("Yellow / 90", p_stats["Yellow"], t_exp, peer_df["Y90"].mean()),
            ]

            fig_unc = go.Figure()
            y_labels = [m[0] for m in u_metrics]

            for idx, (m_label, k_cnt, t_e, p_mean) in enumerate(u_metrics):
                r_pt, r_low, r_high, p_m = get_rate_interval(k_cnt, t_e, p_mean)
                
                # Shaded horizontal interval bar
                fig_unc.add_trace(go.Scatter(
                    x=[r_low, r_high], y=[m_label, m_label],
                    mode="lines",
                    line=dict(color=t["form_played"], width=12),
                    hoverinfo="skip", showlegend=False
                ))
                # Point estimate dot
                fig_unc.add_trace(go.Scatter(
                    x=[r_pt], y=[m_label],
                    mode="markers",
                    marker=dict(color=t["primary_blue"], size=9, line=dict(color=t["white"], width=1.5)),
                    name="Player rate" if idx==0 else None,
                    hoverinfo="text",
                    hovertext=f"{m_label}: {r_pt:.2f} (95% CI: {r_low:.2f} – {r_high:.2f})",
                    showlegend=(idx==0)
                ))
                # Peer mean dashed tick
                fig_unc.add_trace(go.Scatter(
                    x=[p_m, p_m], y=[idx - 0.25, idx + 0.25],
                    mode="lines",
                    line=dict(color=t["text_primary"], width=2.5, dash="dash"),
                    name="Peer mean" if idx==0 else None,
                    hoverinfo="text",
                    hovertext=f"Peer mean: {p_m:.2f}",
                    showlegend=(idx==0)
                ))
                # Value annotation on the far right
                fig_unc.add_annotation(
                    x=max(r_high, p_m) * 1.08 + 0.1, y=m_label,
                    text=f"<b>{r_pt:.2f}</b>", showarrow=False,
                    font=dict(size=10, color=t["text_primary"]), xanchor="left"
                )

            fig_unc.update_layout(
                height=265,
                margin=dict(l=10, r=40, t=15, b=15),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=True, gridcolor=t["divider"], title=dict(text="Rate per 90 minutes", font=dict(size=10.5, color=t["text_muted"])), tickfont=dict(color=t["text_faint"])),
                yaxis=dict(showgrid=False, autorange="reversed", tickfont=dict(size=10, color=t["text_primary"])),
                legend=dict(orientation="h", yanchor="bottom", y=-0.22, xanchor="left", x=0, font=dict(size=8.5, color=t["text_muted"]))
            )
            st.plotly_chart(fig_unc, use_container_width=True, config={"displayModeBar": False})
            st.markdown(f"""<div style="font-size:0.72rem; color:{t['text_faint']}; margin-top:4px;">
A wide interval means few events or few minutes. When the peer-mean line sits outside the interval, the player is clearly above or below average.
</div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)

    # ── Row 2: Standing Among Peers Table (Rank - Z-Score - Percentile) ─────────
    with st.container(key="card_standing_among_peers"):
        st.markdown(f"""<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
    <h3 style="color:{t['text_primary']}; font-size:1.02rem; font-weight:700; margin:0;">Standing among {peer_count} {pos_name.lower()}s</h3>
    <span class="pa-badge">RANK · Z-SCORE · PERCENTILE</span>
</div>
""", unsafe_allow_html=True)

        standings_def = [
            ("Goals", "Goals", "Goals_rank", 0, False),
            ("Assists", "Assists", "Assists_rank", 0, False),
            ("Shots", "Shots", "Shots_rank", 0, False),
            ("Goals / 90", "G90", "G90_rank", 2, True),
            ("Assists / 90", "A90", "A90_rank", 2, True),
            ("Shots / 90", "S90", "S90_rank", 2, True),
            ("Conversion %", "Conv", "Conv_rank", 1, False),
            ("Minutes", "Minutes", "Minutes_rank", 0, False),
            ("Yellow cards", "Yellow", "Yellow_rank", 0, True),  # Inverted rank
        ]

        std_rows_html = ""
        for label, col, rank_col, decimals, is_inverted in standings_def:
            val = p_stats[col]
            peer_m = peer_df[col].mean()
            peer_s = peer_df[col].std() if peer_df[col].std() > 0 else 1.0
            
            z_val = (val - peer_m) / peer_s
            rank_val = int(p_stats[rank_col])
            
            if col in ["G90", "A90", "S90", "Conv", "Minutes"]:
                pct_val = int(round(p_stats[f"{col}_pctile"]))
            elif col == "Yellow":
                pct_val = int(round(p_stats["Discipline_pctile"]))
            else:
                pct_val = int(round(peer_df[col].rank(pct=True).loc[p_stats.name] * 100))

            fmt_val = f"{val:.{decimals}f}" if decimals > 0 else f"{int(val):,}"
            fmt_m = f"{peer_m:.{decimals}f}" if decimals > 0 else f"{peer_m:.1f}"
            fmt_s = f"{peer_s:.{decimals}f}" if decimals > 0 else f"{peer_s:.2f}"

            # Shading with opacity scaling: above average is #3B82F6 at 8-43%, below is #8A94A6 at 8-43%
            is_positive_good = (z_val >= 0) if not (col == "Yellow") else (z_val <= 0)
            op_scale = min(0.43, max(0.08, 0.08 + (min(abs(z_val), 3.0) / 3.0) * 0.35))
            
            if is_positive_good:
                bg_z = f"rgba(59, 130, 246, {op_scale:.2f})" if is_dark else f"rgba(37, 99, 235, {op_scale:.2f})"
                fg_z = t["primary_blue"] if is_dark else "#1D4ED8"
            else:
                bg_z = f"rgba(138, 148, 166, {op_scale:.2f})"
                fg_z = t["text_muted"]
                
            sign_z = "+" if z_val >= 0 else ""
            bar_w = int((pct_val / 100.0) * 110)

            std_rows_html += f"""<tr>
<td style="font-weight:600; color:{t['text_primary']};">{label}</td>
<td style="font-weight:700; text-align:right; color:{t['text_primary']};">{fmt_val}</td>
<td style="color:{t['text_muted']}; text-align:right;">{fmt_m}</td>
<td style="color:{t['text_muted']}; text-align:right;">{fmt_s}</td>
<td style="text-align:center;"><span style="background:{bg_z}; color:{fg_z}; padding:2px 8px; border-radius:4px; font-weight:700; font-size:0.78rem;">{sign_z}{z_val:.2f}</span></td>
<td style="text-align:center; font-weight:600; color:{t['text_primary']};">{rank_val} / {peer_count}</td>
<td style="min-width:140px;">
    <div style="display:flex; align-items:center; gap:8px;">
        <div style="background:{t['chip_bg']}; width:110px; height:7px; border-radius:3.5px; overflow:hidden;">
            <div style="background:{t['primary_blue']}; width:{bar_w}px; height:7px; border-radius:3.5px;"></div>
        </div>
        <span style="font-weight:700; font-size:0.8rem; color:{t['text_primary']}; width:25px; text-align:right;">{pct_val}</span>
    </div>
</td>
</tr>"""

        st.markdown(f"""
<table class="pa-table">
<thead>
<tr>
    <th>METRIC</th>
    <th style="text-align:right;">VALUE</th>
    <th style="text-align:right;">PEER MEAN</th>
    <th style="text-align:right;">PEER SD</th>
    <th style="text-align:center;">Z-SCORE</th>
    <th style="text-align:center;">RANK</th>
    <th>PERCENTILE</th>
</tr>
</thead>
<tbody>
{std_rows_html}
</tbody>
</table>
<div style="font-size:0.72rem; color:{t['text_faint']}; margin-top:10px;">
Rank 1 = highest value. For yellow cards, rank 1 = fewest. z-score shading: blue is better than average, grey is worse.
</div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)

    # ── Row 3: Contributions Through The Season vs Season Form ─────────────────
    s_r3_l, s_r3_r = st.columns([1.1, 1.0])

    # Left: Contributions Line Chart
    with s_r3_l:
        with st.container(key="card_single_contributions"):
            st.markdown(f"""<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
    <h3 style="color:{t['text_primary']}; font-size:1.02rem; font-weight:700; margin:0;">Contributions through the season</h3>
    <span class="pa-badge">CUMULATIVE</span>
</div>
""", unsafe_allow_html=True)

            @st.cache_data(show_spinner=False)
            def get_single_player_trajectory(p_name: str, t_name: str, season_name: str) -> pd.DataFrame:
                df_matches = q(f"""
                    SELECT
                        fp.Match_ID,
                        fp.Goals,
                        fp.Assists
                    FROM Fact_Player_Performance fp
                    JOIN Dim_Player p USING(Player_ID)
                    JOIN Dim_Team t USING(Team_ID)
                    JOIN Dim_Season s USING(Season_ID)
                    WHERE s.Season_Name = '{season_name}' AND p.Player_Name = '{p_name}' AND t.Team_Name = '{t_name}'
                    ORDER BY fp.Match_ID ASC
                """)
                if df_matches.empty:
                    return pd.DataFrame({"Matchday": range(1, 39), "Cum_Goals": 0, "Cum_GA": 0})
                
                df_matches["Matchday"] = range(1, len(df_matches) + 1)
                df_matches["Cum_Goals"] = df_matches["Goals"].cumsum()
                df_matches["Cum_GA"] = (df_matches["Goals"] + df_matches["Assists"]).cumsum()
                return df_matches

            traj_single = get_single_player_trajectory(single_p_name, team_name, sel_season)
            peer_mean_final_ga = peer_df["Goals"].mean() + peer_df["Assists"].mean()
            peer_avg_line = np.linspace(0, peer_mean_final_ga, len(traj_single) if not traj_single.empty else 38)

            fig_st = go.Figure()
            fig_st.add_trace(go.Scatter(
                x=traj_single["Matchday"], y=traj_single["Cum_GA"],
                mode="lines", line=dict(color=t["primary_blue"], width=2.5),
                name="Goals + assists", hoverinfo="x+y"
            ))
            fig_st.add_trace(go.Scatter(
                x=traj_single["Matchday"], y=traj_single["Cum_Goals"],
                mode="lines", line=dict(color="#60A5FA" if is_dark else "#93C5FD", dash="dash", width=1.5),
                name="Goals only", hoverinfo="x+y"
            ))
            fig_st.add_trace(go.Scatter(
                x=traj_single["Matchday"], y=peer_avg_line,
                mode="lines", line=dict(color=t["text_faint"], dash="dash", width=1.5),
                name=f"Average {pos_name.lower()} (G + A)", hoverinfo="x+y"
            ))

            if not traj_single.empty:
                fig_st.add_annotation(
                    x=traj_single["Matchday"].iloc[-1], y=traj_single["Cum_GA"].iloc[-1],
                    text=f"<b>{traj_single['Cum_GA'].iloc[-1]}</b>", showarrow=False,
                    font=dict(size=10.5, color=t["primary_blue"]), xanchor="left"
                )
                fig_st.add_annotation(
                    x=traj_single["Matchday"].iloc[-1], y=peer_avg_line[-1],
                    text=f"<b>{peer_mean_final_ga:.1f}</b>", showarrow=False,
                    font=dict(size=9.5, color=t["text_muted"]), xanchor="left"
                )

            fig_st.update_layout(
                height=250,
                margin=dict(l=10, r=25, t=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(title=dict(text="Team matchday", font=dict(size=10.5, color=t["text_muted"])), showgrid=True, gridcolor=t["divider"], dtick=5, tickfont=dict(color=t["text_faint"])),
                yaxis=dict(showgrid=True, gridcolor=t["divider"], tickfont=dict(color=t["text_faint"])),
                legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="left", x=0, font=dict(size=8.5, color=t["text_muted"]))
            )
            st.plotly_chart(fig_st, use_container_width=True, config={"displayModeBar": False})

    # Right: Season Form (38 Matchday Grid)
    with s_r3_r:
        with st.container(key="card_single_season_form"):
            st.markdown(f"""<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
    <h3 style="color:{t['text_primary']}; font-size:1.02rem; font-weight:700; margin:0;">Season form</h3>
    <span class="pa-badge">PER MATCHDAY</span>
</div>
""", unsafe_allow_html=True)

            @st.cache_data(show_spinner=False)
            def get_team_all_matches_for_player(p_name: str, t_name: str, season_name: str):
                team_matches = q(f"""
                    SELECT tm.Match_ID, tm.Date_ID
                    FROM Fact_Team_Match tm
                    JOIN Dim_Team t USING(Team_ID)
                    JOIN Dim_Season s USING(Season_ID)
                    WHERE s.Season_Name = '{season_name}' AND t.Team_Name = '{t_name}'
                    ORDER BY tm.Match_ID ASC
                """)
                player_perf = q(f"""
                    SELECT fp.Match_ID, fp.Minutes, fp.Goals, fp.Assists
                    FROM Fact_Player_Performance fp
                    JOIN Dim_Player p USING(Player_ID)
                    JOIN Dim_Team t USING(Team_ID)
                    JOIN Dim_Season s USING(Season_ID)
                    WHERE s.Season_Name = '{season_name}' AND p.Player_Name = '{p_name}' AND t.Team_Name = '{t_name}'
                """).set_index("Match_ID")

                blocks = []
                for _, m_row in team_matches.iterrows():
                    mid = m_row["Match_ID"]
                    if mid in player_perf.index:
                        rec = player_perf.loc[mid]
                        g = int(rec["Goals"])
                        a = int(rec["Assists"])
                        mins = int(rec["Minutes"])
                        if g > 0 and a > 0:
                            status = "goal_assist"
                        elif g > 0:
                            status = "goal"
                        elif a > 0:
                            status = "assist"
                        elif mins > 0:
                            status = "played"
                        else:
                            status = "bench"
                        blocks.append({"status": status, "goals": g, "assists": a, "mins": mins})
                    else:
                        blocks.append({"status": "not_in_squad", "goals": 0, "assists": 0, "mins": 0})
                return blocks

            form_blocks = get_team_all_matches_for_player(single_p_name, team_name, sel_season)
            
            # Color mapping for form blocks using user specification
            block_html = ""
            for i, b in enumerate(form_blocks[:38]):
                st_type = b["status"]
                g_num = b["goals"]
                
                if st_type == "goal_assist":
                    bg = t["white"] if is_dark else "#0F172A"
                    text_col = "#0A0F1C" if is_dark else "#FFFFFF"
                    txt = f"<span style='color:{text_col}; font-weight:700; font-size:0.7rem;'>{g_num}</span>"
                elif st_type == "goal":
                    bg = t["amber"]
                    txt = f"<span style='color:#FFFFFF; font-weight:700; font-size:0.7rem;'>{g_num}</span>"
                elif st_type == "assist":
                    bg = t["primary_blue"]
                    txt = ""
                elif st_type == "played":
                    bg = t["form_played"]  # #2B4A86 on dark, #BFD0F7 on light
                    txt = ""
                else:
                    bg = t["form_dnp"]     # #17223A on dark, #F1F5F9 on light
                    txt = ""

                border_style = f"border:1px solid {t['chip_border']};" if st_type == "not_in_squad" else ""

                block_html += f"""<div style="background:{bg}; {border_style} width:16px; height:20px; border-radius:3px; display:flex; align-items:center; justify-content:center; margin:2px;" title="Match {i+1}: {st_type.replace('_',' ')} (Goals: {b['goals']}, Assists: {b['assists']})">
{txt}
</div>"""

            st.markdown(f"""<div style="display:flex; flex-wrap:wrap; width:100%; max-width:390px; margin-top:8px; margin-bottom:12px;">
{block_html}
</div>
<div style="display:flex; flex-wrap:wrap; gap:10px; font-size:0.72rem; color:{t['text_muted']}; margin-top:8px;">
<span><span style="display:inline-block; width:8px; height:8px; background:{t['amber']}; border-radius:2px; margin-right:3px;"></span>Goal</span>
<span><span style="display:inline-block; width:8px; height:8px; background:{t['primary_blue']}; border-radius:2px; margin-right:3px;"></span>Assist only</span>
<span><span style="display:inline-block; width:8px; height:8px; background:{t['white'] if is_dark else '#0F172A'}; border-radius:2px; margin-right:3px;"></span>Goal + assist</span>
<span><span style="display:inline-block; width:8px; height:8px; background:{t['form_played']}; border-radius:2px; margin-right:3px;"></span>Played</span>
<span><span style="display:inline-block; width:8px; height:8px; background:{t['form_dnp']}; border-radius:2px; margin-right:3px; border:1px solid {t['chip_border']};"></span>Not in squad</span>
</div>
<div style="font-size:0.72rem; color:{t['text_faint']}; margin-top:8px;">
Matchdays 1–38, left to right, top row first. Number = goals scored.
</div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)

    # ── Row 4: Contribution to Team vs Closest Profiles ────────────────────────
    s_r4_l, s_r4_r = st.columns([1.0, 1.1])

    # Left: Contribution to Team (Team Share)
    with s_r4_l:
        with st.container(key="card_single_team_contribution"):
            st.markdown(f"""<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
    <h3 style="color:{t['text_primary']}; font-size:1.02rem; font-weight:700; margin:0;">Contribution to {team_name}</h3>
    <span class="pa-badge">TEAM SHARE</span>
</div>
""", unsafe_allow_html=True)

            @st.cache_data(show_spinner=False)
            def get_team_total_stats(t_name: str, season_name: str):
                res = q(f"""
                    SELECT
                        SUM(fp.Goals) AS G,
                        SUM(fp.Assists) AS A,
                        SUM(fp.Shots) AS S,
                        COUNT(DISTINCT fp.Player_ID) AS Squad_Size
                    FROM Fact_Player_Performance fp
                    JOIN Dim_Team t USING(Team_ID)
                    JOIN Dim_Season s USING(Season_ID)
                    WHERE s.Season_Name = '{season_name}' AND t.Team_Name = '{t_name}'
                """).iloc[0]
                return int(res["G"]), int(res["A"]), int(res["S"]), int(res["Squad_Size"])

            team_g, team_a, team_s, team_squad = get_team_total_stats(team_name, sel_season)
            team_ga = team_g + team_a
            player_ga = int(p_stats["Goals"] + p_stats["Assists"])

            pct_g = (p_stats["Goals"] / team_g * 100) if team_g > 0 else 0.0
            pct_ga = (player_ga / team_ga * 100) if team_ga > 0 else 0.0
            pct_s = (p_stats["Shots"] / team_s * 100) if team_s > 0 else 0.0

            st.markdown(f"""<div style="margin-top:12px;">
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
<span style="font-size:0.8rem; font-weight:600; color:{t['text_muted']};">Team goals</span>
<span style="font-size:0.8rem; font-weight:700; color:{t['text_primary']};">{int(p_stats['Goals'])} / {team_g} · {pct_g:.1f}%</span>
</div>
<div style="background:{t['chip_bg']}; height:8px; border-radius:4px; overflow:hidden; margin-bottom:14px;">
<div style="background:{t['primary_blue']}; width:{pct_g:.1f}%; height:8px; border-radius:4px;"></div>
</div>
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
<span style="font-size:0.8rem; font-weight:600; color:{t['text_muted']};">Team goals + assists</span>
<span style="font-size:0.8rem; font-weight:700; color:{t['text_primary']};">{player_ga} / {team_ga} · {pct_ga:.1f}%</span>
</div>
<div style="background:{t['chip_bg']}; height:8px; border-radius:4px; overflow:hidden; margin-bottom:14px;">
<div style="background:{t['amber']}; width:{pct_ga:.1f}%; height:8px; border-radius:4px;"></div>
</div>
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
<span style="font-size:0.8rem; font-weight:600; color:{t['text_muted']};">Team shots</span>
<span style="font-size:0.8rem; font-weight:700; color:{t['text_primary']};">{int(p_stats['Shots'])} / {team_s} · {pct_s:.1f}%</span>
</div>
<div style="background:{t['chip_bg']}; height:8px; border-radius:4px; overflow:hidden; margin-bottom:12px;">
<div style="background:{t['text_primary']}; width:{pct_s:.1f}%; height:8px; border-radius:4px;"></div>
</div>
</div>
<div style="font-size:0.72rem; color:{t['text_faint']}; margin-top:12px;">
Team totals add up all {team_squad} {team_name} squad members in {sel_season}.
</div>""", unsafe_allow_html=True)

    # Right: Closest Profiles (Top 5 Nearest Neighbours)
    with s_r4_r:
        with st.container(key="card_single_closest_profiles"):
            st.markdown(f"""<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
    <h3 style="color:{t['text_primary']}; font-size:1.02rem; font-weight:700; margin:0;">Closest profiles</h3>
    <span class="pa-badge">NEAREST NEIGHBOURS · EUCLIDEAN</span>
</div>
""", unsafe_allow_html=True)

            feats_z = ["G90", "A90", "S90", "Conv", "Minutes", "Y90"]
            z_pop = (peer_df[feats_z] - peer_df[feats_z].mean()) / peer_df[feats_z].std()
            
            vec_p = z_pop.loc[p_stats.name].values
            dists = cdist([vec_p], z_pop)[0]
            peer_df["dist"] = dists

            closest_5 = peer_df[peer_df["Player_Name"] != single_p_name].sort_values("dist").head(5).reset_index(drop=True)

            nn_rows_html = ""
            for idx, r in closest_5.iterrows():
                nn_rows_html += f"""<tr>
<td style="color:{t['text_faint']}; font-weight:600; width:20px;">{idx+1}</td>
<td style="font-weight:700; color:{t['text_primary']};">{r['Player_Name']}</td>
<td style="color:{t['text_muted']};">{r['Team_Name']}</td>
<td style="text-align:right; font-weight:700; color:{t['text_primary']};">{int(r['Goals'])}</td>
<td style="text-align:right; color:{t['text_primary']};">{int(r['Assists'])}</td>
<td style="text-align:right; font-weight:600; color:{t['text_primary']};">{r['G90']:.2f}</td>
<td style="text-align:right; color:{t['text_primary']};">{r['Conv']:.1f}%</td>
<td style="text-align:right; color:{t['text_primary']}; font-weight:700;">{r['dist']:.2f}</td>
</tr>"""

            st.markdown(f"""
<table class="pa-table">
<thead>
<tr>
    <th>#</th>
    <th>PLAYER</th>
    <th>TEAM</th>
    <th style="text-align:right;">GOALS</th>
    <th style="text-align:right;">ASSISTS</th>
    <th style="text-align:right;">G/90</th>
    <th style="text-align:right;">CONV.</th>
    <th style="text-align:right;">DISTANCE</th>
</tr>
</thead>
<tbody>
{nn_rows_html}
</tbody>
</table>""", unsafe_allow_html=True)

    st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)

    # ── Technical Details Box ────────────────────────────────────────────────
    st.markdown(f"""<div class="pa-card">
<div style="display:flex; align-items:center; gap:8px; margin-bottom:12px; cursor:pointer;">
<span style="font-size:0.8rem; color:{t['text_muted']};">▼</span>
<span style="color:{t['text_primary']}; font-size:0.96rem; font-weight:700;">Technical details</span>
<span class="pa-badge" style="margin-left:auto;">METHOD</span>
</div>
<div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:16px; font-size:0.82rem;">
<div>
<div style="color:{t['text_muted']}; font-size:0.72rem; margin-bottom:2px; font-weight:700;">AGGREGATION</div>
<div style="color:{t['text_primary']}; font-weight:500;">SUM over matches for one player-season (OLAP roll-up from player × match)</div>
</div>
<div>
<div style="color:{t['text_muted']}; font-size:0.72rem; margin-bottom:2px; font-weight:700;">PER-90</div>
<div style="color:{t['text_primary']}; font-weight:500;">metric ÷ (minutes ÷ 90)</div>
</div>
<div>
<div style="color:{t['text_muted']}; font-size:0.72rem; margin-bottom:2px; font-weight:700;">BENCHMARK</div>
<div style="color:{t['text_primary']}; font-weight:500;">80 forwards in 2025/26; mean, SD and percentile all use this group</div>
</div>
<div>
<div style="color:{t['text_muted']}; font-size:0.72rem; margin-bottom:2px; font-weight:700;">Z-SCORE</div>
<div style="color:{t['text_primary']}; font-weight:500;">(value − peer mean) ÷ peer SD (population SD)</div>
</div>
<div>
<div style="color:{t['text_muted']}; font-size:0.72rem; margin-bottom:2px; font-weight:700;">95% INTERVAL</div>
<div style="color:{t['text_primary']}; font-weight:500;">Exact Poisson interval for a count, exposure = minutes ÷ 90</div>
</div>
<div>
<div style="color:{t['text_muted']}; font-size:0.72rem; margin-bottom:2px; font-weight:700;">SIMILARITY</div>
<div style="color:{t['text_primary']}; font-weight:500;">Euclidean distance on 6 z-scores (goals, assists, shots per 90, conversion, minutes, yellow per 90)</div>
</div>
<div>
<div style="color:{t['text_muted']}; font-size:0.72rem; margin-bottom:2px; font-weight:700;">AVERAGE FORWARD LINE</div>
<div style="color:{t['text_primary']}; font-weight:500;">Mean cumulative goals + assists of all 80 peers by their team matchday</div>
</div>
<div>
<div style="color:{t['text_muted']}; font-size:0.72rem; margin-bottom:2px; font-weight:700;">SAMPLE SIZE</div>
<div style="color:{t['text_primary']}; font-weight:500;">1,680 minutes. Rates from fewer than about 900 minutes are unstable.</div>
</div>
</div>
</div>""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# MODE 2: MULTIPLE PLAYERS COMPARISON
# ═════════════════════════════════════════════════════════════════════════════
else:
    if len(sel_multi_players) >= 2:
        p_name_a = sel_multi_players[0].split(" (")[0]
        p_name_b = sel_multi_players[1].split(" (")[0]
    elif len(sel_multi_players) == 1:
        p_name_a = sel_multi_players[0].split(" (")[0]
        p_name_b = all_p_df[all_p_df["Player_Name"] != p_name_a].iloc[0]["Player_Name"]
    else:
        p_name_a = all_p_df.iloc[0]["Player_Name"]
        p_name_b = all_p_df.iloc[1]["Player_Name"]

    p_row_a = all_p_df[all_p_df["Player_Name"] == p_name_a].iloc[0]
    p_row_b = all_p_df[all_p_df["Player_Name"] == p_name_b].iloc[0]

    target_position = p_row_a["Position_Name"]
    peer_df = all_p_df[all_p_df["Position_Name"] == target_position].copy().reset_index(drop=True)
    peer_count = len(peer_df)

    # Metadata Strip
    st.markdown(f"""
    <div style="margin-bottom:14px;">
        <span class="meta-pill">source <b>Fact_Player_Performance</b></span>
        <span class="meta-pill">grain <b>player × match</b></span>
        <span class="meta-pill">season <b>{sel_season}</b></span>
        <span class="meta-pill">peer group <b>{peer_count} {target_position.lower()}s</b></span>
        <span class="meta-pill">percentile <b>vs same position</b></span>
    </div>
    """, unsafe_allow_html=True)

    # Hero Cards
    hero_l, hero_r = st.columns(2)

    with hero_l:
        st.markdown(f"""<div class="player-hero-card" style="border-top:3px solid {t['primary_blue']};">
<div style="display:flex; justify-content:space-between; align-items:flex-start;">
    <div style="display:flex; align-items:center; gap:12px;">
        <div style="width:42px; height:42px; border-radius:50%; background:{t['primary_blue']}; color:{t['white']}; display:flex; align-items:center; justify-content:center; font-weight:700; font-size:1rem;">
            {make_initials(p_name_a)}
        </div>
        <div>
            <div style="color:{t['text_primary']}; font-size:1.15rem; font-weight:700;">{p_name_a}</div>
            <div style="color:{t['text_muted']}; font-size:0.78rem;">{p_row_a['Team_Name']} · {p_row_a['Position_Name']} · {sel_season}</div>
        </div>
    </div>
    <span class="pa-badge" style="background:{t['chip_bg']}; color:{t['primary_blue']}; border:1px solid {t['chip_border']};">PLAYER A</span>
</div>
<div style="display:grid; grid-template-columns:repeat(5, 1fr); gap:8px; margin-top:14px; border-top:1px solid {t['divider']}; padding-top:10px;">
    <div><div style="color:{t['text_muted']}; font-size:0.68rem; font-weight:700;">APPS</div><div style="color:{t['text_primary']}; font-size:1.2rem; font-weight:700;">{int(p_row_a['Apps'])}</div></div>
    <div><div style="color:{t['text_muted']}; font-size:0.68rem; font-weight:700;">MINUTES</div><div style="color:{t['text_primary']}; font-size:1.2rem; font-weight:700;">{int(p_row_a['Minutes']):,}</div></div>
    <div><div style="color:{t['text_muted']}; font-size:0.68rem; font-weight:700;">GOALS</div><div style="color:{t['primary_blue']}; font-size:1.2rem; font-weight:700;">{int(p_row_a['Goals'])}</div></div>
    <div><div style="color:{t['text_muted']}; font-size:0.68rem; font-weight:700;">ASSISTS</div><div style="color:{t['primary_blue']}; font-size:1.2rem; font-weight:700;">{int(p_row_a['Assists'])}</div></div>
    <div><div style="color:{t['text_muted']}; font-size:0.68rem; font-weight:700;">G + A</div><div style="color:{t['text_primary']}; font-size:1.2rem; font-weight:700;">{int(p_row_a['Goals'] + p_row_a['Assists'])}</div></div>
</div>
</div>""", unsafe_allow_html=True)

    with hero_r:
        st.markdown(f"""<div class="player-hero-card" style="border-top:3px solid {t['amber']};">
<div style="display:flex; justify-content:space-between; align-items:flex-start;">
    <div style="display:flex; align-items:center; gap:12px;">
        <div style="width:42px; height:42px; border-radius:50%; background:{t['amber']}; color:{t['white']}; display:flex; align-items:center; justify-content:center; font-weight:700; font-size:1rem;">
            {make_initials(p_name_b)}
        </div>
        <div>
            <div style="color:{t['text_primary']}; font-size:1.15rem; font-weight:700;">{p_name_b}</div>
            <div style="color:{t['text_muted']}; font-size:0.78rem;">{p_row_b['Team_Name']} · {p_row_b['Position_Name']} · {sel_season}</div>
        </div>
    </div>
    <span class="pa-badge" style="background:{t['chip_bg']}; color:{t['amber']}; border:1px solid {t['chip_border']};">PLAYER B</span>
</div>
<div style="display:grid; grid-template-columns:repeat(5, 1fr); gap:8px; margin-top:14px; border-top:1px solid {t['divider']}; padding-top:10px;">
    <div><div style="color:{t['text_muted']}; font-size:0.68rem; font-weight:700;">APPS</div><div style="color:{t['text_primary']}; font-size:1.2rem; font-weight:700;">{int(p_row_b['Apps'])}</div></div>
    <div><div style="color:{t['text_muted']}; font-size:0.68rem; font-weight:700;">MINUTES</div><div style="color:{t['text_primary']}; font-size:1.2rem; font-weight:700;">{int(p_row_b['Minutes']):,}</div></div>
    <div><div style="color:{t['text_muted']}; font-size:0.68rem; font-weight:700;">GOALS</div><div style="color:{t['amber']}; font-size:1.2rem; font-weight:700;">{int(p_row_b['Goals'])}</div></div>
    <div><div style="color:{t['text_muted']}; font-size:0.68rem; font-weight:700;">ASSISTS</div><div style="color:{t['amber']}; font-size:1.2rem; font-weight:700;">{int(p_row_b['Assists'])}</div></div>
    <div><div style="color:{t['text_muted']}; font-size:0.68rem; font-weight:700;">G + A</div><div style="color:{t['text_primary']}; font-size:1.2rem; font-weight:700;">{int(p_row_b['Goals'] + p_row_b['Assists'])}</div></div>
</div>
</div>""", unsafe_allow_html=True)

    # Compute Statistical Metrics for Peer Group
    peer_df["G90"] = np.where(peer_df["Minutes"] > 0, peer_df["Goals"] / peer_df["Minutes"] * 90, 0.0)
    peer_df["A90"] = np.where(peer_df["Minutes"] > 0, peer_df["Assists"] / peer_df["Minutes"] * 90, 0.0)
    peer_df["S90"] = np.where(peer_df["Minutes"] > 0, peer_df["Shots"] / peer_df["Minutes"] * 90, 0.0)
    peer_df["Conv"] = np.where(peer_df["Shots"] > 0, peer_df["Goals"] / peer_df["Shots"] * 100, 0.0)
    peer_df["Y90"] = np.where(peer_df["Minutes"] > 0, peer_df["Yellow"] / peer_df["Minutes"] * 90, 0.0)

    for col in ["G90", "A90", "S90", "Conv", "Minutes"]:
        peer_df[f"{col}_pctile"] = peer_df[col].rank(pct=True) * 100
    peer_df["Discipline_pctile"] = 100 - (peer_df["Y90"].rank(pct=True) * 100)

    p_a_stats = peer_df[peer_df["Player_Name"] == p_name_a].iloc[0] if not peer_df[peer_df["Player_Name"] == p_name_a].empty else peer_df.iloc[0]
    p_b_stats = peer_df[peer_df["Player_Name"] == p_name_b].iloc[0] if not peer_df[peer_df["Player_Name"] == p_name_b].empty else (peer_df.iloc[1] if len(peer_df)>1 else peer_df.iloc[0])

    # Row 1: Profile Radar vs Head-to-Head
    r1_l, r1_r = st.columns([1.0, 1.1])

    with r1_l:
        with st.container(key="card_multi_profile_radar"):
            st.markdown(f"""<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
    <h3 style="color:{t['text_primary']}; font-size:1.02rem; font-weight:700; margin:0;">Profile radar</h3>
    <span class="pa-badge">PERCENTILE 0–100</span>
</div>
""", unsafe_allow_html=True)

            radar_axes = ["Goals / 90", "Assists / 90", "Shots / 90", "Conversion", "Minutes", "Discipline"]
            val_pct_a = [
                int(round(p_a_stats["G90_pctile"])),
                int(round(p_a_stats["A90_pctile"])),
                int(round(p_a_stats["S90_pctile"])),
                int(round(p_a_stats["Conv_pctile"])),
                int(round(p_a_stats["Minutes_pctile"])),
                int(round(p_a_stats["Discipline_pctile"])),
            ]
            val_pct_b = [
                int(round(p_b_stats["G90_pctile"])),
                int(round(p_b_stats["A90_pctile"])),
                int(round(p_b_stats["S90_pctile"])),
                int(round(p_b_stats["Conv_pctile"])),
                int(round(p_b_stats["Minutes_pctile"])),
                int(round(p_b_stats["Discipline_pctile"])),
            ]

            fig_rad = go.Figure()
            fig_rad.add_trace(go.Scatterpolar(
                r=val_pct_a + [val_pct_a[0]],
                theta=radar_axes + [radar_axes[0]],
                fill="toself",
                fillcolor="rgba(59, 130, 246, 0.16)",
                line=dict(color=t["primary_blue"], width=2),
                name=p_name_a,
                hoverinfo="theta+r"
            ))
            fig_rad.add_trace(go.Scatterpolar(
                r=val_pct_b + [val_pct_b[0]],
                theta=radar_axes + [radar_axes[0]],
                fill="toself",
                fillcolor="rgba(245, 158, 11, 0.16)",
                line=dict(color=t["amber"], width=2),
                name=p_name_b,
                hoverinfo="theta+r"
            ))

            fig_rad.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, 100], tickvals=[25, 50, 75, 100], tickfont=dict(size=8, color=t["text_faint"]), gridcolor=t["divider"]),
                    angularaxis=dict(tickfont=dict(size=9.5, color=t["text_primary"], weight=600), gridcolor=t["divider"]),
                    bgcolor="rgba(0,0,0,0)"
                ),
                height=265,
                margin=dict(l=20, r=20, t=15, b=15),
                showlegend=False,
                paper_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_rad, use_container_width=True, config={"displayModeBar": False})

            pct_rows = ""
            for ax_name, va, vb in zip(radar_axes, val_pct_a, val_pct_b):
                pct_rows += f"""<tr style="border-bottom:1px solid {t['divider']};">
<td style="color:{t['text_muted']}; font-weight:600; font-size:0.78rem; padding:4px 6px;">{ax_name}</td>
<td style="color:{t['primary_blue']}; font-weight:700; font-size:0.82rem; text-align:right; padding:4px 10px;">{va}</td>
<td style="color:{t['amber']}; font-weight:700; font-size:0.82rem; text-align:right; padding:4px 10px;">{vb}</td>
</tr>"""

            st.markdown(f"""
<table style="width:100%; border-collapse:collapse; margin-top:8px;">
<thead>
<tr style="border-bottom:1px solid {t['card_border']};">
    <th style="color:{t['text_muted']}; font-size:0.68rem; text-align:left; padding:4px 6px;">PERCENTILE VS {target_position.upper()}S</th>
    <th style="color:{t['primary_blue']}; font-size:0.72rem; text-align:right; padding:4px 10px;">A</th>
    <th style="color:{t['amber']}; font-size:0.72rem; text-align:right; padding:4px 10px;">B</th>
</tr>
</thead>
<tbody>
{pct_rows}
</tbody>
</table>
<div style="font-size:0.72rem; color:{t['text_faint']}; margin-top:8px;">
Each axis is the player's percentile among {peer_count} {target_position.lower()}s this season. Discipline is inverted: fewer yellow cards per 90 scores higher.
</div>""", unsafe_allow_html=True)

    with r1_r:
        with st.container(key="card_multi_head_to_head"):
            st.markdown(f"""<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
    <h3 style="color:{t['text_primary']}; font-size:1.02rem; font-weight:700; margin:0;">Head-to-head</h3>
    <span class="pa-badge">DARKER BAR = LEADS</span>
</div>
""", unsafe_allow_html=True)

            h2h_data = [
                ("Appearances", int(p_row_a["Apps"]), int(p_row_b["Apps"]), False, False),
                ("Minutes", int(p_row_a["Minutes"]), int(p_row_b["Minutes"]), False, False),
                ("Minutes / app", round(p_row_a["Minutes"]/p_row_a["Apps"], 1) if p_row_a["Apps"]>0 else 0, round(p_row_b["Minutes"]/p_row_b["Apps"], 1) if p_row_b["Apps"]>0 else 0, False, False),
                ("Goals", int(p_row_a["Goals"]), int(p_row_b["Goals"]), False, False),
                ("Assists", int(p_row_a["Assists"]), int(p_row_b["Assists"]), False, False),
                ("Goal contributions", int(p_row_a["Goals"]+p_row_a["Assists"]), int(p_row_b["Goals"]+p_row_b["Assists"]), False, False),
                ("Shots", int(p_row_a["Shots"]), int(p_row_b["Shots"]), False, False),
                ("Conversion %", round(p_a_stats["Conv"], 1), round(p_b_stats["Conv"], 1), True, False),
                ("Goals / 90", round(p_a_stats["G90"], 2), round(p_b_stats["G90"], 2), False, False),
                ("Assists / 90", round(p_a_stats["A90"], 2), round(p_b_stats["A90"], 2), False, False),
                ("Shots / 90", round(p_a_stats["S90"], 2), round(p_b_stats["S90"], 2), False, False),
                ("Yellow cards", int(p_row_a["Yellow"]), int(p_row_b["Yellow"]), False, True),
                ("Red cards", int(p_row_a["Red"]), int(p_row_b["Red"]), False, True),
            ]

            h2h_rows = ""
            leads_a = 0
            leads_b = 0
            level_cnt = 0

            for label, va, vb, is_pct, is_inverted in h2h_data:
                if is_inverted:
                    lead_a = va < vb
                    lead_b = vb < va
                else:
                    lead_a = va > vb
                    lead_b = vb > va
                
                if lead_a: leads_a += 1
                elif lead_b: leads_b += 1
                else: level_cnt += 1

                max_v = max(va, vb) if max(va, vb) > 0 else 1
                w_a = int((va / max_v) * 85)
                w_b = int((vb / max_v) * 85)

                bg_a = t["primary_blue"] if lead_a else t["form_played"]
                bg_b = t["amber"] if lead_b else ("#92400E" if is_dark else "#FDBA74")

                txt_a = f"{va:.1f}" if is_pct else (f"{va:.2f}" if "90" in label else f"{va:,}")
                txt_b = f"{vb:.1f}" if is_pct else (f"{vb:.2f}" if "90" in label else f"{vb:,}")

                h2h_rows += f"""<div style="display:grid; grid-template-columns:35px 95px 120px 95px 35px; align-items:center; gap:6px; padding:3.5px 0; border-bottom:1px solid {t['divider']};">
        <div style="text-align:right; font-size:0.8rem; font-weight:{700 if lead_a else 500}; color:{t['primary_blue'] if lead_a else t['text_muted']};">{txt_a}</div>
        <div style="display:flex; justify-content:flex-end;">
            <div style="background:{t['chip_bg']}; width:85px; height:7px; border-radius:3.5px; overflow:hidden; display:flex; justify-content:flex-end;">
                <div style="background:{bg_a}; width:{w_a}px; height:7px; border-radius:3.5px;"></div>
            </div>
        </div>
        <div style="text-align:center; font-size:0.75rem; color:{t['text_muted']}; font-weight:600;">{label}</div>
        <div style="display:flex; justify-content:flex-start;">
            <div style="background:{t['chip_bg']}; width:85px; height:7px; border-radius:3.5px; overflow:hidden;">
                <div style="background:{bg_b}; width:{w_b}px; height:7px; border-radius:3.5px;"></div>
            </div>
        </div>
        <div style="text-align:left; font-size:0.8rem; font-weight:{700 if lead_b else 500}; color:{t['amber'] if lead_b else t['text_muted']};">{txt_b}</div>
    </div>"""

            st.markdown(f"""
<div style="display:flex; justify-content:space-between; padding:0 35px 6px 35px; border-bottom:1px solid {t['card_border']}; font-size:0.72rem; font-weight:700;">
    <span style="color:{t['primary_blue']};">A</span>
    <span style="color:{t['text_muted']};">METRIC</span>
    <span style="color:{t['amber']};">B</span>
</div>
<div style="margin-top:4px;">
{h2h_rows}
</div>
<div style="font-size:0.72rem; color:{t['text_faint']}; margin-top:10px;">
Bars are scaled per metric to the larger of the two players. For cards, the lower value leads.
</div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)

    # Row 2: Contributions Timeline & Verdict
    r2_l, r2_r = st.columns([1.1, 1.0])

    with r2_l:
        with st.container(key="card_multi_contributions"):
            st.markdown(f"""<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
    <h3 style="color:{t['text_primary']}; font-size:1.02rem; font-weight:700; margin:0;">Contributions through the season</h3>
    <span class="pa-badge">CUMULATIVE</span>
</div>
""", unsafe_allow_html=True)

            @st.cache_data(show_spinner=False)
            def get_multi_player_trajectory(p_name: str, season_name: str) -> pd.DataFrame:
                df_p = q(f"""
                    SELECT
                        fp.Match_ID,
                        fp.Goals,
                        fp.Assists
                    FROM Fact_Player_Performance fp
                    JOIN Dim_Player p USING(Player_ID)
                    JOIN Dim_Season s USING(Season_ID)
                    WHERE s.Season_Name = '{season_name}' AND p.Player_Name = '{p_name}'
                    ORDER BY fp.Match_ID ASC
                """)
                if df_p.empty:
                    return pd.DataFrame({"Matchday": range(1, 39), "Cum_Goals": 0, "Cum_GA": 0})
                
                df_p["Matchday"] = range(1, len(df_p) + 1)
                df_p["Cum_Goals"] = df_p["Goals"].cumsum()
                df_p["Cum_GA"] = (df_p["Goals"] + df_p["Assists"]).cumsum()
                return df_p

            traj_a = get_multi_player_trajectory(p_name_a, sel_season)
            traj_b = get_multi_player_trajectory(p_name_b, sel_season)

            fig_traj = go.Figure()
            fig_traj.add_trace(go.Scatter(
                x=traj_a["Matchday"], y=traj_a["Cum_GA"],
                mode="lines", line=dict(color=t["primary_blue"], width=2.2),
                name=f"{p_name_a} (Goals + assists)", hoverinfo="x+y"
            ))
            fig_traj.add_trace(go.Scatter(
                x=traj_a["Matchday"], y=traj_a["Cum_Goals"],
                mode="lines", line=dict(color="#60A5FA" if is_dark else "#93C5FD", dash="dash", width=1.5),
                name=f"{p_name_a} (Goals only)", hoverinfo="x+y"
            ))
            fig_traj.add_trace(go.Scatter(
                x=traj_b["Matchday"], y=traj_b["Cum_GA"],
                mode="lines", line=dict(color=t["amber"], width=2.2),
                name=f"{p_name_b} (Goals + assists)", hoverinfo="x+y"
            ))
            fig_traj.add_trace(go.Scatter(
                x=traj_b["Matchday"], y=traj_b["Cum_Goals"],
                mode="lines", line=dict(color="#FCD34D" if is_dark else "#FDBA74", dash="dash", width=1.5),
                name=f"{p_name_b} (Goals only)", hoverinfo="x+y"
            ))

            if not traj_a.empty:
                fig_traj.add_annotation(
                    x=traj_a["Matchday"].iloc[-1], y=traj_a["Cum_GA"].iloc[-1],
                    text=f"<b>{traj_a['Cum_GA'].iloc[-1]}</b>", showarrow=False,
                    font=dict(size=10, color=t["primary_blue"]), xanchor="left"
                )
            if not traj_b.empty:
                fig_traj.add_annotation(
                    x=traj_b["Matchday"].iloc[-1], y=traj_b["Cum_GA"].iloc[-1],
                    text=f"<b>{traj_b['Cum_GA'].iloc[-1]}</b>", showarrow=False,
                    font=dict(size=10, color=t["amber"]), xanchor="left"
                )

            fig_traj.update_layout(
                height=245,
                margin=dict(l=10, r=25, t=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(title=dict(text="Team matchday", font=dict(size=10.5, color=t["text_muted"])), showgrid=True, gridcolor=t["divider"], dtick=5, tickfont=dict(color=t["text_faint"])),
                yaxis=dict(showgrid=True, gridcolor=t["divider"], tickfont=dict(color=t["text_faint"])),
                showlegend=False
            )
            st.plotly_chart(fig_traj, use_container_width=True, config={"displayModeBar": False})
            st.markdown(f"""<div style="font-size:0.72rem; color:{t['text_faint']}; margin-top:4px;">
Team matchday 1–38. A step up means the player scored or assisted in that match. Solid = Goals + Assists, Dashed = Goals only.
</div>""", unsafe_allow_html=True)

    with r2_r:
        with st.container(key="card_multi_verdict"):
            st.markdown(f"""<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
    <h3 style="color:{t['text_primary']}; font-size:1.02rem; font-weight:700; margin:0;">Verdict</h3>
    <span class="pa-badge">13 METRICS</span>
</div>
""", unsafe_allow_html=True)

            w_bar_a = int((leads_a / 13) * 100)
            w_bar_lvl = int((level_cnt / 13) * 100)
            w_bar_b = 100 - w_bar_a - w_bar_lvl

            st.markdown(f"""<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
<div><span style="font-size:1.6rem; font-weight:700; color:{t['primary_blue']};">{leads_a}</span> <span style="font-size:0.8rem; color:{t['text_muted']}; font-weight:600;">metrics led by A</span></div>
<div><span style="font-size:1.6rem; font-weight:700; color:{t['amber']};">{leads_b}</span> <span style="font-size:0.8rem; color:{t['text_muted']}; font-weight:600;">led by B</span></div>
</div>
<div style="display:flex; height:10px; border-radius:5px; overflow:hidden; background:{t['chip_bg']}; margin-bottom:6px;">
<div style="background:{t['primary_blue']}; width:{w_bar_a}%;"></div>
<div style="background:{t['input_border']}; width:{w_bar_lvl}%;"></div>
<div style="background:{t['amber']}; width:{w_bar_b}%;"></div>
</div>
<div style="display:flex; gap:12px; font-size:0.72rem; color:{t['text_muted']}; margin-bottom:14px;">
<span><span style="display:inline-block; width:6px; height:6px; background:{t['primary_blue']}; border-radius:50%; margin-right:3px;"></span>A</span>
<span><span style="display:inline-block; width:6px; height:6px; background:{t['input_border']}; border-radius:50%; margin-right:3px;"></span>Level ({level_cnt})</span>
<span><span style="display:inline-block; width:6px; height:6px; background:{t['amber']}; border-radius:50%; margin-right:3px;"></span>B</span>
</div>""", unsafe_allow_html=True)

            g_per_app_a = (p_row_a["Goals"] / p_row_a["Apps"]) if p_row_a["Apps"]>0 else 0.0
            g_per_app_b = (p_row_b["Goals"] / p_row_b["Apps"]) if p_row_b["Apps"]>0 else 0.0
            ga_per_90_a = ((p_row_a["Goals"]+p_row_a["Assists"]) / p_row_a["Minutes"] * 90) if p_row_a["Minutes"]>0 else 0.0
            ga_per_90_b = ((p_row_b["Goals"]+p_row_b["Assists"]) / p_row_b["Minutes"] * 90) if p_row_b["Minutes"]>0 else 0.0
            spg_a = (p_row_a["Shots"] / p_row_a["Goals"]) if p_row_a["Goals"]>0 else 0.0
            spg_b = (p_row_b["Shots"] / p_row_b["Goals"]) if p_row_b["Goals"]>0 else 0.0
            mean_pct_a = int(np.mean(val_pct_a))
            mean_pct_b = int(np.mean(val_pct_b))

            st.markdown(f"""<table class="pa-table" style="font-size:0.8rem;">
<thead>
<tr>
    <th>SUMMARY</th>
    <th style="color:{t['primary_blue']}; text-align:right;">A</th>
    <th style="color:{t['amber']}; text-align:right;">B</th>
</tr>
</thead>
<tbody>
<tr>
    <td style="color:{t['text_primary']};">Goals per appearance</td>
    <td style="text-align:right; font-weight:700; color:{t['text_primary']};">{g_per_app_a:.2f}</td>
    <td style="text-align:right; font-weight:700; color:{t['text_primary']};">{g_per_app_b:.2f}</td>
</tr>
<tr>
    <td style="color:{t['text_primary']};">Goal contributions / 90</td>
    <td style="text-align:right; font-weight:700; color:{t['text_primary']};">{ga_per_90_a:.2f}</td>
    <td style="text-align:right; font-weight:700; color:{t['text_primary']};">{ga_per_90_b:.2f}</td>
</tr>
<tr>
    <td style="color:{t['text_primary']};">Shots per goal</td>
    <td style="text-align:right; font-weight:700; color:{t['text_primary']};">{spg_a:.1f}</td>
    <td style="text-align:right; font-weight:700; color:{t['text_primary']};">{spg_b:.1f}</td>
</tr>
<tr>
    <td style="color:{t['text_primary']};">Mean percentile (radar)</td>
    <td style="text-align:right; font-weight:700; color:{t['text_primary']};">{mean_pct_a}</td>
    <td style="text-align:right; font-weight:700; color:{t['text_primary']};">{mean_pct_b}</td>
</tr>
</tbody>
</table>""", unsafe_allow_html=True)

    st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)

    # Row 3: Z-Scores & Rate Significance Tests
    r3_l, r3_r = st.columns([1.1, 1.0])

    z_metrics_def = [
        ("Goals / 90", "G90", 2, True),
        ("Assists / 90", "A90", 2, True),
        ("Shots / 90", "S90", 2, True),
        ("Conversion %", "Conv", 1, True),
        ("Minutes", "Minutes", 0, False),
        ("Yellow / 90", "Y90", 2, True),
    ]

    with r3_l:
        with st.container(key="card_multi_standardised_metrics"):
            st.markdown(f"""<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
    <h3 style="color:{t['text_primary']}; font-size:1.02rem; font-weight:700; margin:0;">Standardised metrics vs peers</h3>
    <span class="pa-badge">Z-SCORE · {peer_count} {target_position.upper()}S</span>
</div>
""", unsafe_allow_html=True)

            z_rows = ""
            for label, col, decimals, is_per_90 in z_metrics_def:
                peer_m = peer_df[col].mean()
                peer_s = peer_df[col].std() if peer_df[col].std() > 0 else 1.0
                
                va = p_a_stats[col]
                vb = p_b_stats[col]
                
                za = (va - peer_m) / peer_s
                zb = (vb - peer_m) / peer_s

                fmt_m = f"{peer_m:.{decimals}f}" if decimals > 0 else f"{int(peer_m):,}"
                fmt_s = f"{peer_s:.{decimals}f}" if decimals > 0 else f"{int(peer_s):,}"
                fmt_va = f"{va:.{decimals}f}" if decimals > 0 else f"{int(va):,}"
                fmt_vb = f"{vb:.{decimals}f}" if decimals > 0 else f"{int(vb):,}"

                op_a = min(0.43, max(0.08, 0.08 + (min(abs(za), 3.0) / 3.0) * 0.35))
                op_b = min(0.43, max(0.08, 0.08 + (min(abs(zb), 3.0) / 3.0) * 0.35))

                bg_za = f"rgba(59, 130, 246, {op_a:.2f})" if za >= 0 else f"rgba(138, 148, 166, {op_a:.2f})"
                fg_za = t["primary_blue"] if za >= 0 else t["text_muted"]
                sign_za = "+" if za >= 0 else ""

                bg_zb = f"rgba(245, 158, 11, {op_b:.2f})" if zb >= 0 else f"rgba(138, 148, 166, {op_b:.2f})"
                fg_zb = t["amber"] if zb >= 0 else t["text_muted"]
                sign_zb = "+" if zb >= 0 else ""

                z_rows += f"""<tr>
<td style="font-weight:600; color:{t['text_primary']};">{label}</td>
<td style="color:{t['text_muted']}; text-align:right;">{fmt_m}</td>
<td style="color:{t['text_muted']}; text-align:right;">{fmt_s}</td>
<td style="font-weight:700; text-align:right; color:{t['text_primary']};">{fmt_va}</td>
<td style="text-align:center;"><span style="background:{bg_za}; color:{fg_za}; padding:2px 6px; border-radius:4px; font-weight:700; font-size:0.78rem;">{sign_za}{za:.2f}</span></td>
<td style="font-weight:700; text-align:right; color:{t['text_primary']};">{fmt_vb}</td>
<td style="text-align:center;"><span style="background:{bg_zb}; color:{fg_zb}; padding:2px 6px; border-radius:4px; font-weight:700; font-size:0.78rem;">{sign_zb}{zb:.2f}</span></td>
</tr>"""

            st.markdown(f"""
<table class="pa-table">
<thead>
<tr>
    <th>METRIC</th>
    <th style="text-align:right;">PEER MEAN</th>
    <th style="text-align:right;">PEER SD</th>
    <th style="text-align:right; color:{t['primary_blue']};">A</th>
    <th style="text-align:center; color:{t['primary_blue']};">Z (A)</th>
    <th style="text-align:right; color:{t['amber']};">B</th>
    <th style="text-align:center; color:{t['amber']};">Z (B)</th>
</tr>
</thead>
<tbody>
{z_rows}
</tbody>
</table>
<div style="font-size:0.72rem; color:{t['text_faint']}; margin-top:8px;">
z = 0 is the peer average; +1 is one standard deviation above it. Blue shading marks above average, grey below. For yellow cards, a positive z means more cards.
</div>""", unsafe_allow_html=True)

    with r3_r:
        with st.container(key="card_multi_rate_test"):
            st.markdown(f"""<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
    <h3 style="color:{t['text_primary']}; font-size:1.02rem; font-weight:700; margin:0;">Are the differences real?</h3>
    <span class="pa-badge">RATE TEST · ALPHA = 0.05</span>
</div>
""", unsafe_allow_html=True)

            t1 = max(p_row_a["Minutes"] / 90.0, 0.1)
            t2 = max(p_row_b["Minutes"] / 90.0, 0.1)

            def run_multi_poisson_test(k1, k2, t1, t2):
                k1 = int(k1)
                k2 = int(k2)
                total_k = k1 + k2
                if total_k == 0:
                    return 1.0, 1.0, (0.0, 0.0), "not significant"
                p_null = t1 / (t1 + t2)
                res = stats.binomtest(k1, total_k, p=p_null, alternative="two-sided")
                rate1 = k1 / t1
                rate2 = k2 / t2
                ratio = rate1 / rate2 if rate2 > 0 else 99.0
                se_log = np.sqrt((1.0 / max(k1, 1)) + (1.0 / max(k2, 1)))
                ci_low = np.exp(np.log(max(ratio, 0.01)) - 1.96 * se_log)
                ci_high = np.exp(np.log(max(ratio, 0.01)) + 1.96 * se_log)
                is_sig = res.pvalue < 0.05
                return ratio, res.pvalue, (ci_low, ci_high), "significant" if is_sig else "not significant"

            rate_tests = [
                ("Goals per 90", p_row_a["Goals"], p_row_b["Goals"]),
                ("Assists per 90", p_row_a["Assists"], p_row_b["Assists"]),
                ("Shots per 90", p_row_a["Shots"], p_row_b["Shots"]),
                ("Yellow cards per 90", p_row_a["Yellow"], p_row_b["Yellow"]),
            ]

            rate_rows = ""
            for label, count_a, count_b in rate_tests:
                ratio, p_val, (ci_l, ci_h), sig_text = run_multi_poisson_test(count_a, count_b, t1, t2)
                sig_color = t["online_dot"] if sig_text == "significant" else t["text_faint"]
                rate_rows += f"""<tr>
<td style="font-weight:600; color:{t['text_primary']};">{label}</td>
<td style="text-align:right; font-weight:700; color:{t['text_primary']};">{ratio:.2f}</td>
<td style="text-align:center; color:{t['text_muted']}; font-size:0.75rem;">{ci_l:.2f} – {ci_h:.2f}</td>
<td style="text-align:right; font-weight:700; color:{t['text_primary']};">{p_val:.3f}</td>
<td style="color:{sig_color}; font-weight:600; font-size:0.78rem;">{sig_text}</td>
</tr>"""

            feats_z = ["G90", "A90", "S90", "Conv", "Minutes", "Y90"]
            z_pop = (peer_df[feats_z] - peer_df[feats_z].mean()) / peer_df[feats_z].std()
            vec_a = z_pop.loc[p_a_stats.name].values
            vec_b = z_pop.loc[p_b_stats.name].values

            cos_sim = 1.0 - cosine(vec_a, vec_b) if np.linalg.norm(vec_a)>0 and np.linalg.norm(vec_b)>0 else 0.5
            euc_dist = float(np.linalg.norm(vec_a - vec_b))

            st.markdown(f"""
<table class="pa-table">
<thead>
<tr>
    <th>RATE (A v B)</th>
    <th style="text-align:right;">RATIO</th>
    <th style="text-align:center;">95% CI</th>
    <th style="text-align:right;">P-VALUE</th>
    <th>RESULT</th>
</tr>
</thead>
<tbody>
{rate_rows}
</tbody>
</table>
<div style="font-size:0.72rem; color:{t['text_faint']}; margin-top:8px; margin-bottom:12px;">
Ratio above 1 favours A. If the 95% CI contains 1, the gap could be chance given the minutes played.
</div>

<div style="background:{t['chip_bg']}; border:1px solid {t['chip_border']}; border-radius:8px; padding:10px 14px; display:flex; justify-content:space-between; align-items:center;">
    <div>
        <div style="font-size:0.72rem; font-weight:700; color:{t['text_muted']}; text-transform:uppercase;">PROFILE SIMILARITY</div>
        <div style="font-size:0.8rem; color:{t['text_primary']}; margin-top:2px;">
            cosine (A, B) <b>{cos_sim:.2f}</b> &nbsp;·&nbsp; distance (A, B) <b>{euc_dist:.2f}</b>
        </div>
    </div>
    <span class="pa-badge" style="background:{t['card_bg']}; color:{t['text_muted']}; border:1px solid {t['card_border']};">Z-SPACE</span>
</div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)

    # Row 4: Closest Profiles
    with st.container(key="card_multi_closest_profiles"):
        st.markdown(f"""<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
    <h3 style="color:{t['text_primary']}; font-size:1.02rem; font-weight:700; margin:0;">Closest profiles among {peer_count} {target_position.lower()}s</h3>
    <span class="pa-badge">NEAREST NEIGHBOURS · EUCLIDEAN</span>
</div>
""", unsafe_allow_html=True)

        dists_a = cdist([vec_a], z_pop)[0]
        dists_b = cdist([vec_b], z_pop)[0]
        peer_df["dist_a"] = dists_a
        peer_df["dist_b"] = dists_b

        closest_a = peer_df[peer_df["Player_Name"] != p_name_a].sort_values("dist_a").head(3)
        closest_b = peer_df[peer_df["Player_Name"] != p_name_b].sort_values("dist_b").head(3)

        nn_c1, nn_c2 = st.columns(2)

        with nn_c1:
            st.markdown(f"<div style='font-size:0.78rem; font-weight:700; color:{t['primary_blue']}; margin-bottom:6px;'>Most similar to {p_name_a}</div>", unsafe_allow_html=True)
            rows_nn_a = ""
            for _, r in closest_a.iterrows():
                rows_nn_a += f"""<tr>
<td style="font-weight:700; color:{t['text_primary']};">{r['Player_Name']}</td>
<td style="color:{t['text_muted']};">{r['Team_Name']}</td>
<td style="text-align:right; font-weight:700; color:{t['text_primary']};">{int(r['Goals'])}</td>
<td style="text-align:right; color:{t['text_muted']};">{r['dist_a']:.2f}</td>
</tr>"""
            st.markdown(f"""<table class="pa-table">
<thead>
<tr>
    <th>PLAYER</th>
    <th>TEAM</th>
    <th style="text-align:right;">GOALS</th>
    <th style="text-align:right;">DIST.</th>
</tr>
</thead>
<tbody>{rows_nn_a}</tbody>
</table>""", unsafe_allow_html=True)

        with nn_c2:
            st.markdown(f"<div style='font-size:0.78rem; font-weight:700; color:{t['amber']}; margin-bottom:6px;'>Most similar to {p_name_b}</div>", unsafe_allow_html=True)
            rows_nn_b = ""
            for _, r in closest_b.iterrows():
                rows_nn_b += f"""<tr>
<td style="font-weight:700; color:{t['text_primary']};">{r['Player_Name']}</td>
<td style="color:{t['text_muted']};">{r['Team_Name']}</td>
<td style="text-align:right; font-weight:700; color:{t['text_primary']};">{int(r['Goals'])}</td>
<td style="text-align:right; color:{t['text_muted']};">{r['dist_b']:.2f}</td>
</tr>"""
            st.markdown(f"""<table class="pa-table">
<thead>
<tr>
    <th>PLAYER</th>
    <th>TEAM</th>
    <th style="text-align:right;">GOALS</th>
    <th style="text-align:right;">DIST.</th>
</tr>
</thead>
<tbody>{rows_nn_b}</tbody>
</table>""", unsafe_allow_html=True)

    st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)

    # Technical Details Box
    st.markdown(f"""<div class="pa-card">
<div style="display:flex; align-items:center; gap:8px; margin-bottom:12px; cursor:pointer;">
<span style="font-size:0.8rem; color:{t['text_muted']};">▼</span>
<span style="color:{t['text_primary']}; font-size:0.96rem; font-weight:700;">Technical details</span>
<span class="pa-badge" style="margin-left:auto;">METHOD</span>
</div>
<div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:16px; font-size:0.82rem;">
<div>
<div style="color:{t['text_muted']}; font-size:0.72rem; margin-bottom:2px; font-weight:700;">AGGREGATION</div>
<div style="color:{t['text_primary']}; font-weight:500;">SUM over matches per player-season (OLAP roll-up from player × match)</div>
</div>
<div>
<div style="color:{t['text_muted']}; font-size:0.72rem; margin-bottom:2px; font-weight:700;">PER-90</div>
<div style="color:{t['text_primary']}; font-weight:500;">metric ÷ (minutes ÷ 90)</div>
</div>
<div>
<div style="color:{t['text_muted']}; font-size:0.72rem; margin-bottom:2px; font-weight:700;">PERCENTILE</div>
<div style="color:{t['text_primary']}; font-weight:500;">share of position peers with a value ≤ the player's (weak rank)</div>
</div>
<div>
<div style="color:{t['text_muted']}; font-size:0.72rem; margin-bottom:2px; font-weight:700;">Z-SCORE</div>
<div style="color:{t['text_primary']}; font-weight:500;">(value − peer mean) ÷ peer SD (population SD)</div>
</div>
<div>
<div style="color:{t['text_muted']}; font-size:0.72rem; margin-bottom:2px; font-weight:700;">SIMILARITY</div>
<div style="color:{t['text_primary']}; font-weight:500;">Euclidean distance on 6 z-scores; cosine & distance in Z-space</div>
</div>
<div>
<div style="color:{t['text_muted']}; font-size:0.72rem; margin-bottom:2px; font-weight:700;">RATE TEST</div>
<div style="color:{t['text_primary']}; font-weight:500;">Conditional exact binomial test of two Poisson rates, exposure = minutes ÷ 90</div>
</div>
<div>
<div style="color:{t['text_muted']}; font-size:0.72rem; margin-bottom:2px; font-weight:700;">DISCIPLINE AXIS</div>
<div style="color:{t['text_primary']}; font-weight:500;">inverted: 100 − percentile of Yellow / 90</div>
</div>
<div>
<div style="color:{t['text_muted']}; font-size:0.72rem; margin-bottom:2px; font-weight:700;">SAMPLE SIZE</div>
<div style="color:{t['text_primary']}; font-weight:500;">Rates from fewer than about 900 minutes are unstable.</div>
</div>
</div>
</div>""", unsafe_allow_html=True)
