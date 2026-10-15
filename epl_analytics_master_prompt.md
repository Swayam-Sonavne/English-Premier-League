# MASTER PROMPT FOR ANTIGRAVITY

## EPL Analytics Platform — Complete Product + Technical Requirements

> **IMPORTANT: Read and understand this entire specification before changing the code.**
>
> The current project already contains an EPL/DWM analytics system and synthetic dataset.
>
> **Do not rebuild the project from scratch.**
>
> First inspect the existing codebase, understand what is already implemented, and then modify it to match the requirements below.
>
> The biggest requirement is that **USER and ADMIN are two genuinely different interfaces**, not two login buttons leading to the same dashboard.

---

# 1. PROJECT PURPOSE

We are building a **college mini-project/assignment for Data Warehouse and Mining (DWM)** using an EPL-themed synthetic dataset.

The data is intentionally synthetic.

**Synthetic data is acceptable and must NOT be replaced with real EPL data.**

The project demonstrates:

* Data Warehouse
* OLAP
* Data visualization
* Regression
* Classification
* Clustering
* Association Rule Mining
* Exploratory data analysis

The project has two roles:

```text
                         EPL ANALYTICS PLATFORM
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
               USER LOGIN                  ADMIN LOGIN
                    │                           │
              EPL INSIGHTS              EPL ANALYTICS & DWM
                    │                           │
             Simple analytics          Technical analytics
             Business view             Academic/DWM view
```

---

# 2. MOST IMPORTANT REQUIREMENT

## USER AND ADMIN MUST NOT HAVE THE SAME INTERFACE.

The current implementation is incorrect if:

```text
User Login
    ↓
Same dashboard
    ↓
Graphs + ML + DWM

Admin Login
    ↓
Same dashboard
    ↓
Graphs + ML + DWM
```

That is NOT what we want.

Instead:

```text
USER LOGIN
    ↓
EPL INSIGHTS
    ↓
Simple football/business analytics
```

and:

```text
ADMIN LOGIN
    ↓
EPL ANALYTICS & DWM
    ↓
Complete technical DWM + ML analytics
```

They share the same backend/database/models, but the **navigation, pages, information depth and presentation are different.**

---

# 3. SYSTEM ARCHITECTURE

Use:

```text
                 SAME DATABASE
                       │
                 SAME DATASET
                       │
                SAME ML ENGINE
                       │
              SAME ANALYTICS ENGINE
                       │
            ┌──────────┴──────────┐
            │                     │
        USER UI               ADMIN UI
            │                     │
     EPL INSIGHTS        EPL ANALYTICS & DWM
```

### DO NOT:

* create two databases
* duplicate the dataset
* duplicate ML models
* create two separate analytics engines
* rebuild working backend functionality

### DO:

* reuse the existing database
* reuse existing data
* reuse existing ML implementations
* create separate presentation layers
* implement proper role-based routing

---

# 4. EXISTING DATA WAREHOUSE

The project uses these dimensions:

```text
Dim_Date
Dim_Season
Dim_Team
Dim_Stadium
Dim_City
Dim_Referee
Dim_Player
Dim_Position
```

Facts:

```text
Fact_Match
Fact_Team_Match
Fact_Player_Performance
```

Fact table grain:

```text
Fact_Match
→ 1 row = 1 match

Fact_Team_Match
→ 1 row = 1 team in 1 match

Fact_Player_Performance
→ 1 row = 1 player in 1 match
```

The existing synthetic dataset should be preserved.

---

# 5. USER APPLICATION

## Product name

# EPL INSIGHTS

The normal user is assumed to know nothing about DWM or Machine Learning.

The user wants understandable football information.

---

# 6. USER NAVIGATION

The user navigation MUST be exactly:

```text
EPL INSIGHTS
│
├── Home
├── Match Prediction
├── Team Insights
├── Player Insights
├── Match Explorer
└── Compare
```

These are the only main user pages.

The user should NOT see an admin sidebar.

---

# 7. USER — HOME

Purpose:

Give a simple overview of the EPL dataset.

Show simple information such as:

```text
Total Seasons
Total Teams
Total Matches
Total Players
```

Then useful insights such as:

```text
Most Successful Team
Top Scorer
Highest Scoring Team
Most Wins
```

### IMPORTANT

These must come from the database.

Do NOT hardcode examples such as:

```text
Arsenal — 88 points
Mohamed Salah — 18 goals
```

Those are only examples.

Actual values must come from queries against the existing warehouse.

---

# 8. USER — MATCH PREDICTION

Allow the user to select:

```text
Season
Home Team
Away Team
```

Then show a simple result.

Example:

```text
ARSENAL vs CHELSEA

Arsenal favoured

Prediction:
ARSENAL WIN
```

The user should NOT see technical model information.

### DO NOT show:

```text
62%
Confidence: HIGH
Decision Tree
Naive Bayes
Precision
Recall
F1
Confusion Matrix
```

Instead, if the prediction strength needs to be communicated, use soft wording:

```text
Narrow favourite
Favourite
Clear favourite
```

Do not imply certainty.

---

# 9. USER — TEAM INSIGHTS

Allow the user to select a team.

Show understandable statistics:

```text
Team Name

Matches Played
Wins
Draws
Losses
Goals Scored
Goals Conceded
Points

Recent Form
W W D W W

Performance
Excellent
```

All statistics must come from the database.

Do not hardcode values.

---

# 10. USER — PLAYER INSIGHTS

IMPORTANT:

Each generated player belongs to **one season only**.

Therefore do NOT create fake multi-season player histories.

When a player is selected, show:

```text
Player Name
Season
Team
Position

Matches
Minutes
Goals
Assists
Shots
Yellow Cards
Red Cards
```

Data should come from:

```text
Fact_Player_Performance
Dim_Player
Dim_Season
Dim_Team
Dim_Position
```

---

# 11. USER — MATCH EXPLORER

Allow users to search/filter matches by things such as:

```text
Season
Team
Opponent
Date
Result
```

Display understandable match information:

```text
Home Team
Away Team
Score
Date
Result
```

Simple match statistics may be displayed.

Do NOT show technical DWM/ML information.

---

# 12. USER — COMPARE

Allow:

```text
Team vs Team
```

and:

```text
Player vs Player
```

### Team comparison example

```text
              Team A    Team B

Matches          38        38
Wins             24        20
Goals            72        64
Points           78        69
```

### Player comparison

```text
              Player A    Player B

Matches          30          28
Goals            15          12
Assists           7           9
Shots             53          48
```

Use understandable statistics only.

---

# 13. USER MUST NOT SEE TECHNICAL DWM/ML FEATURES

The user interface must NOT expose:

❌ Regression
❌ Decision Tree
❌ Naive Bayes
❌ Classification metrics
❌ Confusion Matrix
❌ Precision
❌ Recall
❌ F1-score
❌ R²
❌ MAE
❌ RMSE
❌ K-Means
❌ Agglomerative Clustering
❌ Silhouette Score
❌ Dendrogram
❌ Centroids
❌ Apriori
❌ Support
❌ Confidence
❌ Lift
❌ OLAP
❌ Roll-up
❌ Drill-down
❌ Slice
❌ Dice
❌ Pivot
❌ Data Warehouse schema
❌ Fact tables
❌ Dimension tables
❌ Star schema
❌ Snowflake schema
❌ Feature importance
❌ Model parameters
❌ Training/test methodology
❌ Technical algorithm graphs

The user should not even need to know these modules exist.

---

# 14. ADMIN APPLICATION

## Product name

# EPL ANALYTICS & DWM

Admin is the technical/academic interface.

Admin should have access to the complete project.

---

# 15. ADMIN NAVIGATION

Admin navigation MUST be:

```text
ADMIN
│
├── Dashboard
├── EPL Explorer
├── Performance Analysis
├── Match Outcomes
├── Team Analytics
├── Player Analytics
├── Association Analysis
├── OLAP Analysis
└── Data Warehouse
```

The admin sidebar must be different from the user sidebar.

---

# 16. ADMIN — DASHBOARD

Show:

```text
Dataset Summary
Fact Table Counts
Dimension Counts
Model Status
Analytics KPIs
```

Provide links to technical modules.

---

# 17. ADMIN — EPL EXPLORER

Purpose:

Technical exploratory data analysis.

Include:

* filters
* distributions
* rankings
* trends
* season analysis
* team analysis
* player analysis
* charts
* patterns

This is the main technical exploration area.

---

# 18. ADMIN — PERFORMANCE ANALYSIS

This is the regression module.

Show:

```text
Regression Target
Features
Training/Test Methodology
Actual vs Predicted
R²
MAE
RMSE
```

Include technical details.

---

# 19. ADMIN — MATCH OUTCOMES

This is the classification module.

Target:

```text
Win
Draw
Loss
```

Models:

```text
Decision Tree
Gaussian Naive Bayes
```

---

## Prediction features

Use only pre-match features:

```text
Form_Pts5
Form_GF5
Form_GA5
Opp_Form_Pts5
Opp_Form_GF5
Opp_Form_GA5
Is_Home
```

Do NOT use current-match information:

```text
Goals
Shots
Possession
Corners
Fouls
Yellow
Red
Points
Result
```

This prevents data leakage.

---

# 20. ADMIN MATCH PREDICTION DISPLAY

Admin can see the complete technical prediction.

Example:

```text
DECISION TREE

Win     XX.X%
Draw    XX.X%
Loss    XX.X%

Prediction: WIN
```

and:

```text
GAUSSIAN NAIVE BAYES

Win     XX.X%
Draw    XX.X%
Loss    XX.X%

Prediction: WIN
```

Then:

```text
Both Models Agree
```

only if they actually agree.

Then:

```text
Actual Result
```

from the warehouse.

---

# 21. ADMIN MODEL EVALUATION

Show:

```text
Accuracy
Precision
Recall
F1-score
```

for each classification model.

Also show:

```text
Confusion Matrix
```

for both models.

Also show:

```text
Mutual Information
```

for attribute relevance.

Technical details may include:

* tree structure
* decision path
* tree depth
* split criteria
* Naive Bayes parameters
* training/test methodology

---

# 22. ADMIN — TEAM ANALYTICS

This is the clustering module.

Algorithms:

```text
K-Means
Agglomerative Clustering
```

Use team-season profiles.

The clustering should use the appropriate complete population, approximately:

```text
540 team-season profiles
```

A team filter should highlight/select a team.

It should NOT retrain the clustering model every time the user changes a display filter.

---

# 23. CLUSTER NUMBER

Do NOT assume:

```text
K = 4
```

The application should evaluate suitable K values.

If the silhouette analysis recommends:

```text
K = 2
```

then use K = 2.

The number of clusters must come from the analysis, not from a hardcoded assumption.

---

# 24. CLUSTER LABELS

Do NOT hardcode:

```text
Cluster 1 = High-performing
Cluster 2 = Strong
Cluster 3 = Mid-table
Cluster 4 = Lower-performing
```

Instead:

```text
Run clustering
      ↓
Calculate cluster profiles
      ↓
Calculate average performance
      ↓
Rank clusters
      ↓
Generate descriptive labels
```

For example:

```text
Highest average points/goals
→ High-performing

Lowest average points/goals
→ Lower-performing
```

If K changes, the labels should adapt.

---

# 25. ADMIN — PLAYER ANALYTICS

Technical player analysis.

Include:

* player statistics
* distributions
* positions
* seasons
* teams
* goals
* assists
* minutes
* shots
* cards
* comparisons
* advanced patterns

Use actual warehouse data.

---

# 26. ADMIN — ASSOCIATION ANALYSIS

This is the Apriori module.

Show:

```text
Transaction Count
Minimum Support
Minimum Confidence
Minimum Lift
```

Then:

```text
Frequent Itemsets
Association Rules
Support
Confidence
Lift
```

Use the appropriate transaction scope.

Clearly display the transaction count/scope.

---

# 27. ADMIN — OLAP ANALYSIS

Demonstrate:

```text
Roll-up
Drill-down
Slice
Dice
Pivot
```

Use warehouse dimensions.

Examples:

```text
Year → Season → Month
Team → Match
Position → Player
```

The admin must be able to demonstrate actual DWM OLAP operations.

---

# 28. ADMIN — DATA WAREHOUSE

Show:

```text
Star/Snowflake Schema
```

Dimensions:

```text
Dim_Date
Dim_Season
Dim_Team
Dim_Stadium
Dim_City
Dim_Referee
Dim_Player
Dim_Position
```

Facts:

```text
Fact_Match
Fact_Team_Match
Fact_Player_Performance
```

For each table show:

```text
Table Name
Grain
Row Count
Columns
Sample Data
Relationships
```

---

# 29. DATABASE-DRIVEN RULE

Eventually, all actual data displayed by the website must come from the database.

Never hardcode:

* team names
* player names
* goals
* assists
* points
* rankings
* match results
* statistics
* probabilities
* model results

Hardcoded content is allowed only for:

* page titles
* labels
* descriptions
* button text
* explanatory text

---

# 30. USER VS ADMIN — VERY CLEAR EXAMPLE

## USER

```text
ARSENAL vs CHELSEA

Arsenal favoured

Prediction:
Arsenal Win

Clear favourite
```

## ADMIN

```text
ARSENAL vs CHELSEA

DECISION TREE
Win: XX%
Draw: XX%
Loss: XX%

Prediction: WIN


NAIVE BAYES
Win: XX%
Draw: XX%
Loss: XX%

Prediction: WIN


Actual Result: WIN


MODEL PERFORMANCE

             DT       NB

Accuracy     XX%      XX%
Precision    XX%      XX%
Recall       XX%      XX%
F1           XX%      XX%
```

**Same underlying prediction engine. Completely different presentation.**

---

# 31. ROLE-BASED ROUTING

Implement proper role-based routing.

```text
LOGIN
  │
  ├── USER
  │     ↓
  │   /user/home
  │
  └── ADMIN
        ↓
      /admin/dashboard
```

User should only see user navigation.

Admin should see admin navigation.

A normal user should not be able to access admin pages simply by changing the URL.

Protect admin routes with the admin role.

---

# 32. UI DESIGN

This is an academic analytics platform.

Use:

* clean layout
* professional design
* readable typography
* restrained colors
* clear tables
* meaningful charts
* simple navigation

Avoid:

❌ excessive gradients
❌ generic AI dashboard style
❌ giant hero images
❌ stock football photos
❌ unnecessary illustrations
❌ excessive animations
❌ meaningless icons
❌ huge cards
❌ decorative charts
❌ fake statistics

Do not add visuals merely to fill empty space.

---

# 33. DATA / ML ARCHITECTURE

Separate:

```text
ENGINE LAYER
```

from:

```text
DISPLAY LAYER
```

### Engine layer

Responsible for:

* loading data
* preprocessing
* training
* evaluation
* clustering
* association mining
* caching

### Display layer

Responsible for:

* filters
* selecting records
* highlighting results
* displaying charts
* displaying tables

Changing a display filter must NOT automatically retrain a model.

---

# 34. MODEL CACHING

Cache trained models.

Cache keys should depend on:

```text
Model
Features
Target
Hyperparameters
Training configuration
```

Do NOT use:

```text
Selected team
Selected player
Selected season
```

as model cache keys.

Those are display selections.

---

# 35. SAMPLE SIZE

Whenever displaying filtered analysis, show sample size.

Example:

```text
Sample size: n = 186
```

If sample size is very small, provide an appropriate warning.

---

# 36. DATA LEAKAGE

Prediction models must never use information that would only be known after the match.

Do not use current match:

```text
Goals
Shots
Possession
Corners
Fouls
Cards
Points
Result
```

Use only information available before the match.

---

# 37. IMPORTANT CURRENT PRIORITY

### DO NOT FIX EVERYTHING AT ONCE.

The current priority is **architecture and functionality**.

Do this first:

```text
1. Inspect existing project
        ↓
2. Run existing application
        ↓
3. Identify current errors
        ↓
4. Fix application/database connection
        ↓
5. Fix role-based authentication
        ↓
6. Create separate User navigation
        ↓
7. Create separate Admin navigation
        ↓
8. Make User pages user-friendly only
        ↓
9. Preserve Admin technical functionality
        ↓
10. Verify all pages work
```

---

# 38. DO NOT MODIFY THESE YET

There are three known issues that will be handled **after the architecture is working**:

### Issue 1

Hardcoded/example values.

Example:

```text
Mohamed Salah — 18 goals
Arsenal — 88 points
```

These will later be replaced with actual database queries.

### Issue 2

User-facing prediction confidence.

We will later remove:

```text
62%
Confidence: HIGH
```

and replace it with wording such as:

```text
Narrow favourite
Favourite
Clear favourite
```

### Issue 3

Hardcoded cluster names.

We will later make cluster labels dynamically generated from actual cluster profiles.

---

# 39. DO NOT REPLACE THE SYNTHETIC DATA

The project is a college mini-project/assignment.

Synthetic data is intentionally being used.

**Do not replace it with real EPL data.**

The important thing is that:

```text
Synthetic Data
      ↓
Data Warehouse
      ↓
Queries
      ↓
Analytics
      ↓
ML/DWM Algorithms
      ↓
Correct Results
```

work correctly.

---

# 40. FIRST TASK FOR ANTIGRAVITY

Before changing major code, inspect the existing project.

Report:

```text
1. Frontend framework
2. Backend framework
3. Database
4. Existing tables
5. Existing authentication
6. Existing user pages
7. Existing admin pages
8. Existing ML modules
9. Existing DWM modules
10. Existing API routes
11. Existing errors
12. What can be reused
13. What needs to be changed
```

**Do not delete or rewrite working functionality before this inspection.**

---

# 41. FINAL SUCCESS CRITERIA

## USER

```text
Login
 ↓
EPL INSIGHTS
 ↓
Home
Match Prediction
Team Insights
Player Insights
Match Explorer
Compare
```

Simple, understandable, non-technical analytics.

---

## ADMIN

```text
Login
 ↓
EPL ANALYTICS & DWM
 ↓
Dashboard
EPL Explorer
Performance Analysis
Match Outcomes
Team Analytics
Player Analytics
Association Analysis
OLAP Analysis
Data Warehouse
```

Complete technical DWM/ML functionality.

---

# FINAL INSTRUCTION TO ANTIGRAVITY

> **The most important correction is this: User Login and Admin Login must NOT lead to the same feature set. They are two different interfaces over the same backend. User = simple EPL insights. Admin = complete technical DWM/ML analytics. Implement and verify this separation first. Do not currently modify the synthetic dataset, rebuild the ML system, or fix the three known data/prediction/clustering issues. First make the application architecture and role separation correct and working.**
