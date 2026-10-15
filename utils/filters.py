"""
utils/filters.py
Reusable Streamlit filter widgets and display helpers.

KEY RULE (from approved plan):
  Exploration filters (Team, Season, Home/Away, Player, Position)
  must NEVER affect model training populations.
  They are applied to held-out test results / exploration DataFrames only.
"""
import streamlit as st
import pandas as pd
from utils.db import load_dim_team, load_dim_season, load_dim_position


# ── list helpers ────────────────────────────────────────────────────────────
def _team_names() -> list[str]:
    return sorted(load_dim_team().Team_Name.tolist())


def _season_names() -> list[str]:
    return load_dim_season().Season_Name.tolist()  # already ordered by Season_ID


def _position_names() -> list[str]:
    return load_dim_position().Position_Name.tolist()


# ── individual filter widgets ───────────────────────────────────────────────
def team_filter(key: str = "team", label: str = "Team",
                include_all: bool = True) -> str | None:
    """Selectbox for Team. Returns None when 'All teams' is selected."""
    options = (["All teams"] if include_all else []) + _team_names()
    sel = st.selectbox(label, options, key=key)
    return None if sel == "All teams" else sel


def season_filter(key: str = "season", label: str = "Season",
                  include_all: bool = True) -> str | None:
    """Selectbox for Season. Returns None when 'All seasons' is selected."""
    options = (["All seasons"] if include_all else []) + _season_names()
    sel = st.selectbox(label, options, key=key)
    return None if sel == "All seasons" else sel


def home_away_filter(key: str = "home_away") -> str | None:
    """Radio for venue. Returns None (All), 1 (Home), or 0 (Away)."""
    sel = st.radio("Venue", ["All", "Home", "Away"],
                   horizontal=True, key=key)
    return None if sel == "All" else (1 if sel == "Home" else 0)


def position_filter(key: str = "position", label: str = "Position",
                    include_all: bool = True) -> str | None:
    """Selectbox for player position."""
    options = (["All positions"] if include_all else []) + _position_names()
    sel = st.selectbox(label, options, key=key)
    return None if sel == "All positions" else sel


def player_filter(player_df: pd.DataFrame, key: str = "player") -> int | None:
    """
    Selectbox built from a (filtered) player DataFrame.
    Returns Player_ID of the selection, or None if empty.
    """
    if player_df.empty:
        st.info("No players match the current filters.")
        return None
    # Build display label: "Player Name (Position)"
    player_df = player_df.copy()
    player_df["_label"] = player_df["Player_Name"] + " — " + player_df["Position_Name"]
    options = player_df["_label"].tolist()
    sel = st.selectbox("Player", options, key=key)
    row = player_df[player_df["_label"] == sel].iloc[0]
    return int(row["Player_ID"])


# ── DataFrame filtering helpers ─────────────────────────────────────────────
def apply_team_season_filter(
    df: pd.DataFrame,
    team: str | None = None,
    season: str | None = None,
    is_home: int | None = None,
) -> pd.DataFrame:
    """
    Filter a DataFrame by Team_Name, Season_Name, Is_Home.
    Each parameter is optional; None means 'no filter on this column'.
    Returns the filtered DataFrame.
    """
    mask = pd.Series([True] * len(df), index=df.index)
    if team is not None and "Team_Name" in df.columns:
        mask &= df["Team_Name"] == team
    if season is not None and "Season_Name" in df.columns:
        mask &= df["Season_Name"] == season
    if is_home is not None and "Is_Home" in df.columns:
        mask &= df["Is_Home"] == is_home
    return df[mask]


# ── sample-size and warning display ────────────────────────────────────────
def show_sample_size(n: int, threshold: int = 50,
                     label: str = "Samples") -> None:
    """Display n = X metric; yellow warning if n < threshold."""
    col1, col2 = st.columns([1, 3])
    col1.metric(label, f"n = {n:,}")
    if n < threshold:
        col2.warning(
            f"⚠️ Small sample (n = {n:,}) — interpret metrics with caution."
        )


def show_model_info(n_train: int, n_test: int,
                    train_desc: str = "", test_desc: str = "") -> None:
    """Render a compact model population info banner."""
    train_label = f"Train: {n_train:,}" + (f" ({train_desc})" if train_desc else "")
    test_label  = f"Test:  {n_test:,}"  + (f" ({test_desc})"  if test_desc  else "")
    st.caption(f"🔵 Model population — {train_label}  |  {test_label}")


def show_in_sample_warning(season: str, train_seasons: list[str]) -> bool:
    """
    If `season` is in `train_seasons`, show a warning and return True.
    Returns False if the season is in the held-out test set.
    """
    if season in train_seasons:
        st.warning(
            f"⚠️ **In-sample prediction** — {season} was part of the "
            f"training set. Metrics shown here are not held-out test performance."
        )
        return True
    return False


def dwm_label(method: str, lab: int | str = "") -> None:
    """Render a clean analytical method badge."""
    st.markdown(
        f"""<div style="display:inline-flex;align-items:center;gap:8px;border:1px solid var(--line);color:var(--mute);
        padding:5px 12px;border-radius:30px;font-size:0.66rem;letter-spacing:.16em;text-transform:uppercase;font-weight:600;margin-bottom:8px;">
        <span style="width:6px;height:6px;border-radius:50%;background:var(--pk)"></span>Method · <b style="color:var(--ink)">{method}</b></div>""",
        unsafe_allow_html=True,
    )


# ── filter status badge ──────────────────────────────────────────────────────
def filter_status(team: str | None, season: str | None,
                  is_home: int | None = None) -> None:
    """Show a compact 'Active filters' badge if any filter is set."""
    parts = []
    if team:
        parts.append(f"Team: **{team}**")
    if season:
        parts.append(f"Season: **{season}**")
    if is_home is not None:
        parts.append("Venue: **Home**" if is_home == 1 else "Venue: **Away**")
    if parts:
        st.info("🔍 Active display filter — " + " | ".join(parts) +
                "  *(model was trained on the full population)*")
