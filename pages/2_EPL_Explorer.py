"""
pages/2_EPL_Explorer.py — Admin: EPL Explorer
Cascading filters (season -> club -> player, plus stadium) select one set of matches; every card reads from it:
  numbers strip · player profile (when a player is picked) · goals trend · top scorers · results ·
  league table with the club highlighted · insights that describe the club (or the league) in that selection.
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
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: 12px;
    padding: 16px 18px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
    margin-bottom: 16px;
    box-sizing: border-box;
}

/* Metric Cards */
.kpi-metric-box {
    background: var(--card);
    border: 1px solid var(--line);
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
    background: var(--chip);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}
.kpi-title {
    color: var(--mute);
    font-size: 0.8rem;
    font-weight: 500;
    margin-bottom: 2px;
}
.kpi-val {
    color: var(--ink);
    font-size: 1.6rem;
    font-weight: 700;
    line-height: 1.15;
    margin-bottom: 2px;
}
.kpi-sub {
    color: var(--mute);
    font-size: 0.74rem;
}

/* Overview table */
.exp-table {
    width: 100%;
    border-collapse: collapse;
}
.exp-table th {
    text-align: left;
    color: var(--mute);
    font-size: 0.76rem;
    font-weight: 600;
    text-transform: uppercase;
    padding: 8px 10px 10px 10px;
    border-bottom: 1px solid var(--line);
}
.exp-table td {
    padding: 10px;
    color: var(--ink);
    font-size: 0.85rem;
    border-bottom: 1px solid var(--line);
}
.exp-table tr:last-child td {
    border-bottom: none;
}
.exp-team-link {
    color: var(--acc);
    font-weight: 600;
    text-decoration: none;
}
</style>
""", unsafe_allow_html=True)

# ── 1. Cascading filters: each list only offers values that exist for the picks before it ──
_DB_PATH = Path(__file__).resolve().parent.parent / "epl_dw.db"


def run_filtered_query(query: str, params=()):
    with sqlite3.connect(_DB_PATH) as con:
        return pd.read_sql(query, con, params=params)


@st.cache_data(show_spinner=False)
def _opts(sql: str, params: tuple = ()) -> list:
    return run_filtered_query(sql, params).iloc[:, 0].dropna().tolist()


def _where(pairs):
    """[(condition, value)] for the picks that are set -> (' WHERE ...', params)."""
    pairs = [(c, v) for c, v in pairs if v is not None]
    return (" WHERE " + " AND ".join(c for c, _ in pairs) if pairs else ""), tuple(v for _, v in pairs)


@st.cache_data(show_spinner=False)
def _players(where: str, params: tuple) -> pd.DataFrame:
    return run_filtered_query(
        "SELECT fp.Player_ID, dp.Player_Name, t.Team_Name, s.Season_Name FROM Fact_Player_Performance fp "
        "JOIN Dim_Player dp USING(Player_ID) JOIN Dim_Team t ON fp.Team_ID = t.Team_ID "
        f"JOIN Dim_Season s ON fp.Season_ID = s.Season_ID{where} "
        "GROUP BY fp.Player_ID ORDER BY SUM(fp.Minutes) DESC", params)


def _pick(container, label, options, key):
    if st.session_state.get(key) not in options:  # an earlier pick ruled this value out
        st.session_state[key] = options[0]
    return container.selectbox(label, options, key=key)


with st.container(key="card_epl_explorer_filters"):
    f1, f2, f3, f4, f5 = st.columns([1, 1, 1.2, 1.2, 0.55], vertical_alignment="bottom")

    season_opts = ["All Seasons"] + load_dim_season()["Season_Name"].tolist()
    act_season = _pick(f1, "Season", season_opts, "exp_sel_season")
    v_season = None if act_season == "All Seasons" else act_season

    w, prm = _where([("s.Season_Name = ?", v_season)])
    team_opts = ["All Teams"] + _opts(
        "SELECT DISTINCT t.Team_Name FROM Fact_Team_Match tm JOIN Dim_Team t USING(Team_ID) "
        f"JOIN Dim_Season s USING(Season_ID){w} ORDER BY t.Team_Name", prm)
    act_team = _pick(f2, "Team", team_opts, "exp_sel_team")
    v_team = None if act_team == "All Teams" else act_team

    w, prm = _where([("s.Season_Name = ?", v_season), ("t.Team_Name = ?", v_team)])
    pl = _players(w, prm)
    labels = {0: "All Players"}
    for r in pl.itertuples():
        extra = [x for x, show in ((r.Team_Name, not v_team), (r.Season_Name, not v_season)) if show]
        labels[int(r.Player_ID)] = r.Player_Name + (f" · {' '.join(extra)}" if extra else "")
    if st.session_state.get("exp_sel_player") not in labels:
        st.session_state["exp_sel_player"] = 0
    act_player_id = f3.selectbox(f"Player{' · ' + act_team if v_team else ''}", list(labels), key="exp_sel_player",
                                 format_func=labels.get)
    act_player = "All Players" if act_player_id == 0 else labels[act_player_id]

    w, prm = _where([("s.Season_Name = ?", v_season), ("? IN (ht.Team_Name, at_.Team_Name)", v_team)])
    stadium_opts = ["All Stadiums"] + _opts(
        "SELECT DISTINCT st_.Stadium_Name FROM Fact_Match fm JOIN Dim_Season s USING(Season_ID) "
        "JOIN Dim_Team ht ON fm.Home_Team_ID = ht.Team_ID JOIN Dim_Team at_ ON fm.Away_Team_ID = at_.Team_ID "
        f"JOIN Dim_Stadium st_ USING(Stadium_ID){w} ORDER BY st_.Stadium_Name", prm)
    act_stadium = _pick(f4, "Stadium", stadium_opts, "exp_sel_stadium")

    if f5.button("Reset", key="exp_reset", use_container_width=True):
        for k in ("exp_sel_season", "exp_sel_team", "exp_sel_player", "exp_sel_stadium"):
            st.session_state.pop(k, None)
        st.rerun()

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

if act_player_id:
    fm_where.append("fm.Match_ID IN (SELECT fpp.Match_ID FROM Fact_Player_Performance fpp WHERE fpp.Player_ID = ?)")
    fm_params.append(act_player_id)

fm_where_clause = ("WHERE " + " AND ".join(fm_where)) if fm_where else ""

# ── 3. One shared selection: every card below reads from the same set of matches ─────────
from utils.user_views import _css, _cell, _feat, _grid, _league_table, _ordinal, _table_html
from utils.viz import CSS as VIZ_CSS, bars, hrows, stack

_css()
st.markdown(VIZ_CSS + """
<style>
[class*="st-key-xa_"],[class*="st-key-xb_"]{background:var(--card);border:1px solid var(--line);border-radius:8px;
  padding:12px 14px!important;overflow:hidden;flex:0 0 auto!important;gap:.4rem!important}
[class*="st-key-xa_"]{height:340px!important}
[class*="st-key-xb_"]{height:470px!important}
[class*="st-key-xa_"] .stElementContainer:has(.grow),[class*="st-key-xb_"] .stElementContainer:has(.grow){flex:1 1 auto;min-height:0}
[class*="st-key-xa_"] .stElementContainer:has(.grow) div:has(.grow),[class*="st-key-xb_"] .stElementContainer:has(.grow) div:has(.grow){height:100%}
.ins{display:flex;flex-direction:column;justify-content:space-between;height:100%}
.ins div{display:grid;grid-template-columns:26px 1fr;gap:10px;padding:8px 0;border-bottom:1px solid var(--line)}
.ins div:last-child{border-bottom:0}
.ins i{font-style:normal;font:700 .62rem 'Inter';color:var(--pk);border:1px solid var(--line);border-radius:50%;width:24px;height:24px;
  display:flex;align-items:center;justify-content:center}
.ins b{display:block;font-size:.66rem;letter-spacing:.14em;text-transform:uppercase;color:var(--mute);font-weight:600}
.ins span{display:block;font-size:.86rem;color:var(--ink);margin-top:2px;line-height:1.35}
.ins span em{font-style:normal;font-family:'Anton',sans-serif;font-size:1rem}
</style>""", unsafe_allow_html=True)


def _box(html):
    st.markdown(f'<div class="grow">{html}</div>', unsafe_allow_html=True)


ids = set(run_filtered_query(f"""
    SELECT fm.Match_ID FROM Fact_Match fm
    JOIN Dim_Season s USING(Season_ID)
    JOIN Dim_Team ht ON fm.Home_Team_ID = ht.Team_ID
    JOIN Dim_Team at_ ON fm.Away_Team_ID = at_.Team_ID
    JOIN Dim_Stadium st_ USING(Stadium_ID)
    {fm_where_clause}""", fm_params)["Match_ID"])
tm_all, fp_all, fm_all = load_team_match(), load_player_perf(), load_fact_match()
sel_tm = tm_all[tm_all["Match_ID"].isin(ids)]
sel_fm = fm_all[fm_all["Match_ID"].isin(ids)]
sel_fp = fp_all[fp_all["Match_ID"].isin(ids)]
club = None if act_team == "All Teams" else act_team
club_tm = sel_tm[sel_tm["Team_Name"] == club] if club else sel_tm

if not ids:
    st.info("No matches fit this combination of filters. Press Reset to start again.")
    st.stop()

# ── Player profile: shown as soon as a player is picked ─────────────────────
if act_player_id:
    from utils.viz import bars

    _st_cond, _st_par = ("", [])
    if act_stadium != "All Stadiums":
        _st_cond, _st_par = (" AND st_.Stadium_Name = ?", [act_stadium])
    pm = run_filtered_query(f"""
        SELECT fp.Minutes, fp.Goals, fp.Assists, fp.Shots, fp.Yellow, fp.Red, fp.Team_ID, fp.Season_ID,
               dp.Player_Name, pos.Position_Name, t.Team_Name, s.Season_Name, d.Date,
               ht.Team_Name AS Home, at_.Team_Name AS Away, fm.Home_Goals, fm.Away_Goals
        FROM Fact_Player_Performance fp
        JOIN Dim_Player dp USING(Player_ID)
        JOIN Dim_Position pos ON dp.Position_ID = pos.Position_ID
        JOIN Dim_Team t ON fp.Team_ID = t.Team_ID
        JOIN Dim_Season s ON fp.Season_ID = s.Season_ID
        JOIN Fact_Match fm ON fp.Match_ID = fm.Match_ID
        JOIN Dim_Date d ON fm.Date_ID = d.Date_ID
        JOIN Dim_Team ht ON fm.Home_Team_ID = ht.Team_ID
        JOIN Dim_Team at_ ON fm.Away_Team_ID = at_.Team_ID
        JOIN Dim_Stadium st_ ON fm.Stadium_ID = st_.Stadium_ID
        WHERE fp.Player_ID = ?{_st_cond}
        ORDER BY d.Date
    """, [act_player_id] + _st_par)

    if pm.empty:
        st.info("This player has no appearances at the selected stadium.")
    else:
        r0 = pm.iloc[0]
        mins, goals, assists, shots = int(pm.Minutes.sum()), int(pm.Goals.sum()), int(pm.Assists.sum()), int(pm.Shots.sum())
        apps = int((pm.Minutes > 0).sum())
        per90 = lambda v: v / mins * 90 if mins else 0
        squad = run_filtered_query("""
            SELECT Player_ID, SUM(Goals) AS G, SUM(Goals + Assists) AS GA FROM Fact_Player_Performance
            WHERE Team_ID = ? AND Season_ID = ? GROUP BY Player_ID""", [int(r0.Team_ID), int(r0.Season_ID)])
        g_rank = int((squad["G"] > goals).sum()) + 1
        ga_rank = int((squad["GA"] > goals + assists).sum()) + 1
        n_squad = len(squad)

        opp = [a if h == r0.Team_Name else h for h, a in zip(pm.Home, pm.Away)]
        ga_game = (pm.Goals + pm.Assists).tolist()
        labels = [f"{'v' if h == r0.Team_Name else 'at'} {o} ({hg}–{ag})"
                  for h, o, hg, ag in zip(pm.Home, opp, pm.Home_Goals, pm.Away_Goals)]
        best = max(range(len(ga_game)), key=lambda i: ga_game[i])
        _grid(
            _feat(f"{r0.Team_Name} · {r0.Season_Name} · {r0.Position_Name}", r0.Player_Name,
                  f"<b>{goals} goals</b> and <b>{assists} assists</b> in {apps} appearances",
                  (f"{mins:,} minutes", f"#{g_rank} scorer in squad of {n_squad}", f"#{ga_rank} for goals + assists"))
            + _cell("s2", "Goals per 90", f"{per90(goals):.2f}", "per full match played")
            + _cell("s2", "Assists per 90", f"{per90(assists):.2f}", "per full match played")
            + _cell("s2", "Shots", shots, f"<b>{goals / shots:.0%}</b> scored" if shots else "no shots")
            + _cell("s2", "Cards", f"{int(pm.Yellow.sum())} · {int(pm.Red.sum())}", "yellow · red")
            + '<div class="cell s12"><div class="ch"><b>Match by match</b><span>goals + assists</span></div>'
            f'<div style="height:100px;display:flex;flex-direction:column">{bars(ga_game, labels, hi=best, fmt="{:.0f}", base=0)}</div>'
            f'<div class="note">One bar per appearance, in date order; hover a bar for the opponent and score. '
            f'Best game: <b>{labels[best]}</b> with {ga_game[best]} goal contributions.</div></div>'
        )
    st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)


# ── Row A: trend · scorers · results ─────────────────────────────────────────
a1, a2, a3 = st.columns([5, 4, 3], gap="small")
with a1, st.container(key="xa_trend"):
    by_season = sel_fm["Season_ID"].nunique() > 1
    key = "Season_Name" if by_season else "Month"
    g = sel_fm.assign(Month=pd.to_datetime(sel_fm["Date"]).dt.strftime("%b %y"), Sort=pd.to_datetime(sel_fm["Date"]))
    g = (g.groupby(key).agg(H=("Home_Goals", "mean"), A=("Away_Goals", "mean"), S=("Sort", "min")).sort_values("S").reset_index())
    fig = go.Figure()
    fig.add_scatter(x=g[key], y=g["H"], name="Home side", mode="lines+markers", line=dict(color="#3A1B7A", width=2.2), marker=dict(size=4))
    fig.add_scatter(x=g[key], y=g["A"], name="Away side", mode="lines+markers", line=dict(color="#FF3E8E", width=2), marker=dict(size=4))
    fig.update_layout(height=265, margin=dict(l=4, r=4, t=4, b=4), legend=dict(orientation="h", y=1.1, x=0, font=dict(size=10)),
                      xaxis=dict(tickangle=-45, nticks=12, tickfont=dict(size=9)), yaxis=dict(rangemode="tozero", tickfont=dict(size=9)))
    st.markdown(f'<div class="ch"><b>Goals per match</b><span>home v away · by {"season" if by_season else "month"}</span></div>',
                unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with a2, st.container(key="xa_scorers"):
    if club:
        sc = (sel_fp[sel_fp["Team_Name"] == club].groupby(["Player_ID", "Player_Name"])["Goals"].sum()
              .sort_values(ascending=False).head(8))
        rows = [(n + (" ◂" if pid == act_player_id else ""), int(v)) for (pid, n), v in sc.items()]
        title = f"Top scorers · {club}"
    else:
        sc = sel_tm.groupby("Team_Name")["Goals_For"].sum().sort_values(ascending=False).head(8)
        rows = [(n, int(v)) for n, v in sc.items()]
        title = "Top scoring clubs"
    _box(f'<div class="ch"><b>{title}</b><span>goals</span></div><div class="body" style="justify-content:space-around">'
         + (hrows(rows) if rows else '<div class="note">No goals in this selection.</div>') + "</div>")

with a3, st.container(key="xa_results"):
    if club:
        rc = club_tm["Result"].value_counts()
        parts = [(f"{club} won", int(rc.get("W", 0)), "var(--acc)"), ("Drawn", int(rc.get("D", 0)), "#9B98A6"),
                 (f"{club} lost", int(rc.get("L", 0)), "#FF3E8E")]
    else:
        rc = sel_fm["Match_Result"].value_counts()
        parts = [("Home wins", int(rc.get("H", 0)), "var(--acc)"), ("Draws", int(rc.get("D", 0)), "#9B98A6"),
                 ("Away wins", int(rc.get("A", 0)), "#FF3E8E")]
    gpm = (sel_fm["Home_Goals"] + sel_fm["Away_Goals"]).mean()
    n_s = sel_fm["Season_ID"].nunique()
    _box(f'<div class="ch"><b>This selection</b><span>results</span></div>'
         f'<div class="note" style="margin:0 0 10px">{len(ids):,} matches · {n_s} season{"s" if n_s != 1 else ""} · '
         f'{sel_tm["Team_ID"].nunique()} clubs · {sel_fp["Player_ID"].nunique():,} players · {len(sel_fp):,} player records</div>'
         + stack(parts)
         + '<div class="mini" style="margin-top:auto">'
         f'<div><small>Goals / match</small><b>{gpm:.2f}</b></div>'
         f'<div><small>Average crowd</small><b>{int(sel_fm["Attendance"].mean()):,}</b></div>'
         f'<div><small>Clean sheets</small><b>{int((club_tm["Goals_Against"] == 0).sum()):,}</b></div>'
         f'<div><small>Goalless draws</small><b>{int(((sel_fm["Home_Goals"] + sel_fm["Away_Goals"]) == 0).sum()):,}</b></div></div>')

# ── Row B: table · insights ──────────────────────────────────────────────────
b1, b2 = st.columns([7, 5], gap="small")
if act_season != "All Seasons":
    table, table_title, zones = _league_table(act_season), f"League table · {act_season}", True
else:
    t = tm_all.groupby("Team_Name").agg(P=("Result", "size"), W=("Result", lambda r: (r == "W").sum()),
                                        D=("Result", lambda r: (r == "D").sum()), L=("Result", lambda r: (r == "L").sum()),
                                        GF=("Goals_For", "sum"), GA=("Goals_Against", "sum"), Pts=("Points", "sum"))
    t["GD"] = t["GF"] - t["GA"]
    table, table_title, zones = t.sort_values("Pts", ascending=False).reset_index(), "All-time table · 27 seasons", False

with b1, st.container(key="xb_table"):
    _box(f'<div class="ch"><b>{table_title}</b><span>{club or "all clubs"}</span></div>'
         f'<div class="body">{_table_html(table, highlight=club, zones=zones)}</div>'
         + ('<div class="zones"><span><i style="background:var(--acc)"></i>Champions League</span>'
            '<span><i style="background:var(--pk)"></i>Relegated</span></div>' if zones else
            '<div class="note">Pick a season to see that year\'s final table.</div>'))

with b2, st.container(key="xb_insights"):
    items = []
    if club:
        pos = int(table.index[table["Team_Name"] == club][0]) + 1 if club in set(table["Team_Name"]) else None
        items.append(("Standing", f"Finished <em>{_ordinal(pos)}</em> in {act_season}" if pos and act_season != "All Seasons"
                      else f"<em>{_ordinal(pos)}</em> on points across all 27 seasons" if pos else "—"))
        for side, flag in (("Home", 1), ("Away", 0)):
            r = club_tm[club_tm["Is_Home"] == flag]["Result"].value_counts()
            items.append((f"{side} record", f"<em>{r.get('W', 0)}–{r.get('D', 0)}–{r.get('L', 0)}</em> (won–drawn–lost) "
                                            f"from {int(r.sum())} {side.lower()} games"))
        top = sel_fp[sel_fp["Team_Name"] == club].groupby(["Player_ID", "Player_Name"])["Goals"].sum().sort_values(ascending=False)
        if len(top):
            items.append(("Top scorer", f"<em>{top.index[0][1]}</em> with {int(top.iloc[0])} goals"))
        if len(club_tm):
            bw = club_tm.assign(M=club_tm["Goals_For"] - club_tm["Goals_Against"]).sort_values("M", ascending=False).iloc[0]
            opp = fm_all.set_index("Match_ID").loc[bw.Match_ID]
            other = opp["Away_Team_Name"] if bw.Is_Home else opp["Home_Team_Name"]
            items.append(("Biggest win", f"<em>{bw.Goals_For}–{bw.Goals_Against}</em> {'v' if bw.Is_Home else 'at'} {other}, {opp['Season_Name']}"
                          if bw.M > 0 else "No wins in this selection"))
        poss = sel_tm.groupby("Team_Name")["Possession"].mean().sort_values(ascending=False)
        if club in poss.index:
            items.append(("Possession", f"<em>{poss[club]:.1f}%</em> on average, <b style='display:inline;letter-spacing:0;text-transform:none;font-size:.86rem'>"
                                        f"{_ordinal(list(poss.index).index(club) + 1)}</b> of the {len(poss)} clubs in these matches"))
        heading = f"About {club}"
    else:
        agg = sel_tm.groupby("Team_Name").agg(Pts=("Points", "sum"), GF=("Goals_For", "sum"), GA=("Goals_Against", "sum"),
                                              P=("Result", "size"), Poss=("Possession", "mean"))
        best = agg.sort_values("Pts", ascending=False).iloc[0]
        items.append(("Most points", f"<em>{agg['Pts'].idxmax()}</em> with {int(best.Pts)} from {int(best.P)} games"))
        items.append(("Best attack", f"<em>{agg['GF'].idxmax()}</em> scored {int(agg['GF'].max())}"))
        d = agg.assign(GApg=agg["GA"] / agg["P"]).sort_values("GApg")
        items.append(("Best defence", f"<em>{d.index[0]}</em> conceded {d.iloc[0].GApg:.2f} a game"))
        top = sel_fp.groupby(["Player_ID", "Player_Name", "Team_Name"])["Goals"].sum().sort_values(ascending=False)
        if len(top):
            (_, n, tn), v = top.index[0], int(top.iloc[0])
            items.append(("Top scorer", f"<em>{n}</em> ({tn}) with {v} goals"))
        items.append(("Most possession", f"<em>{agg['Poss'].idxmax()}</em> at {agg['Poss'].max():.1f}% on average"))
        heading = "Across the selection"
    _box(f'<div class="ch"><b>Insights</b><span>{heading}</span></div><div class="body"><div class="ins">'
         + "".join(f"<div><i>{i + 1}</i><p style='margin:0'><b>{k}</b><span>{v}</span></p></div>" for i, (k, v) in enumerate(items))
         + "</div></div>")
