"""
pages/3_Performance_Analysis.py — Admin Page 3: Performance Analysis
Matches the UI Inspiration Mockup for Regression Analysis (Lab 4):
  1. Top Control Bar (Target variable, Model toggle, Highlight team, Highlight season, Run model, Feature checkboxes)
  2. 4 Metric Cards (R² score, MAE, RMSE, Test rows)
  3. Actual vs Predicted Goals + Residual Distribution (2 Charts)
  4. Model Comparison Table + Coefficients Progress Bars (2 Cards)
  5. Technical Details Box
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error

st.set_page_config(
    page_title="Performance Analysis — Analytics & DWM",
    page_icon="📈",
    layout="wide",
)

# Role Access Guard
if st.session_state.get("auth_role") != "admin":
    st.warning("🔒 Administrator authentication required to view this technical DWM page.")
    if st.button("🔑 Login as Administrator", key="pa_reg_auth_req_btn"):
        st.session_state["auth_role"] = "admin"
        st.rerun()
    st.stop()

from utils.admin_views import render_admin_sidebar
from utils.db import load_team_match, load_dim_team, load_dim_season
from utils.models import get_regression_model

# Render Admin Sidebar
render_admin_sidebar("Performance Analysis")

# ── Global CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
html, body, .stApp {
}

/* Card Container */
.pa-card, [class*="st-key-card_"] {
    background: #FFFFFF;
    border: 1px solid #D5DBE6;
    border-radius: 12px;
    padding: 16px 18px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
    margin-bottom: 16px;
    box-sizing: border-box;
}

/* Metric Cards */
.pa-metric-box {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 18px 20px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
    box-sizing: border-box;
    height: 100%;
}
.pa-metric-title {
    color: #64748B;
    font-size: 0.8rem;
    font-weight: 500;
    margin-bottom: 4px;
}
.pa-metric-val {
    color: #0F172A;
    font-size: 1.85rem;
    font-weight: 700;
    line-height: 1.15;
    margin-bottom: 4px;
}
.pa-metric-sub {
    color: #94A3B8;
    font-size: 0.76rem;
}

/* Comparison Table */
.pa-table {
    width: 100%;
    border-collapse: collapse;
}
.pa-table th {
    text-align: left;
    color: #64748B;
    font-size: 0.78rem;
    font-weight: 600;
    padding: 8px 10px 10px 10px;
    border-bottom: 1px solid #E2E8F0;
}
.pa-table td {
    padding: 11px 10px;
    color: #0F172A;
    font-size: 0.86rem;
    border-bottom: 1px solid #F1F5F9;
}
.pa-table tr:last-child td {
    border-bottom: none;
}

/* Primary Button */
div[data-testid="stButton"] > button[kind="primary"] {
    background-color: #2563EB !important;
    color: #FFFFFF !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    height: 40px !important;
    border: none !important;
}

/* Hide streamlit radio label margin */
div[data-testid="stRadio"] > label {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

# ── Top Header Bar ──────────────────────────────────────────────────────────
c_head_l, c_head_r = st.columns([3, 1])
with c_head_l:
    st.markdown("<h1 style='color:#0F172A; font-size:2.2rem; font-weight:700; margin:0 0 4px 0;'>Performance Analysis</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#64748B; font-size:0.92rem; margin:0 0 16px 0;'>Regression analysis of team performance • Lab 4</p>", unsafe_allow_html=True)

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

# ── Load Reference Data ─────────────────────────────────────────────────────
teams_list = ["All teams"] + sorted(load_dim_team()["Team_Name"].tolist())
seasons_list = ["All seasons"] + load_dim_season()["Season_Name"].tolist()

# ── 1. Top Control Panel Container ──────────────────────────────────────────
with st.container(key="card_pa_controls"):
    cp1, cp2, cp3, cp4, cp5 = st.columns([1.3, 1.1, 1.25, 1.25, 0.9])

    with cp1:
        st.markdown("<div style='font-size:0.78rem; font-weight:600; color:#334155; margin-bottom:6px;'>Target variable</div>", unsafe_allow_html=True)
        target_var = st.selectbox("Target variable", ["Goals scored", "Points scored"], index=0, label_visibility="collapsed", key="pa_target_var")

    with cp2:
        st.markdown("<div style='font-size:0.78rem; font-weight:600; color:#334155; margin-bottom:6px;'>Model</div>", unsafe_allow_html=True)
        model_type = st.radio("Model", ["Simple", "Multiple"], index=1, horizontal=True, label_visibility="collapsed", key="pa_model_type")

    with cp3:
        st.markdown("<div style='font-size:0.78rem; font-weight:600; color:#334155; margin-bottom:6px;'>Highlight team</div>", unsafe_allow_html=True)
        hl_team = st.selectbox("Highlight team", teams_list, index=0, label_visibility="collapsed", key="pa_hl_team")

    with cp4:
        st.markdown("<div style='font-size:0.78rem; font-weight:600; color:#334155; margin-bottom:6px;'>Highlight season</div>", unsafe_allow_html=True)
        hl_season = st.selectbox("Highlight season", seasons_list, index=0, label_visibility="collapsed", key="pa_hl_season")

    with cp5:
        st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)
        run_btn = st.button("Run model", type="primary", use_container_width=True, key="pa_run_btn")

    # Feature Checkboxes
    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
    f_row_l, f_row_r = st.columns([0.8, 4.2])
    with f_row_l:
        st.markdown("<div style='font-size:0.8rem; font-weight:600; color:#64748B; padding-top:4px;'>Features</div>", unsafe_allow_html=True)

    with f_row_r:
        fc1, fc2, fc3, fc4, fc5 = st.columns(5)
        with fc1:
            use_shots = st.checkbox("Shots", value=True, key="pa_feat_shots", disabled=(model_type == "Simple"))
        with fc2:
            use_corners = st.checkbox("Corners", value=(model_type == "Multiple"), key="pa_feat_corners", disabled=(model_type == "Simple"))
        with fc3:
            use_poss = st.checkbox("Possession", value=(model_type == "Multiple"), key="pa_feat_poss", disabled=(model_type == "Simple"))
        with fc4:
            use_fouls = st.checkbox("Fouls", value=(model_type == "Multiple"), key="pa_feat_fouls", disabled=(model_type == "Simple"))
        with fc5:
            use_home = st.checkbox("Home / Away", value=False, key="pa_feat_home", disabled=(model_type == "Simple"))

    st.markdown("""
    <div style="font-size:0.75rem; color:#94A3B8; margin-top:10px; border-top:1px solid #F1F5F9; padding-top:8px;">
    The model is trained on all 20,520 team-match records and tested on a held-out 25%. Team and season only change what is highlighted below.
    </div>
    """, unsafe_allow_html=True)

# ── 2. Determine Features & Train / Retrieve Model ──────────────────────────
target_col = "Points" if target_var == "Points scored" else "Goals_For"
target_label = "points" if target_var == "Points scored" else "goals"

if model_type == "Simple":
    active_features = ["Shots"]
else:
    active_features = []
    if use_shots: active_features.append("Shots")
    if use_corners: active_features.append("Corners")
    if use_poss: active_features.append("Possession")
    if use_fouls: active_features.append("Fouls")
    if use_home: active_features.append("Is_Home")
    if not active_features:
        active_features = ["Shots"]

# Retrieve cached trained models
reg_res = get_regression_model(tuple(active_features), target=target_col)
reg_simple = get_regression_model(("Shots",), target=target_col)
reg_multi_standard = get_regression_model(("Shots", "Corners", "Possession", "Fouls"), target=target_col)

# Metrics
y_act = reg_res["y_actual"]
y_pred = reg_res["y_pred"]
r2_val = reg_res["r2"]
mae_val = float(mean_absolute_error(y_act, y_pred))
rmse_val = reg_res["rmse"]
n_test = reg_res["n_test"]
n_train = reg_res["n_train"]

test_df = reg_res["test_df"].copy()
test_df["Residual"] = test_df["y_actual"] - test_df["y_pred"]

if run_btn:
    st.toast(f"⚡ Model trained on 20,520 records! (R²: {r2_val:.3f}, MAE: {mae_val:.3f}, RMSE: {rmse_val:.3f})")

# ── 3. KPI Metric Cards (4 Columns) ─────────────────────────────────────────
m1, m2, m3, m4 = st.columns(4)

with m1:
    st.markdown(f"""<div class="pa-metric-box">
<div class="pa-metric-title">R² score</div>
<div class="pa-metric-val">{r2_val:.3f}</div>
<div class="pa-metric-sub">Share of variation explained</div>
</div>""", unsafe_allow_html=True)

with m2:
    st.markdown(f"""<div class="pa-metric-box">
<div class="pa-metric-title">MAE</div>
<div class="pa-metric-val">{mae_val:.3f}</div>
<div class="pa-metric-sub">Mean absolute error, {target_label}</div>
</div>""", unsafe_allow_html=True)

with m3:
    st.markdown(f"""<div class="pa-metric-box">
<div class="pa-metric-title">RMSE</div>
<div class="pa-metric-val">{rmse_val:.3f}</div>
<div class="pa-metric-sub">Root mean squared error, {target_label}</div>
</div>""", unsafe_allow_html=True)

with m4:
    st.markdown(f"""<div class="pa-metric-box">
<div class="pa-metric-title">Test rows</div>
<div class="pa-metric-val">{n_test:,}</div>
<div class="pa-metric-sub">Train rows {n_train:,}</div>
</div>""", unsafe_allow_html=True)

st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

# ── 4. Charts Row (Actual vs Predicted + Residual Distribution) ──────────────
c_act, c_res = st.columns(2)

# Left Chart: Actual vs Predicted
with c_act:
    with st.container(key="card_actual_vs_predicted"):
        st.markdown(f"**Actual vs predicted {target_label}**")
        st.caption("Test set sample. Dashed line = perfect prediction.")

        # Sample for performance / visual cleanliness
        plot_sample = test_df.sample(min(1200, len(test_df)), random_state=42).copy()

        fig_avp = go.Figure()

        # Base points
        is_highlighted = pd.Series(False, index=plot_sample.index)
        if hl_team != "All teams":
            is_highlighted = is_highlighted | (plot_sample["Team_Name"] == hl_team)
        if hl_season != "All seasons":
            is_highlighted = is_highlighted | (plot_sample["Season_Name"] == hl_season)

        if is_highlighted.any() and (hl_team != "All teams" or hl_season != "All seasons"):
            normal_pts = plot_sample[~is_highlighted]
            hl_pts = plot_sample[is_highlighted]

            fig_avp.add_trace(go.Scatter(
                x=normal_pts["y_pred"],
                y=normal_pts["y_actual"],
                mode="markers",
                marker=dict(color="#93C5FD", size=6, opacity=0.35),
                name="Other Matches",
                hoverinfo="skip"
            ))
            fig_avp.add_trace(go.Scatter(
                x=hl_pts["y_pred"],
                y=hl_pts["y_actual"],
                mode="markers",
                marker=dict(color="#1D4ED8", size=8, opacity=0.85, line=dict(color="#FFFFFF", width=1)),
                name=f"Highlighted ({hl_team} / {hl_season})",
                hoverinfo="text",
                hovertext=[f"{row['Team_Name']} ({row['Season_Name']})<br>Actual: {row['y_actual']} | Pred: {row['y_pred']:.2f}" for _, row in hl_pts.iterrows()]
            ))
        else:
            fig_avp.add_trace(go.Scatter(
                x=plot_sample["y_pred"],
                y=plot_sample["y_actual"],
                mode="markers",
                marker=dict(color="#93C5FD", size=6, opacity=0.5),
                hoverinfo="text",
                hovertext=[f"{row['Team_Name']} ({row['Season_Name']})<br>Actual: {row['y_actual']} | Pred: {row['y_pred']:.2f}" for _, row in plot_sample.iterrows()]
            ))

        # Diagonal dashed line (perfect prediction)
        max_axis = float(max(plot_sample["y_actual"].max(), plot_sample["y_pred"].max()) * 1.15) if not plot_sample.empty else 5.5
        fig_avp.add_trace(go.Scatter(
            x=[0, max_axis],
            y=[0, max_axis],
            mode="lines",
            line=dict(color="#334155", width=1.5, dash="dash"),
            showlegend=False,
            hoverinfo="skip"
        ))

        fig_avp.update_layout(
            height=265,
            margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
            xaxis=dict(title=dict(text=f"Predicted {target_label}", font=dict(size=11, color="#64748B")), showgrid=False, range=[-0.2, max_axis]),
            yaxis=dict(title=dict(text=f"Actual {target_label}", font=dict(size=11, color="#64748B")), showgrid=True, gridcolor="#F1F5F9", range=[-0.2, max_axis * 1.2]),
        )
        st.plotly_chart(fig_avp, use_container_width=True, config={"displayModeBar": False})

# Right Chart: Residual Distribution
with c_res:
    with st.container(key="card_residual_distribution"):
        st.markdown("**Residual distribution**")
        st.caption(f"Actual minus predicted {target_label}, all test rows.")

        # Histogram of residuals
        residuals = test_df["Residual"]
        
        # Generate discrete bins
        r_min, r_max = float(residuals.min()), float(residuals.max())
        counts, bin_edges = np.histogram(residuals, bins=18, range=(r_min, r_max))
        bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])

        fig_res = go.Figure(go.Bar(
            x=bin_centers,
            y=counts,
            marker=dict(color="#3B82F6", line=dict(color="#FFFFFF", width=1)),
            width=float((bin_edges[1] - bin_edges[0]) * 0.85)
        ))

        fig_res.update_layout(
            height=265,
            margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
            xaxis=dict(title=dict(text=f"Residual ({target_label})", font=dict(size=11, color="#64748B")), showgrid=False, range=[r_min - 0.5, r_max + 0.5]),
            yaxis=dict(showgrid=True, gridcolor="#F1F5F9", showticklabels=False),
        )
        st.plotly_chart(fig_res, use_container_width=True, config={"displayModeBar": False})

st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)

# ── 5. Bottom Section Row (Model Comparison + Coefficients) ─────────────────
c_comp, c_coef = st.columns(2)

# Left Card: Model Comparison
with c_comp:
    r2_simp = reg_simple["r2"]
    mae_simp = float(mean_absolute_error(reg_simple["y_actual"], reg_simple["y_pred"]))
    rmse_simp = reg_simple["rmse"]

    r2_mult = reg_multi_standard["r2"]
    mae_mult = float(mean_absolute_error(reg_multi_standard["y_actual"], reg_multi_standard["y_pred"]))
    rmse_mult = reg_multi_standard["rmse"]

    is_custom = set(active_features) != {"Shots"} and set(active_features) != {"Shots", "Corners", "Possession", "Fouls"}
    
    custom_row_html = ""
    if is_custom:
        custom_row_html = f"""<tr style="background:#EFF6FF;">
<td style="font-weight:700; color:#1D4ED8;">Active Selection ({len(active_features)} features)</td>
<td style="font-weight:700; color:#1D4ED8;">{r2_val:.3f}</td>
<td style="font-weight:700; color:#1D4ED8;">{mae_val:.3f}</td>
<td style="font-weight:700; color:#1D4ED8;">{rmse_val:.3f}</td>
</tr>"""

    st.markdown(f"""<div class="pa-card">
<h3 style="color:#0F172A; font-size:1.02rem; font-weight:700; margin:0 0 12px 0;">Model comparison</h3>
<table class="pa-table">
<thead>
<tr>
<th>Model</th>
<th>R²</th>
<th>MAE</th>
<th>RMSE</th>
</tr>
</thead>
<tbody>
<tr style="{'background:#EFF6FF;' if model_type == 'Simple' else ''}">
<td style="{'font-weight:700;' if model_type == 'Simple' else ''}">Simple (Shots)</td>
<td>{r2_simp:.3f}</td>
<td>{mae_simp:.3f}</td>
<td>{rmse_simp:.3f}</td>
</tr>
<tr style="{'background:#EFF6FF;' if model_type == 'Multiple' and not is_custom else ''}">
<td style="font-weight:700;">Multiple (4 features)</td>
<td style="font-weight:700;">{r2_mult:.3f}</td>
<td style="font-weight:700;">{mae_mult:.3f}</td>
<td style="font-weight:700;">{rmse_mult:.3f}</td>
</tr>
{custom_row_html}
</tbody>
</table>
<div style="font-size:0.78rem; color:#64748B; margin-top:14px;">
Adding corners, possession and fouls raises R² from {r2_simp:.2f} to {r2_mult:.2f}.
</div>
</div>""", unsafe_allow_html=True)

# Right Card: Coefficients
with c_coef:
    with st.container(key="card_coefficients"):
        st.markdown("**Coefficients**")
        st.caption(f"{target_label.capitalize()} added per extra unit of each feature.")

        coef_dict = reg_res["coef"]
        max_c = max(max(abs(v) for v in coef_dict.values()), 0.08)

        coef_rows_html = ""
        for feat, val in coef_dict.items():
            pct = min(100, int((abs(val) / max_c) * 100))
            pct = max(pct, 2)  # minimum visible line
            coef_rows_html += f"""<div style="display:flex; align-items:center; margin-bottom:12px; font-size:0.85rem;">
<div style="width:95px; color:#1E293B; font-weight:500;">{feat}</div>
<div style="flex:1; background:#EEF2F6; height:8px; border-radius:4px; margin:0 14px; position:relative;">
<div style="background:#2563EB; height:8px; width:{pct}%; border-radius:4px;"></div>
</div>
<div style="width:48px; text-align:right; font-weight:700; color:#0F172A; font-size:0.86rem;">{val:.3f}</div>
</div>"""
        st.markdown(coef_rows_html, unsafe_allow_html=True)

st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)

# ── 6. Technical Details Accordion / Card ────────────────────────────────────
feat_str = ", ".join(active_features)
intercept_val = reg_res["intercept"]

st.markdown(f"""<div class="pa-card">
<div style="display:flex; align-items:center; gap:8px; margin-bottom:12px; cursor:pointer;">
<span style="font-size:0.8rem; color:#64748B;">▼</span>
<span style="color:#0F172A; font-size:0.96rem; font-weight:700;">Technical details</span>
</div>
<div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:16px; font-size:0.82rem;">
<div>
<div style="color:#64748B; font-size:0.74rem; margin-bottom:2px;">Algorithm</div>
<div style="color:#0F172A; font-weight:500;">Linear regression, ordinary least squares (scikit-learn)</div>
</div>
<div>
<div style="color:#64748B; font-size:0.74rem; margin-bottom:2px;">Target</div>
<div style="color:#0F172A; font-weight:500;">{target_col}</div>
</div>
<div>
<div style="color:#64748B; font-size:0.74rem; margin-bottom:2px;">Features</div>
<div style="color:#0F172A; font-weight:500;">{feat_str}</div>
</div>
<div>
<div style="color:#64748B; font-size:0.74rem; margin-bottom:2px;">Intercept</div>
<div style="color:#0F172A; font-weight:500;">{intercept_val:.3f}</div>
</div>
<div>
<div style="color:#64748B; font-size:0.74rem; margin-bottom:2px;">Split</div>
<div style="color:#0F172A; font-weight:500;">75% train, 25% test, random_state 0</div>
</div>
<div>
<div style="color:#64748B; font-size:0.74rem; margin-bottom:2px;">Data</div>
<div style="color:#0F172A; font-weight:500;">Fact_Team_Match, 20,520 rows</div>
</div>
</div>
</div>""", unsafe_allow_html=True)
