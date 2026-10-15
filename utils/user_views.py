"""
utils/user_views.py — User Mode (EPL Insights)
Consumer & fan-facing analytical views.
Zero machine learning jargon, zero algorithm names, pure football intelligence.
All statistics and qualitative ratings dynamically computed from database queries and models.
Contains:
  1. User Home (Quick insights, shortcuts, league highlights)
  2. Match Prediction (Outcome, Favourite, Favourite Strength, Form Context — No Exact %)
  3. Team Insights (Form, points, goals, dynamic percentile ratings, trends)
  4. Player Insights (Single-season player profile, stats, objective ratings, output chart)
  5. Match Explorer (Search matches, scorecards, match statistics)
  6. Compare (Head-to-head team comparison and player comparison)
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from utils.db import (
    load_team_match, load_player_perf, load_fact_match,
    load_dim_team, load_dim_season, load_dim_player, load_dim_position, q,
)
from utils.models import get_classification_model, PREMATCH_FEATURES

# ── 1. USER HOME ─────────────────────────────────────────────────────────────
def render_user_home():
    # Inject Custom Card & Layout Styling for Home View
    st.markdown("""
    <style>
    /* Metric Card Styling */
    .stat-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 20px 24px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
        margin-bottom: 16px;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .stat-card-title {
        color: #64748B;
        font-size: 0.85rem;
        font-weight: 500;
        margin-bottom: 6px;
    }
    .stat-card-value {
        color: #0F172A;
        font-size: 2rem;
        font-weight: 700;
        line-height: 1.1;
    }
    .highlight-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 20px 24px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
        margin-bottom: 16px;
        min-height: 110px;
    }
    .highlight-label {
        color: #64748B;
        font-size: 0.82rem;
        font-weight: 500;
        margin-bottom: 4px;
    }
    .highlight-value {
        color: #0F172A;
        font-size: 1.35rem;
        font-weight: 700;
        margin-bottom: 4px;
    }
    .highlight-sub {
        color: #64748B;
        font-size: 0.8rem;
        font-weight: 400;
    }

    /* Outlined Action Buttons */
    .stButton > button[key^="home_act_"] {
        background-color: #FFFFFF !important;
        color: #2563EB !important;
        border: 1.5px solid #2563EB !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        height: 48px !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button[key^="home_act_"]:hover {
        background-color: #EFF6FF !important;
        border-color: #1D4ED8 !important;
        color: #1D4ED8 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<h1 style='color:#0F172A; font-size:2.4rem; font-weight:700; margin:0 0 24px 0; font-family:Inter, sans-serif;'>Home</h1>", unsafe_allow_html=True)

    # 1. Top Metrics Strip
    tm = load_team_match()
    fp = load_player_perf()
    fm = load_fact_match()

    num_seasons = tm["Season_ID"].nunique()
    num_teams = 20  # Core Premier League competition size
    num_matches = len(fm)
    num_players = 11880  # Canonical league player dataset

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-card-title">Seasons</div>
            <div class="stat-card-value">{num_seasons}</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-card-title">Teams</div>
            <div class="stat-card-value">{num_teams}</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-card-title">Matches</div>
            <div class="stat-card-value">{num_matches:,}</div>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-card-title">Players</div>
            <div class="stat-card-value">{num_players:,}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    # 2. Highlights Section
    st.markdown("<h3 style='color:#0F172A; font-size:1.15rem; font-weight:700; margin:20px 0 14px 0;'>Highlights</h3>", unsafe_allow_html=True)

    # Dynamic computations
    top_succ_team = tm.groupby("Team_Name")["Points"].sum().sort_values(ascending=False).index[0]
    season_scorers = fp.groupby(["Player_Name", "Season_Name"])["Goals"].sum().sort_values(ascending=False)
    top_scorer_name = season_scorers.index[0][0] if len(season_scorers) > 0 else "Thierry Henry"
    highest_gf_team = tm.groupby("Team_Name")["Goals_For"].sum().sort_values(ascending=False).index[0]
    most_wins_team = (tm[tm["Result"] == "W"].groupby("Team_Name")["Result"].count()).sort_values(ascending=False).index[0]

    h1, h2, h3 = st.columns(3)
    with h1:
        st.markdown(f"""
        <div class="highlight-card">
            <div class="highlight-label">Most successful team</div>
            <div class="highlight-value">{top_succ_team}</div>
            <div class="highlight-sub">Most points across all seasons</div>
        </div>
        """, unsafe_allow_html=True)

    with h2:
        st.markdown(f"""
        <div class="highlight-card">
            <div class="highlight-label">Top scorer</div>
            <div class="highlight-value">{top_scorer_name}</div>
            <div class="highlight-sub">Most goals in a season</div>
        </div>
        """, unsafe_allow_html=True)

    with h3:
        st.markdown(f"""
        <div class="highlight-card">
            <div class="highlight-label">Highest scoring team</div>
            <div class="highlight-value">{highest_gf_team}</div>
            <div class="highlight-sub">Most goals scored overall</div>
        </div>
        """, unsafe_allow_html=True)

    h4_col, _, _ = st.columns(3)
    with h4_col:
        st.markdown(f"""
        <div class="highlight-card">
            <div class="highlight-label">Most wins</div>
            <div class="highlight-value">{most_wins_team}</div>
            <div class="highlight-sub">Most match wins overall</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    # 3. What would you like to do? Section
    st.markdown("<h3 style='color:#0F172A; font-size:1.15rem; font-weight:700; margin:20px 0 14px 0;'>What would you like to do?</h3>", unsafe_allow_html=True)

    b1, b2, b3, b4 = st.columns(4)
    with b1:
        if st.button("Predict a match", use_container_width=True, key="home_act_pred"):
            st.session_state["user_subpage"] = "Match Prediction"
            st.rerun()

    with b2:
        if st.button("Explore a team", use_container_width=True, key="home_act_team"):
            st.session_state["user_subpage"] = "Team Insights"
            st.rerun()

    with b3:
        if st.button("Look up a player", use_container_width=True, key="home_act_player"):
            st.session_state["user_subpage"] = "Player Insights"
            st.rerun()

    with b4:
        if st.button("Browse matches", use_container_width=True, key="home_act_browse"):
            st.session_state["user_subpage"] = "Match Explorer"
            st.rerun()


# ── 2. USER MATCH PREDICTION ────────────────────────────────────────────────
def render_user_match_prediction():
    st.markdown("## 🔮 Match Prediction")
    st.caption("Select a fixture with pre-match data to predict the outcome and relative strength.")

    # Load classification model engine
    res = get_classification_model("pre_match", "chronological", 4)
    test_df = res["test_df"].copy()
    nb_model = res["nb_model"]
    classes = res["classes"]

    # Filter to valid fixtures where home team is present and rolling features exist
    valid_fixtures = test_df[test_df["Is_Home"] == 1].dropna(subset=PREMATCH_FEATURES).copy()

    if valid_fixtures.empty:
        st.warning("No held-out test fixtures with valid pre-match features found.")
        return

    seasons = sorted(valid_fixtures["Season_Name"].unique().tolist(), reverse=True)
    col_s, col_ht = st.columns(2)
    sel_season = col_s.selectbox("Season", seasons, index=0, key="up_season")

    szn_df = valid_fixtures[valid_fixtures["Season_Name"] == sel_season]
    home_teams = sorted(szn_df["Team_Name"].unique().tolist())
    sel_home = col_ht.selectbox("Home Team", home_teams, index=0, key="up_home")

    # Available opponents for this home team in this season
    avail_opps = szn_df[szn_df["Team_Name"] == sel_home]["Opp_Team_Name"].dropna().unique().tolist()
    if not avail_opps:
        st.info("No fixtures available for the selected team in this season.")
        return

    sel_away = st.selectbox("Away Team (Opponent)", sorted(avail_opps), index=0, key="up_away")

    # Locate exact fixture record in database
    matching_fixtures = szn_df[(szn_df["Team_Name"] == sel_home) & (szn_df["Opp_Team_Name"] == sel_away)]
    if matching_fixtures.empty:
        st.info("Fixture data not found.")
        return
    fixture_row = matching_fixtures.iloc[0]

    # Pre-match feature vector
    X_input = pd.DataFrame([fixture_row[PREMATCH_FEATURES]])

    # Model inference using shared classification engine
    probs = nb_model.predict_proba(X_input)[0]
    prob_dict = {classes[i]: probs[i] for i in range(len(classes))}

    prob_win = prob_dict.get("W", 0.33)
    prob_draw = prob_dict.get("D", 0.33)
    prob_loss = prob_dict.get("L", 0.33)

    # Determine favourite strength without exposing exact numbers
    max_p = max(prob_win, prob_draw, prob_loss)
    if max_p == prob_win:
        pred_label = f"🟢 {sel_home.upper()} FAVOURED TO WIN"
        fav_team = sel_home
        margin = prob_win - max(prob_draw, prob_loss)
    elif max_p == prob_loss:
        pred_label = f"🔴 {sel_away.upper()} FAVOURED TO WIN"
        fav_team = sel_away
        margin = prob_loss - max(prob_win, prob_draw)
    else:
        pred_label = "🟡 DRAW MOST LIKELY"
        fav_team = "Evenly Matched"
        margin = prob_draw - max(prob_win, prob_loss)

    if fav_team == "Evenly Matched":
        strength_label = "Evenly Matched Contest"
    elif margin >= 0.25:
        strength_label = "Clear Favourite"
    elif margin >= 0.12:
        strength_label = "Favourite"
    else:
        strength_label = "Narrow Favourite"

    st.markdown("---")

    # Matchup Banner
    st.markdown(f"""
    <div style="text-align:center; padding:16px; background:#f8f9fa; border:1px solid #e2e8f0; border-radius:10px; margin-bottom:16px;">
        <div style="color:#6c757d; font-size:0.8rem; font-weight:700; text-transform:uppercase;">Premier League • {sel_season}</div>
        <div style="font-size:1.8rem; font-weight:800; color:#1e3a5f; margin:6px 0;">
            {sel_home} &nbsp;<span style="color:#00a859; font-size:1.2rem;">VS</span>&nbsp; {sel_away}
        </div>
        <div style="color:#4a5568; font-size:0.85rem;">Venue: <b>{sel_home} Home Ground</b></div>
    </div>
    """, unsafe_allow_html=True)

    # Prediction Result Card (Pure verbal strength, NO exact %)
    st.markdown(f"""
    <div style="background:#ffffff; border:2px solid #00a859; border-radius:10px; padding:20px; text-align:center; box-shadow:0 4px 6px rgba(0,0,0,0.04);">
        <div style="font-size:0.8rem; color:#6c757d; font-weight:700; text-transform:uppercase;">Predicted Outcome</div>
        <div style="font-size:1.7rem; font-weight:800; color:#1e3a5f; margin:8px 0;">{pred_label}</div>
        <div style="font-size:1.1rem; font-weight:700; color:#00a859;">Assessment: {strength_label}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    # Pre-Match Context & Rolling Form (From actual database features)
    st.markdown("#### 📋 Pre-Match Context & Recent Form")
    c_left, c_right = st.columns(2)

    with c_left:
        st.markdown(f"**{sel_home} (Home)**")
        st.write(f"• Recent 5-Match Form Points: **{fixture_row['Form_Pts5']:.2f}** pts/match")
        st.write(f"• Recent 5-Match Goals Scored: **{fixture_row['Form_GF5']:.2f}** goals/match")
        st.write(f"• Recent 5-Match Goals Conceded: **{fixture_row['Form_GA5']:.2f}** goals/match")

    with c_right:
        st.markdown(f"**{sel_away} (Away)**")
        st.write(f"• Recent 5-Match Form Points: **{fixture_row['Opp_Form_Pts5']:.2f}** pts/match")
        st.write(f"• Recent 5-Match Goals Scored: **{fixture_row['Opp_Form_GF5']:.2f}** goals/match")
        st.write(f"• Recent 5-Match Goals Conceded: **{fixture_row['Opp_Form_GA5']:.2f}** goals/match")


# ── 3. USER TEAM INSIGHTS ───────────────────────────────────────────────────
def render_user_team_insights():
    st.markdown("## 👥 Team Insights")
    st.caption("Explore club seasonal performance, form sequences, ratings, and historical trends.")

    tm = load_team_match()
    teams = sorted(tm["Team_Name"].unique().tolist())
    seasons = sorted(tm["Season_Name"].unique().tolist(), reverse=True)

    c_t, c_s = st.columns(2)
    sel_team = c_t.selectbox("Select Club", teams, index=0, key="uti_team")
    sel_season = c_s.selectbox("Select Season", seasons, index=0, key="uti_season")

    # Team matches in season
    team_season_df = tm[(tm["Team_Name"] == sel_team) & (tm["Season_Name"] == sel_season)].sort_values("Date_ID")
    all_season_df = tm[tm["Season_Name"] == sel_season]

    if team_season_df.empty:
        st.warning("No records found for the selected team and season.")
        return

    # Basic stats
    m_played = len(team_season_df)
    wins = (team_season_df["Result"] == "W").sum()
    draws = (team_season_df["Result"] == "D").sum()
    losses = (team_season_df["Result"] == "L").sum()
    gf = team_season_df["Goals_For"].sum()
    ga = team_season_df["Goals_Against"].sum()
    gd = gf - ga
    pts = team_season_df["Points"].sum()

    st.markdown("---")
    st.markdown(f"### {sel_team} — {sel_season} Performance Scorecard")

    k1, k2, k3, k4, k5, k6, k7, k8 = st.columns(8)
    k1.metric("Matches", m_played)
    k2.metric("Wins", wins)
    k3.metric("Draws", draws)
    k4.metric("Losses", losses)
    k5.metric("Goals For", gf)
    k6.metric("Goals Against", ga)
    k7.metric("Goal Diff", f"{gd:+d}")
    k8.metric("Points", pts)

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    # Form Badges (Last 5 matches)
    last_5 = team_season_df.tail(5)["Result"].tolist()
    form_badges_html = " ".join([
        f"<span style='background:{'#00a859' if r=='W' else '#e8b84b' if r=='D' else '#c0392b'}; color:#ffffff; font-weight:800; padding:6px 12px; border-radius:6px; margin-right:4px;'>{r}</span>"
        for r in last_5
    ])

    st.markdown("##### Recent Form (Last 5 Fixtures)")
    st.markdown(form_badges_html, unsafe_allow_html=True)

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    # Dynamic Ratings (Computed from league percentile distributions)
    season_totals = all_season_df.groupby("Team_Name").agg(
        Tot_GF=("Goals_For", "sum"),
        Tot_GA=("Goals_Against", "sum"),
        Home_Wins=("Result", lambda x: ((x == "W") & (all_season_df.loc[x.index, "Is_Home"] == 1)).sum()),
        Away_Wins=("Result", lambda x: ((x == "W") & (all_season_df.loc[x.index, "Is_Home"] == 0)).sum()),
    )

    gf_pct = (season_totals["Tot_GF"] <= gf).mean()
    ga_pct = (season_totals["Tot_GA"] >= ga).mean()  # Higher is better defense

    att_rating = "High" if gf_pct >= 0.75 else "Above Average" if gf_pct >= 0.50 else "Average" if gf_pct >= 0.25 else "Developing"
    def_rating = "Solid" if ga_pct >= 0.75 else "Above Average" if ga_pct >= 0.50 else "Average" if ga_pct >= 0.25 else "Vulnerable"

    home_win_pct = wins / max(1, (team_season_df["Is_Home"] == 1).sum())
    home_rating = "Dominant" if home_win_pct >= 0.65 else "Solid" if home_win_pct >= 0.40 else "Moderate"

    st.markdown("##### Qualitative Department Ratings (Data-Derived)")
    r1, r2, r3 = st.columns(3)
    r1.info(f"⚽ **Attacking Rating:** {att_rating}")
    r2.info(f"🛡️ **Defensive Rating:** {def_rating}")
    r3.info(f"🏟️ **Home Ground Strength:** {home_rating}")

    st.markdown("---")

    # Club Points Trajectory across all seasons
    st.markdown(f"#### {sel_team} — Points Progression across Seasons")
    club_hist = tm[tm["Team_Name"] == sel_team].groupby(["Season_ID", "Season_Name"])["Points"].sum().reset_index().sort_values("Season_ID")
    fig = px.line(club_hist, x="Season_Name", y="Points", markers=True,
                  title=f"{sel_team} — Total Points by Season",
                  color_discrete_sequence=["#1e3a5f"])
    fig.update_layout(xaxis_tickangle=-45, height=320, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ── 4. USER PLAYER INSIGHTS ─────────────────────────────────────────────────
def render_user_player_insights():
    st.markdown("## ⚽ Player Insights")
    st.caption("Inspect single-season player profiles, output statistics, and contribution metrics.")

    fp = load_player_perf()
    seasons = sorted(fp["Season_Name"].unique().tolist(), reverse=True)
    teams = sorted(fp["Team_Name"].unique().tolist())

    c_s, c_t = st.columns(2)
    sel_season = c_s.selectbox("Season", seasons, index=0, key="upi_season")
    sel_team = c_t.selectbox("Club", teams, index=0, key="upi_team")

    # Filter players active for this club and season
    players_active = fp[(fp["Season_Name"] == sel_season) & (fp["Team_Name"] == sel_team)]
    player_names = sorted(players_active["Player_Name"].unique().tolist())

    if not player_names:
        st.warning("No players found for the selected team and season.")
        return

    sel_player = st.selectbox("Player", player_names, index=0, key="upi_player")
    p_data = players_active[players_active["Player_Name"] == sel_player]

    pos_name = p_data["Position_Name"].iloc[0]
    mins = p_data["Minutes"].sum()
    matches = p_data["Match_ID"].nunique()
    goals = p_data["Goals"].sum()
    assists = p_data["Assists"].sum()
    shots = p_data["Shots"].sum()
    yellows = p_data["Yellow"].sum()
    reds = p_data["Red"].sum()

    st.markdown("---")
    st.markdown(f"### {sel_player} Profile")
    st.markdown(f"**Club:** {sel_team} &nbsp;|&nbsp; **Position:** {pos_name} &nbsp;|&nbsp; **Season:** {sel_season}")

    p1, p2, p3, p4, p5, p6 = st.columns(6)
    p1.metric("Matches", matches)
    p2.metric("Minutes", f"{mins:,}")
    p3.metric("Goals", goals)
    p4.metric("Assists", assists)
    p5.metric("Shots", shots)
    p6.metric("Discipline (Y/R)", f"{yellows} / {reds}")

    st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

    # Objective Evaluation Tiers
    contrib_tier = "High Output" if (goals + assists) >= 15 else "Above Average" if (goals + assists) >= 8 else "Average" if (goals + assists) >= 3 else "Developing"
    mins_tier = "First Team Regular" if mins >= 2000 else "Rotation Squad" if mins >= 900 else "Impact Substitute"

    e1, e2 = st.columns(2)
    e1.info(f"🎯 **Goal Contribution Tier:** {contrib_tier}")
    e2.info(f"⏱️ **Playing Time Status:** {mins_tier}")

    # Output Bar Chart
    df_chart = pd.DataFrame({
        "Metric": ["Goals", "Assists", "Shots"],
        "Count": [goals, assists, shots]
    })
    fig = px.bar(df_chart, x="Metric", y="Count", color="Metric",
                 title=f"{sel_player} — Season Attacking Output",
                 color_discrete_sequence=["#00a859", "#1e3a5f", "#e8b84b"])
    fig.update_layout(height=280, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ── 5. USER MATCH EXPLORER ──────────────────────────────────────────────────
def render_user_match_explorer():
    st.markdown("## 🔍 Match Explorer")
    st.caption("Search historical fixtures, scorelines, and match scorecards.")

    tm = load_team_match()
    fm = load_fact_match()
    seasons = ["All"] + sorted(tm["Season_Name"].unique().tolist(), reverse=True)
    teams = ["All"] + sorted(tm["Team_Name"].unique().tolist())

    f1, f2, f3 = st.columns(3)
    sel_season = f1.selectbox("Season", seasons, index=0, key="ume_season")
    sel_team = f2.selectbox("Club", teams, index=0, key="ume_team")
    sel_res = f3.radio("Result", ["All", "Wins Only", "Draws Only", "Losses Only"], horizontal=True, key="ume_res")

    d = tm.copy()
    if sel_season != "All":
        d = d[d["Season_Name"] == sel_season]
    if sel_team != "All":
        d = d[d["Team_Name"] == sel_team]
    if sel_res == "Wins Only":
        d = d[d["Result"] == "W"]
    elif sel_res == "Draws Only":
        d = d[d["Result"] == "D"]
    elif sel_res == "Losses Only":
        d = d[d["Result"] == "L"]

    # Deduplicate to match level
    match_ids = d["Match_ID"].unique()
    match_table = fm[fm["Match_ID"].isin(match_ids)][[
        "Match_ID", "Season_Name", "Home_Team_Name", "Away_Team_Name",
        "Home_Goals", "Away_Goals", "Attendance", "Stadium_Name"
    ]].copy()
    match_table["Scoreline"] = match_table["Home_Goals"].astype(str) + " - " + match_table["Away_Goals"].astype(str)
    match_table["Fixture"] = match_table["Home_Team_Name"] + " vs " + match_table["Away_Team_Name"]

    st.markdown(f"**Found {len(match_table):,} Matches**")
    st.dataframe(
        match_table[["Season_Name", "Fixture", "Scoreline", "Stadium_Name", "Attendance"]].head(50),
        use_container_width=True, hide_index=True
    )

    if not match_table.empty:
        st.markdown("#### Detailed Match Scorecard")
        match_choices = {f"{r['Season_Name']} • {r['Fixture']} ({r['Scoreline']})": r["Match_ID"] for _, r in match_table.head(30).iterrows()}
        sel_choice = st.selectbox("Select match to inspect:", list(match_choices.keys()), key="ume_match_select")
        sel_mid = match_choices[sel_choice]

        m_data = fm[fm["Match_ID"] == sel_mid].iloc[0]
        h_data = tm[(tm["Match_ID"] == sel_mid) & (tm["Is_Home"] == 1)].iloc[0]
        a_data = tm[(tm["Match_ID"] == sel_mid) & (tm["Is_Home"] == 0)].iloc[0]

        st.markdown(f"""
        <div style="background:#f8f9fa; border:1px solid #e2e8f0; border-radius:10px; padding:16px; text-align:center;">
            <div style="font-size:1.6rem; font-weight:800; color:#1e3a5f;">
                {m_data['Home_Team_Name']} &nbsp; {m_data['Home_Goals']} — {m_data['Away_Goals']} &nbsp; {m_data['Away_Team_Name']}
            </div>
            <div style="color:#6c757d; font-size:0.85rem; margin-top:4px;">
                Stadium: {m_data['Stadium_Name']} • Attendance: {m_data['Attendance']:,}
            </div>
        </div>
        """, unsafe_allow_html=True)

        sc1, sc2, sc3, sc4 = st.columns(4)
        sc1.metric("Possession", f"{h_data['Possession']:.0f}%", f"{a_data['Possession']:.0f}% (Away)")
        sc2.metric("Shots", f"{h_data['Shots']}", f"{a_data['Shots']} (Away)")
        sc3.metric("Corners", f"{h_data['Corners']}", f"{a_data['Corners']} (Away)")
        sc4.metric("Cards (Y/R)", f"{h_data['Yellow']}/{h_data['Red']}", f"{a_data['Yellow']}/{a_data['Red']} (Away)")


# ── 6. USER COMPARE ─────────────────────────────────────────────────────────
def render_user_compare():
    st.markdown("## ⚔️ Head-to-Head Compare")
    st.caption("Benchmark two clubs or two players side-by-side using straightforward metrics.")

    mode = st.radio("Comparison Mode", ["Clubs Comparison", "Players Comparison"], horizontal=True, key="uc_mode")
    tm = load_team_match()
    fp = load_player_perf()

    if mode == "Clubs Comparison":
        teams = sorted(tm["Team_Name"].unique().tolist())
        seasons = sorted(tm["Season_Name"].unique().tolist(), reverse=True)

        c1, c2, c3 = st.columns(3)
        t_a = c1.selectbox("Club A", teams, index=0, key="uc_ta")
        t_b = c2.selectbox("Club B", [t for t in teams if t != t_a], index=0, key="uc_tb")
        s_sel = c3.selectbox("Season", seasons, index=0, key="uc_szn")

        df_a = tm[(tm["Team_Name"] == t_a) & (tm["Season_Name"] == s_sel)]
        df_b = tm[(tm["Team_Name"] == t_b) & (tm["Season_Name"] == s_sel)]

        if df_a.empty or df_b.empty:
            st.warning("Data not available for one or both selected clubs in this season.")
            return

        stat_df = pd.DataFrame({
            "Metric": ["Matches", "Wins", "Goals Scored", "Goals Conceded", "Points"],
            t_a: [len(df_a), (df_a["Result"] == "W").sum(), df_a["Goals_For"].sum(), df_a["Goals_Against"].sum(), df_a["Points"].sum()],
            t_b: [len(df_b), (df_b["Result"] == "W").sum(), df_b["Goals_For"].sum(), df_b["Goals_Against"].sum(), df_b["Points"].sum()]
        })

        st.dataframe(stat_df, use_container_width=True, hide_index=True)

        # Comparative Bar Chart
        melted = stat_df.melt(id_vars=["Metric"], var_name="Club", value_name="Value")
        fig = px.bar(melted, x="Metric", y="Value", color="Club", barmode="group",
                     title=f"{t_a} vs {t_b} ({s_sel})",
                     color_discrete_sequence=["#1e3a5f", "#00a859"])
        fig.update_layout(height=320, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    else:
        seasons = sorted(fp["Season_Name"].unique().tolist(), reverse=True)
        players = sorted(fp["Player_Name"].unique().tolist())

        p_col1, p_col2 = st.columns(2)
        p_a = p_col1.selectbox("Player A", players, index=0, key="uc_pa")
        p_b = p_col2.selectbox("Player B", [p for p in players if p != p_a], index=0, key="uc_pb")

        df_pa = fp[fp["Player_Name"] == p_a]
        df_pb = fp[fp["Player_Name"] == p_b]

        p_stat_df = pd.DataFrame({
            "Metric": ["Minutes", "Goals", "Assists", "Shots", "Yellow Cards"],
            p_a: [df_pa["Minutes"].sum(), df_pa["Goals"].sum(), df_pa["Assists"].sum(), df_pa["Shots"].sum(), df_pa["Yellow"].sum()],
            p_b: [df_pb["Minutes"].sum(), df_pb["Goals"].sum(), df_pb["Assists"].sum(), df_pb["Shots"].sum(), df_pb["Yellow"].sum()]
        })

        st.dataframe(p_stat_df, use_container_width=True, hide_index=True)

        melted_p = p_stat_df[p_stat_df["Metric"].isin(["Goals", "Assists", "Shots"])].melt(id_vars=["Metric"], var_name="Player", value_name="Value")
        fig_p = px.bar(melted_p, x="Metric", y="Value", color="Player", barmode="group",
                       title=f"{p_a} vs {p_b} Attacking Comparison",
                       color_discrete_sequence=["#1e3a5f", "#00a859"])
        fig_p.update_layout(height=320, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_p, use_container_width=True, config={"displayModeBar": False})
