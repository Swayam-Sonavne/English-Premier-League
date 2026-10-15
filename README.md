# ⚽ English Premier League (EPL) Analytics & Data Warehouse Platform

A comprehensive full-stack Data Warehousing & Mining (DWM) analytics platform built with **Streamlit**, **SQLite (Star Schema)**, **Plotly**, and **Scikit-Learn**. 

Spanning 27 Premier League seasons and over 20,500 team-match records, this platform features dedicated analytical modules for both end-users and administrators.

---

## 🌟 Core Features

### 👤 User Explorer
- **EPL Explorer**: League tables, multi-metric filtering, goals & possession trends, and team profiles.
- **Player Comparison & Profiles**: Multi-season player analytics, radar charts, peer percentiles, and similarity clustering.

### 🛡️ Admin & Data Mining Laboratory
- **Admin Dashboard**: System health KPI strip, model statuses, and transaction volume monitoring.
- **Match Outcomes (Classification)**: Decision Tree, Naïve Bayes, and Logistic Regression with confusion matrices and ROC curves.
- **Team Analytics (Clustering)**: K-Means & Agglomerative Hierarchical clustering, dendrograms, silhouette analysis, and PCA 2D projections.
- **Performance Analysis (Regression)**: Multi-feature linear regression, feature coefficients, and residual error analysis.
- **Association Analysis (Apriori Mining)**: Co-occurrence patterns, frequent itemsets, lift matrices, and tactical rules leading to wins or losses.
- **OLAP Analysis**: Interactive Roll-up, Drill-down, Slice, Dice, and Pivot operations across time, team, and location dimensions.
- **Data Warehouse Schema Viewer**: Interactive star schema visualizer with dimensional dictionary inspection.

---

## 🛠️ Tech Stack
- **Frontend & App Framework**: Streamlit
- **Visualization**: Plotly Graph Objects & Express
- **Machine Learning & Data Mining**: Scikit-Learn, SciPy, Mlxtend
- **Data Processing**: Pandas, NumPy
- **Database**: SQLite (Star Schema with 2 Fact Tables & 7 Dimension Tables)

---

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/<your-username>/<your-repo-name>.git
cd <your-repo-name>
```

### 2. Set up virtual environment (optional but recommended)
```bash
python -m venv venv
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. (Optional) Rebuild Star Schema Database
If `epl_dw.db` needs to be regenerated from raw CSVs:
```bash
python generate_warehouse.py
```

### 5. Launch the Streamlit application
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 📂 Project Structure
```text
├── app.py                     # Main application entry point & router
├── pages/                     # Multi-page analytical modules
│   ├── 1_Dashboard.py
│   ├── 2_EPL_Explorer.py
│   ├── 3_Performance_Analysis.py
│   ├── 4_Match_Outcomes.py
│   ├── 5_Team_Analytics.py
│   ├── 6_Player_Analytics.py
│   ├── 7_Association_Analysis.py
│   ├── 8_OLAP_Analysis.py
│   └── 9_Data_Warehouse.py
├── utils/                     # Database, ML modeling, and theme engines
│   ├── db.py
│   ├── models.py
│   ├── theme.py
│   ├── admin_views.py
│   ├── user_views.py
│   └── filters.py
├── csv/                       # Dimensional and fact CSV extracts
├── generate_warehouse.py      # Star schema ETL script
├── epl_dw.db                  # SQLite Data Warehouse
└── requirements.txt           # Python dependencies
```
