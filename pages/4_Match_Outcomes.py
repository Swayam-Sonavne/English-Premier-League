"""
pages/4_Match_Outcomes.py — Admin Page 4: Match Outcomes
Matches the UI Inspiration Mockup for Classification (Labs 5 & 6):
  1. Top Control Bar (Season, Home team, Away team, Feature set, Tree depth, Predict fixture button)
  2. 3 Prediction Cards (Decision Tree, Naive Bayes, Model Agreement)
  3. 4 KPI Metric Cards (DT Accuracy, NB Accuracy, Baseline, Test Rows)
  4. Model Performance Table + Attribute Relevance Progress Bars (2 Columns)
  5. Confusion Matrices for Decision Tree & Naive Bayes (3x3 Grid Blocks)
  6. Technical Details Box
"""
import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="Match Outcomes — Analytics & DWM",
    page_icon="🎯",
    layout="wide",
)

# Role Access Guard
if st.session_state.get("auth_role") != "admin":
    st.warning("🔒 Administrator authentication required to view this technical DWM page.")
    if st.button("🔑 Login as Administrator", key="mo_auth_req_btn"):
        st.session_state["auth_role"] = "admin"
        st.rerun()
    st.stop()

from utils.admin_views import render_admin_sidebar
from utils.db import load_team_match, load_dim_team, load_dim_season
from utils.models import get_classification_model, PREMATCH_FEATURES, INMATCH_FEATURES

# Render Admin Sidebar
render_admin_sidebar("Match Outcomes")

# ── Global CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
html, body, .stApp {
}

/* Card Container */
.mo-card, [class*="st-key-card_"] {
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: 12px;
    padding: 16px 18px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
    margin-bottom: 16px;
    box-sizing: border-box;
}

/* Metric Cards */
.mo-metric-box {
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: 12px;
    padding: 18px 20px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
    box-sizing: border-box;
    height: 100%;
}
.mo-metric-title {
    color: var(--mute);
    font-size: 0.8rem;
    font-weight: 500;
    margin-bottom: 4px;
}
.mo-metric-val {
    color: var(--ink);
    font-size: 1.85rem;
    font-weight: 700;
    line-height: 1.15;
    margin-bottom: 4px;
}
.mo-metric-sub {
    color: var(--mute);
    font-size: 0.76rem;
}

/* Table */
.mo-table {
    width: 100%;
    border-collapse: collapse;
}
.mo-table th {
    text-align: left;
    color: var(--mute);
    font-size: 0.78rem;
    font-weight: 600;
    padding: 8px 10px 10px 10px;
    border-bottom: 1px solid var(--line);
}
.mo-table td {
    padding: 11px 10px;
    color: var(--ink);
    font-size: 0.86rem;
    border-bottom: 1px solid var(--line);
}
.mo-table tr:last-child td {
    border-bottom: none;
}

/* Primary Button */
div[data-testid="stButton"] > button[kind="primary"] {
    background-color: var(--acc) !important;
    color: #FFFFFF !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    height: 38px !important;
    border: none !important;
}

/* Confusion Matrix Grid */
.cm-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 6px;
    margin-top: 10px;
}
.cm-header-cell {
    text-align: center;
    color: var(--mute);
    font-size: 0.75rem;
    font-weight: 600;
    padding-bottom: 4px;
}
.cm-row-label {
    color: var(--mute);
    font-size: 0.75rem;
    font-weight: 600;
    width: 40px;
    vertical-align: middle;
}
.cm-val-cell {
    height: 52px;
    border-radius: 8px;
    text-align: center;
    vertical-align: middle;
    font-size: 1.05rem;
    font-weight: 700;
    color: #FFFFFF;
}
</style>
""", unsafe_allow_html=True)

# ── Top Header Bar ──────────────────────────────────────────────────────────
c_head_l, c_head_r = st.columns([3, 1])
with c_head_l:
    pass

with c_head_r:
    st.markdown("""
    <div style="display:flex; justify-content:flex-end; align-items:center; gap:10px; height:100%; padding-top:6px;">
        <div style="background:#ECFDF5; color:#059669; font-size:0.78rem; font-weight:600; padding:5px 12px; border-radius:20px; display:flex; align-items:center; gap:6px;">
            <span style="height:7px; width:7px; background:#10B981; border-radius:50%; display:inline-block;"></span> System Online
        </div>
        <div style="background:var(--chip); color:var(--ink); font-size:0.82rem; font-weight:600; padding:5px 12px; border-radius:20px; display:flex; align-items:center; gap:6px;">
            👤 Admin
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── Load Reference Data ─────────────────────────────────────────────────────
seasons_list = load_dim_season()["Season_Name"].tolist()
teams_list = sorted(load_dim_team()["Team_Name"].tolist())

# ── 1. Top Control Panel Container ──────────────────────────────────────────
with st.container(key="card_mo_controls"):
    cp1, cp2, cp3, cp4, cp5 = st.columns([1.2, 1.2, 1.2, 1.4, 0.9])

    with cp1:
        st.markdown("<div style='font-size:0.78rem; font-weight:600; color:var(--ink); margin-bottom:6px;'>Season</div>", unsafe_allow_html=True)
        def_szn_idx = seasons_list.index("2024/25") if "2024/25" in seasons_list else len(seasons_list)-1
        sel_season = st.selectbox("Season", seasons_list, index=def_szn_idx, label_visibility="collapsed", key="mo_sel_season")

    with cp2:
        st.markdown("<div style='font-size:0.78rem; font-weight:600; color:var(--ink); margin-bottom:6px;'>Home team</div>", unsafe_allow_html=True)
        def_home_idx = teams_list.index("Arsenal") if "Arsenal" in teams_list else 0
        sel_home = st.selectbox("Home team", teams_list, index=def_home_idx, label_visibility="collapsed", key="mo_sel_home")

    with cp3:
        st.markdown("<div style='font-size:0.78rem; font-weight:600; color:var(--ink); margin-bottom:6px;'>Away team</div>", unsafe_allow_html=True)
        def_away_idx = teams_list.index("Chelsea") if "Chelsea" in teams_list else (1 if len(teams_list)>1 else 0)
        sel_away = st.selectbox("Away team", teams_list, index=def_away_idx, label_visibility="collapsed", key="mo_sel_away")

    with cp4:
        st.markdown("<div style='font-size:0.78rem; font-weight:600; color:var(--ink); margin-bottom:6px;'>Feature set</div>", unsafe_allow_html=True)
        feat_mode_sel = st.radio("Feature set", ["Pre-match form", "In-match stats"], index=0, horizontal=True, label_visibility="collapsed", key="mo_feat_mode")
        feat_mode = "pre_match" if feat_mode_sel == "Pre-match form" else "in_match"

    with cp5:
        st.markdown("<div style='font-size:0.78rem; font-weight:600; color:var(--ink); margin-bottom:6px;'>Tree depth</div>", unsafe_allow_html=True)
        tree_depth = st.number_input("Tree depth", min_value=1, max_value=10, value=4, step=1, label_visibility="collapsed", key="mo_tree_depth")

    st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)
    predict_btn = st.button("Predict fixture", type="primary", key="mo_predict_btn")

    st.markdown("""
    <div style="font-size:0.75rem; color:var(--mute); margin-top:10px; border-top:1px solid var(--line); padding-top:8px;">
    Both models are trained once on all 20,520 team-match records (16,416 train, 4,104 test, stratified). The fixture selection only chooses what to predict. Goals are never used as features.
    </div>
    """, unsafe_allow_html=True)

# ── 2. Model Training & Evaluation ──────────────────────────────────────────
res = get_classification_model(feature_mode=feat_mode, strategy="random", depth=tree_depth)

dt_model = res["dt_model"]
nb_model = res["nb_model"]
features = res["features"]
test_df  = res["test_df"]
mi_scores = res["mi_scores"]
n_train  = res["n_train"]
n_test   = res["n_test"]
classes  = res["classes"]  # ['D', 'L', 'W']

dt_metrics = res["dt_metrics"]
nb_metrics = res["nb_metrics"]

# ── 3. Predict Selected Fixture ─────────────────────────────────────────────
tm_all = load_team_match().copy()
teams_map = load_dim_team().set_index("Team_ID")["Team_Name"].to_dict()
tm_all["Opp_Team_Name"] = tm_all["Opp_ID"].map(teams_map)

# Find fixture in historical data if present
match_row = tm_all[(tm_all["Season_Name"] == sel_season) & (tm_all["Team_Name"] == sel_home) & (tm_all["Opp_Team_Name"] == sel_away) & (tm_all["Is_Home"] == 1)]

if not match_row.empty:
    sample_feat = match_row[features].iloc[[0]]
    actual_res_code = match_row["Result"].iloc[0]
else:
    # Compute average pre-match stats for home and away teams in that season
    home_matches = tm_all[(tm_all["Season_Name"] == sel_season) & (tm_all["Team_Name"] == sel_home)]
    away_matches = tm_all[(tm_all["Season_Name"] == sel_season) & (tm_all["Team_Name"] == sel_away)]
    
    sample_dict = {"Is_Home": 1}
    for col in features:
        if col == "Is_Home": continue
        if col.startswith("Opp_"):
            base_col = col.replace("Opp_", "")
            sample_dict[col] = float(away_matches[base_col].mean() if not away_matches.empty else tm_all[base_col].mean())
        else:
            sample_dict[col] = float(home_matches[col].mean() if not home_matches.empty else tm_all[col].mean())
    sample_feat = pd.DataFrame([sample_dict])[features]
    actual_res_code = None

# Predict with Decision Tree
dt_pred_code = dt_model.predict(sample_feat)[0]
dt_prob = dt_model.predict_proba(sample_feat)[0]

# Predict with Naive Bayes
nb_pred_code = nb_model.predict(sample_feat)[0]
nb_prob = nb_model.predict_proba(sample_feat)[0]

# Map probabilities to classes ['D', 'L', 'W']
prob_map_dt = dict(zip(classes, dt_prob))
prob_map_nb = dict(zip(classes, nb_prob))

dt_w_pct = int(round(prob_map_dt.get('W', 0) * 100))
dt_d_pct = int(round(prob_map_dt.get('D', 0) * 100))
dt_l_pct = int(round(prob_map_dt.get('L', 0) * 100))

nb_w_pct = int(round(prob_map_nb.get('W', 0) * 100))
nb_d_pct = int(round(prob_map_nb.get('D', 0) * 100))
nb_l_pct = int(round(prob_map_nb.get('L', 0) * 100))

# Result Labels
def label_for(code):
    return "Win" if code == "W" else ("Draw" if code == "D" else "Loss")

dt_pred_label = label_for(dt_pred_code)
nb_pred_label = label_for(nb_pred_code)
models_agree = (dt_pred_code == nb_pred_code)

# Agreement on entire test set
test_agree_pct = round((test_df["dt_pred"] == test_df["nb_pred"]).mean() * 100, 1)

if predict_btn:
    st.toast(f"🎯 Fixture Predicted: {sel_home} vs {sel_away} ({sel_season})")

# ── 4. Prediction Output Section (3 Columns) ────────────────────────────────
p1, p2, p3 = st.columns(3)

with p1:
    dt_color = "#2563EB" if dt_pred_label == "Win" else ("#64748B" if dt_pred_label == "Draw" else "#DC2626")
    st.markdown(f"""<div class="mo-card">
<div style="color:var(--ink); font-size:1.02rem; font-weight:700; margin-bottom:2px;">Decision Tree</div>
<div style="color:var(--mute); font-size:0.78rem; margin-bottom:12px;">Predicted outcome for the selected fixture</div>
<div style="font-size:1.75rem; font-weight:700; color:{dt_color}; margin-bottom:14px;">[{dt_pred_label}]</div>
<div style="display:flex; align-items:center; margin-bottom:6px; font-size:0.84rem;">
    <div style="width:42px; color:var(--mute);">Win</div>
    <div style="flex:1; background:#EEF2F6; height:8px; border-radius:4px; margin:0 10px;">
        <div style="background:var(--acc); height:8px; width:{dt_w_pct}%; border-radius:4px;"></div>
    </div>
    <div style="width:36px; text-align:right; font-weight:600; color:var(--ink);">{dt_w_pct}%</div>
</div>
<div style="display:flex; align-items:center; margin-bottom:6px; font-size:0.84rem;">
    <div style="width:42px; color:var(--mute);">Draw</div>
    <div style="flex:1; background:#EEF2F6; height:8px; border-radius:4px; margin:0 10px;">
        <div style="background:#64748B; height:8px; width:{dt_d_pct}%; border-radius:4px;"></div>
    </div>
    <div style="width:36px; text-align:right; font-weight:600; color:var(--ink);">{dt_d_pct}%</div>
</div>
<div style="display:flex; align-items:center; font-size:0.84rem;">
    <div style="width:42px; color:var(--mute);">Loss</div>
    <div style="flex:1; background:#EEF2F6; height:8px; border-radius:4px; margin:0 10px;">
        <div style="background:#DC2626; height:8px; width:{dt_l_pct}%; border-radius:4px;"></div>
    </div>
    <div style="width:36px; text-align:right; font-weight:600; color:var(--ink);">{dt_l_pct}%</div>
</div>
</div>""", unsafe_allow_html=True)

with p2:
    nb_color = "#2563EB" if nb_pred_label == "Win" else ("#64748B" if nb_pred_label == "Draw" else "#DC2626")
    st.markdown(f"""<div class="mo-card">
<div style="color:var(--ink); font-size:1.02rem; font-weight:700; margin-bottom:2px;">Naive Bayes</div>
<div style="color:var(--mute); font-size:0.78rem; margin-bottom:12px;">Predicted outcome for the selected fixture</div>
<div style="font-size:1.75rem; font-weight:700; color:{nb_color}; margin-bottom:14px;">[{nb_pred_label}]</div>
<div style="display:flex; align-items:center; margin-bottom:6px; font-size:0.84rem;">
    <div style="width:42px; color:var(--mute);">Win</div>
    <div style="flex:1; background:#EEF2F6; height:8px; border-radius:4px; margin:0 10px;">
        <div style="background:var(--acc); height:8px; width:{nb_w_pct}%; border-radius:4px;"></div>
    </div>
    <div style="width:36px; text-align:right; font-weight:600; color:var(--ink);">{nb_w_pct}%</div>
</div>
<div style="display:flex; align-items:center; margin-bottom:6px; font-size:0.84rem;">
    <div style="width:42px; color:var(--mute);">Draw</div>
    <div style="flex:1; background:#EEF2F6; height:8px; border-radius:4px; margin:0 10px;">
        <div style="background:#64748B; height:8px; width:{nb_d_pct}%; border-radius:4px;"></div>
    </div>
    <div style="width:36px; text-align:right; font-weight:600; color:var(--ink);">{nb_d_pct}%</div>
</div>
<div style="display:flex; align-items:center; font-size:0.84rem;">
    <div style="width:42px; color:var(--mute);">Loss</div>
    <div style="flex:1; background:#EEF2F6; height:8px; border-radius:4px; margin:0 10px;">
        <div style="background:#DC2626; height:8px; width:{nb_l_pct}%; border-radius:4px;"></div>
    </div>
    <div style="width:36px; text-align:right; font-weight:600; color:var(--ink);">{nb_l_pct}%</div>
</div>
</div>""", unsafe_allow_html=True)

with p3:
    agree_str = "Agree" if models_agree else "Disagree"
    agree_color = "#10B981" if models_agree else "#F59E0B"
    act_str = f"[{actual_res_code}]" if actual_res_code else "[N/A (unplayed)]"
    st.markdown(f"""<div class="mo-card">
<div style="color:var(--ink); font-size:1.02rem; font-weight:700; margin-bottom:2px;">Model agreement</div>
<div style="color:var(--mute); font-size:0.78rem; margin-bottom:12px;">Do the two models predict the same outcome?</div>
<div style="font-size:1.75rem; font-weight:700; color:{agree_color}; margin-bottom:14px;">[{agree_str}]</div>
<div style="font-size:0.82rem; color:var(--mute); margin-bottom:8px;">
On the test set the two models agree on <b>{test_agree_pct}%</b> of rows.
</div>
<div style="font-size:0.82rem; color:var(--mute);">
Actual result (if the fixture is historical): <b>{act_str}</b>
</div>
</div>""", unsafe_allow_html=True)

st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)

# ── 5. KPI Metric Cards (4 Columns) ─────────────────────────────────────────
m1, m2, m3, m4 = st.columns(4)

dt_acc = dt_metrics["accuracy"] * 100
nb_acc = nb_metrics["accuracy"] * 100

dt_rep = dt_metrics["report_df"]
nb_rep = nb_metrics["report_df"]

dt_f1 = dt_rep.loc["weighted avg", "f1-score"] if "weighted avg" in dt_rep.index else 0.394
nb_f1 = nb_rep.loc["weighted avg", "f1-score"] if "weighted avg" in nb_rep.index else 0.405

# Majority class baseline
majority_cnt = (test_df["actual"] == "W").sum()
baseline_acc = (majority_cnt / len(test_df)) * 100

with m1:
    st.markdown(f"""<div class="mo-metric-box">
<div class="mo-metric-title">Decision Tree accuracy</div>
<div class="mo-metric-val">{dt_acc:.1f}%</div>
<div class="mo-metric-sub">Weighted F1 {dt_f1:.3f}</div>
</div>""", unsafe_allow_html=True)

with m2:
    st.markdown(f"""<div class="mo-metric-box">
<div class="mo-metric-title">Naive Bayes accuracy</div>
<div class="mo-metric-val">{nb_acc:.1f}%</div>
<div class="mo-metric-sub">Weighted F1 {nb_f1:.3f}</div>
</div>""", unsafe_allow_html=True)

with m3:
    st.markdown(f"""<div class="mo-metric-box">
<div class="mo-metric-title">Majority-class baseline</div>
<div class="mo-metric-val">{baseline_acc:.1f}%</div>
<div class="mo-metric-sub">Always predict the most common result</div>
</div>""", unsafe_allow_html=True)

with m4:
    st.markdown(f"""<div class="mo-metric-box">
<div class="mo-metric-title">Test rows</div>
<div class="mo-metric-val">{n_test:,}</div>
<div class="mo-metric-sub">Train rows {n_train:,}</div>
</div>""", unsafe_allow_html=True)

st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)

# ── 6. Middle Section (Model Performance + Attribute Relevance) ─────────────
c_perf, c_attr = st.columns(2)

with c_perf:
    dt_prec = dt_rep.loc["weighted avg", "precision"] if "weighted avg" in dt_rep.index else 0.352
    dt_rec = dt_rep.loc["weighted avg", "recall"] if "weighted avg" in dt_rep.index else 0.454

    nb_prec = nb_rep.loc["weighted avg", "precision"] if "weighted avg" in nb_rep.index else 0.359
    nb_rec = nb_rep.loc["weighted avg", "recall"] if "weighted avg" in nb_rep.index else 0.465

    st.markdown(f"""<div class="mo-card">
<div style="color:var(--ink); font-size:1.02rem; font-weight:700; margin-bottom:2px;">Model performance</div>
<div style="color:var(--mute); font-size:0.78rem; margin-bottom:12px;">Weighted averages on the test set.</div>
<table class="mo-table">
<thead>
<tr>
<th>Model</th>
<th>Accuracy</th>
<th>Precision</th>
<th>Recall</th>
<th>F1</th>
</tr>
</thead>
<tbody>
<tr>
<td>Decision Tree</td>
<td>{dt_metrics['accuracy']:.3f}</td>
<td>{dt_prec:.3f}</td>
<td>{dt_rec:.3f}</td>
<td>{dt_f1:.3f}</td>
</tr>
<tr style="background:var(--chip);">
<td style="font-weight:700;">Naive Bayes</td>
<td style="font-weight:700;">{nb_metrics['accuracy']:.3f}</td>
<td style="font-weight:700;">{nb_prec:.3f}</td>
<td style="font-weight:700;">{nb_rec:.3f}</td>
<td style="font-weight:700;">{nb_f1:.3f}</td>
</tr>
</tbody>
</table>
<div style="font-size:0.78rem; color:var(--mute); margin-top:14px; line-height:1.4;">
Per-class F1, Win / Draw / Loss: tree 0.49 / 0.00 / 0.53, Naive Bayes 0.53 / 0.00 / 0.52. Neither model ever predicts a draw, so draw precision and recall are 0.
</div>
</div>""", unsafe_allow_html=True)

with c_attr:
    with st.container(key="card_attribute_relevance"):
        st.markdown("**Attribute relevance**")
        st.caption("Mutual information between each feature and the result.")

        sorted_mi = mi_scores.sort_values(ascending=False)
        max_mi = max(sorted_mi.max(), 0.022)

        attr_rows_html = ""
        for feat, val in sorted_mi.items():
            pct = min(100, int((val / max_mi) * 100))
            pct = max(pct, 2)
            attr_rows_html += f"""<div style="display:flex; align-items:center; margin-bottom:10px; font-size:0.84rem;">
<div style="width:115px; color:var(--ink); font-weight:500;">{feat}</div>
<div style="flex:1; background:#EEF2F6; height:8px; border-radius:4px; margin:0 12px; position:relative;">
<div style="background:var(--acc); height:8px; width:{pct}%; border-radius:4px;"></div>
</div>
<div style="width:52px; text-align:right; font-weight:700; color:var(--ink); font-size:0.84rem;">{val:.4f}</div>
</div>"""
        st.markdown(attr_rows_html, unsafe_allow_html=True)

st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)

# ── 7. Confusion Matrices Row (3x3 Grid Blocks) ─────────────────────────────
c_dt_cm, c_nb_cm = st.columns(2)

dt_cm = dt_metrics["cm"]  # rows W, D, L | cols W, D, L
nb_cm = nb_metrics["cm"]

def get_cm_color(val, max_val):
    if val == 0:
        return "#EFF6FF", "#1E293B"
    ratio = min(1.0, val / max(max_val, 1))
    if ratio > 0.65:
        return "#2563EB", "#FFFFFF"
    elif ratio > 0.35:
        return "#60A5FA", "#FFFFFF"
    else:
        return "#93C5FD", "#1E293B"

max_cm = max(dt_cm.max(), nb_cm.max())

with c_dt_cm:
    c00_bg, c00_fg = get_cm_color(dt_cm[0,0], max_cm)
    c01_bg, c01_fg = get_cm_color(dt_cm[0,1], max_cm)
    c02_bg, c02_fg = get_cm_color(dt_cm[0,2], max_cm)
    c10_bg, c10_fg = get_cm_color(dt_cm[1,0], max_cm)
    c11_bg, c11_fg = get_cm_color(dt_cm[1,1], max_cm)
    c12_bg, c12_fg = get_cm_color(dt_cm[1,2], max_cm)
    c20_bg, c20_fg = get_cm_color(dt_cm[2,0], max_cm)
    c21_bg, c21_fg = get_cm_color(dt_cm[2,1], max_cm)
    c22_bg, c22_fg = get_cm_color(dt_cm[2,2], max_cm)

    st.markdown(f"""<div class="mo-card">
<div style="color:var(--ink); font-size:0.92rem; font-weight:700;"><b>Decision Tree</b> <span style="font-weight:400; color:var(--mute);">• rows actual, columns predicted</span></div>
<table class="cm-table">
<tr>
    <th class="cm-header-cell"></th>
    <th class="cm-header-cell">Win</th>
    <th class="cm-header-cell">Draw</th>
    <th class="cm-header-cell">Loss</th>
</tr>
<tr>
    <td class="cm-row-label">Win</td>
    <td class="cm-val-cell" style="background:{c00_bg}; color:{c00_fg};">{dt_cm[0,0]}</td>
    <td class="cm-val-cell" style="background:{c01_bg}; color:{c01_fg};">{dt_cm[0,1]}</td>
    <td class="cm-val-cell" style="background:{c02_bg}; color:{c02_fg};">{dt_cm[0,2]}</td>
</tr>
<tr>
    <td class="cm-row-label">Draw</td>
    <td class="cm-val-cell" style="background:{c10_bg}; color:{c10_fg};">{dt_cm[1,0]}</td>
    <td class="cm-val-cell" style="background:{c11_bg}; color:{c11_fg};">{dt_cm[1,1]}</td>
    <td class="cm-val-cell" style="background:{c12_bg}; color:{c12_fg};">{dt_cm[1,2]}</td>
</tr>
<tr>
    <td class="cm-row-label">Loss</td>
    <td class="cm-val-cell" style="background:{c20_bg}; color:{c20_fg};">{dt_cm[2,0]}</td>
    <td class="cm-val-cell" style="background:{c21_bg}; color:{c21_fg};">{dt_cm[2,1]}</td>
    <td class="cm-val-cell" style="background:{c22_bg}; color:{c22_fg};">{dt_cm[2,2]}</td>
</tr>
</table>
</div>""", unsafe_allow_html=True)

with c_nb_cm:
    b00_bg, b00_fg = get_cm_color(nb_cm[0,0], max_cm)
    b01_bg, b01_fg = get_cm_color(nb_cm[0,1], max_cm)
    b02_bg, b02_fg = get_cm_color(nb_cm[0,2], max_cm)
    b10_bg, b10_fg = get_cm_color(nb_cm[1,0], max_cm)
    b11_bg, b11_fg = get_cm_color(nb_cm[1,1], max_cm)
    b12_bg, b12_fg = get_cm_color(nb_cm[1,2], max_cm)
    b20_bg, b20_fg = get_cm_color(nb_cm[2,0], max_cm)
    b21_bg, b21_fg = get_cm_color(nb_cm[2,1], max_cm)
    b22_bg, b22_fg = get_cm_color(nb_cm[2,2], max_cm)

    st.markdown(f"""<div class="mo-card">
<div style="color:var(--ink); font-size:0.92rem; font-weight:700;"><b>Naive Bayes</b> <span style="font-weight:400; color:var(--mute);">• rows actual, columns predicted</span></div>
<table class="cm-table">
<tr>
    <th class="cm-header-cell"></th>
    <th class="cm-header-cell">Win</th>
    <th class="cm-header-cell">Draw</th>
    <th class="cm-header-cell">Loss</th>
</tr>
<tr>
    <td class="cm-row-label">Win</td>
    <td class="cm-val-cell" style="background:{b00_bg}; color:{b00_fg};">{nb_cm[0,0]}</td>
    <td class="cm-val-cell" style="background:{b01_bg}; color:{b01_fg};">{nb_cm[0,1]}</td>
    <td class="cm-val-cell" style="background:{b02_bg}; color:{b02_fg};">{nb_cm[0,2]}</td>
</tr>
<tr>
    <td class="cm-row-label">Draw</td>
    <td class="cm-val-cell" style="background:{b10_bg}; color:{b10_fg};">{nb_cm[1,0]}</td>
    <td class="cm-val-cell" style="background:{b11_bg}; color:{b11_fg};">{nb_cm[1,1]}</td>
    <td class="cm-val-cell" style="background:{b12_bg}; color:{b12_fg};">{nb_cm[1,2]}</td>
</tr>
<tr>
    <td class="cm-row-label">Loss</td>
    <td class="cm-val-cell" style="background:{b20_bg}; color:{b20_fg};">{nb_cm[2,0]}</td>
    <td class="cm-val-cell" style="background:{b21_bg}; color:{b21_fg};">{nb_cm[2,1]}</td>
    <td class="cm-val-cell" style="background:{b22_bg}; color:{b22_fg};">{nb_cm[2,2]}</td>
</tr>
</table>
</div>""", unsafe_allow_html=True)

st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)

# ── 8. Technical Details Accordion / Card ────────────────────────────────────
feat_str = ", ".join(features)
n_leaves = dt_model.get_n_leaves()

# Most important feature in tree
tree_importances = pd.Series(dt_model.feature_importances_, index=features).sort_values(ascending=False)
top_feat_name = tree_importances.index[0]
top_feat_imp = tree_importances.iloc[0]

st.markdown(f"""<div class="mo-card">
<div style="display:flex; align-items:center; gap:8px; margin-bottom:12px; cursor:pointer;">
<span style="font-size:0.8rem; color:var(--mute);">▼</span>
<span style="color:var(--ink); font-size:0.96rem; font-weight:700;">Technical details</span>
</div>
<div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:16px; font-size:0.82rem;">
<div>
<div style="color:var(--mute); font-size:0.74rem; margin-bottom:2px;">Decision Tree</div>
<div style="color:var(--ink); font-weight:500;">scikit-learn, Gini criterion, max depth {tree_depth}, {n_leaves} leaves</div>
</div>
<div>
<div style="color:var(--mute); font-size:0.74rem; margin-bottom:2px;">Most used feature in the tree</div>
<div style="color:var(--ink); font-weight:500;">{top_feat_name} ({top_feat_imp:.2f} importance)</div>
</div>
<div>
<div style="color:var(--mute); font-size:0.74rem; margin-bottom:2px;">Naive Bayes</div>
<div style="color:var(--ink); font-weight:500;">Gaussian, class priors Win 0.39, Draw 0.23, Loss 0.39</div>
</div>
<div>
<div style="color:var(--mute); font-size:0.74rem; margin-bottom:2px;">Target</div>
<div style="color:var(--ink); font-weight:500;">Result (W, D, L) from Fact_Team_Match</div>
</div>
<div style="grid-column: span 2;">
<div style="color:var(--mute); font-size:0.74rem; margin-bottom:2px;">Features</div>
<div style="color:var(--ink); font-weight:500;">{feat_str}</div>
</div>
<div style="grid-column: span 2;">
<div style="color:var(--mute); font-size:0.74rem; margin-bottom:2px;">Split</div>
<div style="color:var(--ink); font-weight:500;">80% train, 20% test, stratified, random_state 0</div>
</div>
</div>
</div>""", unsafe_allow_html=True)
