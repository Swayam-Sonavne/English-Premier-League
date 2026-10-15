"""
pages/5_Team_Analytics.py — Admin Page 5: Team Analytics
Matches the UI Inspiration Mockup for Clustering (Labs 7 & 8):
  1. Breadcrumbs & Metadata Tag Pills
  2. Top Control Panel (Level, Method, K clusters, Highlight team/season, Feature checkboxes, Run button)
  3. 6 KPI Metric Cards (Recommended K, Silhouette KM, Silhouette Agglo, Adjusted Rand, PCA Variance, Team-Seasons)
  4. 4 Visual Charts in 2x2 Grid (Elbow Method, Silhouette by K, 2D PCA Cluster Map, Ward Dendrogram)
  5. Cluster Profiles Table (Centroids in original units + Total row)
  6. Centroid Heatmap (Z-scores) + K-Means vs Agglomerative Contingency Table
  7. Cluster Membership Card (Most Frequent Teams & Top Team-Seasons)
  8. Season Breakdown Card (when a season is highlighted)
  9. Technical Details Box
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.cluster.hierarchy import dendrogram, linkage, fcluster
from sklearn.metrics import silhouette_score, adjusted_rand_score
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

st.set_page_config(
    page_title="Team Analytics — Analytics & DWM",
    page_icon="👥",
    layout="wide",
)

# Role Access Guard
if st.session_state.get("auth_role") != "admin":
    st.warning("🔒 Administrator authentication required to view this technical DWM page.")
    if st.button("🔑 Login as Administrator", key="ta_auth_req_btn"):
        st.session_state["auth_role"] = "admin"
        st.rerun()
    st.stop()

from utils.admin_views import render_admin_sidebar
from utils.db import load_team_profiles, load_dim_team, load_dim_season
from utils.models import (
    get_cluster_recommendations,
    CLUSTER_FEATURES,
)

# Render Admin Sidebar
render_admin_sidebar("Team Analytics")

# ── Global CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
html, body, .stApp {
}

/* Card Container */
.ta-card, [class*="st-key-card_"] {
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: 12px;
    padding: 16px 18px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
    margin-bottom: 16px;
    box-sizing: border-box;
}

/* Metric Cards */
.ta-metric-box {
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: 12px;
    padding: 16px 18px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
    box-sizing: border-box;
    height: 100%;
}
.ta-metric-title {
    color: var(--mute);
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    margin-bottom: 3px;
}
.ta-metric-val {
    color: var(--ink);
    font-size: 1.7rem;
    font-weight: 700;
    line-height: 1.15;
    margin-bottom: 3px;
}
.ta-metric-sub {
    color: var(--mute);
    font-size: 0.74rem;
}

/* Meta Pill */
.meta-pill {
    background: var(--chip);
    color: var(--mute);
    font-size: 0.75rem;
    padding: 3px 10px;
    border-radius: 6px;
    display: inline-block;
    margin-right: 6px;
    margin-bottom: 6px;
    font-weight: 500;
}
.meta-pill b {
    color: var(--ink);
    font-weight: 700;
}

/* Table */
.ta-table {
    width: 100%;
    border-collapse: collapse;
}
.ta-table th {
    text-align: left;
    color: var(--mute);
    font-size: 0.74rem;
    font-weight: 700;
    text-transform: uppercase;
    padding: 8px 10px 10px 10px;
    border-bottom: 1px solid var(--line);
}
.ta-table td {
    padding: 9px 10px;
    color: var(--ink);
    font-size: 0.84rem;
    border-bottom: 1px solid var(--line);
}
.ta-table tr:last-child td {
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

/* Small Card Header Badge */
.ta-badge {
    background: var(--chip);
    color: var(--mute);
    font-size: 0.7rem;
    font-weight: 700;
    padding: 2px 7px;
    border-radius: 4px;
    text-transform: uppercase;
}
</style>
""", unsafe_allow_html=True)

# ── Top Breadcrumbs & Header Bar ─────────────────────────────────────────────
st.markdown("<div style='color:var(--mute); font-size:0.8rem; margin-bottom:2px;'>Admin / Team Analytics</div>", unsafe_allow_html=True)

c_head_l, c_head_r = st.columns([3, 1.2])
with c_head_l:
    pass

with c_head_r:
    st.markdown("""
    <div style="display:flex; justify-content:flex-end; align-items:center; gap:8px; height:100%; padding-top:6px;">
        <span class="ta-badge">LABS 7 · 8</span>
        <div style="background:#ECFDF5; color:#059669; font-size:0.76rem; font-weight:600; padding:4px 10px; border-radius:20px; display:flex; align-items:center; gap:5px;">
            <span style="height:6px; width:6px; background:#10B981; border-radius:50%; display:inline-block;"></span> System Online
        </div>
        <div style="background:var(--chip); color:var(--ink); font-size:0.78rem; font-weight:600; padding:4px 10px; border-radius:20px;">
            Admin
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── Load Reference Data ─────────────────────────────────────────────────────
raw_prof = load_team_profiles()
recs = get_cluster_recommendations()

team_list = ["All teams"] + sorted(raw_prof["Team_Name"].unique().tolist())
season_list = ["All seasons"] + sorted(raw_prof["Season_Name"].unique().tolist())

# ── 1. Top Control Panel Container ──────────────────────────────────────────
with st.container(key="card_ta_controls"):
    cp1, cp2, cp3, cp4, cp5, cp6 = st.columns([1.1, 1.3, 1.2, 1.1, 1.1, 0.9])

    with cp1:
        st.markdown("<div style='font-size:0.78rem; font-weight:600; color:var(--ink); margin-bottom:6px;'>Level</div>", unsafe_allow_html=True)
        sel_level = st.selectbox("Level", ["Team + Season", "Team all-time"], index=0, label_visibility="collapsed", key="ta_level")

    with cp2:
        st.markdown("<div style='font-size:0.78rem; font-weight:600; color:var(--ink); margin-bottom:6px;'>Method</div>", unsafe_allow_html=True)
        sel_method = st.radio("Method", ["K-Means", "Agglomerative"], index=0, horizontal=True, label_visibility="collapsed", key="ta_method")

    with cp3:
        st.markdown("<div style='font-size:0.78rem; font-weight:600; color:var(--ink); margin-bottom:6px;'>Clusters K (recommended 2)</div>", unsafe_allow_html=True)
        k_val = st.number_input("Clusters K", min_value=2, max_value=8, value=2, step=1, label_visibility="collapsed", key="ta_k_val")

    with cp4:
        st.markdown("<div style='font-size:0.78rem; font-weight:600; color:var(--ink); margin-bottom:6px;'>Highlight team</div>", unsafe_allow_html=True)
        hl_team = st.selectbox("Highlight team", team_list, index=0, label_visibility="collapsed", key="ta_hl_team")

    with cp5:
        st.markdown("<div style='font-size:0.78rem; font-weight:600; color:var(--ink); margin-bottom:6px;'>Highlight season</div>", unsafe_allow_html=True)
        hl_season = st.selectbox("Highlight season", season_list, index=0, label_visibility="collapsed", key="ta_hl_season")

    with cp6:
        st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)
        run_btn = st.button("Run clustering", type="primary", key="ta_run_btn")

    # Feature Checkboxes
    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
    f_row_l, f_row_r = st.columns([0.8, 4.2])
    with f_row_l:
        st.markdown("<div style='font-size:0.78rem; font-weight:700; color:var(--mute); padding-top:4px;'>FEATURES</div>", unsafe_allow_html=True)

    with f_row_r:
        fc1, fc2, fc3, fc4, fc5, fc6, fc7 = st.columns(7)
        feat_map = {
            "Goals_For_mean": fc1.checkbox("Goals for", value=True, key="ta_f_gf"),
            "Goals_Against_mean": fc2.checkbox("Goals against", value=True, key="ta_f_ga"),
            "Shots_mean": fc3.checkbox("Shots", value=True, key="ta_f_sh"),
            "Possession_mean": fc4.checkbox("Possession %", value=True, key="ta_f_poss"),
            "Corners_mean": fc5.checkbox("Corners", value=True, key="ta_f_cor"),
            "Fouls_mean": fc6.checkbox("Fouls", value=True, key="ta_f_fls"),
            "Pts_per_Match": fc7.checkbox("Points / match", value=True, key="ta_f_pts"),
        }

    active_features = [f for f, active in feat_map.items() if active]
    if not active_features:
        active_features = CLUSTER_FEATURES  # fallback

# ── Dynamic Profile Aggregation & Clustering ────────────────────────────────
if sel_level == "Team all-time":
    # Aggregate by team across all seasons
    working_df = raw_prof.groupby("Team_Name", as_index=False)[CLUSTER_FEATURES].mean()
    working_df["Season_Name"] = "All-Time"
    obs_count = len(working_df)
    unit_str = "team all-time"
else:
    working_df = raw_prof.copy()
    obs_count = len(working_df)
    unit_str = "team-season"

# Metadata Strip
st.markdown(f"""
<div style="margin-bottom:14px;">
    <span class="meta-pill">source <b>Fact_Team_Match</b></span>
    <span class="meta-pill">unit <b>{unit_str}</b></span>
    <span class="meta-pill">observations <b>{obs_count}</b></span>
    <span class="meta-pill">features <b>{len(active_features)}</b></span>
    <span class="meta-pill">scaling <b>StandardScaler</b></span>
    <span class="meta-pill">K-Means <b>n_init 10 • seed 0</b></span>
    <span class="meta-pill">linkage <b>Ward</b></span>
</div>
""", unsafe_allow_html=True)

# Compute Clustering
scaler = StandardScaler()
Z_scaled = scaler.fit_transform(working_df[active_features].values)

# K-Means
km_model = KMeans(n_clusters=k_val, n_init=10, random_state=0).fit(Z_scaled)
km_labels = km_model.labels_
km_sil = float(silhouette_score(Z_scaled, km_labels))

# Agglomerative
Z_link = linkage(Z_scaled, method="ward")
agg_labels_raw = fcluster(Z_link, k_val, criterion="maxclust")
agg_labels = (agg_labels_raw - 1)  # 0-indexed
agg_sil = float(silhouette_score(Z_scaled, agg_labels))

# Adjusted Rand
ari_val = float(adjusted_rand_score(km_labels, agg_labels))

# PCA 2D
pca = PCA(n_components=2, random_state=0)
pca_coords = pca.fit_transform(Z_scaled)
pca_var1 = round(pca.explained_variance_ratio_[0] * 100, 1)
pca_var2 = round(pca.explained_variance_ratio_[1] * 100, 1)
pca_total_var = round(sum(pca.explained_variance_ratio_) * 100, 1)

working_df["PC1"] = pca_coords[:, 0]
working_df["PC2"] = pca_coords[:, 1]
working_df["KM_Cluster"] = km_labels
working_df["Agg_Cluster"] = agg_labels

# Set active cluster based on chosen method
if sel_method == "K-Means":
    working_df["Active_Cluster"] = km_labels
else:
    working_df["Active_Cluster"] = agg_labels

# Rank clusters by mean points per match so Cluster 1 = lower, Cluster K = top
cluster_rank_order = working_df.groupby("Active_Cluster")["Pts_per_Match"].mean().sort_values().index.tolist()
cluster_rank_map = {old_c: new_rank for new_rank, old_c in enumerate(cluster_rank_order)}
working_df["Ranked_Cluster"] = working_df["Active_Cluster"].map(cluster_rank_map)

cluster_palette = ["#3B82F6", "#F59E0B", "#10B981", "#8B5CF6", "#EC4899", "#14B8A6", "#6366F1", "#F97316"]

if run_btn:
    st.toast(f"⚡ Clustering updated: {sel_method} (K = {k_val}, Silhouette: {km_sil if sel_method=='K-Means' else agg_sil:.3f})")

# ── 3. KPI Metric Strip (6 Columns) ─────────────────────────────────────────
m1, m2, m3, m4, m5, m6 = st.columns(6)

with m1:
    st.markdown(f"""<div class="ta-metric-box">
<div class="ta-metric-title">RECOMMENDED K</div>
<div class="ta-metric-val">{recs['recommended_k']}</div>
<div class="ta-metric-sub">highest silhouette</div>
</div>""", unsafe_allow_html=True)

with m2:
    st.markdown(f"""<div class="ta-metric-box">
<div class="ta-metric-title">SILHOUETTE K-MEANS</div>
<div class="ta-metric-val" style="color:var(--acc);">{km_sil:.3f}</div>
<div class="ta-metric-sub">K = {k_val}</div>
</div>""", unsafe_allow_html=True)

with m3:
    st.markdown(f"""<div class="ta-metric-box">
<div class="ta-metric-title">SILHOUETTE AGGLO.</div>
<div class="ta-metric-val" style="color:#EA580C;">{agg_sil:.3f}</div>
<div class="ta-metric-sub">K = {k_val}</div>
</div>""", unsafe_allow_html=True)

with m4:
    st.markdown(f"""<div class="ta-metric-box">
<div class="ta-metric-title">ADJUSTED RAND</div>
<div class="ta-metric-val">{ari_val:.3f}</div>
<div class="ta-metric-sub">method agreement</div>
</div>""", unsafe_allow_html=True)

with m5:
    st.markdown(f"""<div class="ta-metric-box">
<div class="ta-metric-title">PCA VARIANCE</div>
<div class="ta-metric-val">{pca_total_var:.1f}%</div>
<div class="ta-metric-sub">first two components</div>
</div>""", unsafe_allow_html=True)

with m6:
    st.markdown(f"""<div class="ta-metric-box">
<div class="ta-metric-title">{ 'TEAMS' if sel_level == 'Team all-time' else 'TEAM-SEASONS' }</div>
<div class="ta-metric-val">{obs_count}</div>
<div class="ta-metric-sub">{ '20 all-time clubs' if sel_level == 'Team all-time' else '20 teams × 27 seasons' }</div>
</div>""", unsafe_allow_html=True)

st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

# ── 4. Charts Grid Row 1 (Elbow Method & Silhouette by K) ───────────────────
r1_c1, r1_c2 = st.columns(2)

# Chart 1: Elbow Method
with r1_c1:
    with st.container(key="card_elbow_method"):
        st.markdown("""
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
            <h3 style="color:var(--ink); font-size:1.02rem; font-weight:700; margin:0;">Elbow method · inertia</h3>
            <span class="ta-badge">LAB 7</span>
        </div>
        """, unsafe_allow_html=True)

        fig_elbow = go.Figure()
        fig_elbow.add_trace(go.Scatter(
            x=recs["ks"],
            y=recs["inertias"],
            mode="lines+markers",
            line=dict(color="#2563EB", width=2.5),
            marker=dict(color="#2563EB", size=7),
            hoverinfo="x+y"
        ))
        fig_elbow.update_layout(
            height=245,
            margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(title=dict(text="Number of clusters K", font=dict(size=11, color="#64748B")), showgrid=False, dtick=1),
            yaxis=dict(showgrid=True, gridcolor="#F1F5F9"),
        )
        st.plotly_chart(fig_elbow, use_container_width=True, config={"displayModeBar": False})

# Chart 2: Silhouette Score by K
with r1_c2:
    with st.container(key="card_silhouette_score"):
        st.markdown("""
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
            <h3 style="color:var(--ink); font-size:1.02rem; font-weight:700; margin:0;">Silhouette score by K</h3>
            <span class="ta-badge">LAB 7</span>
        </div>
        """, unsafe_allow_html=True)

        fig_sil = go.Figure()
        fig_sil.add_trace(go.Scatter(
            x=recs["ks"],
            y=recs["silhouettes"],
            mode="lines+markers",
            line=dict(color="#EA580C", width=2.5),
            marker=dict(color="#EA580C", size=7),
            hoverinfo="x+y"
        ))
        rec_k = recs["recommended_k"]
        rec_sil = recs["silhouettes"][recs["ks"].index(rec_k)]
        fig_sil.add_trace(go.Scatter(
            x=[rec_k], y=[rec_sil],
            mode="markers+text",
            marker=dict(color="#FFFFFF", size=10, line=dict(color="#EA580C", width=2.5)),
            text=[f"K = {rec_k} (recommended)"],
            textposition="top right",
            hoverinfo="skip",
            showlegend=False
        ))

        fig_sil.update_layout(
            height=245,
            margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(title=dict(text="Number of clusters K", font=dict(size=11, color="#64748B")), showgrid=False, dtick=1),
            yaxis=dict(showgrid=True, gridcolor="#F1F5F9", range=[0.15, 0.42]),
            showlegend=False
        )
        st.plotly_chart(fig_sil, use_container_width=True, config={"displayModeBar": False})

st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)

# ── 5. Charts Grid Row 2 (PCA Cluster Map & Ward Dendrogram) ─────────────────
r2_c1, r2_c2 = st.columns(2)

# Chart 3: Cluster Map (PCA)
with r2_c1:
    with st.container(key="card_cluster_map_pca"):
        st.markdown(f"""
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
            <h3 style="color:var(--ink); font-size:1.02rem; font-weight:700; margin:0;">Cluster map · {sel_method}, K = {k_val}</h3>
            <span class="ta-badge">PCA PROJECTION</span>
        </div>
        """, unsafe_allow_html=True)

        fig_pca = go.Figure()
        
        # Highlight filter check
        is_filtering = (hl_team != "All teams" or hl_season != "All seasons")

        # Plot base clusters
        for rank_idx in range(k_val):
            c_sub = working_df[working_df["Ranked_Cluster"] == rank_idx]
            c_name = f"Cluster {rank_idx + 1} - {'Lower-performing' if rank_idx == 0 else ('High-performing' if rank_idx == k_val-1 else 'Mid-tier')} (n={len(c_sub)})"
            c_color = cluster_palette[rank_idx % len(cluster_palette)]

            pt_opacity = 0.15 if is_filtering else 0.65
            pt_size = 5 if is_filtering else 6

            fig_pca.add_trace(go.Scatter(
                x=c_sub["PC1"],
                y=c_sub["PC2"],
                mode="markers",
                marker=dict(color=c_color, size=pt_size, opacity=pt_opacity),
                name=c_name,
                hoverinfo="text",
                hovertext=[f"{row['Team_Name']} ({row['Season_Name']})<br>Cluster {rank_idx+1}<br>Points/Match: {row['Pts_per_Match']:.2f}" for _, row in c_sub.iterrows()]
            ))

        # Highlight points prominently when filtered
        if is_filtering:
            hl_sub = working_df.copy()
            if hl_team != "All teams": hl_sub = hl_sub[hl_sub["Team_Name"] == hl_team]
            if hl_season != "All seasons": hl_sub = hl_sub[hl_sub["Season_Name"] == hl_season]
            
            if not hl_sub.empty:
                # Group highlighted points by cluster to show their respective cluster colors and team names!
                for rank_idx in range(k_val):
                    hl_c_sub = hl_sub[hl_sub["Ranked_Cluster"] == rank_idx]
                    if not hl_c_sub.empty:
                        c_color = cluster_palette[rank_idx % len(cluster_palette)]
                        fig_pca.add_trace(go.Scatter(
                            x=hl_c_sub["PC1"],
                            y=hl_c_sub["PC2"],
                            mode="markers+text",
                            marker=dict(
                                color=c_color,
                                size=12,
                                line=dict(color="#0F172A", width=2)
                            ),
                            text=hl_c_sub["Team_Name"],
                            textposition="top center",
                            textfont=dict(size=9.5, color="#0F172A", family="sans-serif"),
                            name=f"★ {hl_season if hl_season!='All seasons' else hl_team} (Cluster {rank_idx+1})",
                            hoverinfo="text",
                            hovertext=[f"⭐ {row['Team_Name']} ({row['Season_Name']})<br><b>Cluster {rank_idx+1}</b> | Pts/Match: {row['Pts_per_Match']:.2f}<br>GF: {row['Goals_For_mean']:.2f} | GA: {row['Goals_Against_mean']:.2f}" for _, row in hl_c_sub.iterrows()]
                        ))

        fig_pca.update_layout(
            height=280,
            margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(title=dict(text=f"PC1 ({pca_var1}% of variance)", font=dict(size=11, color="#64748B")), showgrid=True, gridcolor="#F1F5F9"),
            yaxis=dict(title=dict(text=f"PC2 ({pca_var2}%)", font=dict(size=11, color="#64748B")), showgrid=True, gridcolor="#F1F5F9"),
            legend=dict(orientation="v", yanchor="top", y=0.98, xanchor="left", x=0.02, bgcolor="rgba(255,255,255,0.88)", font=dict(size=8.5))
        )
        st.plotly_chart(fig_pca, use_container_width=True, config={"displayModeBar": False})

        if is_filtering and not hl_sub.empty:
            hl_title = f"Season {hl_season}" if hl_season != "All seasons" else f"Team {hl_team}"
            if hl_team != "All teams" and hl_season != "All seasons":
                hl_title = f"{hl_team} ({hl_season})"
            
            # Summary by cluster
            c_summary_items = []
            for rank_idx in range(k_val):
                c_teams = hl_sub[hl_sub["Ranked_Cluster"] == rank_idx]["Team_Name"].tolist()
                c_color = cluster_palette[rank_idx % len(cluster_palette)]
                if c_teams:
                    c_summary_items.append(f"<span style='color:{c_color}; font-weight:700;'>Cluster {rank_idx+1} ({len(c_teams)}):</span> " + ", ".join(c_teams))
            
            summary_html = " &nbsp;|&nbsp; ".join(c_summary_items)
            st.markdown(f"""<div style="background:#FEF2F2; border:1px solid #FECACA; border-radius:8px; padding:8px 12px; font-size:0.8rem; color:#991B1B; margin-top:6px;">
    <b>📌 Classification for {hl_title}:</b><br>{summary_html}
    </div>""", unsafe_allow_html=True)

# Chart 4: Dendrogram
with r2_c2:
    with st.container(key="card_dendrogram"):
        st.markdown("""
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
            <h3 style="color:var(--ink); font-size:1.02rem; font-weight:700; margin:0;">Dendrogram · Ward linkage</h3>
            <span class="ta-badge">LAB 8</span>
        </div>
        """, unsafe_allow_html=True)

        ddata = dendrogram(Z_link, p=30, truncate_mode="lastp", no_plot=True)
        
        fig_dend = go.Figure()
        for xs, ys in zip(ddata["icoord"], ddata["dcoord"]):
            fig_dend.add_trace(go.Scatter(
                x=xs, y=ys,
                mode="lines",
                line=dict(color="#64748B", width=1.5),
                hoverinfo="none",
                showlegend=False
            ))

        # Cut line for K
        cut_y = 44.0 if k_val == 2 else (32.0 if k_val == 3 else 22.0)
        fig_dend.add_trace(go.Scatter(
            x=[0, max(max(xs) for xs in ddata["icoord"])],
            y=[cut_y, cut_y],
            mode="lines",
            line=dict(color="#EA580C", dash="dash", width=1.5),
            name=f"cut for K = {k_val}",
            hoverinfo="none"
        ))

        fig_dend.update_layout(
            height=280,
            margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(title=dict(text="Truncated to last merges · merge distance on y", font=dict(size=10.5, color="#64748B")), showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=True, gridcolor="#F1F5F9"),
            legend=dict(orientation="h", yanchor="top", y=0.98, xanchor="right", x=0.98, font=dict(size=10))
        )
        st.plotly_chart(fig_dend, use_container_width=True, config={"displayModeBar": False})

st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)

# ── 6. Season Highlight Breakdown Card (if Season or Team is Selected) ───────
if is_filtering and not hl_sub.empty:
    sorted_hl = hl_sub.sort_values(["Ranked_Cluster", "Pts_per_Match"], ascending=[False, False])
    
    table_rows = ""
    for _, row in sorted_hl.iterrows():
        c_idx = int(row["Ranked_Cluster"])
        c_color = cluster_palette[c_idx % len(cluster_palette)]
        c_name = f"Cluster {c_idx + 1} ({'High-performing' if c_idx==k_val-1 else ('Lower-performing' if c_idx==0 else 'Mid-tier')})"
        
        table_rows += f"""<tr>
<td><b>{row['Team_Name']}</b></td>
<td><span style="display:inline-block; width:8px; height:8px; background:{c_color}; border-radius:2px; margin-right:6px;"></span><span style="font-weight:700; color:{c_color};">{c_name}</span></td>
<td><b>{row['Pts_per_Match']:.2f}</b></td>
<td>{row['Goals_For_mean']:.2f}</td>
<td>{row['Goals_Against_mean']:.2f}</td>
<td>{row['Possession_mean']:.1f}%</td>
<td>{row['Shots_mean']:.1f}</td>
<td>{row['Corners_mean']:.1f}</td>
<td>{row['Fouls_mean']:.1f}</td>
<td>PC1: {row['PC1']:.2f}, PC2: {row['PC2']:.2f}</td>
</tr>"""

    with st.container(key="card_classification_matrix"):
        st.markdown(f"""
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
            <h3 style="color:var(--ink); font-size:1.02rem; font-weight:700; margin:0;">🎯 {hl_season if hl_season!='All seasons' else hl_team} Club Classification Matrix</h3>
            <span class="ta-badge">{len(hl_sub)} CLUBS CLASSIFIED · {sel_method.upper()}</span>
        </div>
        <div style="font-size:0.8rem; color:var(--mute); margin-bottom:12px;">
        Exact cluster assignment and performance statistics for all teams in <b>{hl_season if hl_season!='All seasons' else hl_team}</b> based on active {len(active_features)} features.
        </div>
        <table class="ta-table">
        <thead>
        <tr>
            <th>CLUB</th>
            <th>ASSIGNED CLUSTER</th>
            <th>PTS / MATCH</th>
            <th>GOALS FOR</th>
            <th>GOALS AGAINST</th>
            <th>POSSESSION</th>
            <th>SHOTS</th>
            <th>CORNERS</th>
            <th>FOULS</th>
            <th>PCA POSITION</th>
        </tr>
        </thead>
        <tbody>
        {table_rows}
        </tbody>
        </table>
        """, unsafe_allow_html=True)
    st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)

# ── 7. Cluster Profiles Table ────────────────────────────────────────────────
cluster_rows_html = ""
for rank_idx in range(k_val):
    c_sub = working_df[working_df["Ranked_Cluster"] == rank_idx]
    c_color = cluster_palette[rank_idx % len(cluster_palette)]
    c_name = f"Cluster {rank_idx + 1} - {'Lower-performing' if rank_idx == 0 else ('High-performing' if rank_idx == k_val-1 else 'Mid-tier')}"
    
    gf_m = c_sub["Goals_For_mean"].mean()
    ga_m = c_sub["Goals_Against_mean"].mean()
    sh_m = c_sub["Shots_mean"].mean()
    poss_m = c_sub["Possession_mean"].mean()
    cor_m = c_sub["Corners_mean"].mean()
    fl_m = c_sub["Fouls_mean"].mean()
    pts_m = c_sub["Pts_per_Match"].mean()

    cluster_rows_html += f"""<tr>
<td><span style="display:inline-block; width:8px; height:8px; background:{c_color}; border-radius:2px; margin-right:6px;"></span><b>{c_name}</b></td>
<td>{len(c_sub)}</td>
<td>{gf_m:.2f}</td>
<td>{ga_m:.2f}</td>
<td>{sh_m:.2f}</td>
<td>{poss_m:.2f}</td>
<td>{cor_m:.2f}</td>
<td>{fl_m:.2f}</td>
<td><b>{pts_m:.2f}</b></td>
</tr>"""

# Total row
tot_gf = working_df["Goals_For_mean"].mean()
tot_ga = working_df["Goals_Against_mean"].mean()
tot_sh = working_df["Shots_mean"].mean()
tot_poss = working_df["Possession_mean"].mean()
tot_cor = working_df["Corners_mean"].mean()
tot_fl = working_df["Fouls_mean"].mean()
tot_pts = working_df["Pts_per_Match"].mean()

cluster_rows_html += f"""<tr style="background:var(--card); font-weight:700;">
<td>All profiles</td>
<td>{obs_count}</td>
<td>{tot_gf:.2f}</td>
<td>{tot_ga:.2f}</td>
<td>{tot_sh:.2f}</td>
<td>{tot_poss:.2f}</td>
<td>{tot_cor:.2f}</td>
<td>{tot_fl:.2f}</td>
<td><b>{tot_pts:.2f}</b></td>
</tr>"""

with st.container(key="card_cluster_profiles"):
    st.markdown(f"""
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
        <h3 style="color:var(--ink); font-size:1.02rem; font-weight:700; margin:0;">Cluster profiles - centroids in original units</h3>
        <span class="ta-badge">MEAN PER PROFILE</span>
    </div>
    <table class="ta-table">
    <thead>
    <tr>
        <th>CLUSTER</th>
        <th>SIZE</th>
        <th>GOALS FOR</th>
        <th>GOALS AGAINST</th>
        <th>SHOTS</th>
        <th>POSSESSION %</th>
        <th>CORNERS</th>
        <th>FOULS</th>
        <th>POINTS / MATCH</th>
    </tr>
    </thead>
    <tbody>
    {cluster_rows_html}
    </tbody>
    </table>
    <div style="font-size:0.75rem; color:var(--mute); margin-top:10px;">
    Names are generated from the profile: clusters are ranked by mean points per match.
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)

# ── 8. Centroid Heatmap + K-Means vs Agglomerative ──────────────────────────
c_hm, c_ari = st.columns(2)

with c_hm:
    # Compute Z-scores for each cluster
    z_df = pd.DataFrame(Z_scaled, columns=active_features)
    z_df["Ranked_Cluster"] = working_df["Ranked_Cluster"].values
    z_means = z_df.groupby("Ranked_Cluster").mean()

    hm_headers = "".join([f"<th style='text-align:center; font-size:0.7rem;'>{feat.replace('_mean','').replace('_',' ')}</th>" for feat in active_features])

    hm_rows_html = ""
    for rank_idx in range(k_val):
        cells_html = f"<td><b>Cluster {rank_idx+1}</b></td>"
        if rank_idx in z_means.index:
            row_data = z_means.loc[rank_idx]
            for val in row_data:
                is_pos = val >= 0
                bg = "#DBEAFE" if is_pos else "#FFEDD5"
                fg = "#1D4ED8" if is_pos else "#C2410C"
                sign = "+" if is_pos else ""
                cells_html += f'<td style="background:{bg}; color:{fg}; font-weight:700; text-align:center; border-radius:4px; font-size:0.82rem;">{sign}{val:.2f}</td>'
        hm_rows_html += f"<tr>{cells_html}</tr>"

    with st.container(key="card_centroid_heatmap"):
        st.markdown(f"""
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
            <h3 style="color:var(--ink); font-size:1.02rem; font-weight:700; margin:0;">Centroid heatmap · standardised</h3>
            <span class="ta-badge">Z-SCORE</span>
        </div>
        <table class="ta-table" style="border-collapse:separate; border-spacing:4px 6px;">
        <thead>
        <tr>
            <th></th>
            {hm_headers}
        </tr>
        </thead>
        <tbody>
        {hm_rows_html}
        </tbody>
        </table>
        <div style="font-size:0.75rem; color:var(--mute); margin-top:8px;">
        Blue = above average, orange = below average.
        </div>
        """, unsafe_allow_html=True)

with c_ari:
    # Contingency Table
    contingency = pd.crosstab(km_labels, agg_labels)
    
    ct_rows_html = ""
    for km_i in range(k_val):
        row_cells = f"<td>K-Means {km_i+1}</td>"
        for ag_j in range(k_val):
            cnt = contingency.loc[km_i, ag_j] if km_i in contingency.index and ag_j in contingency.columns else 0
            row_cells += f"<td style='text-align:center; font-weight:600;'>{cnt}</td>"
        ct_rows_html += f"<tr>{row_cells}</tr>"

    ag_headers = "".join([f"<th style='text-align:center;'>AGGLO. {j+1}</th>" for j in range(k_val)])

    with st.container(key="card_kmeans_vs_agglo"):
        st.markdown(f"""
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
            <h3 style="color:var(--ink); font-size:1.02rem; font-weight:700; margin:0;">K-Means vs Agglomerative</h3>
            <span class="ta-badge">LAB 7 · LAB 8</span>
        </div>
        <table class="ta-table" style="margin-bottom:16px;">
        <thead>
        <tr>
            <th>METHOD</th>
            {ag_headers}
        </tr>
        </thead>
        <tbody>
        {ct_rows_html}
        </tbody>
        </table>
        <div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:12px; border-top:1px solid var(--line); padding-top:12px;">
            <div>
                <div style="color:var(--mute); font-size:0.7rem; font-weight:700;">ADJUSTED RAND</div>
                <div style="color:var(--ink); font-size:1.4rem; font-weight:700;">{ari_val:.3f}</div>
            </div>
            <div>
                <div style="color:var(--mute); font-size:0.7rem; font-weight:700;">SILHOUETTE K-MEANS</div>
                <div style="color:var(--acc); font-size:1.4rem; font-weight:700;">{km_sil:.3f}</div>
            </div>
            <div>
                <div style="color:var(--mute); font-size:0.7rem; font-weight:700;">SILHOUETTE AGGLO.</div>
                <div style="color:#EA580C; font-size:1.4rem; font-weight:700;">{agg_sil:.3f}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)

# ── 9. Cluster Membership Card ──────────────────────────────────────────────
memb_rows_html = ""
for rank_idx in range(k_val):
    c_sub = working_df[working_df["Ranked_Cluster"] == rank_idx]
    c_color = cluster_palette[rank_idx % len(cluster_palette)]
    c_name = f"Cluster {rank_idx + 1}"
    
    # Top 4 most frequent clubs
    top_clubs = c_sub["Team_Name"].value_counts().head(4)
    clubs_str = ", ".join([f"{club} ({cnt})" for club, cnt in top_clubs.items()])
    
    # Top 3 highest points per match seasons
    top_seasons = c_sub.sort_values("Pts_per_Match", ascending=False).head(3)
    if sel_level == "Team all-time":
        seasons_str = "; ".join([f"{r['Team_Name']} ({r['Pts_per_Match']:.2f})" for _, r in top_seasons.iterrows()])
    else:
        seasons_str = "; ".join([f"{r['Team_Name']} {r['Season_Name']} ({r['Pts_per_Match']:.2f})" for _, r in top_seasons.iterrows()])

    memb_rows_html += f"""<tr>
<td><span style="display:inline-block; width:8px; height:8px; background:{c_color}; border-radius:2px; margin-right:6px;"></span><b>{c_name}</b></td>
<td>{clubs_str}</td>
<td>{seasons_str}</td>
</tr>"""

with st.container(key="card_cluster_membership"):
    st.markdown(f"""
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
        <h3 style="color:var(--ink); font-size:1.02rem; font-weight:700; margin:0;">Cluster membership</h3>
        <span class="ta-badge">MOST FREQUENT TEAMS · TOP PERFORMERS BY POINTS PER MATCH</span>
    </div>
    <table class="ta-table">
    <thead>
    <tr>
        <th style="width:150px;">CLUSTER</th>
        <th>MOST FREQUENT TEAMS (PROFILES)</th>
        <th>HIGHEST POINTS PER MATCH</th>
    </tr>
    </thead>
    <tbody>
    {memb_rows_html}
    </tbody>
    </table>
    """, unsafe_allow_html=True)

st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)

# ── 10. Technical Details Box ───────────────────────────────────────────────
st.markdown("""<div class="ta-card">
<div style="display:flex; align-items:center; gap:8px; margin-bottom:12px; cursor:pointer;">
<span style="font-size:0.8rem; color:var(--mute);">▼</span>
<span style="color:var(--ink); font-size:0.96rem; font-weight:700;">Technical details</span>
</div>
<div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:16px; font-size:0.82rem;">
<div>
<div style="color:var(--mute); font-size:0.74rem; margin-bottom:2px;">K-MEANS</div>
<div style="color:var(--ink); font-weight:500;">scikit-learn, k-means++, n_init 10, random_state 0, K from silhouette</div>
</div>
<div>
<div style="color:var(--mute); font-size:0.74rem; margin-bottom:2px;">AGGLOMERATIVE</div>
<div style="color:var(--ink); font-weight:500;">scipy linkage, Ward, cut with fcluster maxclust</div>
</div>
<div>
<div style="color:var(--mute); font-size:0.74rem; margin-bottom:2px;">PREPROCESSING</div>
<div style="color:var(--ink); font-weight:500;">Standardised (zero mean, unit variance) across active selected features</div>
</div>
<div>
<div style="color:var(--mute); font-size:0.74rem; margin-bottom:2px;">CLUSTER NAMES</div>
<div style="color:var(--ink); font-weight:500;">Ranked dynamically from mean points per match, never hard-coded</div>
</div>
<div style="grid-column: span 2;">
<div style="color:var(--mute); font-size:0.74rem; margin-bottom:2px;">TRAINING SCOPE</div>
<div style="color:var(--ink); font-weight:500;">Clustering computed dynamically across selected level and features with clear highlighting on selected seasons.</div>
</div>
<div style="grid-column: span 2;">
<div style="color:var(--mute); font-size:0.74rem; margin-bottom:2px;">INTERPRETATION</div>
<div style="color:var(--ink); font-weight:500;">Silhouette favours K = 2. A larger K can be chosen for more detailed styles, and must be justified in the report.</div>
</div>
</div>
</div>""", unsafe_allow_html=True)
