"""
utils/models.py
All ML model training functions for the EPL DWM Platform.
Every function is @st.cache_resource — keyed on MODEL CONFIGURATION only.
Changing display filters (Team, Season, Home/Away) must NEVER trigger retraining.

Rules enforced here:
  - Regression : 75/25 random split (random_state=0); full 20,520-row population
  - Classification : chronological split by default (seasons 1-20 train, 21-27 test)
                     or random split; full 20,520-row population
  - Clustering : all 540 team-season profiles; no held-out concept
  - Apriori : full scope by default; scope change is intentional config change
"""

import numpy as np
import pandas as pd
import streamlit as st
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.feature_selection import mutual_info_classif
from sklearn.linear_model import LinearRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    mean_squared_error,
    r2_score,
    silhouette_score,
    adjusted_rand_score,
)
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier
from scipy.cluster.hierarchy import linkage, fcluster
from mlxtend.frequent_patterns import apriori, association_rules


# ── feature definitions ─────────────────────────────────────────────────────
PREMATCH_FEATURES = [
    "Form_Pts5", "Form_GF5", "Form_GA5",
    "Opp_Form_Pts5", "Opp_Form_GF5", "Opp_Form_GA5",
    "Is_Home",
]

INMATCH_FEATURES = [
    "Shots", "Corners", "Fouls", "Possession",
    "Yellow", "Red", "Is_Home",
]

CLUSTER_FEATURES = [
    "Goals_For_mean", "Goals_Against_mean", "Shots_mean",
    "Possession_mean", "Corners_mean", "Fouls_mean", "Pts_per_Match",
]

# Seasons used for chronological split
TRAIN_SEASON_IDS = list(range(1, 21))   # seasons 1–20  (1999/00 – 2018/19)
TEST_SEASON_IDS  = list(range(21, 28))  # seasons 21–27 (2019/20 – 2025/26)


# ── Regression ──────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner="Training regression model…")
def get_regression_model(features: tuple, target: str = "Goals_For") -> dict:
    """
    Train LinearRegression on the full Fact_Team_Match population.
    Cache key = (features tuple, target).
    Returns a dict with model, test data, predictions, and metrics.
    Changing display filters must NOT call this function again.
    """
    from utils.db import load_team_match
    tm = load_team_match().copy()

    X = tm[list(features)]
    y = tm[target]

    X_train, X_test, y_train, y_test, idx_train, idx_test = train_test_split(
        X, y, tm.index, test_size=0.25, random_state=0
    )

    model = LinearRegression().fit(X_train, y_train)
    y_pred = model.predict(X_test)

    test_df = tm.loc[idx_test, ["Team_Name", "Season_Name", "Is_Home"]].copy()
    test_df["y_actual"] = y_test.values
    test_df["y_pred"]   = y_pred

    return {
        "model"    : model,
        "features" : list(features),
        "target"   : target,
        "test_df"  : test_df,
        "y_actual" : y_test.values,
        "y_pred"   : y_pred,
        "r2"       : r2_score(y_test, y_pred),
        "rmse"     : float(np.sqrt(mean_squared_error(y_test, y_pred))),
        "coef"     : dict(zip(list(features), model.coef_.round(4))),
        "intercept": float(round(model.intercept_, 4)),
        "n_train"  : len(X_train),
        "n_test"   : len(X_test),
    }


# ── Classification ──────────────────────────────────────────────────────────
def get_decision_tree_path(dt_model, features: list, sample_df: pd.DataFrame) -> list:
    """
    Extract the actual fitted decision path traversed for a single sample.
    Returns list of dicts: {'node_id', 'feature', 'value', 'threshold', 'direction', 'rule'}
    """
    if sample_df.empty:
        return []
    X_val = sample_df[features].values
    node_indicator = dt_model.decision_path(X_val)
    leaf_id = dt_model.apply(X_val)[0]
    node_index = node_indicator.indices[node_indicator.indptr[0]:node_indicator.indptr[1]]

    rules = []
    for node_id in node_index:
        if leaf_id == node_id:
            continue
        feat_idx = dt_model.tree_.feature[node_id]
        feat_name = features[feat_idx]
        thresh = dt_model.tree_.threshold[node_id]
        val = float(sample_df[feat_name].iloc[0])
        direction = "<=" if val <= thresh else ">"
        rules.append({
            "node_id": int(node_id),
            "feature": feat_name,
            "value": val,
            "threshold": float(thresh),
            "direction": direction,
            "rule": f"{feat_name} ({val:.2f}) {direction} {thresh:.2f}",
        })
    return rules


@st.cache_resource(show_spinner="Training classification models…")
def get_classification_model(
    feature_mode: str,   # "pre_match" | "in_match"
    strategy: str,       # "chronological" | "random"
    depth: int,          # Decision Tree max_depth
) -> dict:
    """
    Train DecisionTreeClassifier + GaussianNB on the full population.
    Cache key = (feature_mode, strategy, depth).
    Changing display filters must NOT call this function again.
    """
    from utils.db import load_team_match, load_dim_team
    tm = load_team_match().copy()
    teams_map = load_dim_team().set_index("Team_ID")["Team_Name"].to_dict()
    tm["Opp_Team_Name"] = tm["Opp_ID"].map(teams_map)

    features = PREMATCH_FEATURES if feature_mode == "pre_match" else INMATCH_FEATURES
    X = tm[features]
    y = tm["Result"]

    meta_cols = [
        "Team_Match_ID", "Match_ID", "Date_ID", "Team_Name", "Opp_Team_Name",
        "Season_Name", "Season_ID", "Result", "Goals_For", "Goals_Against"
    ]
    all_cols = list(dict.fromkeys(meta_cols + list(features)))

    if strategy == "chronological":
        train_mask = tm["Season_ID"].isin(TRAIN_SEASON_IDS)
        test_mask  = tm["Season_ID"].isin(TEST_SEASON_IDS)
        X_train, y_train = X[train_mask], y[train_mask]
        X_test,  y_test  = X[test_mask],  y[test_mask]
        test_df = tm[test_mask][all_cols].copy()
        train_season_names = tm[train_mask]["Season_Name"].unique().tolist()
        test_season_names  = tm[test_mask]["Season_Name"].unique().tolist()
    else:
        X_tr, X_te, y_tr, y_te, idx_tr, idx_te = train_test_split(
            X, y, tm.index, test_size=0.2, random_state=0, stratify=y
        )
        X_train, y_train = X_tr, y_tr
        X_test,  y_test  = X_te, y_te
        test_df = tm.loc[idx_te, all_cols].copy()
        train_season_names = tm.loc[idx_tr, "Season_Name"].unique().tolist()
        test_season_names  = tm.loc[idx_te, "Season_Name"].unique().tolist()

    # Attribute relevance (mutual information) — computed on training set
    mi_scores = pd.Series(
        mutual_info_classif(X_train, y_train, random_state=0),
        index=features
    ).sort_values(ascending=True)

    # Decision Tree
    dt = DecisionTreeClassifier(max_depth=depth, random_state=0).fit(X_train, y_train)
    dt_pred = dt.predict(X_test)
    dt_proba = dt.predict_proba(X_test)

    # Naive Bayes
    nb = GaussianNB().fit(X_train, y_train)
    nb_pred = nb.predict(X_test)
    nb_proba = nb.predict_proba(X_test)

    classes = list(dt.classes_)  # e.g. ['D', 'L', 'W']
    labels  = ["W", "D", "L"]   # canonical result order

    def _metrics(y_true, y_pred):
        return {
            "accuracy"  : round(accuracy_score(y_true, y_pred), 4),
            "report_df" : pd.DataFrame(
                classification_report(y_true, y_pred, output_dict=True, zero_division=0)
            ).T.round(3),
            "cm"        : confusion_matrix(y_true, y_pred, labels=labels),
            "cm_labels" : labels,
        }

    test_df = test_df.reset_index(drop=True)
    test_df["dt_pred"] = dt_pred
    test_df["nb_pred"] = nb_pred
    test_df["actual"]  = y_test.values

    # Add class probabilities to test_df
    for i, cls_name in enumerate(classes):
        test_df[f"dt_prob_{cls_name}"] = dt_proba[:, i].round(4)
        test_df[f"nb_prob_{cls_name}"] = nb_proba[:, i].round(4)

    return {
        "dt_model"          : dt,
        "nb_model"          : nb,
        "features"          : features,
        "feature_mode"      : feature_mode,
        "strategy"          : strategy,
        "test_df"           : test_df,
        "mi_scores"         : mi_scores,
        "dt_metrics"        : _metrics(y_test, dt_pred),
        "nb_metrics"        : _metrics(y_test, nb_pred),
        "n_train"           : len(X_train),
        "n_test"            : len(X_test),
        "train_season_names": train_season_names,
        "test_season_names" : test_season_names,
        "classes"           : classes,
    }


# ── Clustering — K recommendation (runs once, k-independent) ───────────────
@st.cache_resource(show_spinner="Computing cluster recommendations…")
def get_cluster_recommendations() -> dict:
    """
    Compute KMeans inertia + silhouette for k=2..8 on all 540 profiles.
    Cached independently of get_kmeans_model so changing K doesn't
    recompute recommendations.
    """
    from utils.db import load_team_profiles
    prof = load_team_profiles()
    Z = StandardScaler().fit_transform(prof[CLUSTER_FEATURES].values)

    ks, inertias, silhouettes = [], [], []
    for k in range(2, 9):
        km = KMeans(n_clusters=k, n_init=10, random_state=0).fit(Z)
        ks.append(k)
        inertias.append(km.inertia_)
        silhouettes.append(silhouette_score(Z, km.labels_))

    recommended_k = ks[int(np.argmax(silhouettes))]
    return {
        "ks"            : ks,
        "inertias"      : inertias,
        "silhouettes"   : silhouettes,
        "recommended_k" : recommended_k,
        "max_silhouette": max(silhouettes),
    }


@st.cache_resource(show_spinner="Running K-Means clustering…")
def get_kmeans_model(k: int) -> dict:
    """
    KMeans on all 540 team-season profiles.
    Cache key = k.
    User's team/season filter is applied externally for highlighting only.
    """
    from utils.db import load_team_profiles
    prof = load_team_profiles()
    Z = StandardScaler().fit_transform(prof[CLUSTER_FEATURES].values)

    km     = KMeans(n_clusters=k, n_init=10, random_state=0).fit(Z)
    pca    = PCA(n_components=2, random_state=0).fit_transform(Z)
    labels = km.labels_

    profile_df = prof.copy()
    profile_df["Cluster"] = labels.astype(str)
    profile_df["PC1"] = pca[:, 0]
    profile_df["PC2"] = pca[:, 1]

    cluster_means = (
        profile_df.groupby("Cluster")[CLUSTER_FEATURES]
        .mean().round(3)
    )

    return {
        "k"            : k,
        "labels"       : labels,
        "inertia"      : km.inertia_,
        "silhouette"   : silhouette_score(Z, labels),
        "profile_df"   : profile_df,
        "cluster_means": cluster_means,
        "Z"            : Z,
        "pca_coords"   : pca,
    }


@st.cache_resource(show_spinner="Computing hierarchical linkage…")
def get_agglomerative_linkage() -> dict:
    """
    Compute Ward linkage on all 540 profiles. Cached once (K-independent).
    fcluster() is called externally with whatever K is selected.
    """
    from utils.db import load_team_profiles
    prof = load_team_profiles()
    Z = StandardScaler().fit_transform(prof[CLUSTER_FEATURES].values)
    Z_link = linkage(Z, method="ward")
    return {
        "Z_link"  : Z_link,
        "Z"       : Z,
        "prof"    : prof,
        "features": CLUSTER_FEATURES,
    }


def get_agglomerative_clusters(k: int) -> pd.DataFrame:
    """
    Apply fcluster to cached linkage for given k.
    Returns profile_df with 'Agg_Cluster' column.
    Not cached — fast operation, depends on cached linkage.
    """
    agg = get_agglomerative_linkage()
    prof = agg["prof"].copy()
    prof["Agg_Cluster"] = fcluster(agg["Z_link"], k, criterion="maxclust").astype(str)
    return prof


# ── Apriori ─────────────────────────────────────────────────────────────────
# NOTE: @st.cache_data (not resource) — scope change is intentional config change.
# Percentile thresholds are recomputed within the selected scope.

@st.cache_data(show_spinner="Building transaction set…", ttl=3600)
def get_apriori_transactions(
    scope: str,        # "all" | "team" | "season"
    scope_value: str,  # Team_Name or Season_Name (ignored when scope="all")
) -> tuple[pd.DataFrame, int, str]:
    """
    Build a boolean transaction DataFrame from Fact_Team_Match.
    Uses ALL rows in the given scope — no silent sampling.
    Returns (transactions_df, n_transactions, scope_label).
    """
    from utils.db import load_team_match
    tm = load_team_match().copy()

    if scope == "team" and scope_value:
        d = tm[tm["Team_Name"] == scope_value].copy()
        scope_label = f"{scope_value} (team)"
    elif scope == "season" and scope_value:
        d = tm[tm["Season_Name"] == scope_value].copy()
        scope_label = f"{scope_value} (season)"
    else:
        d = tm.copy()
        scope_label = "All teams — all seasons"

    # Percentiles computed within scope for meaningful thresholds
    hi = lambda col: d[col] >= d[col].quantile(0.67)
    lo = lambda col: d[col] <= d[col].quantile(0.33)

    transactions = pd.DataFrame({
        "High_Shots"      : hi("Shots"),
        "Low_Shots"       : lo("Shots"),
        "High_Corners"    : hi("Corners"),
        "High_Fouls"      : hi("Fouls"),
        "High_Possession" : hi("Possession"),
        "Low_Possession"  : lo("Possession"),
        "Has_Card"        : (d["Yellow"] + d["Red"]) >= 3,
        "Home"            : d["Is_Home"] == 1,
        "Away"            : d["Is_Home"] == 0,
        "Win"             : d["Result"] == "W",
        "Draw"            : d["Result"] == "D",
        "Loss"            : d["Result"] == "L",
    }).reset_index(drop=True)

    return transactions, len(transactions), scope_label


# ── Apriori item-category map (for trivial rule filtering) ──────────────────
ITEM_CATEGORY = {
    "High_Shots": "Shots", "Low_Shots": "Shots",
    "High_Corners": "Corners",
    "High_Fouls": "Fouls",
    "High_Possession": "Possession", "Low_Possession": "Possession",
    "Has_Card": "Cards",
    "Home": "Venue", "Away": "Venue",
    "Win": "Result", "Draw": "Result", "Loss": "Result",
}


def run_apriori(
    transactions: pd.DataFrame,
    min_support: float,
    min_confidence: float,
    min_lift: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Run Apriori and return (frequent_itemsets_df, rules_df).
    Trivial rules (same attribute category on both sides) are removed.
    """
    fi = apriori(transactions, min_support=min_support, use_colnames=True)

    if len(fi) < 2:
        return fi, pd.DataFrame()

    rules = association_rules(fi, metric="confidence", min_threshold=min_confidence)

    if rules.empty:
        return fi, rules

    # Filter by lift
    rules = rules[rules["lift"] >= min_lift]

    # Remove trivial rules (same attribute category on antecedent and consequent)
    def _not_trivial(row):
        ant_cats = {ITEM_CATEGORY.get(i, i) for i in row["antecedents"]}
        con_cats = {ITEM_CATEGORY.get(i, i) for i in row["consequents"]}
        return len(ant_cats & con_cats) == 0

    rules = rules[rules.apply(_not_trivial, axis=1)].copy()

    # Format frozensets to readable strings
    for col in ["antecedents", "consequents"]:
        rules[col] = rules[col].apply(lambda s: ", ".join(sorted(s)))

    # Clean up float columns
    for col in ["support", "confidence", "lift"]:
        rules[col] = rules[col].round(4)

    return fi, rules.sort_values("lift", ascending=False).reset_index(drop=True)
