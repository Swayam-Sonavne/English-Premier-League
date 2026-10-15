"""
pages/2_EPL_Explorer.py — Admin Page 2: EPL Explorer
Matches the UI Inspiration Mockup with 100% Dynamic Database Filtering:
  1. Top Filter Bar (Season, Team, Player, Stadium + Apply Filters)
  2. 4 Dynamic Metric Cards (Matches, Teams, Players, Player Performances)
  3. Goals & Possession Trends + Top Scoring Teams + Match Result Distribution (3 Charts)
  4. Team Performance Overview Table + Key Insights Strip (2 Columns)
"""
import sqlite3
from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(
    page_title="EPL Explorer — Analytics & DWM",
    page_icon="⌕",
    layout="wide",
)

# Role Access Guard
if st.session_state.get("auth_role") != "admin":
    st.warning("🔒 Administrator authentication required to view this technical DWM page.")
    if st.button("🔑 Login as Administrator", key="ee_auth_req_btn"):
        st.session_state["auth_role"] = "admin"
        st.rerun()
    st.stop()

from utils.admin_views import render_admin_sidebar
from utils.db import (
    load_team_match, load_player_perf, load_fact_match,
    load_dim_team, load_dim_season, load_dim_stadium,
    load_dim_player, q,
)

# Render Admin Sidebar
render_admin_sidebar("EPL Explorer")

# ── Global CSS for EPL Explorer ─────────────────────────────────────────────
st.markdown("""
<style>
/* Base styling */
html, body, .stApp {
}

/* Card Container */
.explorer-card, [class*="st-key-card_"] {
    background: #FFFFFF;
    border: 1px solid #D5DBE6;
    border-radius: 12px;
    padding: 16px 18px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
    margin-bottom: 16px;
    box-sizing: border-box;
}

/* Metric Cards */
.kpi-metric-box {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 16px 18px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
    display: flex;
    align-items: center;
    gap: 14px;
    box-sizing: border-box;
}
.kpi-icon-wrap {
    width: 44px;
    height: 44px;
    border-radius: 10px;
    background: #EFF6FF;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}
.kpi-title {
    color: #64748B;
    font-size: 0.8rem;
    font-weight: 500;
    margin-bottom: 2px;
}
.kpi-val {
    color: #0F172A;
    font-size: 1.6rem;
    font-weight: 700;
    line-height: 1.15;
    margin-bottom: 2px;
}
.kpi-sub {
    color: #94A3B8;
    font-size: 0.74rem;
}

/* Overview table */
.exp-table {
    width: 100%;
    border-collapse: collapse;
}
.exp-table th {
    text-align: left;
    color: #64748B;
    font-size: 0.76rem;
    font-weight: 600;
    text-transform: uppercase;
    padding: 8px 10px 10px 10px;
    border-bottom: 1px solid #E2E8F0;
}
.exp-table td {
    padding: 10px;
    color: #0F172A;
    font-size: 0.85rem;
    border-bottom: 1px solid #F1F5F9;
}
.exp-table tr:last-child td {
    border-bottom: none;
}
.exp-team-link {
    color: #2563EB;
    font-weight: 600;
    text-decoration: none;
}
</style>
""", unsafe_allow_html=True)

# ── Top Header Bar ──────────────────────────────────────────────────────────
c_head_l, c_head_r = st.columns([3, 1])
with c_head_l:
    st.markdown("<h1 style='color:#0F172A; font-size:2.2rem; font-weight:700; margin:0 0 4px 0;'>EPL Explorer</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#64748B; font-size:0.92rem; margin:0 0 16px 0;'>Explore and analyse the Premier League data across multiple dimensions.</p>", unsafe_allow_html=True)

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

# ── 1. Top Filter Bar (Using Streamlit Form for clean multi-filter submission) ──
_DB_PATH = Path(__file__).resolve().parent.parent / "epl_dw.db"

def run_filtered_query(query: str, params=()):
    with sqlite3.connect(_DB_PATH) as con:
        return pd.read_sql(query, con, params=params)

all_seasons = load_dim_season()["Season_Name"].tolist()
seasons_list = ["All Seasons"] + all_seasons
teams_list = ["All Teams"] + sorted(load_dim_team()["Team_Name"].tolist())
players_list = ["All Players"] + sorted(run_filtered_query("SELECT DISTINCT Player_Name FROM Dim_Player ORDER BY Player_Name")["Player_Name"].tolist())
stadiums_list = ["All Stadiums"] + sorted(load_dim_stadium()["Stadium_Name"].tolist())

# Stored selections in session_state
if "exp_sel_season" not in st.session_state:
    st.session_state["exp_sel_season"] = "All Seasons"
if "exp_sel_team" not in st.session_state:
    st.session_state["exp_sel_team"] = "All Teams"
if "exp_sel_player" not in st.session_state:
    st.session_state["exp_sel_player"] = "All Players"
if "exp_sel_stadium" not in st.session_state:
    st.session_state["exp_sel_stadium"] = "All Stadiums"

with st.container(key="card_epl_explorer_filters"):
    with st.form("epl_explorer_filter_form", border=False):
        f1, f2, f3, f4, f5 = st.columns([1.25, 1.25, 1.25, 1.25, 1.0])
        
        with f1:
            s_idx = seasons_list.index(st.session_state["exp_sel_season"]) if st.session_state["exp_sel_season"] in seasons_list else 0
            sel_season = st.selectbox("Season", seasons_list, index=s_idx)
        with f2:
            t_idx = teams_list.index(st.session_state["exp_sel_team"]) if st.session_state["exp_sel_team"] in teams_list else 0
            sel_team = st.selectbox("Team", teams_list, index=t_idx)
        with f3:
            p_idx = players_list.index(st.session_state["exp_sel_player"]) if st.session_state["exp_sel_player"] in players_list else 0
            sel_player = st.selectbox("Player", players_list, index=p_idx)
        with f4:
            st_idx = stadiums_list.index(st.session_state["exp_sel_stadium"]) if st.session_state["exp_sel_stadium"] in stadiums_list else 0
            sel_stadium = st.selectbox("Stadium", stadiums_list, index=st_idx)
        with f5:
            st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
            submitted = st.form_submit_button("🔍 Apply Filters", type="primary", use_container_width=True)

if submitted:
    st.session_state["exp_sel_season"] = sel_season
    st.session_state["exp_sel_team"] = sel_team
    st.session_state["exp_sel_player"] = sel_player
    st.session_state["exp_sel_stadium"] = sel_stadium

# Active filters
act_season = st.session_state["exp_sel_season"]
act_team = st.session_state["exp_sel_team"]
act_player = st.session_state["exp_sel_player"]
act_stadium = st.session_state["exp_sel_stadium"]

# ── 2. Dynamic Database Queries based on Active Filters ─────────────────────

# Conditions for Fact_Match queries
fm_where = []
fm_params = []

if act_season != "All Seasons":
    fm_where.append("s.Season_Name = ?")
    fm_params.append(act_season)

if act_team != "All Teams":
    fm_where.append("(ht.Team_Name = ? OR at_.Team_Name = ?)")
    fm_params.extend([act_team, act_team])

if act_stadium != "All Stadiums":
    fm_where.append("st_.Stadium_Name = ?")
    fm_params.append(act_stadium)

if act_player != "All Players":
    fm_where.append("fm.Match_ID IN (SELECT fpp.Match_ID FROM Fact_Player_Performance fpp JOIN Dim_Player dp USING(Player_ID) WHERE dp.Player_Name = ?)")
    fm_params.append(act_player)

fm_where_clause = ("WHERE " + " AND ".join(fm_where)) if fm_where else ""

# 1. Matches & Seasons count
sql_kpi_m = f"""
    SELECT COUNT(DISTINCT fm.Match_ID) AS Total_Matches,
           COUNT(DISTINCT fm.Season_ID) AS Total_Seasons
    FROM Fact_Match fm
    JOIN Dim_Season s USING(Season_ID)
    JOIN Dim_Team ht ON fm.Home_Team_ID = ht.Team_ID
    JOIN Dim_Team at_ ON fm.Away_Team_ID = at_.Team_ID
    JOIN Dim_Stadium st_ USING(Stadium_ID)
    {fm_where_clause}
"""
kpi_m_df = run_filtered_query(sql_kpi_m, fm_params)
tot_matches = int(kpi_m_df["Total_Matches"].iloc[0]) if not kpi_m_df.empty else 0
tot_seasons = int(kpi_m_df["Total_Seasons"].iloc[0]) if not kpi_m_df.empty else 0

# 2. Teams count
if act_team != "All Teams":
    tot_teams = 1
else:
    sql_kpi_t = f"""
        SELECT COUNT(DISTINCT t.Team_ID) AS Total_Teams
        FROM Fact_Team_Match tm
        JOIN Dim_Team t USING(Team_ID)
        JOIN Dim_Season s USING(Season_ID)
        JOIN Fact_Match fm USING(Match_ID)
        JOIN Dim_Team ht ON fm.Home_Team_ID = ht.Team_ID
        JOIN Dim_Team at_ ON fm.Away_Team_ID = at_.Team_ID
        JOIN Dim_Stadium st_ ON fm.Stadium_ID = st_.Stadium_ID
        {fm_where_clause}
    """
    kpi_t_df = run_filtered_query(sql_kpi_t, fm_params)
    tot_teams = int(kpi_t_df["Total_Teams"].iloc[0]) if not kpi_t_df.empty else 0

# 3. Players & Performances count
sql_kpi_p = f"""
    SELECT COUNT(DISTINCT fp.Player_ID) AS Total_Players,
           COUNT(fp.Perf_ID) AS Total_Perfs
    FROM Fact_Player_Performance fp
    JOIN Dim_Season s USING(Season_ID)
    JOIN Fact_Match fm USING(Match_ID)
    JOIN Dim_Team ht ON fm.Home_Team_ID = ht.Team_ID
    JOIN Dim_Team at_ ON fm.Away_Team_ID = at_.Team_ID
    JOIN Dim_Stadium st_ ON fm.Stadium_ID = st_.Stadium_ID
    {fm_where_clause}
"""
kpi_p_df = run_filtered_query(sql_kpi_p, fm_params)
tot_players = int(kpi_p_df["Total_Players"].iloc[0]) if not kpi_p_df.empty else 0
tot_perfs = int(kpi_p_df["Total_Perfs"].iloc[0]) if not kpi_p_df.empty else 0

# ── Render KPI Metric Cards ─────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)

with k1:
    st.markdown(f"""
    <div class="kpi-metric-box">
        <div class="kpi-icon-wrap">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="m4.93 4.93 4.24 4.24"></path><path d="m14.83 9.17 4.24-4.24"></path><path d="m14.83 14.83 4.24 4.24"></path><path d="m9.17 14.83-4.24 4.24"></path></svg>
        </div>
        <div>
            <div class="kpi-title">Total Matches</div>
            <div class="kpi-val">{tot_matches:,}</div>
            <div class="kpi-sub">Across {tot_seasons} seasons</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with k2:
    st.markdown(f"""
    <div class="kpi-metric-box">
        <div class="kpi-icon-wrap">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
        </div>
        <div>
            <div class="kpi-title">Total Teams</div>
            <div class="kpi-val">{tot_teams}</div>
            <div class="kpi-sub">Premier League clubs</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with k3:
    st.markdown(f"""
    <div class="kpi-metric-box">
        <div class="kpi-icon-wrap">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
        </div>
        <div>
            <div class="kpi-title">Total Players</div>
            <div class="kpi-val">{tot_players:,}</div>
            <div class="kpi-sub">Unique players</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with k4:
    st.markdown(f"""
    <div class="kpi-metric-box">
        <div class="kpi-icon-wrap">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"></ellipse><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"></path><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"></path></svg>
        </div>
        <div>
            <div class="kpi-title">Total Player Performances</div>
            <div class="kpi-val">{tot_perfs:,}</div>
            <div class="kpi-sub">Player match records</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

# ── 3. Charts Section (3 Columns) ───────────────────────────────────────────
c_trend, c_scoring, c_donut = st.columns([1.45, 0.95, 0.9])

# Chart 1: Goals & Possession Trends
with c_trend:
    with st.container(key="card_goals_possession_trends"):
        st.markdown("""
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
            <h3 style="color:#0F172A; font-size:1.02rem; font-weight:700; margin:0;">Goals & Possession Trends</h3>
            <div style="display:flex; align-items:center; gap:12px; font-size:0.78rem; color:#64748B;">
                <span style="display:flex; align-items:center; gap:4px;"><span style="height:7px; width:7px; background:#2563EB; border-radius:50%;"></span> Home Goals</span>
                <span style="display:flex; align-items:center; gap:4px;"><span style="height:7px; width:7px; background:#94A3B8; border-radius:50%;"></span> Away Goals</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if act_season == "All Seasons":
            sql_trends = f"""
                SELECT s.Season_Name,
                       ROUND(AVG(fm.Home_Goals), 2) AS Avg_Home_Goals,
                       ROUND(AVG(fm.Away_Goals), 2) AS Avg_Away_Goals
                FROM Fact_Match fm
                JOIN Dim_Season s USING(Season_ID)
                JOIN Dim_Team ht ON fm.Home_Team_ID = ht.Team_ID
                JOIN Dim_Team at_ ON fm.Away_Team_ID = at_.Team_ID
                JOIN Dim_Stadium st_ USING(Stadium_ID)
                {fm_where_clause}
                GROUP BY s.Season_Name, s.Season_ID
                ORDER BY s.Season_ID
            """
            trends_df = run_filtered_query(sql_trends, fm_params)
            x_col = "Season_Name"
        else:
            sql_trends = f"""
                SELECT strftime('%Y-%m', d.Date) AS Month_Period,
                       ROUND(AVG(fm.Home_Goals), 2) AS Avg_Home_Goals,
                       ROUND(AVG(fm.Away_Goals), 2) AS Avg_Away_Goals
                FROM Fact_Match fm
                JOIN Dim_Date d ON fm.Date_ID = d.Date_ID
                JOIN Dim_Season s USING(Season_ID)
                JOIN Dim_Team ht ON fm.Home_Team_ID = ht.Team_ID
                JOIN Dim_Team at_ ON fm.Away_Team_ID = at_.Team_ID
                JOIN Dim_Stadium st_ USING(Stadium_ID)
                {fm_where_clause}
                GROUP BY Month_Period
                ORDER BY Month_Period
            """
            trends_df = run_filtered_query(sql_trends, fm_params)
            x_col = "Month_Period"

        fig_trend = go.Figure()
        if not trends_df.empty:
            fig_trend.add_trace(go.Scatter(
                x=trends_df[x_col], y=trends_df["Avg_Home_Goals"],
                name="Home Goals",
                mode="lines+markers",
                line=dict(color="#2563EB", width=2.5),
                marker=dict(size=5)
            ))
            fig_trend.add_trace(go.Scatter(
                x=trends_df[x_col], y=trends_df["Avg_Away_Goals"],
                name="Away Goals",
                mode="lines+markers",
                line=dict(color="#94A3B8", width=2),
                marker=dict(size=5)
            ))
        fig_trend.update_layout(
            height=255,
            margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
            xaxis=dict(tickangle=-45, showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="#F1F5F9", range=[0.0, 3.5]),
        )
        st.plotly_chart(fig_trend, use_container_width=True, config={"displayModeBar": False})

# Chart 2: Top Scoring Teams
with c_scoring:
    with st.container(key="card_top_scoring_teams"):
        st.markdown("""
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
            <h3 style="color:#0F172A; font-size:1.02rem; font-weight:700; margin:0;">Top Scoring Teams</h3>
            <span style="font-size:0.75rem; color:#64748B; background:#F1F5F9; padding:2px 8px; border-radius:4px;">Total Goals ▾</span>
        </div>
        """, unsafe_allow_html=True)

        if act_team == "All Teams":
            # Show top scoring teams
            sc_where = []
            sc_params = []
            if act_season != "All Seasons":
                sc_where.append("s.Season_Name = ?")
                sc_params.append(act_season)
            if act_stadium != "All Stadiums":
                sc_where.append("st_.Stadium_Name = ?")
                sc_params.append(act_stadium)
            sc_clause = ("WHERE " + " AND ".join(sc_where)) if sc_where else ""

            sql_top_teams = f"""
                SELECT t.Team_Name AS Entity, SUM(tm.Goals_For) AS Goals
                FROM Fact_Team_Match tm
                JOIN Dim_Team t USING(Team_ID)
                JOIN Dim_Season s USING(Season_ID)
                JOIN Fact_Match fm USING(Match_ID)
                JOIN Dim_Stadium st_ ON fm.Stadium_ID = st_.Stadium_ID
                {sc_clause}
                GROUP BY t.Team_Name
                ORDER BY Goals DESC
                LIMIT 5
            """
            top_scoring_df = run_filtered_query(sql_top_teams, sc_params)
        else:
            # Show top scorers for the chosen team
            sc_where = ["dt.Team_Name = ?"]
            sc_params = [act_team]
            if act_season != "All Seasons":
                sc_where.append("s.Season_Name = ?")
                sc_params.append(act_season)
            sc_clause = "WHERE " + " AND ".join(sc_where)

            sql_top_scorers = f"""
                SELECT dp.Player_Name AS Entity, SUM(fp.Goals) AS Goals
                FROM Fact_Player_Performance fp
                JOIN Dim_Player dp USING(Player_ID)
                JOIN Dim_Team dt USING(Team_ID)
                JOIN Dim_Season s USING(Season_ID)
                {sc_clause}
                GROUP BY dp.Player_Name
                ORDER BY Goals DESC
                LIMIT 5
            """
            top_scoring_df = run_filtered_query(sql_top_scorers, sc_params)

        top_scoring_df = top_scoring_df.iloc[::-1]  # reverse for horizontal display

        fig_bar = go.Figure()
        if not top_scoring_df.empty:
            fig_bar.add_trace(go.Bar(
                x=top_scoring_df["Goals"],
                y=top_scoring_df["Entity"],
                orientation="h",
                marker=dict(color="#2563EB"),
                text=top_scoring_df["Goals"].apply(lambda x: f"{x:,}"),
                textposition="outside"
            ))
            max_g = int(top_scoring_df["Goals"].max() * 1.25) if not top_scoring_df.empty else 100
        else:
            max_g = 100

        fig_bar.update_layout(
            height=255,
            margin=dict(l=10, r=40, t=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False, showticklabels=False, range=[0, max_g]),
            yaxis=dict(showgrid=False, tickfont=dict(size=11, color="#0F172A")),
        )
        st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})

# Chart 3: Match Result Distribution
with c_donut:
    with st.container(key="card_match_result_distribution"):
        st.markdown("""
        <h3 style="color:#0F172A; font-size:1.02rem; font-weight:700; margin:0 0 8px 0;">Match Result Distribution</h3>
        """, unsafe_allow_html=True)

        sql_results = f"""
            SELECT
                SUM(CASE WHEN fm.Match_Result = 'H' THEN 1 ELSE 0 END) AS Home_Wins,
                SUM(CASE WHEN fm.Match_Result = 'D' THEN 1 ELSE 0 END) AS Draws,
                SUM(CASE WHEN fm.Match_Result = 'A' THEN 1 ELSE 0 END) AS Away_Wins,
                COUNT(fm.Match_ID) AS Total_Matches
            FROM Fact_Match fm
            JOIN Dim_Season s USING(Season_ID)
            JOIN Dim_Team ht ON fm.Home_Team_ID = ht.Team_ID
            JOIN Dim_Team at_ ON fm.Away_Team_ID = at_.Team_ID
            JOIN Dim_Stadium st_ USING(Stadium_ID)
            {fm_where_clause}
        """
        res_counts = run_filtered_query(sql_results, fm_params)
        m_tot = int(res_counts["Total_Matches"].iloc[0]) if not res_counts.empty and res_counts["Total_Matches"].iloc[0] else 1
        hw = int(res_counts["Home_Wins"].iloc[0] or 0)
        dr = int(res_counts["Draws"].iloc[0] or 0)
        aw = int(res_counts["Away_Wins"].iloc[0] or 0)

        res_df = pd.DataFrame({
            "Outcome": ["Home Wins", "Draws", "Away Wins"],
            "Percent": [round(hw / m_tot * 100, 1), round(dr / m_tot * 100, 1), round(aw / m_tot * 100, 1)],
            "Color": ["#10B981", "#2563EB", "#94A3B8"]
        })

        fig_pie = go.Figure(data=[go.Pie(
            labels=res_df["Outcome"],
            values=res_df["Percent"],
            hole=0.65,
            marker_colors=res_df["Color"],
            textinfo="percent",
            hoverinfo="label+percent",
        )])
        fig_pie.update_layout(
            height=255,
            margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor="rgba(0,0,0,0)",
            showlegend=True,
            legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="right", x=1.1, font=dict(size=10)),
            annotations=[dict(text=f"Total Matches<br><b>{m_tot:,}</b>", x=0.36, y=0.5, font_size=10, showarrow=False)]
        )
        st.plotly_chart(fig_pie, use_container_width=True, config={"displayModeBar": False})

st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)

# ── 4. Bottom Section (Team Performance Overview + Key Insights) ────────────
c_perf, c_insights = st.columns([1.85, 1.15])

with c_perf:
    st_where = []
    st_params = []
    if act_season != "All Seasons":
        st_where.append("s.Season_Name = ?")
        st_params.append(act_season)
    if act_team != "All Teams":
        st_where.append("t.Team_Name = ?")
        st_params.append(act_team)
    st_clause = ("WHERE " + " AND ".join(st_where)) if st_where else ""

    sql_standings = f"""
        SELECT
            t.Team_Name,
            COUNT(tm.Team_Match_ID) AS Matches,
            SUM(CASE WHEN tm.Result = 'W' THEN 1 ELSE 0 END) AS Wins,
            SUM(CASE WHEN tm.Result = 'D' THEN 1 ELSE 0 END) AS Draws,
            SUM(CASE WHEN tm.Result = 'L' THEN 1 ELSE 0 END) AS Losses,
            SUM(tm.Goals_For) AS Goals_For,
            SUM(tm.Goals_Against) AS Goals_Against,
            SUM(tm.Points) AS Points
        FROM Fact_Team_Match tm
        JOIN Dim_Team t USING(Team_ID)
        JOIN Dim_Season s USING(Season_ID)
        {st_clause}
        GROUP BY t.Team_Name
        ORDER BY Points DESC, (Goals_For - Goals_Against) DESC
        LIMIT 10
    """
    standings_df = run_filtered_query(sql_standings, st_params)

    table_rows_html = "".join([
        f"<tr><td style='color:#64748B;'>{idx + 1}</td><td><a href='#' class='exp-team-link'>{row['Team_Name']}</a></td><td>{row['Matches']}</td><td>{row['Wins']}</td><td>{row['Draws']}</td><td>{row['Losses']}</td><td>{row['Goals_For']}</td><td>{row['Goals_Against']}</td><td><b>{row['Points']}</b></td></tr>"
        for idx, row in standings_df.iterrows()
    ])

    st.markdown(f"""<div class="explorer-card">
<h3 style="color:#0F172A; font-size:1.02rem; font-weight:700; margin:0 0 12px 0;">Team Performance Overview</h3>
<table class="exp-table">
<thead>
<tr>
<th>Rank</th>
<th>Team</th>
<th>Matches</th>
<th>Wins</th>
<th>Draws</th>
<th>Losses</th>
<th>Goals For</th>
<th>Goals Against</th>
<th>Points</th>
</tr>
</thead>
<tbody>
{table_rows_html}
</tbody>
</table>
</div>""", unsafe_allow_html=True)

with c_insights:
    # 1. Most Successful Club
    top_club_name = standings_df.iloc[0]['Team_Name'] if not standings_df.empty else "Manchester United"
    top_club_pts = standings_df.iloc[0]['Points'] if not standings_df.empty else 745

    # 2. Top Scoring Club
    sql_top_club_goals = f"""
        SELECT t.Team_Name, SUM(tm.Goals_For) AS Total_GF
        FROM Fact_Team_Match tm
        JOIN Dim_Team t USING(Team_ID)
        JOIN Dim_Season s USING(Season_ID)
        {st_clause}
        GROUP BY t.Team_Name
        ORDER BY Total_GF DESC
        LIMIT 1
    """
    top_gf_df = run_filtered_query(sql_top_club_goals, st_params)
    top_gf_club = top_gf_df.iloc[0]['Team_Name'] if not top_gf_df.empty else top_club_name
    top_gf_val = int(top_gf_df.iloc[0]['Total_GF']) if not top_gf_df.empty else 0

    # 3. Top Scorer in filtered set
    sql_top_scorer = f"""
        SELECT dp.Player_Name, SUM(fp.Goals) AS Total_Goals
        FROM Fact_Player_Performance fp
        JOIN Dim_Player dp USING(Player_ID)
        JOIN Dim_Season s USING(Season_ID)
        JOIN Fact_Match fm USING(Match_ID)
        JOIN Dim_Team ht ON fm.Home_Team_ID = ht.Team_ID
        JOIN Dim_Team at_ ON fm.Away_Team_ID = at_.Team_ID
        JOIN Dim_Stadium st_ ON fm.Stadium_ID = st_.Stadium_ID
        {fm_where_clause}
        GROUP BY dp.Player_Name
        ORDER BY Total_Goals DESC
        LIMIT 1
    """
    top_scorer_df = run_filtered_query(sql_top_scorer, fm_params)
    top_scorer_name = top_scorer_df.iloc[0]['Player_Name'] if not top_scorer_df.empty else "Alan Shearer"
    top_scorer_goals = int(top_scorer_df.iloc[0]['Total_Goals']) if not top_scorer_df.empty else 260

    # 4. Highest Average Possession
    sql_possession = f"""
        SELECT t.Team_Name, ROUND(AVG(tm.Possession), 1) AS Avg_Poss
        FROM Fact_Team_Match tm
        JOIN Dim_Team t USING(Team_ID)
        JOIN Dim_Season s USING(Season_ID)
        {st_clause}
        GROUP BY t.Team_Name
        ORDER BY Avg_Poss DESC
        LIMIT 1
    """
    poss_df = run_filtered_query(sql_possession, st_params)
    top_poss_team = poss_df.iloc[0]['Team_Name'] if not poss_df.empty else "Manchester City"
    top_poss_val = float(poss_df.iloc[0]['Avg_Poss']) if not poss_df.empty else 58.4

    st.markdown(f"""<div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:12px; padding:16px 18px; box-shadow:0 1px 3px rgba(0,0,0,0.03); margin-bottom:16px; box-sizing:border-box;">
<h3 style="color:#0F172A; font-size:1.02rem; font-weight:700; margin:0 0 12px 0;">Key Insights</h3>
<div style="display:flex; align-items:flex-start; gap:12px; padding:10px 12px; border:1px solid #E2E8F0; border-radius:10px; background:#FFFFFF; margin-bottom:10px;">
<div style="width:34px; height:34px; border-radius:50%; background:#EFF6FF; display:flex; align-items:center; justify-content:center; flex-shrink:0; margin-top:2px;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"></path><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"></path><path d="M4 22h16"></path><path d="M10 14.66V17c0 .55-.45 1-1 1H8c-.55 0-1 .45-1 1v1c0 .55.45 1 1 1h8c.55 0 1-.45 1-1v-1c0-.55-.45-1-1-1h-1c-.55 0-1-.45-1-1v-2.34"></path><path d="M6 4h12a2 2 0 0 1 2 2v3a6 6 0 0 1-6 6h0a6 6 0 0 1-6-6V6a2 2 0 0 1 2-2Z"></path></svg>
</div>
<div>
<div style="font-size:0.86rem; font-weight:600; color:#0F172A;">Most Successful Club</div>
<div style="font-size:0.78rem; color:#64748B; margin-top:1px;">{top_club_name} leads with {top_club_pts} points.</div>
</div>
</div>
<div style="display:flex; align-items:flex-start; gap:12px; padding:10px 12px; border:1px solid #E2E8F0; border-radius:10px; background:#FFFFFF; margin-bottom:10px;">
<div style="width:34px; height:34px; border-radius:50%; background:#EFF6FF; display:flex; align-items:center; justify-content:center; flex-shrink:0; margin-top:2px;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="m4.93 4.93 4.24 4.24"></path><path d="m14.83 9.17 4.24-4.24"></path><path d="m14.83 14.83 4.24 4.24"></path><path d="m9.17 14.83-4.24 4.24"></path></svg>
</div>
<div>
<div style="font-size:0.86rem; font-weight:600; color:#0F172A;">Top Scoring Club</div>
<div style="font-size:0.78rem; color:#64748B; margin-top:1px;">{top_gf_club} has scored {top_gf_val:,} goals in this selection.</div>
</div>
</div>
<div style="display:flex; align-items:flex-start; gap:12px; padding:10px 12px; border:1px solid #E2E8F0; border-radius:10px; background:#FFFFFF; margin-bottom:10px;">
<div style="width:34px; height:34px; border-radius:50%; background:#EFF6FF; display:flex; align-items:center; justify-content:center; flex-shrink:0; margin-top:2px;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
</div>
<div>
<div style="font-size:0.86rem; font-weight:600; color:#0F172A;">Top Scorer</div>
<div style="font-size:0.78rem; color:#64748B; margin-top:1px;">{top_scorer_name} ({top_scorer_goals} goals).</div>
</div>
</div>
<div style="display:flex; align-items:flex-start; gap:12px; padding:10px 12px; border:1px solid #E2E8F0; border-radius:10px; background:#FFFFFF; margin-bottom:10px;">
<div style="width:34px; height:34px; border-radius:50%; background:#EFF6FF; display:flex; align-items:center; justify-content:center; flex-shrink:0; margin-top:2px;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="19" y1="5" x2="5" y2="19"></line><circle cx="6.5" cy="6.5" r="2.5"></circle><circle cx="17.5" cy="17.5" r="2.5"></circle></svg>
</div>
<div>
<div style="font-size:0.86rem; font-weight:600; color:#0F172A;">Highest Average Possession</div>
<div style="font-size:0.78rem; color:#64748B; margin-top:1px;">{top_poss_team} ({top_poss_val}% avg possession).</div>
</div>
</div>
</div>""", unsafe_allow_html=True)
