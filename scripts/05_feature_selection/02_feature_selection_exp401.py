# PURPOSE

# try to find 06_probability_model/recursive_feature_elimination.py
# would be the more up to date version of the RFE

"""
Feature Selection Pipeline for Binary Peat Presence Model (exp401)
Steps:
  1. Load binary_peat_features_extracted.csv (with tasseled cap bands added)
  2. Separate continuous vs one-hot encoded covariates
  3. Correlation filter on continuous covariates only (threshold=0.85)
  4. RFECV on (reduced continuous + all one-hot) combined
  5. Save feature lists and diagnostics at each step
"""

import os, json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import RFECV
from sklearn.model_selection import StratifiedKFold

# ── CONFIG ──────────────────────────────────────────────────────
BASE      = '/folder/'
INPUT_CSV = os.path.join(BASE, '00_data/processed/binary_peat_features_extracted.csv')
OUT_DIR   = os.path.join(BASE, '05_results/feature_selection_exp401')
os.makedirs(OUT_DIR, exist_ok=True)

CORR_THRESHOLD = 0.85
TARGET_COL     = 'peat_binary'
RANDOM_STATE   = 42

# ── COLUMN DEFINITIONS ──────────────────────────────────────────
METADATA_COLS = ['lat', 'long', TARGET_COL]

PEAT_MAP_PREFIXES = [
    'mn_nwi_cowardin_', 'histosols_10m_',
    'MN_organic_soils_classified_', 'MN_ANY_organic_component_',
]
PEAT_MAP_EXACT = ['gNATSGO_MN_26915', 'npc_peatland_indicator_10m']

# These are kept as a group and excluded from correlation filter
ONEHOT_PREFIXES = [
    'quaternary_geology_',
    'pennockLandformClass_',
    'geomorphons_',
]

# Tasseled cap — validate they're present
TC_BANDS   = ['TCB', 'TCG', 'TCW']
TC_SEASONS = ['s2_spring', 's2_summer', 's2_fall']
EXPECTED_TC_COLS = [f'{s}_{b}' for s in TC_SEASONS for b in TC_BANDS]

# ── LOAD ─────────────────────────────────────────────────────────
print("Loading data...")
df = pd.read_csv(INPUT_CSV)
print(f"  Shape: {df.shape}")
print(f"  Target balance:\n{df[TARGET_COL].value_counts()}\n")

# ── SEPARATE COLUMN TYPES ─────────────────────────────────────────
def is_peat_map(c):
    return c in PEAT_MAP_EXACT or any(c.startswith(p) for p in PEAT_MAP_PREFIXES)

def is_onehot(c):
    return any(c.startswith(p) for p in ONEHOT_PREFIXES)

def is_excluded(c):
    return c in METADATA_COLS or is_peat_map(c)

peat_map_cols   = [c for c in df.columns if is_peat_map(c)]
onehot_cols     = [c for c in df.columns if is_onehot(c) and not is_excluded(c)]
continuous_cols = [c for c in df.columns if not is_excluded(c) and not is_onehot(c)]

missing_tc = [c for c in EXPECTED_TC_COLS if c not in df.columns]
if missing_tc:
    print(f"WARNING: Missing tasseled cap cols: {missing_tc}\n")
else:
    print(f"All {len(EXPECTED_TC_COLS)} tasseled cap columns found.\n")

print(f"Continuous : {len(continuous_cols)}")
print(f"One-hot    : {len(onehot_cols)}")
print(f"Peat maps  : {len(peat_map_cols)} (excluded)\n")

with open(os.path.join(OUT_DIR, 'column_categorization.json'), 'w') as f:
    json.dump({'continuous': continuous_cols, 'onehot': onehot_cols,
               'peat_map_excluded': peat_map_cols}, f, indent=2)

# ── STEP 1: CORRELATION MATRIX (continuous only) ──────────────────
print("STEP 1: Correlation matrix...")

X_cont = df[continuous_cols].copy()

# Drop zero-variance
zero_var = X_cont.columns[X_cont.std() == 0].tolist()
if zero_var:
    print(f"  Dropping zero-variance: {zero_var}")
    X_cont = X_cont.drop(columns=zero_var)
    continuous_cols = X_cont.columns.tolist()

X_filled = X_cont.fillna(X_cont.median())
corr = X_filled.corr()
corr.to_csv(os.path.join(OUT_DIR, 'correlation_matrix_continuous.csv'))

# Heatmap
n = len(continuous_cols)
fsz = max(40, n * 0.28)
fig, ax = plt.subplots(figsize=(fsz, fsz))
sns.heatmap(corr, ax=ax, cmap='coolwarm', vmin=-1, vmax=1,
            xticklabels=True, yticklabels=True, linewidths=0, square=True)
ax.set_title(f'Continuous Covariate Correlation Matrix (n={n})', fontsize=16)
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, 'correlation_matrix_heatmap.png'), dpi=80, bbox_inches='tight')
plt.close()

# Clustermap (better for reading which vars cluster together)
cg = sns.clustermap(corr, cmap='coolwarm', vmin=-1, vmax=1,
                    figsize=(fsz, fsz), xticklabels=True, yticklabels=True, linewidths=0)
cg.savefig(os.path.join(OUT_DIR, 'correlation_clustermap.png'), dpi=80, bbox_inches='tight')
plt.close()
print("  Saved heatmap and clustermap.\n")

# ── STEP 2: DROP HIGH CORRELATION FEATURES ────────────────────────
print(f"STEP 2: Dropping continuous features with |r| > {CORR_THRESHOLD}...")

upper = corr.abs().where(
    pd.DataFrame(np.triu(np.ones(corr.shape), k=1).astype(bool),
                 index=corr.index, columns=corr.columns)
)

pairs = []
for col in upper.columns:
    for partner in upper.index[upper[col] > CORR_THRESHOLD]:
        pairs.append({'dropped': col, 'correlated_with': partner,
                      'correlation': round(corr.loc[partner, col], 4)})

pairs_df = pd.DataFrame(pairs).sort_values('correlation', ascending=False)
pairs_df.to_csv(os.path.join(OUT_DIR, 'high_correlation_pairs.csv'), index=False)

corr_drop = list(set(pairs_df['dropped'].tolist())) if len(pairs_df) else []
continuous_reduced = [c for c in continuous_cols if c not in corr_drop]

print(f"  Before: {len(continuous_cols)}  |  Dropped: {len(corr_drop)}  |  After: {len(continuous_reduced)}")
print(f"  Dropped: {corr_drop}\n")

with open(os.path.join(OUT_DIR, 'features_after_corr_filter.json'), 'w') as f:
    json.dump({'continuous_reduced': continuous_reduced,
               'dropped_by_correlation': corr_drop,
               'onehot_kept': onehot_cols}, f, indent=2)

# ── STEP 3: RFECV ─────────────────────────────────────────────────
# One-hot cols skipped correlation filter but included here
rfe_features = continuous_reduced + onehot_cols
print(f"STEP 3: RFECV on {len(rfe_features)} features")
print(f"  ({len(continuous_reduced)} continuous + {len(onehot_cols)} one-hot)\n")

X = df[rfe_features].copy()
y = df[TARGET_COL].copy()

for col in continuous_reduced:
    if X[col].isna().any():
        X[col] = X[col].fillna(X[col].median())

# Stratified subsample if large dataset
if len(X) > 150_000:
    idx = df.groupby(TARGET_COL, group_keys=False).apply(
        lambda g: g.sample(min(len(g), 75_000), random_state=RANDOM_STATE)
    ).index
    X_rfe, y_rfe = X.loc[idx], y.loc[idx]
    print(f"  Subsampled to {len(X_rfe)} rows")
else:
    X_rfe, y_rfe = X, y

print(f"  Shape: {X_rfe.shape}  |  Balance: {y_rfe.value_counts().to_dict()}\n")

rf = RandomForestClassifier(
    n_estimators=100,
    max_depth=15,        # shallower = faster for feature selection stage
    n_jobs=-1,
    class_weight='balanced',
    random_state=RANDOM_STATE
)

rfecv = RFECV(
    estimator=rf,
    step=5,              # drop 5 per round; use step=1 for finer resolution
    cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE),
    scoring='roc_auc',
    n_jobs=-1,
    verbose=2,
    min_features_to_select=10
)

print("Fitting RFECV...")
rfecv.fit(X_rfe, y_rfe)

final_features = [f for f, s in zip(rfe_features, rfecv.support_) if s]
best_auc = float(max(rfecv.cv_results_['mean_test_score']))

pd.DataFrame({
    'feature': rfe_features,
    'selected': rfecv.support_,
    'ranking': rfecv.ranking_
}).sort_values('ranking').to_csv(os.path.join(OUT_DIR, 'rfecv_feature_ranking.csv'), index=False)

with open(os.path.join(OUT_DIR, 'final_selected_features.json'), 'w') as f:
    json.dump({'n_features': rfecv.n_features_,
               'best_roc_auc': round(best_auc, 4),
               'features': final_features}, f, indent=2)

# Score curve
mean_s = rfecv.cv_results_['mean_test_score']
std_s  = rfecv.cv_results_['std_test_score']
x_range = range(rfecv.min_features_to_select,
                rfecv.min_features_to_select + len(mean_s) * 5, 5)
fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(list(x_range), mean_s, 'b-o', markersize=4)
ax.fill_between(list(x_range), mean_s - std_s, mean_s + std_s, alpha=0.2, color='blue')
ax.axvline(rfecv.n_features_, color='red', linestyle='--',
           label=f'Optimal: {rfecv.n_features_} features')
ax.set_xlabel('Number of Features')
ax.set_ylabel('CV ROC-AUC')
ax.set_title('RFECV Score Curve (exp401)')
ax.legend(); ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, 'rfecv_score_curve.png'), dpi=150, bbox_inches='tight')
plt.close()

# ── SUMMARY ──────────────────────────────────────────────────────
print(f"\n{'='*55}")
print(f"DONE")
print(f"  Input features           : {len(continuous_cols) + len(onehot_cols)}")
print(f"  After correlation filter : {len(rfe_features)}")
print(f"  After RFECV              : {len(final_features)}")
print(f"  Best CV ROC-AUC          : {best_auc:.4f}")
print(f"\nOutputs → {OUT_DIR}")
print("  column_categorization.json")
print("  correlation_matrix_continuous.csv")
print("  correlation_matrix_heatmap.png")
print("  correlation_clustermap.png   ← best for reading variable clusters")
print("  high_correlation_pairs.csv   ← every pair above threshold")
print("  features_after_corr_filter.json")
print("  rfecv_feature_ranking.csv")
print("  rfecv_score_curve.png")
print("  final_selected_features.json  ← USE THIS FOR TRAINING")
