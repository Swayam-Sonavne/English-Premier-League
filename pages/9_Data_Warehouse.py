"""
pages/9_Data_Warehouse.py — Admin Page 9: Data Warehouse
Lab 1: Star, Snowflake, Galaxy schemas + table previews + DWM syllabus coverage.
"""
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Data Warehouse — EPL Analytics & DWM",
    page_icon="🗄️",
    layout="wide",
)

# Role Access Guard
if st.session_state.get("auth_role") != "admin":
    st.warning("🔒 Administrator authentication required to view this technical DWM page.")
    if st.button("🔑 Login as Administrator", key="dw_auth_req_btn"):
        st.session_state["auth_role"] = "admin"
        st.rerun()
    st.stop()

from utils.admin_views import render_admin_sidebar
render_admin_sidebar("Data Warehouse")

from utils.db import load_row_counts, load_table_preview, q
from utils.filters import dwm_label
from utils.schema_diagrams import draw_star_schema, draw_snowflake_schema, draw_galaxy_schema

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="background:linear-gradient(135deg, #0d1b2a, #1e3a5f); padding:20px; border-radius:10px; margin-bottom:18px; color:#ffffff;">
    <span style="background:#e8b84b; color:#0d1b2a; padding:3px 8px; border-radius:12px; font-size:0.75rem; font-weight:800;">ADMIN LAYER • LAB 1</span>
    <h1 style="color:#ffffff; margin:6px 0 2px 0; font-size:2rem;">🗄️ Data Warehouse Architecture & Schemas</h1>
    <p style="color:#cdd8e3; font-size:0.95rem; margin:0;">
        Academic reference and structural inspection — Star, Snowflake, and Galaxy schemas, table dictionary, and syllabus matrix.
    </p>
</div>
""", unsafe_allow_html=True)

dwm_label("Data Warehouse Design", 1)

# ── 1. Dataset Summary ────────────────────────────────────────────────────────
st.subheader("Dataset Summary")
counts = load_row_counts()

dim_tables  = ["Dim_Date","Dim_Season","Dim_Team","Dim_Stadium",
               "Dim_City","Dim_Referee","Dim_Player","Dim_Position"]
fact_tables = ["Fact_Match","Fact_Team_Match","Fact_Player_Performance"]

total_fact = sum(counts[t] for t in fact_tables)
total_dim  = sum(counts[t] for t in dim_tables)

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Seasons",         f"{counts['Dim_Season']:,}")
k2.metric("Teams",           f"{counts['Dim_Team']:,}")
k3.metric("Matches",         f"{counts['Fact_Match']:,}")
k4.metric("Team-Match rows", f"{counts['Fact_Team_Match']:,}")
k5.metric("Player rows",     f"{counts['Fact_Player_Performance']:,}")
k6.metric("Total Fact rows", f"{total_fact:,}")

st.divider()

col_d, col_f = st.columns(2)

with col_d:
    st.markdown("#### Dimension Tables")
    dim_df = pd.DataFrame({
        "Table": dim_tables,
        "Rows":  [counts[t] for t in dim_tables],
        "Type":  ["Date hierarchy","Season","Team (snowflake)","Stadium (snowflake)",
                  "City (shared snowflake)","Referee","Player (snowflake)","Position (snowflake)"],
    })
    st.dataframe(dim_df, use_container_width=True, hide_index=True)

with col_f:
    st.markdown("#### Fact Tables")
    grain_map = {
        "Fact_Match":               "1 row = 1 match",
        "Fact_Team_Match":          "1 row = 1 team × 1 match",
        "Fact_Player_Performance":  "1 row = 1 player × 1 match",
    }
    fact_df = pd.DataFrame({
        "Table": fact_tables,
        "Rows":  [counts[t] for t in fact_tables],
        "Grain": [grain_map[t] for t in fact_tables],
    })
    st.dataframe(fact_df, use_container_width=True, hide_index=True)

st.divider()

# ── 2. Schema Diagrams (Reusing working matplotlib visualizers) ────────────────
st.subheader("Schema Diagrams")

tab_star, tab_snow, tab_galaxy = st.tabs([
    "⭐ Star Schema",
    "❄️ Snowflake Schema",
    "🌌 Galaxy Schema (Fact Constellation)",
])

with tab_star:
    st.markdown("""
    **Star Schema** — `Fact_Match` at the centre, directly joined to 6 dimension tables via foreign keys.
    """)
    with st.spinner("Rendering diagram…"):
        fig = draw_star_schema()
        st.pyplot(fig, use_container_width=True)

with tab_snow:
    st.markdown("""
    **Snowflake Schema** — Normalizes three dimension chains:
    `Dim_Team → Dim_City`, `Dim_Stadium → Dim_City`, `Dim_Player → Dim_Position`.
    """)
    with st.spinner("Rendering diagram…"):
        fig = draw_snowflake_schema()
        st.pyplot(fig, use_container_width=True)

with tab_galaxy:
    st.markdown("""
    **Galaxy Schema (Fact Constellation)** — Three fact tables of distinct grains sharing conformed dimensions.
    `Match_ID` acts as the cross-fact linkage key enabling **drill-across** operations.
    """)
    with st.spinner("Rendering diagram…"):
        fig = draw_galaxy_schema()
        st.pyplot(fig, use_container_width=True)

st.divider()

# ── 3. Table Preview ──────────────────────────────────────────────────────────
st.subheader("Table Preview")
all_tables = dim_tables + fact_tables
selected_table = st.selectbox("Select a table to preview", all_tables)

preview_df = load_table_preview(selected_table, limit=100)
st.caption(f"Showing up to 100 rows from **{selected_table}** ({counts[selected_table]:,} total rows)")
st.dataframe(preview_df, use_container_width=True, hide_index=True)

# ── 4. Syllabus Coverage ──────────────────────────────────────────────────────
st.divider()
st.subheader("Academic DWM Syllabus Coverage")

coverage = pd.DataFrame([
    {"Lab": 1, "Topic": "Data Warehouse Design", "Method": "Star / Snowflake / Galaxy Schemas", "Page": "pages/9_Data_Warehouse.py", "Status": "✅ Verified"},
    {"Lab": 2, "Topic": "OLAP Operations", "Method": "Roll-up, Drill-down, Slice, Dice, Pivot, Drill-across", "Page": "pages/8_OLAP_Analysis.py", "Status": "✅ Verified"},
    {"Lab": 3, "Topic": "Data Visualization & EDA", "Method": "Multi-Dimensional Distributions & Trends", "Page": "pages/2_EPL_Explorer.py", "Status": "✅ Verified"},
    {"Lab": 4, "Topic": "Regression Analysis", "Method": "Simple & Multiple Linear Regression (SLR/MLR)", "Page": "pages/3_Performance_Analysis.py", "Status": "✅ Verified"},
    {"Lab": 5, "Topic": "Classification (Decision Tree)", "Method": "Attribute Relevance (MI) + Gini Decision Tree", "Page": "pages/4_Match_Outcomes.py", "Status": "✅ Verified"},
    {"Lab": 6, "Topic": "Classification (Naive Bayes)", "Method": "Gaussian Naïve Bayes Class Probabilities", "Page": "pages/4_Match_Outcomes.py", "Status": "✅ Verified"},
    {"Lab": 7, "Topic": "Clustering (K-Means)", "Method": "K-Means on 540 Profiles, Silhouette, 2D PCA", "Page": "pages/5_Team_Analytics.py", "Status": "✅ Verified"},
    {"Lab": 8, "Topic": "Clustering (Hierarchical)", "Method": "Ward's Linkage Dendrogram & Trajectory", "Page": "pages/5_Team_Analytics.py", "Status": "✅ Verified"},
    {"Lab": 9, "Topic": "Association Rule Mining", "Method": "Apriori on all 20,520 Transactions", "Page": "pages/7_Association_Analysis.py", "Status": "✅ Verified"},
])

st.dataframe(coverage, use_container_width=True, hide_index=True)
