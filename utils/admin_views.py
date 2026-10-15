"""
utils/admin_views.py — Admin mode: shared chrome hook and the Control room dashboard.
"""
import streamlit as st

from utils.db import load_row_counts, q


def render_admin_sidebar(current_page="Dashboard"):
    """Admin chrome: shared top nav, theme and page header (the sidebar is no longer used)."""
    from utils.shell import render_shell
    return render_shell("admin", current_page)


def render_admin_dashboard():
    """Control room: what the warehouse holds, which engines are ready, and how the data moves season to season."""
    from utils.user_views import _all_time, _cell, _css, _feat, _fill, _grid
    from utils.viz import bars, hrows, stack

    _css()
    st.markdown("""
<style>
.eng{display:flex;flex-direction:column;justify-content:space-between;height:100%}
.eng div{display:grid;grid-template-columns:10px 1fr auto;gap:10px;align-items:center;padding:6px 0;border-bottom:1px solid var(--line)}
.eng div:last-child{border-bottom:0}
.eng i{width:8px;height:8px;border-radius:50%;background:#16A34A;box-shadow:0 0 0 3px rgba(22,163,74,.15)}
.eng b{display:block;font-size:.78rem;color:var(--ink)}
.eng small{display:block;font-size:.66rem;color:var(--mute);line-height:1.35}
.eng em{font-style:normal;font:700 .56rem 'Inter';letter-spacing:.14em;text-transform:uppercase;color:#16A34A}
.split2{display:grid;grid-template-rows:1fr 1fr;gap:12px;height:100%}
.split2>div{display:flex;flex-direction:column;min-height:0}
.split2 .t{font:600 .58rem 'Inter';letter-spacing:.16em;text-transform:uppercase;color:var(--mute);margin-bottom:2px}
</style>""", unsafe_allow_html=True)

    counts = load_row_counts()
    facts = [("Player performances", counts["Fact_Player_Performance"]), ("Team-match rows", counts["Fact_Team_Match"]),
             ("Matches", counts["Fact_Match"])]
    dims = [("Players", counts["Dim_Player"]), ("Dates", counts["Dim_Date"]), ("Seasons", counts["Dim_Season"]),
            ("Referees", counts["Dim_Referee"]), ("Teams", counts["Dim_Team"]), ("Stadiums", counts["Dim_Stadium"]),
            ("Cities", counts["Dim_City"]), ("Positions", counts["Dim_Position"])]
    total = sum(counts.values())
    split = q("SELECT Match_Result AS R, COUNT(*) AS N FROM Fact_Match GROUP BY Match_Result").set_index("R")["N"]

    _grid(
        _feat("Data warehouse <em>star schema</em>", f"{total:,} rows", "<b>11 tables</b> · 3 fact · 8 dimension",
              ("27 seasons", "20 clubs", "1999/00 – 2025/26"))
        + '<div class="cell s4"><div class="lab">Fact tables · the events</div><div style="margin-top:auto;padding-top:10px">'
        + hrows(facts) + "</div></div>"
        + '<div class="cell s4"><div class="lab">Every match result</div><div style="margin-top:auto;padding-top:10px">'
        + stack([("Home wins", int(split.get("H", 0)), "var(--acc)"), ("Draws", int(split.get("D", 0)), "#9B98A6"),
                 ("Away wins", int(split.get("A", 0)), "#FF3E8E")])
        + "</div></div>"
    )

    c1, c2, c3 = st.columns([4, 5, 3], gap="small")
    with c1, st.container(key="fill_engines"):
        engines = [
            ("Database", "SQLite warehouse, epl_dw.db", "Online"),
            ("Classification", "Decision tree, naive Bayes and logistic regression predict win / draw / loss", "Ready"),
            ("Regression", "Linear model: how shots, possession and fouls move goals", "Ready"),
            ("Clustering", "K-Means and hierarchical grouping of club styles", "Ready"),
            ("Association rules", "Apriori: match events that occur together", "Ready"),
            ("OLAP", "Roll-up, drill-down, slice, dice and pivot over the cube", "Ready"),
        ]
        _fill('<div class="ch"><b>Engines</b><span>live check</span></div><div class="body"><div class="eng">'
              + "".join(f"<div><i></i><span><b>{n}</b><small>{d}</small></span><em>{s}</em></div>" for n, d, s in engines)
              + "</div></div>")

    with c2, st.container(key="fill_seasons"):
        a = _all_time()
        ps = a["per_season"]
        crowd = q("""SELECT s.Season_Name, AVG(fm.Attendance) AS A FROM Fact_Match fm JOIN Dim_Season s USING(Season_ID)
                     GROUP BY s.Season_ID, s.Season_Name ORDER BY s.Season_ID""")
        last = len(ps) - 1
        _fill('<div class="ch"><b>Season by season</b><span>from Fact_Match</span></div><div class="body"><div class="split2">'
              f'<div><div class="t">Goals per match</div>{bars(ps["GPM"].tolist(), ps["Season_Name"].tolist(), hi=last, avg=a["avg_gpm"])}</div>'
              f'<div><div class="t">Average crowd</div>{bars(crowd["A"].tolist(), crowd["Season_Name"].tolist(), hi=last, avg=crowd["A"].mean(), fmt="{:,.0f}")}</div>'
              '</div></div><div class="note">Latest season highlighted; dashed lines are the 27-season averages.</div>')

    with c3, st.container(key="fill_dims"):
        _fill('<div class="ch"><b>Dimension tables</b><span>the context</span></div><div class="body" style="justify-content:space-between">'
              + hrows(dims, sqrt=True) + '</div><div class="note">Dimensions describe the who, when and where that each fact row points to.</div>')
