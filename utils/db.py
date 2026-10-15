"""
utils/db.py
Centralised database access for the EPL DWM Platform.
All loaders are @st.cache_data so each query runs once per session.
DB path is resolved absolutely from this file's location so the app
works regardless of the working directory Streamlit is launched from.
"""
import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

# ── absolute path to epl_dw.db ─────────────────────────────────────────────
_DB_PATH = Path(__file__).resolve().parent.parent / "epl_dw.db"


# ── generic query helper ────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def q(sql: str) -> pd.DataFrame:
    """Run an arbitrary SQL query and return a DataFrame (cached)."""
    with sqlite3.connect(_DB_PATH) as con:
        return pd.read_sql(sql, con)


# ── dimension loaders ───────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_dim_season() -> pd.DataFrame:
    return q("SELECT * FROM Dim_Season ORDER BY Season_ID")


@st.cache_data(show_spinner=False)
def load_dim_team() -> pd.DataFrame:
    return q("SELECT * FROM Dim_Team ORDER BY Team_Name")


@st.cache_data(show_spinner=False)
def load_dim_stadium() -> pd.DataFrame:
    return q("""
        SELECT s.*, c.City_Name
        FROM Dim_Stadium s
        JOIN Dim_City c USING(City_ID)
        ORDER BY s.Stadium_Name
    """)


@st.cache_data(show_spinner=False)
def load_dim_city() -> pd.DataFrame:
    return q("SELECT * FROM Dim_City ORDER BY City_Name")


@st.cache_data(show_spinner=False)
def load_dim_player() -> pd.DataFrame:
    return q("""
        SELECT p.*, pos.Position_Name
        FROM Dim_Player p
        JOIN Dim_Position pos USING(Position_ID)
        ORDER BY p.Player_Name
    """)


@st.cache_data(show_spinner=False)
def load_dim_position() -> pd.DataFrame:
    return q("SELECT * FROM Dim_Position ORDER BY Position_ID")


@st.cache_data(show_spinner=False)
def load_dim_referee() -> pd.DataFrame:
    return q("SELECT * FROM Dim_Referee ORDER BY Referee_ID")


# ── fact loaders ────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)  # shared, not copied per call: big frames, read-only
def load_fact_match() -> pd.DataFrame:
    """Fact_Match joined with all its dimensions."""
    return q("""
        SELECT
            fm.*,
            d.Date, d.Day, d.Month, d.Month_Name, d.Quarter, d.Year, d.Day_of_Week,
            s.Season_Name, s.Start_Year, s.End_Year,
            ht.Team_Name   AS Home_Team_Name,
            at_.Team_Name  AS Away_Team_Name,
            st_.Stadium_Name,
            r.Referee_Name
        FROM Fact_Match fm
        JOIN Dim_Date    d   ON fm.Date_ID      = d.Date_ID
        JOIN Dim_Season  s   ON fm.Season_ID    = s.Season_ID
        JOIN Dim_Team    ht  ON fm.Home_Team_ID = ht.Team_ID
        JOIN Dim_Team    at_ ON fm.Away_Team_ID = at_.Team_ID
        JOIN Dim_Stadium st_ ON fm.Stadium_ID   = st_.Stadium_ID
        JOIN Dim_Referee r   ON fm.Referee_ID   = r.Referee_ID
        ORDER BY fm.Match_ID
    """)


@st.cache_resource(show_spinner=False)  # shared, not copied per call: big frames, read-only
def load_team_match() -> pd.DataFrame:
    """
    Fact_Team_Match joined with Dim_Team and Dim_Season.
    This is the primary DataFrame used by Regression, Classification,
    Clustering, Apriori, and most exploration queries.
    ~20,520 rows.
    """
    return q("""
        SELECT
            tm.*,
            t.Team_Name,
            s.Season_Name,
            s.Season_ID AS _Season_ID_check
        FROM Fact_Team_Match tm
        JOIN Dim_Team   t USING(Team_ID)
        JOIN Dim_Season s USING(Season_ID)
        ORDER BY tm.Team_Match_ID
    """)


@st.cache_resource(show_spinner=False)  # shared, not copied per call: big frames, read-only
def load_player_perf() -> pd.DataFrame:
    """
    Fact_Player_Performance joined with Dim_Player, Dim_Position,
    Dim_Team, Dim_Season.
    ~287,280 rows.
    """
    return q("""
        SELECT
            fp.*,
            p.Player_Name, p.Nationality,
            pos.Position_Name,
            t.Team_Name,
            s.Season_Name
        FROM Fact_Player_Performance fp
        JOIN Dim_Player   p   USING(Player_ID)
        JOIN Dim_Position pos ON p.Position_ID = pos.Position_ID
        JOIN Dim_Team     t   USING(Team_ID)
        JOIN Dim_Season   s   USING(Season_ID)
        ORDER BY fp.Perf_ID
    """)


@st.cache_data(show_spinner=False)
def load_team_profiles() -> pd.DataFrame:
    """
    540-row Team × Season aggregation used for clustering.
    Columns: Team_Name, Season_Name, Season_ID, + 7 feature columns.
    """
    return q("""
        SELECT
            t.Team_Name,
            s.Season_Name,
            s.Season_ID,
            AVG(tm.Goals_For)      AS Goals_For_mean,
            AVG(tm.Goals_Against)  AS Goals_Against_mean,
            AVG(tm.Shots)          AS Shots_mean,
            AVG(tm.Possession)     AS Possession_mean,
            AVG(tm.Corners)        AS Corners_mean,
            AVG(tm.Fouls)          AS Fouls_mean,
            AVG(tm.Points)         AS Pts_per_Match
        FROM Fact_Team_Match tm
        JOIN Dim_Team   t USING(Team_ID)
        JOIN Dim_Season s USING(Season_ID)
        GROUP BY tm.Team_ID, tm.Season_ID
        ORDER BY t.Team_Name, s.Season_ID
    """)


# ── row count helper (for Data Warehouse page) ──────────────────────────────
@st.cache_data(show_spinner=False)
def load_row_counts() -> dict:
    """Return {table_name: row_count} for all 11 warehouse tables."""
    tables = [
        "Dim_Date", "Dim_Season", "Dim_Team", "Dim_Stadium",
        "Dim_City", "Dim_Referee", "Dim_Player", "Dim_Position",
        "Fact_Match", "Fact_Team_Match", "Fact_Player_Performance",
    ]
    return {t: q(f"SELECT COUNT(*) AS c FROM {t}").c[0] for t in tables}


@st.cache_data(show_spinner=False)
def load_table_preview(table_name: str, limit: int = 100) -> pd.DataFrame:
    """Return up to `limit` rows from any warehouse table."""
    allowed = {
        "Dim_Date", "Dim_Season", "Dim_Team", "Dim_Stadium",
        "Dim_City", "Dim_Referee", "Dim_Player", "Dim_Position",
        "Fact_Match", "Fact_Team_Match", "Fact_Player_Performance",
    }
    if table_name not in allowed:
        raise ValueError(f"Unknown table: {table_name}")
    return q(f"SELECT * FROM {table_name} LIMIT {limit}")
