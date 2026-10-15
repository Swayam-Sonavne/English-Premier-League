"""
utils/olap.py
All 6 OLAP query builders for the EPL DWM Platform.
Each function returns (sql_string, result_DataFrame).
Displaying the SQL string is intentional — academic transparency for Lab 2.
"""
import pandas as pd
from utils.db import q


# ── shared FROM clause and measure string ────────────────────────────────────
_FROM = """
    FROM Fact_Match fm
    JOIN Dim_Season  s   ON fm.Season_ID    = s.Season_ID
    JOIN Dim_Date    d   ON fm.Date_ID      = d.Date_ID
    JOIN Dim_Team    ht  ON fm.Home_Team_ID = ht.Team_ID
    JOIN Dim_Team    at_ ON fm.Away_Team_ID = at_.Team_ID
    JOIN Dim_Stadium st_ ON fm.Stadium_ID   = st_.Stadium_ID
    JOIN Dim_Referee r   ON fm.Referee_ID   = r.Referee_ID
"""

_MEAS = "COUNT(*) AS Matches, SUM(fm.Home_Goals + fm.Away_Goals) AS Total_Goals, ROUND(AVG(fm.Attendance)) AS Avg_Attendance"


# ── 1. Roll-up ───────────────────────────────────────────────────────────────
def olap_rollup(level: str) -> tuple[str, pd.DataFrame]:
    """
    Roll-up from match level to Month+Season, Season, or All.
    level: "Date → Season + Month" | "Season + Month → Season" | "Season → All"
    """
    if level == "Date → Season + Month":
        group = "s.Season_Name, d.Month, d.Month_Name"
        select = f"s.Season_Name, d.Month, d.Month_Name, {_MEAS}"
        order  = "s.Season_Name, d.Month"
    elif level == "Season + Month → Season":
        group  = "s.Season_Name"
        select = f"s.Season_Name, {_MEAS}"
        order  = "s.Season_Name"
    else:  # Season → All
        group  = None
        select = f"'All Seasons' AS Level, {_MEAS}"
        order  = None

    if group:
        sql = f"SELECT {select} {_FROM} GROUP BY {group} ORDER BY {order}"
    else:
        sql = f"SELECT {select} {_FROM}"

    sql = _clean(sql)
    return sql, q(sql)


# ── 2. Drill-down ────────────────────────────────────────────────────────────
def olap_drilldown(season_name: str, level: str) -> tuple[str, pd.DataFrame]:
    """
    Drill down within a season to Quarter, Month, or Date.
    """
    if level == "Quarter":
        group  = "d.Quarter"
        select = f"d.Quarter, {_MEAS}"
        order  = "d.Quarter"
    elif level == "Month":
        group  = "d.Quarter, d.Month, d.Month_Name"
        select = f"d.Quarter, d.Month, d.Month_Name, {_MEAS}"
        order  = "d.Month"
    else:  # Date
        group  = "d.Date"
        select = f"d.Date, {_MEAS}"
        order  = "d.Date"

    sql = f"""
        SELECT {select}
        {_FROM}
        WHERE s.Season_Name = '{season_name}'
        GROUP BY {group}
        ORDER BY {order}
    """
    sql = _clean(sql)
    return sql, q(sql)


# ── 3. Slice ──────────────────────────────────────────────────────────────────
def olap_slice(season_name: str) -> tuple[str, pd.DataFrame]:
    """
    Slice: fix Season dimension, show all home-team stats for that season.
    """
    sql = f"""
        SELECT
            ht.Team_Name AS Home_Team,
            {_MEAS}
        {_FROM}
        WHERE s.Season_Name = '{season_name}'
        GROUP BY ht.Team_Name
        ORDER BY Total_Goals DESC
    """
    sql = _clean(sql)
    return sql, q(sql)


# ── 4. Dice ──────────────────────────────────────────────────────────────────
def olap_dice(season_names: list[str], team_names: list[str]) -> tuple[str, pd.DataFrame]:
    """
    Dice: multi-select Seasons AND Home Teams — cross-section.
    """
    if not season_names or not team_names:
        return "", pd.DataFrame()

    s_list = "', '".join(season_names)
    t_list = "', '".join(team_names)

    sql = f"""
        SELECT
            s.Season_Name,
            ht.Team_Name AS Home_Team,
            {_MEAS}
        {_FROM}
        WHERE s.Season_Name IN ('{s_list}')
          AND ht.Team_Name  IN ('{t_list}')
        GROUP BY s.Season_Name, ht.Team_Name
        ORDER BY s.Season_Name, Total_Goals DESC
    """
    sql = _clean(sql)
    return sql, q(sql)


# ── 5. Pivot ──────────────────────────────────────────────────────────────────
def olap_pivot() -> tuple[str, pd.DataFrame]:
    """
    Pivot: Team × Season total-points matrix from Fact_Team_Match.
    Returns (sql, long_df) — caller pivots for heatmap display.
    """
    sql = """
        SELECT
            t.Team_Name,
            s.Season_Name,
            SUM(tm.Points) AS Total_Points
        FROM Fact_Team_Match tm
        JOIN Dim_Team   t USING(Team_ID)
        JOIN Dim_Season s USING(Season_ID)
        GROUP BY t.Team_Name, s.Season_Name
        ORDER BY t.Team_Name, s.Season_Name
    """
    sql = _clean(sql)
    long = q(sql)
    return sql, long


# ── 6. Drill-across ───────────────────────────────────────────────────────────
def olap_drill_across() -> tuple[str, pd.DataFrame]:
    """
    Drill-across: compare Fact_Match total goals vs
    Fact_Player_Performance total goals per season.
    Equal totals confirm a reconciled warehouse.
    """
    sql = """
        SELECT
            s.Season_Name,
            m.Match_Goals,
            p.Player_Goals,
            (m.Match_Goals - p.Player_Goals) AS Difference
        FROM (
            SELECT Season_ID,
                   SUM(Home_Goals + Away_Goals) AS Match_Goals
            FROM Fact_Match
            GROUP BY Season_ID
        ) m
        JOIN (
            SELECT Season_ID,
                   SUM(Goals) AS Player_Goals
            FROM Fact_Player_Performance
            GROUP BY Season_ID
        ) p USING(Season_ID)
        JOIN Dim_Season s USING(Season_ID)
        ORDER BY s.Season_ID
    """
    sql = _clean(sql)
    return sql, q(sql)


# ── helper ────────────────────────────────────────────────────────────────────
def _clean(sql: str) -> str:
    """Strip excess whitespace from SQL for display."""
    return "\n".join(line for line in sql.strip().splitlines() if line.strip())
