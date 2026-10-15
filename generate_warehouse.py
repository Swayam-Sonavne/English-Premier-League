"""Builds epl_dw.db: synthetic EPL warehouse (6 dims + snowflake dims, 3 facts).
Synthetic data with hidden team strength so mining labs find real patterns."""
import numpy as np, pandas as pd, sqlite3, os
rng = np.random.default_rng(42)
T = [("Arsenal","London","Emirates Stadium",60000),("Aston Villa","Birmingham","Villa Park",42000),
("Brentford","London","Gtech Stadium",17000),("Brighton","Brighton","Amex Stadium",31000),
("Burnley","Burnley","Turf Moor",21900),("Chelsea","London","Stamford Bridge",40000),
("Crystal Palace","London","Selhurst Park",25000),("Everton","Liverpool","Goodison Park",39500),
("Fulham","London","Craven Cottage",29000),("Leeds","Leeds","Elland Road",37700),
("Leicester","Leicester","King Power Stadium",32000),("Liverpool","Liverpool","Anfield",61000),
("Man City","Manchester","Etihad Stadium",53400),("Man United","Manchester","Old Trafford",74000),
("Newcastle","Newcastle","St James Park",52300),("Nottm Forest","Nottingham","City Ground",30400),
("Southampton","Southampton","St Marys",32000),("Spurs","London","Tottenham Stadium",62000),
("West Ham","London","London Stadium",62500),("Wolves","Wolverhampton","Molineux",32000)]
FN = "James Liam Noah Oliver Jack Harry Leo Mateo Ravi Omar Luca Ben Sam Theo Kai Diego Jon Ali Marco Finn".split()
LN = "Smith Jones Silva Khan Brown Taylor Santos Murphy Wilson Evans Garcia Rossi Novak Okafor Diaz Hughes Clarke".split()
NAT = ["England","France","Spain","Brazil","Portugal","Ireland","Nigeria","Germany","Argentina","Netherlands"]
POS = [1]*2 + [2]*8 + [3]*8 + [4]*4            # 22-man squad: GK, DEF, MID, FWD
pidx = np.array(POS) - 1
wg, ws, wa = np.array([0,.1,.35,1.]), np.array([0,.2,.6,1.]), np.array([0,.15,.7,.5])
N = 20; base = rng.normal(0, .6, N); base[[0,5,11,12,13,17]] += .9   # big clubs stronger
M, TM, P, players, roster = [], [], [], [], {}
mid = 0; nxt = 1
for si, y in enumerate(range(1999, 2026)):                 # 27 seasons x 380 = 10,260 matches
    sid = si + 1; st = base + rng.normal(0, .4, N)         # season-specific strength
    for t in range(N):
        ids = np.arange(nxt, nxt + 22); nxt += 22; roster[(t, si)] = ids
        for i, p in zip(ids, POS):
            players.append((int(i), f"{rng.choice(FN)} {rng.choice(LN)}", p, rng.choice(NAT)))
    pairs = [(h, a) for h in range(N) for a in range(N) if h != a]; rng.shuffle(pairs)
    for k, (h, a) in enumerate(pairs):
        mid += 1
        dt = pd.Timestamp(y, 8, 10) + pd.Timedelta(days=7*(k//10) + int(rng.integers(0, 3)))
        did = int(dt.strftime("%Y%m%d"))
        # chain: strength -> possession -> shots -> corners -> goals -> result (+ noise at every step)
        ph = int(np.clip(50 + 5*(st[h]-st[a]) + 2 + rng.normal(0, 4), 28, 72)); poss = [ph, 100-ph]
        sh = [rng.poisson(max(4, 13.5 + 1.5*st[h] - .7*st[a] + .25*(ph-50))),
              rng.poisson(max(4, 11 + 1.5*st[a] - .7*st[h] + .25*(50-ph)))]
        co = [rng.poisson(max(1, 1.5 + .3*sh[0])), rng.poisson(max(1, 1.5 + .3*sh[1]))]
        g = [rng.poisson((.075*sh[i] + .07*co[i]) * np.exp(.07*(st[x]-st[y]))) for i, (x, y) in enumerate(((h, a), (a, h)))]
        fo = [rng.poisson(max(5, 11 - .06*(ph-50))), rng.poisson(max(5, 11 + .06*(ph-50)))]   # fouls: deliberately weak link
        res = "H" if g[0] > g[1] else "A" if g[0] < g[1] else "D"
        att = int(T[h][3] * np.clip(.8 + .06*st[h] + rng.normal(0, .06), .5, 1))
        M.append((mid, did, sid, h+1, a+1, h+1, int(rng.integers(1, 26)), g[0], g[1], att,
                  round(100*att/T[h][3], 1), res))
        for side, (tm, op) in enumerate(((h, a), (a, h))):
            gf, ga = g[side], g[1-side]; yc = rng.poisson(1.7); rc = int(rng.random() < .05)
            TM.append((mid, did, sid, tm+1, op+1, 1-side, gf, ga, sh[side], co[side],
                       fo[side], yc, rc, poss[side], 3 if gf > ga else int(gf == ga),
                       "W" if gf > ga else "D" if gf == ga else "L"))
            sel = np.concatenate(([rng.integers(0, 2)], rng.choice(np.arange(2, 22), 13, replace=False)))
            pi = pidx[sel]; r = np.zeros(14, int)
            if rc: r[rng.integers(14)] = 1
            mins = np.r_[np.full(11, 90), rng.integers(10, 40, 3)]
            P.append(np.column_stack([np.full(14, mid), np.full(14, did), np.full(14, sid), roster[(tm, si)][sel],
                np.full(14, tm+1), mins, rng.multinomial(gf, wg[pi]/wg[pi].sum()),
                rng.multinomial(int(round(gf*.75)), wa[pi]/wa[pi].sum()),
                rng.multinomial(sh[side], ws[pi]/ws[pi].sum()), rng.multinomial(yc, np.ones(14)/14), r]))

fm = pd.DataFrame(M, columns="Match_ID Date_ID Season_ID Home_Team_ID Away_Team_ID Stadium_ID Referee_ID Home_Goals Away_Goals Attendance Occupancy_Pct Match_Result".split())
tm = pd.DataFrame(TM, columns="Match_ID Date_ID Season_ID Team_ID Opp_ID Is_Home Goals_For Goals_Against Shots Corners Fouls Yellow Red Possession Points Result".split())
tm = tm.sort_values(["Team_ID", "Date_ID", "Match_ID"])
for c, n in [("Points","Form_Pts5"), ("Goals_For","Form_GF5"), ("Goals_Against","Form_GA5")]:
    tm[n] = tm.groupby("Team_ID")[c].transform(lambda s: s.shift(1).rolling(5, min_periods=1).mean())
tm = tm.fillna({"Form_Pts5": 1.4, "Form_GF5": 1.4, "Form_GA5": 1.4})
opp = tm[["Match_ID","Team_ID","Form_Pts5","Form_GF5","Form_GA5"]]
opp.columns = ["Match_ID","Opp_ID","Opp_Form_Pts5","Opp_Form_GF5","Opp_Form_GA5"]
tm = tm.merge(opp, on=["Match_ID", "Opp_ID"]).sort_values(["Match_ID", "Is_Home"], ascending=[True, False])
tm.insert(0, "Team_Match_ID", range(1, len(tm)+1))
fp = pd.DataFrame(np.vstack(P), columns="Match_ID Date_ID Season_ID Player_ID Team_ID Minutes Goals Assists Shots Yellow Red".split())
fp.insert(0, "Perf_ID", range(1, len(fp)+1))
dd = pd.to_datetime(sorted(fm.Date_ID.unique()), format="%Y%m%d")
dim_date = pd.DataFrame({"Date_ID": dd.strftime("%Y%m%d").astype(int), "Date": dd.strftime("%Y-%m-%d"), "Day": dd.day,
    "Month": dd.month, "Month_Name": dd.strftime("%B"), "Quarter": dd.quarter, "Year": dd.year, "Day_of_Week": dd.strftime("%A")})
cities = sorted({t[1] for t in T}); cid = {c: i+1 for i, c in enumerate(cities)}
tables = {
 "Dim_Date": dim_date,
 "Dim_Season": pd.DataFrame({"Season_ID": range(1, 28), "Season_Name": [f"{y}/{str(y+1)[2:]}" for y in range(1999, 2026)],
                             "Start_Year": range(1999, 2026), "End_Year": range(2000, 2027)}),
 "Dim_Team": pd.DataFrame({"Team_ID": range(1, 21), "Team_Name": [t[0] for t in T], "City_ID": [cid[t[1]] for t in T]}),
 "Dim_Stadium": pd.DataFrame({"Stadium_ID": range(1, 21), "Stadium_Name": [t[2] for t in T], "City_ID": [cid[t[1]] for t in T],
                              "Capacity": [t[3] for t in T]}),
 "Dim_City": pd.DataFrame({"City_ID": cid.values(), "City_Name": cid.keys()}),
 "Dim_Referee": pd.DataFrame({"Referee_ID": range(1, 26), "Referee_Name": [f"Referee {i}" for i in range(1, 26)]}),
 "Dim_Player": pd.DataFrame(players, columns=["Player_ID", "Player_Name", "Position_ID", "Nationality"]),
 "Dim_Position": pd.DataFrame({"Position_ID": [1,2,3,4], "Position_Name": ["Goalkeeper","Defender","Midfielder","Forward"]}),
 "Fact_Match": fm, "Fact_Team_Match": tm, "Fact_Player_Performance": fp}
if os.path.exists("epl_dw.db"): os.remove("epl_dw.db")
with sqlite3.connect("epl_dw.db") as con:
    for n, d in tables.items():
        d.to_sql(n, con, index=False); print(f"{n:26s}{len(d):>9,}")
