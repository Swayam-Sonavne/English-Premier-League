"""
landing.py — Scroll-story landing page with sign in / sign up.

Layout follows a long editorial scroll: dark hero (monochrome ball, liquid colour reveal
under the cursor), pinned statement, rotating 3D stadium, pinned DWM pipeline, horizontal
mining cards, the warehouse table list with a ball that sticks then shoots forward, a
"football basics" band for non-fans, and the auth card.

CSS scroll-driven animations handle most motion. A small script (injected through a
zero-height component) handles the liquid reveal, the three.js stadium and the ball trigger.
"""
import hashlib
import hmac
import json
import os
import secrets
import sqlite3

import streamlit as st
import streamlit.components.v1 as components

ROOT = os.path.dirname(os.path.dirname(__file__))
USERS_FILE = os.path.join(ROOT, "users.json")
STATIC = os.path.join(ROOT, "static")
DB = os.path.join(ROOT, "epl_dw.db")


# ── local user store (salted PBKDF2) ──────────────────────────────────────────
def _load_users():
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _hash(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 120_000).hex()


def register_user(username, password):
    users = _load_users()
    if username in users or username in ("user", "admin"):
        return False, "That username is already taken."
    salt = secrets.token_hex(16)
    users[username] = {"salt": salt, "hash": _hash(password, salt), "role": "user"}
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)
    return True, ""


def check_login(username, password, workspace):
    """Return role or None. Demo accounts user/user and admin/admin always work."""
    if (username, password) == ("user", "user") and workspace == "User":
        return "user"
    if (username, password) == ("admin", "admin") and workspace == "Admin":
        return "admin"
    rec = _load_users().get(username)
    if rec and workspace == "User" and hmac.compare_digest(rec["hash"], _hash(password, rec["salt"])):
        return rec["role"]
    return None


# ── data ──────────────────────────────────────────────────────────────────────
@st.cache_data
def _facts():
    con = sqlite3.connect(DB)
    q = lambda s: con.execute(s).fetchall()
    clubs = q("select t.Team_Name, c.City_Name from Dim_Team t join Dim_City c using(City_ID) order by t.Team_Name")
    tables = [(n, q(f"select count(*) from {n}")[0][0]) for n in (
        "Fact_Match", "Fact_Team_Match", "Fact_Player_Performance", "Dim_Date", "Dim_Season", "Dim_Team",
        "Dim_Player", "Dim_Position", "Dim_Stadium", "Dim_City", "Dim_Referee")]
    res = dict(q("select Match_Result, round(count(*)*100.0/(select count(*) from Fact_Match),1) from Fact_Match group by 1"))
    goals, avg_goals = q("select sum(Home_Goals+Away_Goals), round(avg(Home_Goals+Away_Goals),2) from Fact_Match")[0]
    con.close()
    return {"clubs": clubs, "tables": tables, "res": res, "goals": goals, "avg_goals": avg_goals}


CLUB_COLOURS = {
    "Arsenal": "#EF0107", "Aston Villa": "#95BFE5", "Brentford": "#E30613", "Brighton": "#0057B8",
    "Burnley": "#6C1D45", "Chelsea": "#034694", "Crystal Palace": "#1B458F", "Everton": "#003399",
    "Fulham": "#111111", "Leeds": "#FFCD00", "Leicester": "#003090", "Liverpool": "#C8102E",
    "Man City": "#6CABDD", "Man United": "#DA291C", "Newcastle": "#241F20", "Nottm Forest": "#DD0000",
    "Southampton": "#D71920", "Spurs": "#132257", "West Ham": "#7A263A", "Wolves": "#FDB913",
}

TABLE_NOTES = {
    "Fact_Match": "One row per match: score, attendance, referee.",
    "Fact_Team_Match": "Each match seen from both teams: shots, possession, points.",
    "Fact_Player_Performance": "Every player in every match: minutes, goals, assists.",
    "Dim_Date": "Calendar details for each match day.",
    "Dim_Season": "The 27 seasons, 1999/00 to 2025/26.",
    "Dim_Team": "The 20 clubs.",
    "Dim_Player": "Every player who appears in the data.",
    "Dim_Position": "Goalkeeper, defender, midfielder, forward.",
    "Dim_Stadium": "Home ground of each club.",
    "Dim_City": "The city each club plays in.",
    "Dim_Referee": "Match officials.",
}

PIPELINE = [
    ("Collect", "Every result, shot and card since 1999/00."),
    ("Organise", "Arranged into fact and dimension tables."),
    ("Summarise", "Zoom from whole seasons down to one match."),
    ("Discover", "Models predict results and spot patterns."),
]

MINING = [
    ("Classification", "Decision Tree · Naive Bayes · Logistic",
     "Predicts Win, Draw or Loss from recent form and match stats.",
     "Predicting pass or fail from attendance and homework."),
    ("Clustering", "K-Means · Hierarchical",
     "Groups clubs with similar playing styles, without being told the groups.",
     "Sorting students into study groups by habits."),
    ("Regression", "Linear regression",
     "Measures how much shots, possession or fouls change the goals scored.",
     "How many marks does each extra hour of study add?"),
    ("Association", "Apriori",
     "Finds things that tend to happen together, such as many shots and a win.",
     "Shoppers who buy bread often buy butter."),
    ("OLAP", "Roll-up · Drill-down · Slice · Dice · Pivot",
     "Interactive summaries of goals, points and attendance at any level.",
     "A pivot table in Excel, but over 27 seasons."),
    ("Warehouse", "3 facts · 8 dimensions",
     "The star schema itself, browsable table by table.",
     "The filing cabinet everything else reads from."),
]

STATS = [("27", "seasons"), ("10,260", "matches"), ("27,139", "goals")]
STATEMENT_TAIL = ("Every goal, shot and card on record.", "One question:", "what really wins games?")


CSS = r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Anton&family=Inter:wght@400;500;600;700&display=swap');
:root{--ink:#09080D;--paper:#F3F2F6;--pk:#FF3E8E;--cy:#3CD3EE;--pu:#3A1B7A;--mute:rgba(255,255,255,.58);--mute-d:rgba(9,8,13,.55)}
html,body,.stApp{background:var(--ink)!important;margin:0!important}
[data-stale="true"]{opacity:0!important;transition:none!important;pointer-events:none!important}
.st-key-topbar [data-stale="true"]{display:none!important}
[data-testid="stHeader"],[data-testid="stSidebar"],[data-testid="stToolbar"],[data-testid="stDecoration"],footer{display:none!important}
.block-container{padding:0!important;max-width:100%!important}
[data-testid="stMainBlockContainer"] [data-testid="stVerticalBlock"]{gap:0!important}
[data-testid="stMarkdownContainer"]{width:100%}
.stElementContainer:has(iframe[height="0"]){display:none}
section.stMain{scroll-timeline:--pg block}
.lp,.lp *{box-sizing:border-box}
.lp{font-family:'Inter',sans-serif;color:#fff;position:relative}
.lp .an{font-family:'Anton',sans-serif;text-transform:uppercase;font-weight:400;line-height:.92;letter-spacing:.005em}
.lp a{text-decoration:none!important}
.lines{position:absolute;inset:0;pointer-events:none;z-index:0;
  background-image:repeating-linear-gradient(90deg,transparent 0,transparent calc(100%/7 - 1px),var(--ln) calc(100%/7 - 1px),var(--ln) calc(100%/7))}
.dark{background:var(--ink);--ln:rgba(255,255,255,.07)}
.light{background:var(--paper);color:var(--ink);--ln:rgba(9,8,13,.07)}
.bf{background:url(/app/static/ball_front.webp) center/contain no-repeat}
.bs{background:url(/app/static/ball_side.webp) center/contain no-repeat}

/* nav */
.nv{position:fixed;z-index:80;top:16px;left:16px;right:16px;display:flex;justify-content:space-between;align-items:center;pointer-events:none}
.nv>*{pointer-events:auto}
.nv-logo{display:flex;align-items:center;gap:10px;background:rgba(9,8,13,.72);backdrop-filter:blur(10px);padding:8px 16px 8px 8px;border-radius:40px}
.nv-logo i{width:30px;height:30px;display:block;animation:spin 8s linear infinite}
.nv-logo b{font-family:'Anton';font-weight:400;font-size:1.25rem;letter-spacing:.06em;color:#fff}
.nv-logo b em{font-style:normal;color:var(--pk)}
.nv nav{display:flex;gap:4px;background:rgba(9,8,13,.72);backdrop-filter:blur(10px);padding:6px;border-radius:40px}
.nv nav a{color:#fff!important;font-size:.72rem;letter-spacing:.16em;text-transform:uppercase;padding:9px 14px;border-radius:30px;transition:background .2s}
.nv nav a:hover{background:rgba(255,255,255,.1)}
.nv nav a.go{background:var(--pk);font-weight:700}
@keyframes spin{to{transform:rotate(360deg)}}

/* 1 hero */
.hero{position:relative;height:100vh;min-height:640px;overflow:clip;cursor:crosshair}
.hero-media{position:absolute;inset:0;z-index:1}
.hero-media img{position:absolute;width:min(92vh,62vw);aspect-ratio:1;left:50%;top:52%;margin:calc(min(92vh,62vw)/-2) 0 0 calc(min(92vh,62vw)/-2);
  filter:grayscale(1) contrast(1.1) brightness(.78);animation:heroIn 1.6s cubic-bezier(.2,.8,.2,1) both}
.hero-media canvas{position:absolute;inset:0;z-index:2;pointer-events:none}
.hero .lines{z-index:3}
.hero .num{position:absolute;z-index:4;left:50%;top:50%;transform:translate(-50%,-50%);font-size:clamp(110px,15vw,250px);
  color:#fff;animation:numIn 1.2s .3s cubic-bezier(.2,.8,.2,1) both;mix-blend-mode:difference}
.hero .stl,.hero .str{position:absolute;z-index:5;top:30%;font-size:.78rem;color:var(--mute)}
.hero .stl{left:24px}.hero .str{right:24px;text-align:right;max-width:200px}
.hero .stl div,.hero .str div{margin-bottom:20px;animation:up .9s both}
.hero .stl div:nth-child(2),.hero .str div:nth-child(2){animation-delay:.12s}
.hero .stl div:nth-child(3),.hero .str div:nth-child(3){animation-delay:.24s}
.hero .stl,.hero .str,.hero .title,.hero .nxt{text-shadow:0 2px 18px rgba(0,0,0,.7)}
.hero .stl b,.hero .str b{display:block;font-family:'Anton';font-weight:400;font-size:1.7rem;line-height:1;color:#fff}
.hero .str p{font-size:.85rem;color:#fff;margin:0;line-height:1.35}
.hero .title{position:absolute;z-index:5;left:24px;bottom:36px;max-width:430px;animation:up 1s .4s both}
.hero .title .h1{font-family:'Anton';font-weight:400;font-size:clamp(34px,4.2vw,62px);line-height:.92;margin:0 0 12px;color:#fff;text-transform:uppercase;padding:0}
.hero .title p{margin:0;color:var(--mute);font-size:.88rem;line-height:1.5}
.hero .nxt{position:absolute;z-index:5;right:24px;bottom:36px;text-align:right;font-size:.75rem;color:var(--mute);animation:up 1s .5s both}
.hero .nxt b{display:block;font-family:'Anton';font-weight:400;font-size:1.5rem;color:#fff}
.hero .hint{position:absolute;z-index:5;left:50%;bottom:30px;transform:translateX(-50%);font-size:.66rem;letter-spacing:.32em;color:#fff;opacity:.8}
.hero .hint::after{content:'';display:block;width:1px;height:34px;background:#fff;margin:10px auto 0;animation:drip 1.8s infinite}
@keyframes heroIn{from{opacity:0;transform:scale(.85) rotate(-25deg)}}
@keyframes numIn{from{opacity:0;transform:translate(-50%,-38%) scale(.9)}}
@keyframes up{from{opacity:0;transform:translateY(30px)}}
@keyframes drip{0%{transform:scaleY(0);transform-origin:top}50%{transform:scaleY(1);transform-origin:top}51%{transform-origin:bottom}100%{transform:scaleY(0);transform-origin:bottom}}

/* 2 statement (pinned) */
.story{position:relative;height:260vh;view-timeline:--st block}
.story .pin{position:sticky;top:0;height:100vh;display:flex;align-items:center;justify-content:center;overflow:clip}
.story .stats{position:relative;z-index:2;display:flex;flex-direction:column;align-items:center;gap:.6vh;padding:0 24px}
.story .sl{display:flex;align-items:baseline;gap:.35em;font-family:'Anton',sans-serif;text-transform:uppercase;line-height:.95;
  font-size:clamp(48px,7.4vw,124px);color:rgba(9,8,13,.12)}
.story .sl b{font-weight:400;color:rgba(255,62,142,.2);font-variant-numeric:tabular-nums}
.story .sl span{font-size:.5em;letter-spacing:.02em}
.story .tail{margin:3.5vh 0 0;text-align:center;font:600 clamp(15px,1.35vw,21px) 'Inter';color:#3A3744;max-width:640px}
.story .tail em{display:block;font:400 clamp(28px,3vw,48px) 'Anton',sans-serif;text-transform:uppercase;color:var(--ink);font-style:normal;margin-top:6px}
.story .tail em i{font-style:normal;color:var(--pk)}
.story .fl{position:absolute;z-index:1;border-radius:4px;overflow:hidden;box-shadow:0 30px 60px rgba(9,8,13,.18)}
.story .fl1{left:5vw;top:56%;width:clamp(130px,14vw,210px);aspect-ratio:1;box-shadow:none;border-radius:50%;overflow:visible;filter:drop-shadow(0 30px 30px rgba(9,8,13,.25))}
.story .fl2{right:4vw;top:16%;width:clamp(170px,18vw,270px);background:#fff;padding:18px;color:var(--ink)}
.fl2 small{font-size:.66rem;letter-spacing:.18em;text-transform:uppercase;color:var(--mute-d)}
.fl2 .bar{display:flex;align-items:center;gap:10px;margin-top:12px;font-size:.78rem;font-weight:600}
.fl2 .bar i{display:block;height:10px;border-radius:5px}
.fl2 .bar span{width:44px}

/* 3 clubs + stadium */
.clubs{position:relative;padding:18vh 0 14vh;view-timeline:--cl block}
.clubs .hd{position:relative;z-index:2;text-align:center;padding:0 24px;margin-bottom:6vh}
.clubs .hd .h2{font-size:clamp(32px,4.2vw,64px);margin:0 0 14px}
.clubs .hd p{color:var(--mute-d);max-width:560px;margin:0 auto;line-height:1.55}
.cgrid{position:relative;z-index:2;display:grid;grid-template-columns:1fr 1fr 2.8fr 1fr 1fr}
.cgrid .col{display:flex;flex-direction:column}
.club{height:22vh;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;gap:6px;padding:0 8px}
.club b{font-family:'Anton';font-weight:400;font-size:clamp(15px,1.4vw,22px);text-transform:uppercase;color:var(--ink);transition:color .25s,transform .25s;line-height:1}
.club small{font-size:.62rem;letter-spacing:.2em;text-transform:uppercase;color:var(--mute-d)}
.club:hover b{color:var(--c);transform:scale(1.08)}
.cgrid .mid{position:relative}
.stad{position:sticky;top:12vh;height:76vh;display:flex;align-items:center;justify-content:center}
.stad canvas{width:100%!important;height:100%!important}
.stad .fallback{width:70%;aspect-ratio:1}
.stad .cap{position:absolute;bottom:2vh;left:0;right:0;text-align:center;font-size:.66rem;letter-spacing:.22em;text-transform:uppercase;color:var(--mute-d)}
.btn{display:inline-flex;align-items:center;gap:8px;background:var(--pk);color:#fff!important;font-family:'Anton';font-weight:400;text-transform:uppercase;letter-spacing:.06em;padding:12px 22px;font-size:1rem}
.btn:hover{background:#e52a78}
.clubs .cta{text-align:center;margin-top:4vh;position:relative;z-index:2}

/* 4 under the hood (subtle) */
.how{position:relative;padding:16vh 6vw}
.how .k{position:relative;z-index:2;font-size:.68rem;letter-spacing:.3em;color:var(--pk);margin-bottom:14px}
.how .t{position:relative;z-index:2;font-size:clamp(26px,3vw,44px);margin:0 0 7vh;max-width:620px;color:#fff}
.steps{position:relative;z-index:2;display:grid;grid-template-columns:repeat(4,1fr);border-top:1px solid rgba(255,255,255,.14)}
.step{padding:24px 20px 0 0;position:relative}
.step::before{content:'';position:absolute;top:-1px;left:0;height:1px;width:0;background:var(--pk);transition:width .6s}
.step:hover::before{width:100%}
.step span{font:600 .7rem 'Inter';letter-spacing:.2em;color:var(--mute)}
.step b{display:block;font-family:'Anton';font-weight:400;text-transform:uppercase;font-size:1.5rem;margin:10px 0 8px;color:#fff}
.step p{margin:0;font-size:.85rem;line-height:1.5;color:var(--mute);max-width:230px}

/* 5 mining (horizontal, pinned) */
.mine{position:relative;height:340vh;view-timeline:--mn block}
.mine .pin{position:sticky;top:0;height:100vh;overflow:clip;display:flex;flex-direction:column;justify-content:center;padding-top:64px}
.mine .ghost{position:absolute;top:50%;left:0;transform:translateY(-50%);white-space:nowrap;font-size:34vw;color:rgba(9,8,13,.045);z-index:0}
.mine .hd{position:relative;z-index:2;padding:0 6vw;margin-bottom:5vh;display:flex;justify-content:space-between;align-items:end;gap:24px}
.mine .hd .h2{font-size:clamp(32px,4vw,60px);margin:0}
.mine .hd p{max-width:380px;color:var(--mute-d);line-height:1.55;margin:0}
.track{position:relative;z-index:2;display:flex;gap:22px;padding:0 6vw;width:max-content}
.mcard{width:min(300px,74vw);height:44vh;min-height:300px;background:#fff;padding:22px;display:flex;flex-direction:column;border:1px solid rgba(9,8,13,.08);transition:transform .3s,box-shadow .3s}
.mcard:hover{transform:translateY(-8px);box-shadow:0 30px 60px rgba(58,27,122,.15)}
.mcard .n{font-family:'Anton';font-size:2.6rem;line-height:1;color:transparent;-webkit-text-stroke:1.5px var(--pu)}
.mcard .h4{font-family:'Anton';font-weight:400;text-transform:uppercase;font-size:1.45rem;margin:12px 0 4px;color:var(--ink);padding:0}
.mcard .k{font-size:.66rem;letter-spacing:.16em;text-transform:uppercase;color:var(--pk);font-weight:700;margin-bottom:16px}
.mcard p{font-size:.84rem;line-height:1.55;color:var(--mute-d);margin:0}
.mcard .eg{margin-top:auto;font-size:.85rem;color:var(--ink);background:var(--paper);padding:12px 14px;border-left:3px solid var(--pu)}
.mcard .eg b{display:block;font-size:.62rem;letter-spacing:.18em;text-transform:uppercase;color:var(--pu);margin-bottom:4px}

/* 6 warehouse with sticky ball */
.wh{position:relative;padding:14vh 0 22vh}
.wh .rail{position:absolute;inset:0;z-index:3;pointer-events:none}
.wh .rollball{position:sticky;top:calc(50vh - 14vh);margin:0 auto;width:28vh;height:28vh;transition:transform 1.1s cubic-bezier(.65,0,.35,1)}
.wh .rollball i{display:block;width:100%;height:100%;filter:drop-shadow(0 30px 40px rgba(0,0,0,.6));transition:transform 1.1s cubic-bezier(.65,0,.35,1)}
.wh.go .rollball{transform:translateY(110vh)}
.wh.go .rollball i{transform:rotate(540deg)}
.wh .rollball::before{content:'';position:absolute;left:50%;bottom:100%;width:6px;height:0;margin-left:-3px;background:linear-gradient(transparent,var(--pk));transition:height 1.1s}
.wh.go .rollball::before{height:60vh}
.wh .hd{position:relative;z-index:2;display:flex;justify-content:center;align-items:center;gap:calc(28vh + 2vw);padding:12vh 24px 14vh}
.wh .hd .h2{font-size:clamp(36px,4.6vw,76px);margin:0}
.rows{position:relative;z-index:2;padding:0 6vw}
.row{display:grid;grid-template-columns:1.3fr 1fr auto;align-items:end;gap:20px;padding:22px 0 14px;border-bottom:1px solid rgba(255,255,255,.18)}
.row .h5{font-family:'Anton';font-weight:400;font-size:clamp(17px,1.6vw,24px);margin:0;color:#fff;text-transform:uppercase;padding:0;line-height:1}
.row .h5 span{font:700 .6rem 'Inter';letter-spacing:.16em;vertical-align:middle;margin-left:12px;padding:4px 8px;border-radius:2px;background:var(--pu)}
.row .h5 span.f{background:var(--pk)}
.row p{margin:0;color:var(--mute);font-size:.82rem;text-align:right}
.row .c{font-family:'Anton';font-size:1.2rem;color:#fff;min-width:110px;text-align:right}

/* 7 basics band */
.basics{position:relative;padding:0 0 14vh}
.stripes{height:24vh;background:repeating-linear-gradient(90deg,#e6e4ec 0 7vw,#f3f2f6 7vw 14vw);
  -webkit-mask-image:linear-gradient(180deg,#000,transparent);mask-image:linear-gradient(180deg,#000,transparent)}
.basics .hd{text-align:center;padding:4vh 24px 6vh;position:relative;z-index:2}
.basics .hd .h2{font-size:clamp(32px,4vw,60px);margin:0 0 14px}
.basics .hd p{color:var(--mute-d);max-width:560px;margin:0 auto;line-height:1.55}
.facts{position:relative;z-index:2;display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:rgba(9,8,13,.1);margin:0 6vw;border:1px solid rgba(9,8,13,.1)}
.fact{background:var(--paper);padding:30px 24px}
.fact b{display:block;font-family:'Anton';font-weight:400;font-size:clamp(34px,3.4vw,52px);line-height:1;color:var(--pu)}
.fact .h6{font:700 .8rem 'Inter';letter-spacing:.12em;text-transform:uppercase;margin:12px 0 8px;color:var(--ink);padding:0}
.fact p{margin:0;font-size:.86rem;line-height:1.5;color:var(--mute-d)}
.basics .cta{text-align:center;margin-top:6vh;position:relative;z-index:2}

/* 8 join */
.join{position:relative;height:118vh;overflow:clip}
.join .ghost{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);font-size:22vw;white-space:nowrap;color:#17141f}
.join .tag{position:absolute;top:10vh;left:0;right:0;text-align:center;font-size:.7rem;letter-spacing:.3em;color:var(--pk)}
.st-key-authwrap{margin-top:-86vh;position:relative;z-index:5;padding:0 16px 18vh}
.st-key-authcard{background:#fff!important;border-radius:6px!important;padding:34px 34px 26px!important;box-shadow:0 40px 80px rgba(0,0,0,.45)}
.st-key-authcard .h3{font-family:'Anton';font-weight:400;text-transform:uppercase;font-size:2rem;line-height:1;margin:0 0 6px;color:var(--ink);padding:0}
.st-key-authcard .sub{color:var(--mute-d);font-size:.88rem;margin:0 0 6px}
.st-key-authcard label p,.st-key-authcard [data-testid="stWidgetLabel"] p{color:var(--ink)!important;font-size:.8rem!important;font-weight:600!important}
.st-key-authcard input{background:#efeef3!important;color:var(--ink)!important;border:0!important;border-radius:3px!important;height:46px!important}
.st-key-authcard [data-baseweb="input"]{background:#efeef3!important;border:1px solid transparent!important;border-radius:3px!important}
.st-key-authcard [data-baseweb="input"]:focus-within{border-color:var(--pk)!important}
.st-key-authcard [data-baseweb="input"] button{background:#efeef3!important}
.st-key-authcard button[kind="primary"]{background:var(--pk)!important;color:#fff!important;border:0!important;border-radius:3px!important;height:50px!important;margin-top:8px}
.st-key-authcard button[kind="primary"] p{font-family:'Anton';text-transform:uppercase;letter-spacing:.08em;font-size:1.1rem}
.st-key-authcard button[kind="primary"]:hover{background:#e52a78!important}
.st-key-authcard button[data-baseweb="tab"] p{font-family:'Anton';text-transform:uppercase;font-size:1.25rem;letter-spacing:.04em;color:rgba(9,8,13,.4)}
.st-key-authcard button[data-baseweb="tab"][aria-selected="true"] p{color:var(--ink)}
.st-key-authcard [data-baseweb="tab-highlight"]{background:var(--pk)!important}
.st-key-authcard [data-baseweb="tab-border"]{background:rgba(9,8,13,.1)!important}
.st-key-authcard [data-testid="stRadio"] label p{color:var(--ink)!important}
.st-key-authcard [data-testid="stAlert"] p{color:inherit!important}
.lp-foot{display:flex;justify-content:space-between;flex-wrap:wrap;gap:12px;padding:30px 24px;border-top:1px solid rgba(255,255,255,.1);font-size:.7rem;letter-spacing:.18em;text-transform:uppercase;color:var(--mute)}

/* ── scroll-driven motion ── */
@supports (animation-timeline:view()){
  .hero .num{animation:numIn 1.2s .3s cubic-bezier(.2,.8,.2,1) both,numOut linear both;animation-timeline:auto,view();animation-range:normal,exit 0% exit 100%}
  @keyframes numOut{to{transform:translate(-50%,-10%) scale(1.5);opacity:0}}
  .hero .stl,.hero .str,.hero .title,.hero .nxt{animation:fadeOut linear both;animation-timeline:view();animation-range:exit 0% exit 50%}
  @keyframes fadeOut{to{opacity:0;transform:translateY(-60px)}}

  .story .sl{animation:slin linear both;animation-timeline:--st;animation-range:contain calc(var(--i)*18%) contain calc(var(--i)*18% + 16%)}
  .story .sl b{animation:numon linear both;animation-timeline:--st;animation-range:contain calc(var(--i)*18%) contain calc(var(--i)*18% + 16%)}
  @keyframes slin{from{transform:translateY(40px);opacity:.35}to{transform:none;opacity:1;color:var(--ink)}}
  @keyframes numon{to{color:var(--pk)}}
  .story .tail{animation:tailin linear both;animation-timeline:--st;animation-range:contain 56% contain 74%}
  @keyframes tailin{from{opacity:0;transform:translateY(24px)}to{opacity:1;transform:none}}
  .story .fl1{animation:fl1 linear both;animation-timeline:--st;animation-range:cover 10% cover 90%}
  .story .fl2{animation:fl2 linear both;animation-timeline:--st;animation-range:cover 10% cover 90%}
  @keyframes fl1{from{transform:translateY(55vh) rotate(-8deg)}to{transform:translateY(-75vh) rotate(6deg)}}
  @keyframes fl2{from{transform:translateY(65vh) rotate(5deg)}to{transform:translateY(-55vh) rotate(-4deg)}}

  .club{animation:pop linear both;animation-timeline:view();animation-range:entry 0% entry 80%}
  @keyframes pop{from{opacity:0;transform:translateY(50px)}}
  .clubs .hd .h2,.mine .hd,.basics .hd,.wh .hd .h2,.fact{animation:pop linear both;animation-timeline:view();animation-range:entry 10% entry 70%}

  .step{animation:pop linear both;animation-timeline:view();animation-range:entry 10% entry 80%}
  .how .t{animation:pop linear both;animation-timeline:view();animation-range:entry 10% entry 70%}

  .mine .track{animation:hscroll linear both;animation-timeline:--mn;animation-range:contain 0% contain 100%}
  @keyframes hscroll{0%,6%{transform:translateX(0)}94%,100%{transform:translateX(calc(-100% + 100vw))}}
  .mine .ghost{animation:ghost linear both;animation-timeline:--mn;animation-range:cover 0% cover 100%}
  @keyframes ghost{from{transform:translate(10vw,-50%)}to{transform:translate(-60vw,-50%)}}

  .row{animation:rowlit linear both;animation-timeline:view();animation-range:cover 30% cover 70%}
  @keyframes rowlit{0%,100%{opacity:.4}40%,60%{opacity:1;border-color:var(--pk)}}

  .stripes{animation:grow linear both;animation-timeline:view();animation-range:entry 0% entry 100%}
  @keyframes grow{from{transform:scaleY(.2);transform-origin:top}}
  .join .ghost{animation:ghostj linear both;animation-timeline:view();animation-range:cover 0% cover 70%}
  @keyframes ghostj{from{transform:translate(-50%,-10%) scale(.8);opacity:0}}
}
@media(max-width:900px){
  .nv nav a:not(.go){display:none}
  .hero .stl,.hero .str{display:none}
  .hero-media img{width:112vw;margin:-56vw 0 0 -56vw;top:46%}
  .hero .hint{display:none}
  .cgrid{grid-template-columns:1fr 1fr}.cgrid .mid{display:none}
  .steps{grid-template-columns:1fr 1fr;row-gap:30px}
  .row{grid-template-columns:1fr auto}.row p{display:none}
  .facts{grid-template-columns:1fr 1fr}
  .wh .hd{gap:4vw;flex-direction:column}
  .story .fl{display:none}
}
</style>
"""

PARENT_JS = r"""
(function(){
if(window.__pldw) return; window.__pldw=1;
const P = window, D = document;

/* liquid colour reveal on the hero image */
function liquid(){
  const hero=D.querySelector('.hero'), img=D.querySelector('.hero-media img'), cv=D.getElementById('liquid');
  if(!hero||!img||!cv||!img.complete){return;}
  if(cv.dataset.on) return; cv.dataset.on='1';
  if(!D.getElementById('lp-goo')){
    const s=D.createElementNS('http://www.w3.org/2000/svg','svg');
    s.setAttribute('width','0');s.setAttribute('height','0');s.style.position='absolute';
    s.innerHTML='<defs><filter id="lp-goo"><feGaussianBlur in="SourceGraphic" stdDeviation="14" result="b"/>'+
      '<feColorMatrix in="b" mode="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 26 -11" result="g"/>'+
      '<feComposite in="SourceGraphic" in2="g" operator="atop"/></filter></defs>';
    D.body.appendChild(s);
  }
  cv.style.filter='url(#lp-goo)';
  const ctx=cv.getContext('2d'); let W=0,H=0;
  function size(){const r=hero.getBoundingClientRect();W=r.width;H=r.height;cv.width=W;cv.height=H;}
  size(); P.addEventListener('resize',size);
  const pts=[]; let last=null;
  function add(x,y){
    if(last){const dx=x-last.x,dy=y-last.y,n=Math.max(1,Math.floor(Math.hypot(dx,dy)/9));
      for(let i=1;i<=n;i++)pts.push({x:last.x+dx*i/n,y:last.y+dy*i/n,r:54+Math.random()*34,l:1,vx:(Math.random()-.5)*.7,vy:.25+Math.random()*.6});}
    last={x,y};
  }
  hero.addEventListener('pointermove',e=>{const r=hero.getBoundingClientRect();add(e.clientX-r.left,e.clientY-r.top);});
  hero.addEventListener('pointerleave',()=>{last=null;});
  // short self-drawn sweep so people discover the effect
  const t0=performance.now();
  (function intro(){const t=(performance.now()-t0)/1400; if(t>1){last=null;return;}
    const ir=img.getBoundingClientRect(), hr=hero.getBoundingClientRect();
    add(ir.left-hr.left+ir.width*(.2+.6*t), ir.top-hr.top+ir.height*(.5+.22*Math.sin(t*6.3))); requestAnimationFrame(intro);})();
  function frame(){
    if(!D.body.contains(cv)) return;
    ctx.clearRect(0,0,W,H);
    if(pts.length){
      ctx.globalCompositeOperation='source-over'; ctx.fillStyle='#fff';
      for(let i=pts.length-1;i>=0;i--){const p=pts[i]; p.l-=.011; p.x+=p.vx; p.y+=p.vy;
        if(p.l<=0){pts.splice(i,1);continue;}
        ctx.beginPath(); ctx.arc(p.x,p.y,p.r*Math.pow(p.l,.55),0,6.2832); ctx.fill();}
      const ir=img.getBoundingClientRect(), hr=hero.getBoundingClientRect();
      ctx.globalCompositeOperation='source-in';
      ctx.drawImage(img, ir.left-hr.left, ir.top-hr.top, ir.width, ir.height);
      ctx.globalCompositeOperation='source-over';
    }
    requestAnimationFrame(frame);
  }
  frame();
}

/* warehouse ball: sticks in the middle, then shoots forward past ~22% of the section */
function rollball(){
  const wh=D.querySelector('.wh'), sc=D.querySelector('section.stMain');
  if(!wh||!sc){return;}
  if(wh.dataset.on) return; wh.dataset.on='1';
  const check=()=>{ if(!D.body.contains(wh)) return;
    const r=wh.getBoundingClientRect(); wh.classList.toggle('go', -r.top > r.height*0.22); };
  sc.addEventListener('scroll',check,{passive:true}); check();
}

/* rotating 3D stadium (three.js) */
function loadThree(cb){
  if(P.THREE) return cb();
  let s=D.getElementById('lp-three');
  if(!s){s=D.createElement('script');s.id='lp-three';s.src='https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js';D.head.appendChild(s);}
  s.addEventListener('load',cb);
}
function stadium(){
  const host=D.querySelector('.stad'), sec=D.querySelector('.clubs');
  if(!host||!sec){return;}
  if(host.dataset.on) return; host.dataset.on='1';
  loadThree(()=>{ try{ build(host,sec); }catch(e){ console.warn('stadium',e); } });
}
function build(host,sec){
  const T=P.THREE;
  const fb=host.querySelector('.fallback'); if(fb) fb.style.display='none';
  const r=new T.WebGLRenderer({antialias:true,alpha:true});
  r.setPixelRatio(Math.min(P.devicePixelRatio||1,2));
  r.outputEncoding=T.sRGBEncoding; r.toneMapping=T.ACESFilmicToneMapping; r.toneMappingExposure=1.05;
  r.shadowMap.enabled=true; r.shadowMap.type=T.PCFSoftShadowMap;
  host.prepend(r.domElement);
  const scene=new T.Scene();
  const cam=new T.PerspectiveCamera(30,1,1,3000);
  const canvasTex=(w,h,draw,rx,ry)=>{const c=D.createElement('canvas');c.width=w;c.height=h;draw(c.getContext('2d'),w,h);
    const t=new T.CanvasTexture(c);t.encoding=T.sRGBEncoding;t.anisotropy=8;
    if(rx){t.wrapS=t.wrapT=T.RepeatWrapping;t.repeat.set(rx,ry);} return t;};

  // lighting: cool sky, warm low sun with soft shadows
  scene.add(new T.HemisphereLight(0xdfe8ff,0x34343c,.65));
  const sun=new T.DirectionalLight(0xfff1dc,1.6); sun.position.set(140,190,90); sun.castShadow=true;
  sun.shadow.mapSize.set(2048,2048); Object.assign(sun.shadow.camera,{left:-150,right:150,top:150,bottom:-150,near:10,far:600});
  sun.shadow.bias=-0.0006; scene.add(sun);
  const fill=new T.DirectionalLight(0xc8d4ff,.35); fill.position.set(-120,80,-140); scene.add(fill);

  const stad=new T.Group(); scene.add(stad);
  const OVAL=.76;

  // pitch: mowing stripes, grain, full markings
  const pitchTex=canvasTex(2100,1360,(g,w,h)=>{
    for(let i=0;i<20;i++){g.fillStyle=i%2?'#3d8a34':'#47963b';g.fillRect(i*w/20,0,w/20+1,h);}
    for(let i=0;i<26000;i++){g.fillStyle=`rgba(${Math.random()<.5?0:255},${Math.random()<.5?40:255},0,.05)`;g.fillRect(Math.random()*w,Math.random()*h,2,2);}
    const s=w/105; g.strokeStyle='rgba(255,255,255,.92)'; g.lineWidth=s*.14;
    const L=(x,y,ww,hh)=>g.strokeRect(x*s,y*s,ww*s,hh*s);
    L(0.5,.5,104,67); g.beginPath();g.moveTo(52.5*s,.5*s);g.lineTo(52.5*s,67.5*s);g.stroke();
    g.beginPath();g.arc(52.5*s,34*s,9.15*s,0,7);g.stroke();
    L(.5,13.85,16.5,40.3);L(88,13.85,16.5,40.3);L(.5,24.85,5.5,18.3);L(99,24.85,5.5,18.3);
    g.beginPath();g.arc(11.5*s,34*s,9.15*s,-.93,.93);g.stroke();g.beginPath();g.arc(93.5*s,34*s,9.15*s,Math.PI-.93,Math.PI+.93);g.stroke();
    g.fillStyle='#fff';[[11.5,34],[93.5,34],[52.5,34]].forEach(([x,y])=>{g.beginPath();g.arc(x*s,y*s,s*.3,0,7);g.fill();});
  });
  const pitch=new T.Mesh(new T.PlaneGeometry(105,68),new T.MeshStandardMaterial({map:pitchTex,roughness:.95}));
  pitch.rotation.x=-Math.PI/2; pitch.receiveShadow=true; stad.add(pitch);
  const surround=new T.Mesh(new T.CircleGeometry(72,96),new T.MeshStandardMaterial({color:0x2f6d29,roughness:1}));
  surround.rotation.x=-Math.PI/2; surround.scale.set(1,OVAL*.98,1); surround.position.y=-.05; surround.receiveShadow=true; stad.add(surround);
  // goals
  [-1,1].forEach(sx=>{const gm=new T.MeshStandardMaterial({color:0xffffff});
    const g=new T.Group(); [[0,1.2,-3.66],[0,1.2,3.66]].forEach(([x,y,z])=>{const p=new T.Mesh(new T.CylinderGeometry(.12,.12,2.44,8),gm);p.position.set(x,y,z);g.add(p);});
    const bar=new T.Mesh(new T.CylinderGeometry(.12,.12,7.32,8),gm);bar.rotation.x=Math.PI/2;bar.position.y=2.44;g.add(bar);
    g.position.x=sx*52.5; stad.add(g);});

  // seating: Wembley red, with visible rows via a striped texture along the lathe profile
  const seatTex=canvasTex(64,512,(g,w,h)=>{const rows=32;
    for(let i=0;i<rows;i++){const y=i*h/rows;g.fillStyle='#b3121d';g.fillRect(0,y,w,h/rows);
      g.fillStyle='#5c0a10';g.fillRect(0,y+h/rows*.62,w,h/rows*.38);
      g.fillStyle='rgba(255,255,255,.06)';g.fillRect(0,y,w,1);}
    for(let i=0;i<30;i++){g.fillStyle='rgba(20,0,0,.35)';g.fillRect(Math.random()*w,0,1,h);} },60,1);
  const seatMat=new T.MeshStandardMaterial({map:seatTex,roughness:.8,side:T.DoubleSide});
  const tier=(r0,r1,h0,h1,steps)=>{const pts=[];for(let i=0;i<=steps;i++){const rr=r0+(r1-r0)*i/steps,hh=h0+(h1-h0)*i/steps;
      pts.push(new T.Vector2(rr,hh));pts.push(new T.Vector2(rr+(r1-r0)/steps*.55,hh));}
    const m=new T.Mesh(new T.LatheGeometry(pts,160),seatMat);m.scale.set(1,1,OVAL);m.castShadow=m.receiveShadow=true;return m;};
  stad.add(tier(64,80,.6,14,14)); stad.add(tier(81,93,16,27,10)); stad.add(tier(94,104,29,40,9));
  // concourse fascias between tiers
  const concrete=new T.MeshStandardMaterial({color:0xd8d6d2,roughness:.9,side:T.DoubleSide});
  [[80.5,14,2.2],[93.5,27,2.2]].forEach(([rad,y,h])=>{const f=new T.Mesh(new T.CylinderGeometry(rad,rad,h,160,1,true),concrete);
    f.scale.set(1,1,OVAL);f.position.y=y+h/2-.2;f.castShadow=true;stad.add(f);});
  const pitchWall=new T.Mesh(new T.CylinderGeometry(63.6,63.6,1.4,160,1,true),new T.MeshStandardMaterial({color:0x1d1d22,roughness:.6,side:T.DoubleSide}));
  pitchWall.scale.set(1,1,OVAL);pitchWall.position.y=.6;stad.add(pitchWall);

  // outer facade: pale cladding with dark vertical glazing fins
  const facadeTex=canvasTex(1024,128,(g,w,h)=>{g.fillStyle='#cfd2d6';g.fillRect(0,0,w,h);
    for(let i=0;i<64;i++){g.fillStyle='#4a5560';g.fillRect(i*w/64+4,10,w/64-10,h-20);g.fillStyle='rgba(255,255,255,.18)';g.fillRect(i*w/64+4,10,3,h-20);} },6,1);
  const facade=new T.Mesh(new T.CylinderGeometry(106,104,44,160,1,true),new T.MeshStandardMaterial({map:facadeTex,roughness:.5,metalness:.3,side:T.DoubleSide}));
  facade.scale.set(1,1,OVAL);facade.position.y=22;facade.castShadow=facade.receiveShadow=true;stad.add(facade);

  // roof: solid white outer ring plus translucent inner panels
  const ring=(ri,ro,y0,y1,mat)=>{const m=new T.Mesh(new T.LatheGeometry([new T.Vector2(ri,y0),new T.Vector2(ro,y1),new T.Vector2(ro,y1-1.2),new T.Vector2(ri,y0-.8)],160),mat);
    m.scale.set(1,1,OVAL);m.castShadow=true;m.receiveShadow=true;stad.add(m);return m;};
  ring(96,108,47,45.5,new T.MeshStandardMaterial({color:0xf4f4f2,roughness:.55,metalness:.15,side:T.DoubleSide}));
  ring(84,96.2,48,47,new T.MeshPhysicalMaterial({color:0xe9eef2,roughness:.25,metalness:0,transmission:0,transparent:true,opacity:.38,side:T.DoubleSide}));
  // roof edge lighting strip
  const glow=new T.Mesh(new T.TorusGeometry(84,.35,6,200),new T.MeshStandardMaterial({color:0xffffff,emissive:0xfff3d1,emissiveIntensity:1.4}));
  glow.rotation.x=Math.PI/2;glow.scale.set(1,OVAL,1);glow.position.y=47.4;stad.add(glow);

  // the arch: white lattice tube rising over the north stand, tilted back
  const archGroup=new T.Group();
  const archMat=new T.MeshStandardMaterial({color:0xffffff,roughness:.3,metalness:.55});
  const arc=new T.TorusGeometry(116,1.5,16,220,Math.PI);
  const archMesh=new T.Mesh(arc,archMat); archMesh.castShadow=true; archGroup.add(archMesh);
  const lattice=new T.Mesh(new T.TorusGeometry(116,2.5,6,440,Math.PI),new T.MeshBasicMaterial({color:0xffffff,wireframe:true,transparent:true,opacity:.35}));
  archGroup.add(lattice);
  archGroup.scale.set(1,.82,1); archGroup.position.set(0,-4,-34); archGroup.rotation.x=-0.5; stad.add(archGroup);
  // arch feet
  [-1,1].forEach(sx=>{const f=new T.Mesh(new T.CylinderGeometry(3,4,4,12),concrete);f.position.set(sx*116,-4,-34);stad.add(f);});

  // podium the stadium sits on
  const podium=new T.Mesh(new T.CylinderGeometry(112,108,6,160),new T.MeshStandardMaterial({color:0xbfbcc4,roughness:.95}));
  podium.scale.set(1,1,OVAL);podium.position.y=-3.1;podium.receiveShadow=true;stad.add(podium);

  // soft contact shadow so it reads as floating
  const shTex=canvasTex(256,256,(g,w,h)=>{const gr=g.createRadialGradient(w/2,h/2,0,w/2,h/2,w/2);
    gr.addColorStop(0,'rgba(9,8,13,.42)');gr.addColorStop(.6,'rgba(9,8,13,.16)');gr.addColorStop(1,'rgba(9,8,13,0)');g.fillStyle=gr;g.fillRect(0,0,w,h);});
  const shadow=new T.Mesh(new T.PlaneGeometry(330,330*OVAL),new T.MeshBasicMaterial({map:shTex,transparent:true,depthWrite:false}));
  shadow.rotation.x=-Math.PI/2; shadow.position.y=-26; scene.add(shadow);

  // a real model in static/wembley.glb replaces the built-in one
  if(host.dataset.model){
    const swap=()=>new T.GLTFLoader().load(host.dataset.model,gl=>{
      const m=gl.scene, box=new T.Box3().setFromObject(m), size=box.getSize(new T.Vector3()), c=box.getCenter(new T.Vector3());
      const k=230/Math.max(size.x,size.z);
      m.scale.setScalar(k); m.position.set(-c.x*k,-box.min.y*k,-c.z*k);
      m.traverse(o=>{if(o.isMesh){o.castShadow=o.receiveShadow=true;}});
      while(stad.children.length) stad.remove(stad.children[0]);
      stad.add(m);
    },undefined,e=>console.warn('wembley.glb',e));
    if(T.GLTFLoader) swap(); else {const s=D.createElement('script');
      s.src='https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js';s.onload=swap;D.head.appendChild(s);}
  }
  function resize(){const w=host.clientWidth,h=host.clientHeight;if(!w||!h)return;r.setSize(w,h,false);cam.aspect=w/h;cam.updateProjectionMatrix();}
  resize(); P.addEventListener('resize',resize);
  let ang=.8, t=0;
  (function loop(){
    if(!D.body.contains(host)) return;
    const b=sec.getBoundingClientRect(), vh=P.innerHeight;
    if(b.bottom>-200 && b.top<vh+200){
      if(host.clientWidth && Math.abs(host.clientWidth/host.clientHeight-cam.aspect)>.01) resize();
      const p=Math.min(1,Math.max(0,(vh-b.top)/(b.height+vh)));
      t+=.016; const target=.8+p*Math.PI*1.6+t*.04;
      ang+=(target-ang)*.07;
      stad.position.y=Math.sin(t*.9)*2.2; shadow.material.opacity=.85-Math.sin(t*.9)*.12;
      // keep the whole stadium (bounding radius ~150 incl. arch) inside the frame
      const vf=cam.fov*Math.PI/180, hf=2*Math.atan(Math.tan(vf/2)*cam.aspect);
      const dist=150/Math.sin(Math.min(vf,hf)/2)*.8;
      const el=.62-.18*p;
      cam.position.set(Math.cos(ang)*dist*Math.cos(el),dist*Math.sin(el),Math.sin(ang)*dist*Math.cos(el)); cam.lookAt(0,10,0);
      r.render(scene,cam);
    }
    requestAnimationFrame(loop);
  })();
}

/* smooth scrolling (Lenis) on Streamlit's scroll container */
let lenis=null;
function smooth(){
  const wrap=D.querySelector('section.stMain'), content=D.querySelector('[data-testid="stMainBlockContainer"]');
  if(!wrap||!content) return;
  if(lenis && lenis.options.wrapper===wrap) return;
  if(!P.Lenis){
    if(!D.getElementById('lp-lenis')){const s=D.createElement('script');s.id='lp-lenis';
      s.src='https://unpkg.com/lenis@1.1.18/dist/lenis.min.js';D.head.appendChild(s);}
    return;
  }
  if(lenis) lenis.destroy();
  wrap.style.scrollBehavior='auto';
  lenis=new P.Lenis({wrapper:wrap,content:content,lerp:.085,smoothWheel:true}); P.__lenis=lenis;
  (function raf(t){lenis.raf(t);requestAnimationFrame(raf);})(performance.now());
}
// nav links glide instead of jumping
D.addEventListener('click',e=>{
  const a=e.target.closest&&e.target.closest('.lp a[href^="#"]'); if(!a) return;
  const el=D.querySelector(a.getAttribute('href')); if(!el) return;
  e.preventDefault();
  if(lenis) lenis.scrollTo(el,{duration:1.6}); else el.scrollIntoView({behavior:'smooth'});
});
const scan=()=>{liquid();rollball();stadium();smooth();};
scan(); setInterval(scan,700);
})();
"""


def _html(f):
    clubs = f["clubs"]
    cols = [clubs[0:5], clubs[5:10], clubs[10:15], clubs[15:20]]

    def col(items):
        return "<div class='col'>" + "".join(
            f'<div class="club" style="--c:{CLUB_COLOURS.get(n, "#3A1B7A")}"><b>{n}</b><small>{c}</small></div>'
            for n, c in items) + "</div>"

    grid = col(cols[0]) + col(cols[1]) + (
        '<div class="mid"><div class="stad"' + (' data-model="app/static/wembley.glb"' if os.path.exists(os.path.join(STATIC, "wembley.glb")) else "") + '><div class="fallback bs"></div>'
        '<div class="cap">Keep scrolling · the stadium turns</div></div></div>') + col(cols[2]) + col(cols[3])

    steps = "".join(f'<div class="step"><span>0{i + 1}</span><b>{t}</b><p>{d}</p></div>'
                    for i, (t, d) in enumerate(PIPELINE))

    cards = "".join(
        f'<div class="mcard"><div class="n">0{i + 1}</div><div class="h4">{t}</div><div class="k">{k}</div><p>{d}</p>'
        f'<div class="eg"><b>Everyday example</b>{eg}</div></div>'
        for i, (t, k, d, eg) in enumerate(MINING))

    rows = "".join(
        f'<div class="row"><div class="h5">{n.replace("_", " ")}<span class="{"f" if n.startswith("Fact") else ""}">'
        f'{"FACT" if n.startswith("Fact") else "DIMENSION"}</span></div><p>{TABLE_NOTES[n]}</p><div class="c">{c:,}</div></div>'
        for n, c in f["tables"])

    res = f["res"]
    bars = "".join(
        f'<div class="bar"><span>{lab}</span><i style="width:{v * 1.6:.0f}px;background:{c_}"></i>{v}%</div>'
        for lab, v, c_ in (("Home", res.get("H", 0), "#3A1B7A"), ("Draw", res.get("D", 0), "#3CD3EE"),
                           ("Away", res.get("A", 0), "#FF3E8E")))
    matches = dict(f["tables"])["Fact_Match"]

    html = f"""
<div class="lp">
<header class="nv"><a class="nv-logo" href="#top"><i class="bf"></i><b>EPL<em>·</em>Analytics</b></a>
<nav><a href="#story">Story</a><a href="#clubs">Clubs</a><a href="#pipeline">Pipeline</a><a href="#mining">Mining</a><a href="#warehouse">Warehouse</a><a class="go" href="#join">Sign in</a></nav></header>
<section class="hero dark" id="top">
<div class="hero-media"><img alt="Premier League match ball" src="/app/static/ball_side.webp"><canvas id="liquid"></canvas></div>
<div class="lines"></div>
<div class="num an">27</div>
<div class="stl"><div><b>27</b>Seasons</div><div><b>20</b>Clubs</div><div><b>{matches:,}</b>Matches</div></div>
<div class="str"><div><p>Every match is a row. Every season is a pattern.</p></div><div><b>{f['goals']:,}</b>Goals recorded</div><div><b>11</b>Warehouse tables</div></div>
<div class="title"><div class="h1">Premier<br>League</div><p>A data warehousing and mining project. Football is only the dataset; the star schema, OLAP and models are the subject.</p></div>
<div class="nxt">Latest season<b>2025/26</b></div>
<div class="hint">MOVE · SCROLL</div>
</section>
<section class="story light" id="story"><div class="pin"><div class="lines"></div>
<div class="fl fl1 bf"></div>
<div class="fl fl2"><small>Results, all matches</small>{bars}</div>
<div class="stats">{"".join(f'<div class="sl" style="--i:{i}"><b>{n}</b><span>{w}</span></div>' for i, (n, w) in enumerate(STATS))}
<p class="tail">{STATEMENT_TAIL[0]} {STATEMENT_TAIL[1]}<em><i>{STATEMENT_TAIL[2]}</i></em></p></div></div></section>
<section class="clubs light" id="clubs"><div class="lines"></div>
<div class="hd"><div class="h2 an">20 clubs.<br>One warehouse.</div><p>Every club in the data, with its home city. Each one is a row in the <b>Dim_Team</b> table, and every match they play links back to it.</p></div>
<div class="cgrid">{grid}</div>
<div class="cta"><a class="btn" href="#join">Explore the clubs ›</a></div>
</section>
<section class="how dark" id="pipeline"><div class="lines"></div>
<div class="k">UNDER THE HOOD</div>
<div class="t an">From raw results to predictions, in four steps.</div>
<div class="steps">{steps}</div></section>
<section class="mine light" id="mining"><div class="pin"><div class="lines"></div>
<div class="ghost an">Data mining</div>
<div class="hd"><div class="h2 an">Six techniques,<br>one dataset</div><p>What each method does here, plus an everyday comparison. No football knowledge needed.</p></div>
<div class="track">{cards}</div></div></section>
<section class="wh dark" id="warehouse"><div class="lines"></div>
<div class="rail"><div class="rollball"><i class="bs"></i></div></div>
<div class="hd"><div class="h2 an">Inside</div><div class="h2 an">Warehouse</div></div>
<div class="rows">{rows}</div>
</section>
<section class="basics light" id="basics"><div class="stripes"></div><div class="lines"></div>
<div class="hd"><div class="h2 an">New to football?</div><p>Four facts that make the rest of the platform readable.</p></div>
<div class="facts">
<div class="fact"><b>3·1·0</b><div class="h6">Points</div><p>A win earns 3 points, a draw 1, a loss 0. Most points at the end of the season wins the league.</p></div>
<div class="fact"><b>38</b><div class="h6">Matches a season</div><p>20 clubs each play every other club twice, once at home and once away.</p></div>
<div class="fact"><b>{res.get('H', 0):.0f}%</b><div class="h6">Home advantage</div><p>Share of matches the home side won. Draws were {res.get('D', 0):.0f}%, away wins {res.get('A', 0):.0f}%.</p></div>
<div class="fact"><b>{f['avg_goals']}</b><div class="h6">Goals per match</div><p>The average across every match in the warehouse.</p></div>
</div>
<div class="cta"><a class="btn" href="#join">Start exploring ›</a></div>
</section>
<section class="join dark" id="join"><div class="lines"></div><div class="ghost an">Kick off</div><div class="tag">SIGN IN · SIGN UP</div></section>
</div>"""
    return "\n".join(line.strip() for line in html.splitlines() if line.strip())


def render_landing():
    f = _facts()
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(_html(f), unsafe_allow_html=True)

    with st.container(key="authwrap"):
        _, mid, _ = st.columns([1, 1.15, 1])
        with mid:
            with st.container(key="authcard"):
                st.markdown('<div class="h3">Kick off</div><p class="sub">Users explore clubs and players. Admins get the warehouse, OLAP and mining lab.</p>',
                            unsafe_allow_html=True)
                t_in, t_up = st.tabs(["Sign in", "Sign up"])
                with t_in:
                    mode = st.radio("Workspace", ["User", "Admin"], horizontal=True, key="login_mode_toggle")
                    u = st.text_input("Username", value="user" if mode == "User" else "admin", key=f"in_username_{mode}")
                    p = st.text_input("Password", value="user" if mode == "User" else "admin", type="password", key=f"in_password_{mode}")
                    if st.button("Sign in", type="primary", use_container_width=True, key="btn_signin_submit"):
                        role = check_login(u.strip().lower(), p.strip(), mode)
                        if role:
                            st.session_state.update(auth_role=role, user_subpage="Dashboard", sb_user_nav_radio="Dashboard")
                            st.rerun()
                        else:
                            st.error("Invalid username or password for this workspace.")
                with t_up:
                    nu = st.text_input("Choose a username", key="su_user")
                    np1 = st.text_input("Password (min 6 characters)", type="password", key="su_pw1")
                    np2 = st.text_input("Confirm password", type="password", key="su_pw2")
                    if st.button("Create account", type="primary", use_container_width=True, key="btn_signup"):
                        nu_c = nu.strip().lower()
                        if len(nu_c) < 3:
                            st.error("Username must be at least 3 characters.")
                        elif len(np1) < 6:
                            st.error("Password must be at least 6 characters.")
                        elif np1 != np2:
                            st.error("Passwords do not match.")
                        else:
                            ok, msg = register_user(nu_c, np1)
                            if ok:
                                st.session_state.update(auth_role="user", user_subpage="Dashboard", sb_user_nav_radio="Dashboard")
                                st.rerun()
                            else:
                                st.error(msg)

    st.markdown('<div class="lp dark"><div class="lp-foot"><span>EPL Analytics — Data Warehousing &amp; Mining project</span>'
                '<span>27 seasons · 1999/00 – 2025/26</span></div></div>', unsafe_allow_html=True)
    # inject once into the main page so listeners survive Streamlit reruns
    components.html("<script>const d=window.parent.document;if(!window.parent.__pldw){const s=d.createElement('script');"
                    f"s.textContent={json.dumps(PARENT_JS)};d.head.appendChild(s);}}</script>", height=0)
