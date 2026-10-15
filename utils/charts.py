"""
utils/charts.py
Shared Plotly chart factory functions for the EPL DWM Platform.
All functions return a Plotly Figure object.
Consistent styling is applied across all pages.
"""
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# ── colour palette ───────────────────────────────────────────────────────────
EPL_BLUE    = "#1e3a5f"
EPL_GREEN   = "#00a859"
EPL_PURPLE  = "#6f42c1"
EPL_GOLD    = "#e8b84b"
SEQ_SCALE   = "Blues"
DIV_SCALE   = "RdYlGn"

_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, Segoe UI, sans-serif", size=13),
    margin=dict(l=40, r=20, t=50, b=40),
)


def _apply(fig: go.Figure) -> go.Figure:
    fig.update_layout(**_LAYOUT)
    return fig


# ── basic charts ─────────────────────────────────────────────────────────────
def line_chart(df: pd.DataFrame, x: str, y: str, title: str,
               color: str | None = None, markers: bool = True) -> go.Figure:
    fig = px.line(df, x=x, y=y, title=title, color=color, markers=markers,
                  color_discrete_sequence=px.colors.qualitative.Set2)
    return _apply(fig)


def bar_chart(df: pd.DataFrame, x: str, y: str, title: str,
              orientation: str = "v", color: str | None = None,
              color_discrete_sequence=None) -> go.Figure:
    kw = dict(x=x, y=y, title=title, orientation=orientation)
    if color:
        kw["color"] = color
    if color_discrete_sequence:
        kw["color_discrete_sequence"] = color_discrete_sequence
    else:
        kw["color_discrete_sequence"] = [EPL_BLUE]
    fig = px.bar(df, **kw)
    return _apply(fig)


def scatter_chart(df: pd.DataFrame, x: str, y: str, title: str,
                  color: str | None = None, hover_data: list | None = None,
                  opacity: float = 0.5, size: str | None = None) -> go.Figure:
    kw = dict(x=x, y=y, title=title, opacity=opacity,
              color_discrete_sequence=px.colors.qualitative.Set2)
    if color:
        kw["color"] = color
    if hover_data:
        kw["hover_data"] = hover_data
    if size:
        kw["size"] = size
    fig = px.scatter(df, **kw)
    return _apply(fig)


def pie_chart(df: pd.DataFrame, names: str, title: str,
              values: str | None = None) -> go.Figure:
    kw = dict(names=names, title=title,
              color_discrete_sequence=px.colors.qualitative.Set2)
    if values:
        kw["values"] = values
    fig = px.pie(df, **kw)
    fig.update_traces(textposition="inside", textinfo="percent+label")
    return _apply(fig)


def heatmap(matrix: pd.DataFrame, title: str,
            text_auto: bool = True,
            color_scale: str = "Blues") -> go.Figure:
    fig = px.imshow(matrix, text_auto=text_auto, title=title,
                    color_continuous_scale=color_scale, aspect="auto")
    return _apply(fig)


# ── specialised charts ───────────────────────────────────────────────────────
def actual_vs_predicted(y_actual: np.ndarray, y_pred: np.ndarray,
                        title: str, n: int,
                        max_points: int = 1500) -> go.Figure:
    """Scatter of actual vs predicted values with a perfect-fit diagonal."""
    idx = np.random.default_rng(0).choice(len(y_actual),
                                          min(max_points, len(y_actual)),
                                          replace=False)
    df = pd.DataFrame({"Actual": y_actual[idx], "Predicted": y_pred[idx]})
    fig = px.scatter(df, x="Actual", y="Predicted",
                     title=f"{title} (n = {n:,})",
                     opacity=0.45,
                     color_discrete_sequence=[EPL_BLUE])
    lo = min(df.Actual.min(), df.Predicted.min())
    hi = max(df.Actual.max(), df.Predicted.max())
    fig.add_shape(type="line", x0=lo, y0=lo, x1=hi, y1=hi,
                  line=dict(color=EPL_GREEN, dash="dash", width=2))
    return _apply(fig)


def confusion_matrix_chart(cm: np.ndarray, labels: list,
                            title: str = "Confusion Matrix") -> go.Figure:
    fig = px.imshow(cm, x=labels, y=labels, text_auto=True, title=title,
                    labels=dict(x="Predicted", y="Actual"),
                    color_continuous_scale="Blues")
    fig.update_layout(xaxis_title="Predicted", yaxis_title="Actual")
    return _apply(fig)


def pca_scatter(profile_df: pd.DataFrame,
                color_col: str,
                hover_cols: list,
                highlight_idx: int | None = None,
                title: str = "Team-Season Clusters (PCA)") -> go.Figure:
    """
    PCA scatter for clustering. If highlight_idx is given, that point is
    drawn larger with a black border and labelled.
    """
    fig = px.scatter(
        profile_df, x="PC1", y="PC2",
        color=color_col,
        hover_data=hover_cols,
        title=title,
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    if highlight_idx is not None:
        row = profile_df.iloc[highlight_idx]
        fig.add_trace(go.Scatter(
            x=[row["PC1"]], y=[row["PC2"]],
            mode="markers+text",
            marker=dict(size=16, color=EPL_GOLD,
                        line=dict(color="black", width=2)),
            text=[f"{row['Team_Name']} {row['Season_Name']}"],
            textposition="top center",
            name="Selected",
            showlegend=True,
        ))
    return _apply(fig)


def correlation_heatmap(df: pd.DataFrame, cols: list,
                        title: str = "Correlation Heatmap") -> go.Figure:
    corr = df[cols].corr().round(2)
    return heatmap(corr, title, text_auto=True, color_scale="RdBu_r")


def form_trend_chart(df: pd.DataFrame, team: str) -> go.Figure:
    """Rolling form (points per match) over matches for a team."""
    d = df.sort_values("Match_ID")[["Match_ID", "Form_Pts5"]].copy()
    fig = px.line(d, x="Match_ID", y="Form_Pts5",
                  title=f"{team} — 5-match rolling points",
                  color_discrete_sequence=[EPL_GREEN], markers=False)
    fig.update_xaxes(title="Match")
    fig.update_yaxes(title="Avg pts (last 5)")
    return _apply(fig)


def league_table_bar(df: pd.DataFrame) -> go.Figure:
    """Horizontal bar chart of total points by team (sorted)."""
    d = df.sort_values("Points")
    fig = px.bar(d, x="Points", y="Team_Name", orientation="h",
                 title="League Table — Total Points",
                 color="Points", color_continuous_scale="Blues")
    return _apply(fig)
