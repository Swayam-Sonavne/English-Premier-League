"""
Phase 1 verification — runs outside Streamlit context.
Mocks st.cache_data and st.cache_resource so utils can be imported directly.
"""
import sys
sys.path.insert(0, '.')

# ── mock streamlit decorators so utils import cleanly outside Streamlit ──────
from unittest.mock import MagicMock, patch
import types

st_mock = types.ModuleType("streamlit")
st_mock.cache_data     = lambda **kw: (lambda f: f)
st_mock.cache_resource = lambda **kw: (lambda f: f)
st_mock.cache_data.__call__ = lambda f: f
sys.modules["streamlit"] = st_mock

# ── now import utils ──────────────────────────────────────────────────────────
from utils.db import load_row_counts, load_team_match, load_player_perf, load_team_profiles
from utils.models import PREMATCH_FEATURES, INMATCH_FEATURES, CLUSTER_FEATURES, TRAIN_SEASON_IDS, TEST_SEASON_IDS
from utils.olap import olap_rollup, olap_drill_across
print("ALL IMPORTS OK")

# Test: DB row counts
counts = load_row_counts()
for t, n in counts.items():
    print(f"  {t:<30s} {n:>10,}")

assert counts["Fact_Match"]             == 10260,  "Fact_Match wrong"
assert counts["Fact_Team_Match"]        == 20520,  "FTM wrong"
assert counts["Fact_Player_Performance"]== 287280, "FPP wrong"
assert counts["Dim_Team"]              == 20
assert counts["Dim_Season"]            == 27
print("ROW COUNTS OK")

# Test: team_match columns
tm = load_team_match()
required = [
    "Team_Match_ID","Match_ID","Season_ID","Team_ID","Is_Home",
    "Goals_For","Goals_Against","Shots","Corners","Fouls",
    "Yellow","Red","Possession","Points","Result",
    "Form_Pts5","Form_GF5","Form_GA5",
    "Opp_Form_Pts5","Opp_Form_GF5","Opp_Form_GA5",
    "Team_Name","Season_Name"
]
for c in required:
    assert c in tm.columns, f"Missing: {c}"
print(f"Team_Match columns OK ({len(tm):,} rows)")

# Test: player perf
fp = load_player_perf()
assert len(fp) == 287280
print(f"Player_Perf OK ({len(fp):,} rows)")

# Test: clustering profiles
prof = load_team_profiles()
assert len(prof) == 540
print(f"Team profiles OK ({len(prof)} rows = 20 x 27)")

# Test: OLAP roll-up
_, df = olap_rollup("Season + Month → Season")
assert len(df) == 27
print(f"OLAP Roll-up OK ({len(df)} seasons)")

# Test: Drill-across reconciliation
_, da = olap_drill_across()
assert len(da) == 27
assert all(da["Difference"] == 0), f"NOT RECONCILED:\n{da[da['Difference']!=0]}"
print("Drill-across OK — warehouse reconciled (all seasons Difference=0)")

# Test: no leakage in pre-match features
leakage = {"Goals_For","Goals_Against","Points","Result"}
for f in PREMATCH_FEATURES:
    assert f not in leakage, f"LEAKAGE: {f}"
print(f"No leakage in pre-match features: {PREMATCH_FEATURES}")

# Test: chronological split integrity
train_tm = tm[tm["Season_ID"].isin(TRAIN_SEASON_IDS)]
test_tm  = tm[tm["Season_ID"].isin(TEST_SEASON_IDS)]
assert len(train_tm) + len(test_tm) == 20520
print(f"Chronological split — train: {len(train_tm):,}  test: {len(test_tm):,}")

# Test: clustering population
from utils.db import load_team_profiles
prof = load_team_profiles()
assert len(prof) == 540
teams  = prof["Team_Name"].nunique()
seasons= prof["Season_ID"].nunique()
assert teams == 20 and seasons == 27
print(f"Clustering population: {len(prof)} profiles ({teams} teams × {seasons} seasons)")

print()
print("=== PHASE 1 VERIFICATION PASSED ===")
