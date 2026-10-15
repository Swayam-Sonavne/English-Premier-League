"""
utils/user_views.py — User mode, three one-screen pages built as modular grids.

  Dashboard  season highlights, full table with zones, goals trend, match predictor
  Clubs      a club's season: finish, record, trend, recent results, optional rival
  Players    a player's season: output, build-up through the season, top scorers

Every picker lives in the page header (the `slot` from the shell); the cards below follow it.
Cards are plain HTML so they size to the screen and render without chart round-trips.
"""
import pandas as pd
import streamlit as st

from utils.db import load_fact_match, load_player_perf, load_team_match
from utils.theme import PK
from utils.viz import CSS as VIZ_CSS, bars, hrows, stack

CSS = """
<style>
/* grid rows */
/* a row of related facts is ONE card, split by thin rules */
.bento{display:grid;grid-template-columns:repeat(12,1fr);gap:0;margin-bottom:10px;background:var(--card);
  border:1px solid var(--line);border-radius:8px;overflow:hidden}
.cell{background:transparent;border-left:1px solid var(--line);padding:12px 16px;min-width:0;display:flex;flex-direction:column}
.bento>.cell:first-child{border-left:0}
.cell.s12{border-left:0;border-top:1px solid var(--line)}
.s2{grid-column:span 2}.s3{grid-column:span 3}.s4{grid-column:span 4}.s6{grid-column:span 6}.s8{grid-column:span 8}.s12{grid-column:span 12}
.cell .lab{font:600 .58rem 'Inter';letter-spacing:.18em;text-transform:uppercase;color:var(--mute)}
.cell .big{font-family:'Anton',sans-serif;font-size:clamp(1.3rem,1.9vw,1.9rem);line-height:1.05;color:var(--ink);margin-top:auto;padding-top:8px;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.cell .sub{font-size:.72rem;color:var(--mute);margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.cell .sub b{color:var(--ink)}
/* featured card */
.feat{position:relative;overflow:hidden;background:linear-gradient(135deg,#2A0E5C 0%,#3A1B7A 60%,#5B2BB0 100%)!important;border:0!important;color:#fff;min-height:132px}
.feat .lab{color:rgba(255,255,255,.7)}
.feat .lab em{font-style:normal;color:#FF8FBF}
.feat .big{color:#fff;font-size:clamp(1.8rem,2.8vw,2.8rem);position:relative;z-index:1}
.feat .sub{color:rgba(255,255,255,.75);position:relative;z-index:1}
.feat .sub b{color:#fff}
.feat .ball{position:absolute;right:-34px;bottom:-40px;width:150px;height:150px;opacity:.9;
  background:url(/app/static/ball_front.webp) center/contain no-repeat;animation:pl-spin 30s linear infinite}
.feat .wdl{display:flex;gap:6px;margin-top:8px;position:relative;z-index:1}
.feat .wdl span{font:700 .62rem 'Inter';letter-spacing:.1em;padding:3px 8px;border-radius:20px;background:rgba(255,255,255,.14)}
/* card heads */
.ch{display:flex;justify-content:space-between;align-items:baseline;gap:8px;margin-bottom:8px}
.ch b{font-family:'Anton',sans-serif;font-weight:400;text-transform:uppercase;font-size:.98rem;letter-spacing:.02em;color:var(--ink)}
.ch span{font:600 .58rem 'Inter';letter-spacing:.16em;text-transform:uppercase;color:var(--pk)}
.note{font-size:.66rem;color:var(--faint);margin-top:6px;line-height:1.4}
.note b{color:var(--mute)}
/* full-height cards in the lower row */
[class*="st-key-fill_"]{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px 14px!important;
  height:calc(100vh - var(--fill-top, 362px))!important;min-height:330px;overflow:hidden;flex:0 0 auto!important}
[class*="st-key-fill_"] .stElementContainer:has(.grow){flex:1 1 auto;min-height:0}
[class*="st-key-fill_"] .stElementContainer:has(.grow) div:has(.grow){height:100%}
.grow{height:100%;display:flex;flex-direction:column;min-height:0}
.grow .body{flex:1;min-height:0;display:flex;flex-direction:column}
.st-key-fill_table{height:calc(100vh - var(--table-top, 226px))!important}
.cell.s3 .big,.cell.s2 .big{font-size:clamp(1.05rem,1.5vw,1.6rem)}
/* league table */
.lt{width:100%;height:100%;border-collapse:collapse;font-size:clamp(10px,1.45vh,13px);line-height:1.05}
.lt th{font:600 .56rem 'Inter';letter-spacing:.14em;text-transform:uppercase;color:var(--faint);text-align:right;padding:0 5px 4px;border-bottom:1px solid var(--line)}
.lt td{padding:0 5px;text-align:right;color:var(--ink);border-bottom:1px solid var(--line);white-space:nowrap}
.lt th:nth-child(-n+2),.lt td:nth-child(-n+2){text-align:left}
.lt tr:last-child td{border-bottom:0}
.lt td.n{width:22px;color:var(--faint);border-left:3px solid transparent;padding-left:6px}
.lt tr.top td.n{border-left-color:var(--acc);color:var(--acc);font-weight:700}
.lt tr.rel td.n{border-left-color:var(--pk);color:var(--pk);font-weight:700}
.lt tr.me td{background:var(--chip);font-weight:700}
.lt td.p{font-family:'Anton',sans-serif;font-size:1.15em}
.lt td.gd{color:var(--mute)}
.zones{display:flex;gap:14px;font-size:.62rem;color:var(--mute);margin-top:6px}
.zones i{display:inline-block;width:8px;height:8px;border-radius:2px;margin-right:5px;vertical-align:-1px}
/* small stats grid */
.mini{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:10px}
.mini div{border-top:1px solid var(--line);padding-top:6px}
.mini small{display:block;font:600 .56rem 'Inter';letter-spacing:.14em;text-transform:uppercase;color:var(--mute)}
.mini b{font-family:'Anton',sans-serif;font-weight:400;font-size:1.15rem;color:var(--ink)}
/* predictor */
.vs{text-align:center;margin:2px 0 6px}
.vs .o{font:600 .58rem 'Inter';letter-spacing:.18em;text-transform:uppercase;color:var(--mute)}
.vs .w{font-family:'Anton',sans-serif;font-size:1.5rem;color:var(--pk);text-transform:uppercase;line-height:1.1}
.cmp{display:grid;grid-template-columns:1fr 2fr 1fr;align-items:center;gap:8px;padding:3px 0;border-bottom:1px solid var(--line);font-size:.74rem}
.cmp:last-child{border-bottom:0}
.cmp .a,.cmp .b{font-family:'Anton',sans-serif;font-size:1rem;color:var(--ink)}
.cmp .b{text-align:right}
.cmp .m{text-align:center;color:var(--mute);font-size:.6rem;letter-spacing:.14em;text-transform:uppercase}
.cmp .bar{display:flex;height:4px;margin-top:4px;border-radius:2px;overflow:hidden;background:var(--chip)}
.cmph{display:flex;justify-content:space-between;font:700 .62rem 'Inter';letter-spacing:.1em;text-transform:uppercase;margin:10px 0 2px}
/* results list */
.rl{display:flex;flex-direction:column;justify-content:space-between;height:100%}
.rl div{display:grid;grid-template-columns:22px 1fr auto;align-items:center;gap:8px;font-size:.76rem;border-bottom:1px solid var(--line);padding:3px 0;color:var(--ink)}
.rl div:last-child{border-bottom:0}
.rl em{font-style:normal;font-family:'Anton',sans-serif;font-size:.95rem}
.res{display:inline-block;width:20px;height:20px;line-height:20px;text-align:center;border-radius:3px;font:700 .62rem 'Inter';color:#fff}
.res.W{background:#16A34A}.res.D{background:#9B98A6}.res.L{background:var(--pk)}
.form{display:flex;gap:4px;margin-top:4px}
@media(max-width:1000px){.s2,.s3,.s4{grid-column:span 6}[class*="st-key-fill_"]{height:auto}}
</style>
"""


def _css():
    st.markdown(CSS + VIZ_CSS, unsafe_allow_html=True)


def _cell(cls, label, big, sub=""):
    return f'<div class="cell {cls}"><div class="lab">{label}</div><div class="big" title="{big}">{big}</div><div class="sub">{sub}</div></div>'


def _feat(label, big, sub, chips=()):
    wdl = "".join(f"<span>{c}</span>" for c in chips)
    return (f'<div class="cell feat s4"><div class="ball"></div><div class="lab">{label}</div><div class="big">{big}</div>'
            f'<div class="sub">{sub}</div><div class="wdl">{wdl}</div></div>')


def _grid(html):
    st.markdown(f'<div class="bento">{html}</div>', unsafe_allow_html=True)


def _fill(html):
    st.markdown(f'<div class="grow">{html}</div>', unsafe_allow_html=True)


def _ordinal(n):
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


# ── cached season data ────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def _league_table(season):
    tm = load_team_match()
    d = tm[tm["Season_Name"] == season]
    g = d.groupby("Team_Name").agg(P=("Result", "size"), W=("Result", lambda r: (r == "W").sum()),
                                   D=("Result", lambda r: (r == "D").sum()), L=("Result", lambda r: (r == "L").sum()),
                                   GF=("Goals_For", "sum"), GA=("Goals_Against", "sum"), Pts=("Points", "sum"))
    g["GD"] = g["GF"] - g["GA"]
    return g.sort_values(["Pts", "GD", "GF"], ascending=False).reset_index()


@st.cache_data(show_spinner=False)
def _season_story(season):
    t = _league_table(season)
    fm = load_fact_match()
    m = fm[fm["Season_Name"] == season].copy()
    m["Margin"] = (m["Home_Goals"] - m["Away_Goals"]).abs()
    big = m.sort_values(["Margin", "Home_Goals"], ascending=False).iloc[0]
    fp = load_player_perf()
    sc = fp[fp["Season_Name"] == season].groupby(["Player_Name", "Team_Name"])["Goals"].sum().sort_values(ascending=False)
    return {"table": t, "champ": t.iloc[0], "runner": t.iloc[1],
            "attack": t.sort_values("GF", ascending=False).iloc[0], "defence": t.sort_values("GA").iloc[0],
            "scorer": (sc.index[0][0], sc.index[0][1], int(sc.iloc[0])), "big": big,
            "gpm": (m["Home_Goals"] + m["Away_Goals"]).mean()}


@st.cache_data(show_spinner=False)
def _all_time():
    fm = load_fact_match().assign(G=lambda d: d["Home_Goals"] + d["Away_Goals"])
    ps = fm.groupby(["Season_ID", "Season_Name"])["G"].mean().reset_index(name="GPM")
    return {"per_season": ps, "matches": len(fm), "goals": int(fm["G"].sum()),
            "home": (fm["Match_Result"] == "H").mean(), "avg_gpm": fm["G"].mean(), "crowd": int(fm["Attendance"].mean())}


def _table_html(t, highlight=None, rows=None, zones=True):
    n = len(t)
    t = t if rows is None else t.iloc[rows[0]:rows[1]]
    body = ""
    for r in t.itertuples():
        pos = r.Index + 1
        cls = ("top " if zones and pos <= 4 else "") + ("rel " if zones and pos > n - 3 else "") + ("me" if r.Team_Name == highlight else "")
        body += (f'<tr class="{cls}"><td class="n">{pos}</td><td>{r.Team_Name}</td><td>{r.P}</td><td>{r.W}</td><td>{r.D}</td>'
                 f'<td>{r.L}</td><td class="gd">{r.GD:+d}</td><td class="p">{r.Pts}</td></tr>')
    return ('<table class="lt"><tr><th></th><th>Club</th><th>P</th><th>W</th><th>D</th><th>L</th><th>GD</th><th>Pts</th></tr>'
            f"{body}</table>")


def _seasons():
    return sorted(load_team_match()["Season_Name"].unique(), reverse=True)


# ── 1. DASHBOARD ──────────────────────────────────────────────────────────────
def render_user_dashboard(slot):
    _css()
    with slot:
        season = st.selectbox("Season", _seasons(), key="dash_season")
    s = _season_story(season)
    c, r = s["champ"], s["runner"]
    gap = int(c.Pts - r.Pts)
    big = s["big"]
    left, right = st.columns([8, 4], gap="small")
    with left:
        _grid(
            _feat(f"Champions <em>{season}</em>", c.Team_Name,
                  f"<b>{c.Pts} points</b> · " + (f"{gap} clear of {r.Team_Name}" if gap else f"level with {r.Team_Name}, ahead on goal difference"),
                  (f"{c.W} won", f"{c.D} drawn", f"{c.L} lost"))
            + _cell("s2", "Top scorer", s["scorer"][0], f"<b>{s['scorer'][2]} goals</b> · {s['scorer'][1]}")
            + _cell("s2", "Best attack", s["attack"].Team_Name, f"<b>{s['attack'].GF} scored</b>")
            + _cell("s2", "Best defence", s["defence"].Team_Name, f"<b>{s['defence'].GA} conceded</b>")
            + _cell("s2", "Biggest win", f"{big.Home_Goals}–{big.Away_Goals}", f"<b>{big.Home_Team_Name}</b> v {big.Away_Team_Name}")
        )
        c2, c3 = st.columns([5, 4], gap="small")
        with c2, st.container(key="fill_trend"):
            a = _all_time()
            ps = a["per_season"]
            hi = int(ps.index[ps["Season_Name"] == season][0])
            _fill(f'<div class="ch"><b>Goals per match</b><span>every season</span></div>'
                  f'<div class="body">{bars(ps["GPM"].tolist(), ps["Season_Name"].tolist(), hi=hi, avg=a["avg_gpm"], avg_label="27-season avg")}</div>'
                  f'<div class="note">Average goals in one match, one bar per season. <b>{season}</b> is highlighted at <b>{s["gpm"]:.2f}</b>.</div>'
                  f'<div class="mini"><div><small>Matches</small><b>{a["matches"]:,}</b></div><div><small>Goals</small><b>{a["goals"]:,}</b></div>'
                  f'<div><small>Home side wins</small><b>{a["home"]:.0%}</b></div><div><small>Average crowd</small><b>{a["crowd"]:,}</b></div></div>')
        with c3, st.container(key="fill_pred"):
            _predictor(season)

    with right, st.container(key="fill_table"):
        _fill(f'<div class="ch"><b>League table</b><span>{season}</span></div><div class="body">{_table_html(s["table"])}</div>'
              '<div class="zones"><span><i style="background:var(--acc)"></i>Champions League</span>'
              '<span><i style="background:var(--pk)"></i>Relegated</span></div>')


def _predictor(season):
    from utils.models import PREMATCH_FEATURES, get_classification_model  # heavy: load only when needed

    res = get_classification_model("pre_match", "chronological", 4)
    fx = res["test_df"]
    fx = fx[fx["Is_Home"] == 1].dropna(subset=PREMATCH_FEATURES)
    st.markdown('<div class="ch"><b>Predict a match</b><span>from recent form</span></div>', unsafe_allow_html=True)
    if fx.empty:
        st.caption("No fixtures with pre-match form available.")
        return
    avail = sorted(fx["Season_Name"].unique(), reverse=True)
    use = season if season in avail else avail[0]
    s = fx[fx["Season_Name"] == use]
    home = st.selectbox("Home team", sorted(s["Team_Name"].unique()), key=f"pr_home_{use}")
    away = st.selectbox("Away team", sorted(s[s["Team_Name"] == home]["Opp_Team_Name"].dropna().unique()), key=f"pr_away_{use}")
    row = s[(s["Team_Name"] == home) & (s["Opp_Team_Name"] == away)].iloc[0]
    p = dict(zip(res["classes"], res["nb_model"].predict_proba(pd.DataFrame([row[PREMATCH_FEATURES]]))[0]))
    w, d, l = (p.get(k, 0) for k in ("W", "D", "L"))
    verdict = f"{home} win" if w >= max(d, l) else (f"{away} win" if l >= d else "Draw")
    note = "" if use == season else f'<div class="note">Uses {use} fixtures, the seasons the model was tested on.</div>'
    st.markdown(
        f'<div class="vs"><div class="o">Most likely</div><div class="w">{verdict}</div></div>'
        + stack([("Home win", round(w * 100), "var(--acc)"), ("Draw", round(d * 100), "#9B98A6"), ("Away win", round(l * 100), PK)], fmt="{}%")
        + f'<div class="cmph"><span style="color:var(--acc)">{home}</span><span style="color:var(--pk)">{away}</span></div>'
        + "".join(f'<div class="cmp"><div class="a">{row[a]:.1f}</div><div class="m">{lab}</div><div class="b">{row[b]:.1f}</div></div>'
                  for lab, a, b in [("Points / game", "Form_Pts5", "Opp_Form_Pts5"), ("Scored / game", "Form_GF5", "Opp_Form_GF5"),
                                    ("Conceded / game", "Form_GA5", "Opp_Form_GA5")])
        + '<div class="note">Form is the average over each side\'s previous five matches.</div>' + note,
        unsafe_allow_html=True)


# ── 2. CLUBS ──────────────────────────────────────────────────────────────────
def _club_season(tm, team, season):
    d = tm[(tm["Team_Name"] == team) & (tm["Season_Name"] == season)].sort_values("Date_ID")
    return d, {"P": len(d), "W": int((d["Result"] == "W").sum()), "D": int((d["Result"] == "D").sum()),
               "L": int((d["Result"] == "L").sum()), "GF": int(d["Goals_For"].sum()), "GA": int(d["Goals_Against"].sum()),
               "Pts": int(d["Points"].sum()), "Poss": d["Possession"].mean() if len(d) else 0,
               "Shots": d["Shots"].mean() if len(d) else 0}


def render_user_clubs(slot):
    _css()
    tm = load_team_match()
    teams = sorted(tm["Team_Name"].unique())
    with slot:
        a, b, c = st.columns(3, gap="small")
        team = a.selectbox("Club", teams, key="cl_team")
        season = b.selectbox("Season", _seasons(), key="cl_season")
        rival = c.selectbox("Compare with", ["None"] + [x for x in teams if x != team], key="cl_rival")

    d, s = _club_season(tm, team, season)
    if d.empty:
        st.info(f"{team} did not play in {season}.")
        return
    table = _league_table(season)
    pos = int(table.index[table["Team_Name"] == team][0]) + 1
    rank = lambda col, asc=False: int(table[col].rank(ascending=asc, method="min")[table["Team_Name"] == team].iloc[0])
    _grid(
        _feat(f"{team} <em>{season}</em>", f"Finished {_ordinal(pos)}", f"<b>{s['Pts']} points</b> from {s['P']} games",
              (f"{s['W']} won", f"{s['D']} drawn", f"{s['L']} lost"))
        + _cell("s2", "Goals scored", s["GF"], f"<b>{_ordinal(rank('GF'))}</b> most in the league")
        + _cell("s2", "Goals conceded", s["GA"], f"<b>{_ordinal(rank('GA', True))}</b> fewest in the league")
        + _cell("s2", "Possession", f"{s['Poss']:.0f}%", "average share of the ball")
        + _cell("s2", "Shots per game", f"{s['Shots']:.1f}", f"<b>{s['GF'] / max(1, s['Shots'] * s['P']):.0%}</b> turned into goals")
    )

    c1, c2, c3 = st.columns([5, 4, 3], gap="small")
    with c1, st.container(key="fill_ctrend"):
        hist = tm[tm["Team_Name"] == team].groupby(["Season_ID", "Season_Name"])["Points"].sum().reset_index()
        hi = hist.index[hist["Season_Name"] == season]
        body = bars(hist["Points"].tolist(), hist["Season_Name"].tolist(), hi=int(hi[0]) if len(hi) else None,
                    avg=hist["Points"].mean(), fmt="{:.0f}", avg_label="club avg")
        extra = ""
        if rival != "None":
            rh = tm[tm["Team_Name"] == rival].groupby("Season_Name")["Points"].sum()
            extra = (f'<div class="note">{rival} averaged <b>{rh.mean():.0f}</b> points a season over {len(rh)} seasons; '
                     f'{team} averaged <b>{hist["Points"].mean():.0f}</b>.</div>')
        _fill(f'<div class="ch"><b>Points every season</b><span>{team}</span></div><div class="body">{body}</div>'
              f'<div class="note"><b>{season}</b> highlighted. The dashed line is the club\'s own average.</div>{extra}')

    with c2, st.container(key="fill_results"):
        fm = load_fact_match().set_index("Match_ID")
        last = d.tail(10).iloc[::-1]
        rows = "".join(
            f'<div><span class="res {r.Result}">{r.Result}</span>'
            f'<span>{"v" if r.Is_Home else "at"} {fm.loc[r.Match_ID, "Away_Team_Name" if r.Is_Home else "Home_Team_Name"]}</span>'
            f'<em>{r.Goals_For}–{r.Goals_Against}</em></div>' for r in last.itertuples())
        _fill(f'<div class="ch"><b>Last 10 results</b><span>{season}</span></div><div class="body"><div class="rl">{rows}</div></div>'
              '<div class="note">"v" = at home, "at" = away. Score shown from this club\'s side.</div>')

    with c3, st.container(key="fill_side"):
        if rival == "None":
            lo = max(0, min(pos - 4, len(table) - 7))
            _fill(f'<div class="ch"><b>Around them</b><span>table</span></div>'
                  f'<div class="body">{_table_html(table, highlight=team, rows=(lo, lo + 7))}</div>'
                  '<div class="note">Pick a club in "Compare with" for a head-to-head.</div>')
        else:
            rd, rs = _club_season(tm, rival, season)
            if rd.empty:
                _fill(f'<div class="ch"><b>Head to head</b><span>{season}</span></div><div class="note">{rival} did not play in {season}.</div>')
            else:
                def line(label, x, y, fmt="{:.0f}"):
                    tot = (x + y) or 1
                    return (f'<div class="cmp"><div class="a">{fmt.format(x)}</div><div class="m">{label}'
                            f'<div class="bar"><div style="flex:{x / tot:.3f};background:var(--acc)"></div>'
                            f'<div style="flex:{y / tot:.3f};background:var(--pk)"></div></div></div><div class="b">{fmt.format(y)}</div></div>')
                meet = d[d["Opp_ID"].isin(rd["Team_ID"].unique())]
                form = "".join(f'<span class="res {x}">{x}</span>' for x in meet["Result"])
                _fill(f'<div class="ch"><b>Head to head</b><span>{season}</span></div>'
                      f'<div class="cmph"><span style="color:var(--acc)">{team}</span><span style="color:var(--pk)">{rival}</span></div>'
                      '<div class="body">' + "".join([
                          line("Points", s["Pts"], rs["Pts"]), line("Wins", s["W"], rs["W"]), line("Scored", s["GF"], rs["GF"]),
                          line("Conceded", s["GA"], rs["GA"]), line("Shots / game", s["Shots"], rs["Shots"], "{:.1f}"),
                          line("Possession %", s["Poss"], rs["Poss"])]) + "</div>"
                      + (f'<div class="note">{team} when they met:</div><div class="form">{form}</div>' if form else ""))


# ── 3. PLAYERS ────────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def _season_players(season):
    """Per-season slices and rankings, computed once per season and shared (read-only)."""
    fp = load_player_perf()
    fs = fp[fp["Season_Name"] == season].merge(load_fact_match()[["Match_ID", "Date"]], on="Match_ID")
    per = (fs.groupby(["Player_ID", "Player_Name", "Team_Name"])
           .agg(Min=("Minutes", "sum"), G=("Goals", "sum"), A=("Assists", "sum")).reset_index())
    by_club = {c: g.sort_values("Min", ascending=False)["Player_ID"].tolist() for c, g in per.groupby("Team_Name")}
    names = dict(zip(per["Player_ID"], per["Player_Name"]))
    labels = {i: f"{n} · {t}" for i, n, t in zip(per["Player_ID"], per["Player_Name"], per["Team_Name"])}
    ranked = per.sort_values(["G", "A"], ascending=False)
    return {"fs": fs, "by_club": by_club, "names": names, "labels": labels, "top": ranked["Player_ID"].head(200).tolist(),
            "scorers": ranked.head(12), "rank": per.set_index("Player_ID")["G"].rank(ascending=False, method="min")}


def _player_season(fs, pid):
    p = fs[fs["Player_ID"] == pid]
    mins = int(p["Minutes"].sum())
    per90 = lambda v: v / mins * 90 if mins else 0
    return p, {"Apps": p["Match_ID"].nunique(), "Mins": mins, "Goals": int(p["Goals"].sum()), "Assists": int(p["Assists"].sum()),
               "Shots": int(p["Shots"].sum()), "Yellow": int(p["Yellow"].sum()), "Red": int(p["Red"].sum()),
               "G90": per90(p["Goals"].sum()), "A90": per90(p["Assists"].sum()), "S90": per90(p["Shots"].sum())}


def render_user_players(slot):
    _css()
    with slot:
        a, b, c, e = st.columns(4, gap="small")
        season = a.selectbox("Season", _seasons(), key="pl_season")
        sp = _season_players(season)
        fs = sp["fs"]
        club = b.selectbox("Club", sorted(sp["by_club"]), key="pl_club")
        pid = c.selectbox("Player", sp["by_club"][club], key=f"pl_id_{season}_{club}", format_func=sp["names"].get)
        rival_id = e.selectbox("Compare with", [0] + [i for i in sp["top"] if i != pid], key=f"pl_rival_{season}",
                               format_func=lambda i: "None" if i == 0 else sp["labels"][i])
    name = sp["names"][pid]
    rival = "None" if rival_id == 0 else sp["labels"][rival_id]

    p, s = _player_season(fs, pid)
    pos = p["Position_Name"].iloc[0] if not p.empty else "—"
    rk = int(sp["rank"].get(pid, 0)) if s["Goals"] else None
    _grid(
        _feat(f"{club} · {pos}", name, f"<b>{s['Goals']} goals</b> and <b>{s['Assists']} assists</b> in {season}",
              (f"{s['Apps']} games", f"{s['Mins']:,} minutes", f"#{rk} scorer" if rk else "no goals"))
        + _cell("s2", "Goals per 90 min", f"{s['G90']:.2f}", "goals per full match played")
        + _cell("s2", "Shots", s["Shots"], f"<b>{s['Goals'] / max(1, s['Shots']):.0%}</b> scored")
        + _cell("s2", "Minutes per goal", f"{s['Mins'] // s['Goals']:,}" if s["Goals"] else "—", "lower is better")
        + _cell("s2", "Cards", f"{s['Yellow']} · {s['Red']}", "yellow · red")
    )

    c1, c2 = st.columns([7, 5], gap="small")
    with c1, st.container(key="fill_pout"):
        if rival == "None":
            m = p.sort_values("Date")
            cum = (m["Goals"] + m["Assists"]).cumsum().tolist() or [0]
            labels = [f"Game {i}" for i in range(1, len(cum) + 1)]
            _fill(f'<div class="ch"><b>Goals + assists, building up</b><span>{name}</span></div>'
                  f'<div class="body">{bars(cum, labels, hi=len(cum) - 1, fmt="{:.0f}")}</div>'
                  '<div class="note">Running total after each appearance. Pick a player in "Compare with" to compare per 90 minutes.</div>')
        else:
            _, r = _player_season(fs, rival_id)
            rows = lambda x: [("Goals / 90", x["G90"]), ("Assists / 90", x["A90"]), ("Shots / 90", x["S90"])]
            _fill(f'<div class="ch"><b>Per 90 minutes</b><span>{season}</span></div><div class="body" style="justify-content:space-around">'
                  f'<div><div class="cmph"><span style="color:var(--acc)">{name}</span></div>{hrows(rows(s), "{:.2f}")}</div>'
                  f'<div><div class="cmph"><span style="color:var(--pk)">{rival}</span></div>{hrows(rows(r), "{:.2f}", PK)}</div></div>'
                  '<div class="note">Per-90 rates put players with different minutes on the same footing.</div>')

    with c2, st.container(key="fill_scorers"):
        rows = "".join(
            f'<tr class="{"me" if r.Player_ID == pid else ""}"><td class="n">{i + 1}</td><td>{r.Player_Name}</td>'
            f'<td class="gd">{r.Team_Name}</td><td>{r.A}</td><td class="p">{r.G}</td></tr>'
            for i, r in enumerate(sp["scorers"].itertuples()))
        _fill(f'<div class="ch"><b>Top scorers</b><span>{season}</span></div><div class="body"><table class="lt"><tr><th></th><th>Player</th>'
              f'<th>Club</th><th>Ast</th><th>Goals</th></tr>{rows}</table></div>')
