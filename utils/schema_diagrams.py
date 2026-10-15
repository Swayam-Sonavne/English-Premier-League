"""
utils/schema_diagrams.py
Matplotlib-based Star, Snowflake and Galaxy schema diagrams
for the Data Warehouse academic page (Lab 1).
Each function returns a matplotlib Figure.
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

# ── colours ───────────────────────────────────────────────────────────────────
FACT_BG    = "#e8b84b"   # gold  — fact tables
FACT_FG    = "#1a1a1a"
DIM_BG     = "#1e3a5f"   # dark blue — core dimensions
DIM_FG     = "#ffffff"
SNOW_BG    = "#2e6da4"   # lighter blue — snowflake sub-dimensions
SNOW_FG    = "#ffffff"
ARROW_COL  = "#555555"
FONT       = "DejaVu Sans"


def _box(ax, x, y, w, h, title, body_lines,
         bg=DIM_BG, fg=DIM_FG, fontsize=7.5):
    """Draw a table box with a title row and column list."""
    # outer box
    rect = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02",
                           linewidth=1.2, edgecolor="#333",
                           facecolor=bg, zorder=3)
    ax.add_patch(rect)
    # title bar (top quarter of box)
    title_h = h * 0.28
    title_rect = FancyBboxPatch((x, y + h - title_h), w, title_h,
                                 boxstyle="round,pad=0.02",
                                 linewidth=0, edgecolor=bg,
                                 facecolor=bg, zorder=4)
    ax.add_patch(title_rect)
    ax.text(x + w / 2, y + h - title_h / 2, title,
            ha="center", va="center", fontsize=fontsize + 0.5,
            fontweight="bold", color=fg, fontfamily=FONT, zorder=5)
    # divider
    ax.plot([x + 0.01, x + w - 0.01], [y + h - title_h, y + h - title_h],
            color="#888", linewidth=0.8, zorder=5)
    # body text
    if body_lines:
        body = "\n".join(body_lines)
        ax.text(x + 0.04, y + h - title_h - 0.03, body,
                ha="left", va="top", fontsize=fontsize - 1,
                color=fg, fontfamily=FONT, zorder=5,
                linespacing=1.5)


def _arrow(ax, x0, y0, x1, y1):
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                arrowprops=dict(arrowstyle="-|>", color=ARROW_COL,
                                lw=1.2, mutation_scale=10),
                zorder=2)


# ─────────────────────────────────────────────────────────────────────────────
# 1. STAR SCHEMA
# ─────────────────────────────────────────────────────────────────────────────
def draw_star_schema() -> plt.Figure:
    fig, ax = plt.subplots(figsize=(13, 8))
    ax.set_xlim(0, 13); ax.set_ylim(0, 8)
    ax.axis("off")
    fig.patch.set_facecolor("#f8f9fa")
    ax.set_facecolor("#f8f9fa")
    ax.set_title("Star Schema — Fact_Match at Centre",
                 fontsize=13, fontweight="bold", pad=10, fontfamily=FONT)

    bw, bh = 2.6, 2.4

    # Central fact
    _box(ax, 4.7, 2.8, bw, bh,
         "Fact_Match",
         ["Match_ID (PK)", "Date_ID (FK)", "Season_ID (FK)",
          "Home_Team_ID (FK)", "Away_Team_ID (FK)",
          "Stadium_ID (FK)", "Referee_ID (FK)",
          "Home_Goals, Away_Goals",
          "Attendance, Occupancy_Pct",
          "Match_Result"],
         bg=FACT_BG, fg=FACT_FG, fontsize=7)

    # Dim_Date — top
    _box(ax, 4.7, 5.5, bw, bh, "Dim_Date",
         ["Date_ID (PK)", "Date, Day, Month",
          "Month_Name, Quarter",
          "Year, Day_of_Week"])
    _arrow(ax, 6.0, 5.5, 6.0, 5.2)

    # Dim_Season — top-right
    _box(ax, 9.8, 5.5, 2.4, bh, "Dim_Season",
         ["Season_ID (PK)", "Season_Name",
          "Start_Year, End_Year"])
    _arrow(ax, 10.9, 5.5, 7.3, 4.6)

    # Dim_Team (Home) — left
    _box(ax, 0.2, 4.8, 2.4, bh, "Dim_Team (Home)",
         ["Team_ID (PK)", "Team_Name", "City_ID (FK)"])
    _arrow(ax, 2.6, 5.8, 4.7, 4.1)

    # Dim_Team (Away) — bottom-left
    _box(ax, 0.2, 1.8, 2.4, bh, "Dim_Team (Away)",
         ["Team_ID (PK)", "Team_Name", "City_ID (FK)"])
    _arrow(ax, 2.6, 3.1, 4.7, 3.6)

    # Dim_Stadium — bottom
    _box(ax, 4.7, 0.1, bw, bh, "Dim_Stadium",
         ["Stadium_ID (PK)", "Stadium_Name",
          "City_ID (FK)", "Capacity"])
    _arrow(ax, 6.0, 2.8, 6.0, 2.5)

    # Dim_Referee — right
    _box(ax, 9.8, 2.8, 2.4, bh, "Dim_Referee",
         ["Referee_ID (PK)", "Referee_Name"])
    _arrow(ax, 9.8, 3.8, 7.3, 3.8)

    # Legend
    handles = [
        mpatches.Patch(facecolor=FACT_BG, edgecolor="#333", label="Fact Table"),
        mpatches.Patch(facecolor=DIM_BG,  edgecolor="#333", label="Dimension Table"),
    ]
    ax.legend(handles=handles, loc="lower right", fontsize=9)
    plt.tight_layout()
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# 2. SNOWFLAKE SCHEMA
# ─────────────────────────────────────────────────────────────────────────────
def draw_snowflake_schema() -> plt.Figure:
    fig, ax = plt.subplots(figsize=(14, 7))
    ax.set_xlim(0, 14); ax.set_ylim(0, 7)
    ax.axis("off")
    fig.patch.set_facecolor("#f8f9fa")
    ax.set_facecolor("#f8f9fa")
    ax.set_title("Snowflake Schema — Normalised Dimension Chains",
                 fontsize=13, fontweight="bold", pad=10, fontfamily=FONT)

    bw, bh = 2.4, 2.0

    # Fact_Match centre
    _box(ax, 5.3, 2.5, 2.6, 2.2,
         "Fact_Match",
         ["Match_ID", "Date_ID", "Season_ID",
          "Home/Away_Team_ID",
          "Stadium_ID", "Referee_ID",
          "Goals, Attendance"],
         bg=FACT_BG, fg=FACT_FG, fontsize=7)

    # Dim_Team (left)
    _box(ax, 2.2, 4.0, bw, bh, "Dim_Team",
         ["Team_ID (PK)", "Team_Name", "City_ID (FK)→"])
    _arrow(ax, 4.6, 4.8, 5.3, 4.1)

    # Dim_City (shared, far left)
    _box(ax, 0.1, 4.0, 1.9, bh, "Dim_City",
         ["City_ID (PK)", "City_Name"],
         bg=SNOW_BG, fg=SNOW_FG)
    _arrow(ax, 2.0, 4.8, 2.2, 4.8)

    # Dim_Stadium (bottom-left)
    _box(ax, 2.2, 1.0, bw, bh, "Dim_Stadium",
         ["Stadium_ID (PK)", "Stadium_Name",
          "City_ID (FK)→", "Capacity"])
    _arrow(ax, 4.6, 2.0, 5.3, 3.0)
    # Stadium → City
    _arrow(ax, 2.2, 1.8, 2.0, 4.0)

    # Dim_Season (top)
    _box(ax, 5.3, 5.0, bw, bh, "Dim_Season",
         ["Season_ID (PK)", "Season_Name",
          "Start_Year, End_Year"])
    _arrow(ax, 6.5, 5.0, 6.5, 4.7)

    # Dim_Player (right)
    _box(ax, 9.0, 4.0, bw, bh, "Dim_Player",
         ["Player_ID (PK)", "Player_Name",
          "Position_ID (FK)→", "Nationality"])
    _arrow(ax, 9.0, 4.8, 7.9, 4.1)   # note: connects to Fact_Player_Performance conceptually

    # Dim_Position (far right)
    _box(ax, 11.5, 4.0, 2.2, bh, "Dim_Position",
         ["Position_ID (PK)", "Position_Name"],
         bg=SNOW_BG, fg=SNOW_FG)
    _arrow(ax, 11.5, 4.8, 11.4, 4.8)

    # Dim_Referee (bottom-right)
    _box(ax, 9.0, 1.0, bw, bh, "Dim_Referee",
         ["Referee_ID (PK)", "Referee_Name"])
    _arrow(ax, 9.0, 2.0, 7.9, 2.8)

    # Dim_Date (top-right)
    _box(ax, 9.0, 5.0, bw, bh, "Dim_Date",
         ["Date_ID (PK)", "Date, Day, Month",
          "Quarter, Year"])
    _arrow(ax, 9.0, 5.8, 7.9, 4.5)

    # Snowflake chains label
    ax.text(0.1, 0.3,
            "Snowflake chains:  Dim_Team → Dim_City  |  Dim_Stadium → Dim_City  |  Dim_Player → Dim_Position",
            fontsize=8.5, color="#333", fontstyle="italic", fontfamily=FONT)

    handles = [
        mpatches.Patch(facecolor=FACT_BG, edgecolor="#333", label="Fact Table"),
        mpatches.Patch(facecolor=DIM_BG,  edgecolor="#333", label="Dimension Table"),
        mpatches.Patch(facecolor=SNOW_BG, edgecolor="#333", label="Snowflake Dimension"),
    ]
    ax.legend(handles=handles, loc="lower right", fontsize=9)
    plt.tight_layout()
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# 3. GALAXY / FACT CONSTELLATION SCHEMA
# ─────────────────────────────────────────────────────────────────────────────
def draw_galaxy_schema() -> plt.Figure:
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.set_xlim(0, 14); ax.set_ylim(0, 8)
    ax.axis("off")
    fig.patch.set_facecolor("#f8f9fa")
    ax.set_facecolor("#f8f9fa")
    ax.set_title("Galaxy Schema (Fact Constellation) — Three Fact Tables Sharing Conformed Dimensions",
                 fontsize=12, fontweight="bold", pad=10, fontfamily=FONT)

    # ── three fact tables ──────────────────────────────────────────────
    # Fact_Match (left)
    _box(ax, 0.3, 3.5, 2.8, 3.5,
         "Fact_Match",
         ["Match_ID (PK)", "Date_ID (FK)",
          "Season_ID (FK)", "Home_Team_ID (FK)",
          "Away_Team_ID (FK)", "Stadium_ID (FK)",
          "Referee_ID (FK)", "Home_Goals",
          "Away_Goals", "Attendance",
          "Occupancy_Pct, Match_Result",
          "Grain: 1 row = 1 match",
          "Rows: 10,260"],
         bg=FACT_BG, fg=FACT_FG, fontsize=6.8)

    # Fact_Team_Match (centre)
    _box(ax, 5.2, 2.8, 2.8, 4.2,
         "Fact_Team_Match",
         ["Team_Match_ID (PK)", "Match_ID",
          "Date_ID (FK)", "Season_ID (FK)",
          "Team_ID (FK)", "Opp_ID (FK)",
          "Is_Home, Goals_For",
          "Goals_Against, Shots",
          "Corners, Fouls, Yellow, Red",
          "Possession, Points, Result",
          "Form_Pts5, Form_GF5, Form_GA5",
          "Opp_Form_Pts5/GF5/GA5",
          "Grain: 1 row = 1 team × 1 match",
          "Rows: 20,520"],
         bg=FACT_BG, fg=FACT_FG, fontsize=6.5)

    # Fact_Player_Performance (right)
    _box(ax, 10.2, 3.5, 2.8, 3.5,
         "Fact_Player_Performance",
         ["Perf_ID (PK)", "Match_ID",
          "Date_ID (FK)", "Season_ID (FK)",
          "Player_ID (FK)", "Team_ID (FK)",
          "Minutes, Goals",
          "Assists, Shots",
          "Yellow, Red",
          "Grain: 1 row = 1 player × 1 match",
          "Rows: 287,280"],
         bg=FACT_BG, fg=FACT_FG, fontsize=6.8)

    # ── conformed dimensions (top row) ────────────────────────────────
    _box(ax, 0.5, 0.2, 2.0, 1.9, "Dim_Date",
         ["Date_ID (PK)", "Date, Day, Month",
          "Quarter, Year"])
    _box(ax, 3.0, 0.2, 2.0, 1.9, "Dim_Season",
         ["Season_ID (PK)", "Season_Name",
          "Start_Year, End_Year"])
    _box(ax, 5.5, 0.2, 2.0, 1.9, "Dim_Team",
         ["Team_ID (PK)", "Team_Name",
          "City_ID (FK)"])
    _box(ax, 8.0, 0.2, 2.2, 1.9, "Dim_Player",
         ["Player_ID (PK)", "Player_Name",
          "Position_ID (FK)"])
    _box(ax, 10.7, 0.2, 2.2, 1.9, "Dim_Stadium / Referee",
         ["Stadium_ID, Stadium_Name",
          "Referee_ID, Referee_Name"])

    # ── arrows: facts → shared dimensions ─────────────────────────────
    # Date arrows
    _arrow(ax, 1.7,  3.5, 1.2,  2.1)   # Fact_Match → Date
    _arrow(ax, 6.4,  2.8, 4.5,  2.1)   # Fact_Team_Match → Date
    _arrow(ax, 11.3, 3.5, 9.0,  2.1)   # Fact_Player → Date  (approx)

    # Season arrows
    _arrow(ax, 1.7,  3.5, 3.7,  2.1)
    _arrow(ax, 6.4,  2.8, 3.9,  2.1)
    _arrow(ax, 11.3, 3.5, 4.5,  2.1)

    # Team arrows
    _arrow(ax, 1.7,  4.5, 6.0,  2.1)
    _arrow(ax, 6.4,  3.5, 6.2,  2.1)
    _arrow(ax, 11.3, 4.5, 7.0,  2.1)

    # Player arrow
    _arrow(ax, 11.3, 4.0, 9.1,  2.1)

    # Stadium/Referee arrow from Fact_Match
    _arrow(ax, 1.7,  3.8, 11.2, 2.1)

    # Match_ID link (between fact tables)
    ax.annotate("", xy=(5.2, 5.5), xytext=(3.1, 5.5),
                arrowprops=dict(arrowstyle="<->", color="#c0392b", lw=1.5))
    ax.text(4.15, 5.65, "Match_ID", ha="center", fontsize=7.5,
            color="#c0392b", fontfamily=FONT)
    ax.annotate("", xy=(10.2, 5.5), xytext=(8.0, 5.5),
                arrowprops=dict(arrowstyle="<->", color="#c0392b", lw=1.5))
    ax.text(9.1, 5.65, "Match_ID", ha="center", fontsize=7.5,
            color="#c0392b", fontfamily=FONT)

    # Caption
    ax.text(0.2, 7.75,
            "Conformed dimensions (Dim_Date, Dim_Season, Dim_Team) are shared across all three fact tables. "
            "Match_ID links facts for drill-across.",
            fontsize=8, color="#333", fontstyle="italic", fontfamily=FONT)

    handles = [
        mpatches.Patch(facecolor=FACT_BG, edgecolor="#333", label="Fact Table"),
        mpatches.Patch(facecolor=DIM_BG,  edgecolor="#333", label="Conformed Dimension"),
    ]
    ax.legend(handles=handles, loc="lower right", fontsize=9)
    plt.tight_layout()
    return fig
