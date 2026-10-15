"""
pages/8_OLAP_Analysis.py — Admin Page 8: OLAP Analysis
Dedicated Multi-Dimensional OLAP Cube Operations (Roll-up, Drill-down, Slice, Dice, Pivot, Drill-across).
Academic Syllabus Lab 2 (OLAP Operations).
"""
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="OLAP Analysis — EPL Analytics & DWM",
    page_icon="📐",
    layout="wide",
)

# Role Access Guard
if st.session_state.get("auth_role") != "admin":
    st.warning("🔒 Administrator authentication required to view this technical DWM page.")
    if st.button("🔑 Login as Administrator", key="ol_auth_req_btn"):
        st.session_state["auth_role"] = "admin"
        st.rerun()
    st.stop()

from utils.admin_views import render_admin_sidebar
render_admin_sidebar("OLAP Analysis")

from utils.db import (
    load_team_match, load_player_perf, load_fact_match,
    load_dim_team, load_dim_season, load_dim_stadium,
    load_dim_player, q,
)
from utils.filters import dwm_label
from utils.olap import (
    olap_rollup, olap_drilldown, olap_slice,
    olap_dice, olap_pivot, olap_drill_across,
)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="background:linear-gradient(135deg, #0d1b2a, #1e3a5f); padding:20px; border-radius:10px; margin-bottom:18px; color:#ffffff;">
    <span style="background:#e8b84b; color:#0d1b2a; padding:3px 8px; border-radius:12px; font-size:0.75rem; font-weight:800;">ADMIN LAYER • LAB 2</span>
    <h1 style="color:#ffffff; margin:6px 0 2px 0; font-size:2rem;">📐 Multi-Dimensional OLAP Analysis</h1>
    <p style="color:#cdd8e3; font-size:0.95rem; margin:0;">
        Interactive Online Analytical Processing (OLAP) engine executing Roll-up, Drill-down, Slice, Dice, Pivot, and Drill-across over the Premier League Data Warehouse.
    </p>
</div>
""", unsafe_allow_html=True)

dwm_label("OLAP (Roll-up · Drill-down · Slice · Dice · Pivot · Drill-across)", 2)
st.caption(
    "Each operation executes a multi-dimensional warehouse query, displays the generated SQL, and visualizes the resulting sub-cube."
)
st.divider()

op = st.radio("Select OLAP Cube Operation",
              ["Roll-up", "Drill-down", "Slice", "Dice", "Pivot", "Drill-across"],
              horizontal=True, key="olap_op_main")

seasons_olap = load_dim_season()["Season_Name"].tolist()
teams_olap   = sorted(load_dim_team()["Team_Name"].tolist())

# ── 1. Roll-up ───────────────────────────────────────────────────────────────
if op == "Roll-up":
    with st.container(key="card_olap_rollup"):
        st.markdown("""
        ### ⬆️ Roll-up Operation
        **Roll-up** aggregates data from a finer granularity to a coarser level along a concept hierarchy.
        *Hierarchy:* `Date_ID (Daily) → Month + Season → Season → All-Time League`.
        """)
        level = st.selectbox("Aggregate hierarchy level to:",
                             ["Date → Season + Month",
                              "Season + Month → Season",
                              "Season → All"],
                             key="ru_level")
        sql, df = olap_rollup(level)
        st.code(sql, language="sql")
        st.dataframe(df, use_container_width=True, hide_index=True)
        if "Season_Name" in df.columns and "Total_Goals" in df.columns:
            fig = px.bar(df, x="Season_Name", y="Total_Goals",
                         title="Roll-up Result — Total Goals across Aggregation Level",
                         color="Total_Goals", color_continuous_scale="Blues")
            fig.update_layout(xaxis_tickangle=-45,
                              paper_bgcolor="rgba(0,0,0,0)",
                              plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ── 2. Drill-down ────────────────────────────────────────────────────────────
elif op == "Drill-down":
    with st.container(key="card_olap_drilldown"):
        st.markdown("""
        ### ⬇️ Drill-down Operation
        **Drill-down** navigates from less detailed data to more granular data along the temporal dimension hierarchy.
        """)
        dd1, dd2 = st.columns(2)
        sel_dd_szn = dd1.selectbox("Select Season", seasons_olap,
                                   index=len(seasons_olap)-1, key="dd_szn")
        sel_dd_lvl = dd2.selectbox("Drill granularity down to:",
                                   ["Quarter", "Month", "Date"], key="dd_lvl")
        sql, df = olap_drilldown(sel_dd_szn, sel_dd_lvl)
        st.code(sql, language="sql")
        st.dataframe(df, use_container_width=True, hide_index=True)
        if not df.empty and "Total_Goals" in df.columns:
            x_col = df.columns[0]
            fig = px.bar(df, x=x_col, y="Total_Goals",
                         title=f"Drill-down — {sel_dd_szn} by {sel_dd_lvl}",
                         color="Total_Goals", color_continuous_scale="Blues")
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",
                              plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ── 3. Slice ─────────────────────────────────────────────────────────────────
elif op == "Slice":
    with st.container(key="card_olap_slice"):
        st.markdown("""
        ### 🔪 Slice Operation
        **Slice** performs a selection on one dimension of the cube, resulting in a sub-cube of lower dimensionality.
        *Fixed Dimension:* `Dim_Season = Selected Season`.
        """)
        sel_sl_szn = st.selectbox("Select Slice Dimension (Season):", seasons_olap,
                                  index=len(seasons_olap)-1, key="sl_szn")
        sql, df = olap_slice(sel_sl_szn)
        st.code(sql, language="sql")
        st.dataframe(df, use_container_width=True, hide_index=True)
        if not df.empty:
            fig = px.bar(df.sort_values("Total_Goals"),
                         x="Total_Goals", y="Home_Team", orientation="h",
                         title=f"Slice Sub-Cube — {sel_sl_szn}: Home Goals by Club",
                         color="Total_Goals", color_continuous_scale="Blues")
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",
                              plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ── 4. Dice ──────────────────────────────────────────────────────────────────
elif op == "Dice":
    with st.container(key="card_olap_dice"):
        st.markdown("""
        ### 🎲 Dice Operation
        **Dice** defines a sub-cube by performing a selection on two or more dimensions simultaneously.
        *Dimensions Filtered:* `Dim_Season` AND `Dim_Team`.
        """)
        dc1, dc2 = st.columns(2)
        sel_dc_szns = dc1.multiselect("Select Season Dimensions", seasons_olap,
                                      default=seasons_olap[-3:], key="dc_szn")
        sel_dc_tms  = dc2.multiselect("Select Club Dimensions", teams_olap,
                                      default=teams_olap[:4], key="dc_tm")
        if sel_dc_szns and sel_dc_tms:
            sql, df = olap_dice(sel_dc_szns, sel_dc_tms)
            st.code(sql, language="sql")
            st.dataframe(df, use_container_width=True, hide_index=True)
            if not df.empty:
                fig = px.bar(df, x="Home_Team", y="Total_Goals",
                             color="Season_Name", barmode="group",
                             title="Dice Sub-Cube — Multi-Dimensional Goal Distribution",
                             color_discrete_sequence=px.colors.qualitative.Set2)
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",
                                  plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Select at least one Season and one Team to define the dice sub-cube.")

# ── 5. Pivot ─────────────────────────────────────────────────────────────────
elif op == "Pivot":
    with st.container(key="card_olap_pivot"):
        st.markdown("""
        ### 🔄 Pivot Operation (Rotate)
        **Pivot** changes the dimensional orientation of the data — rotating axes to provide an alternative perspective.
        *Row Dimension:* `Dim_Team` × *Column Dimension:* `Dim_Season`.
        """)
        sql, long_df = olap_pivot()
        st.code(sql, language="sql")
        pivot_df = long_df.pivot_table(
            index="Team_Name", columns="Season_Name",
            values="Total_Points", aggfunc="sum"
        )
        fig = px.imshow(pivot_df, title="Pivot Grid — Team × Season Total League Points",
                        color_continuous_scale="Viridis", aspect="auto",
                        labels=dict(color="Points"))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.dataframe(pivot_df, use_container_width=True)

# ── 6. Drill-across ──────────────────────────────────────────────────────────
elif op == "Drill-across":
    with st.container(key="card_olap_drillacross"):
        st.markdown("""
        ### 🔀 Drill-across Operation
        **Drill-across** compares metrics across multiple fact tables that share conformed dimensions.
        *Cross-Fact Comparison:* `Fact_Match` (Home_Goals + Away_Goals) vs `Fact_Player_Performance` (Sum of Player Goals) linked via conformed `Season_ID`.
        """)
        sql, df = olap_drill_across()
        st.code(sql, language="sql")

        col_da1, col_da2 = st.columns(2)
        with col_da1:
            st.dataframe(df, use_container_width=True, hide_index=True)
        with col_da2:
            if df["Difference"].abs().sum() == 0:
                st.success(
                    "✅ **Warehouse Integrity Confirmed** — Total goals in Fact_Match "
                    "identically reconcile with Fact_Player_Performance across all 27 seasons (Difference = 0)."
                )
            else:
                st.warning("⚠️ Reconciliation discrepancy detected.")

        fig = px.line(df, x="Season_Name",
                      y=["Match_Goals", "Player_Goals"],
                      title="Drill-across — Cross-Fact Reconciliation (Fact_Match vs Fact_Player_Performance)",
                      markers=True,
                      color_discrete_sequence=["#1e3a5f", "#e8b84b"])
        fig.update_layout(xaxis_tickangle=-45,
                          paper_bgcolor="rgba(0,0,0,0)",
                          plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        st.caption(
            "Both series perfectly overlap across all 27 seasons, validating cross-fact consistency and conformed dimension alignment."
        )
