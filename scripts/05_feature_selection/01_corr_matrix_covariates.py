# PURPOSE
#   Runs the pairwise correlation matrix across the full covariate stack to flag
#   highly-correlated covariate pairs 

import os, json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

# ── CONFIG ───────────────────────────────────────────────────────
BASE      = '/folder'
INPUT_CSV = os.path.join(BASE, '00_data/processed/binary_peat_features_extracted.csv')
OUT_DIR   = os.path.join(BASE, '05_results/correlation_analysis')
os.makedirs(OUT_DIR, exist_ok=True)

CORR_THRESHOLD = 0.85
TARGET_COL     = 'peat_binary'

EXCLUDE_EXACT = ['lat', 'long', TARGET_COL,
                 'gNATSGO_MN_26915', 'npc_peatland_indicator_10m']

EXCLUDE_PREFIXES = [
    'mn_nwi_cowardin_', 'histosols_10m_',
    'MN_organic_soils_classified_', 'MN_ANY_organic_component_',
    'quaternary_geology_', 'pennockLandformClass_', 'geomorphons_',
]

# ── LOAD ─────────────────────────────────────────────────────────
print("Loading CSV...")
df = pd.read_csv(INPUT_CSV, low_memory=False)
print(f"  Shape: {df.shape}\n")

# ── SELECT CONTINUOUS COVARIATES ──────────────────────────────────
def is_excluded(c):
    return c in EXCLUDE_EXACT or any(c.startswith(p) for p in EXCLUDE_PREFIXES)

cont_cols = [c for c in df.columns if not is_excluded(c)]

# Force numeric, drop fully-NaN cols
X = df[cont_cols].apply(pd.to_numeric, errors='coerce')
all_nan = [c for c in X.columns if X[c].isna().all()]
if all_nan:
    print(f"  Dropping entirely NaN cols: {all_nan}")
    X = X.drop(columns=all_nan)

X = X.fillna(X.median())
cont_cols = X.columns.tolist()
print(f"  Continuous covariates: {len(cont_cols)}")
print(f"  Columns: {cont_cols}\n")

# ── CORRELATION MATRIX ────────────────────────────────────────────
print("Computing correlation matrix...")
corr = X.corr()
corr.to_csv(os.path.join(OUT_DIR, 'correlation_matrix.csv'))
print("Saved: correlation_matrix.csv")

# ── HEATMAP ───────────────────────────────────────────────────────
n = len(cont_cols)
fsz = max(40, n * 0.28)
fig, ax = plt.subplots(figsize=(fsz, fsz))
sns.heatmap(corr, ax=ax, cmap='coolwarm', vmin=-1, vmax=1,
            xticklabels=True, yticklabels=True, linewidths=0, square=True)
ax.set_title(f'Continuous Covariate Pearson Correlation (n={n})', fontsize=16)
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, 'correlation_heatmap.png'), dpi=80, bbox_inches='tight')
plt.close()
print("Saved: correlation_heatmap.png")

# ── HIGH CORRELATION PAIRS ────────────────────────────────────────
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
print(f"\nPairs above {CORR_THRESHOLD}: {len(pairs_df)}")
print(pairs_df.to_string(index=False))

# ── REDUCED FEATURE LIST ──────────────────────────────────────────
drop_cols = list(set(pairs_df['dropped'].tolist())) if len(pairs_df) else []
reduced   = [c for c in cont_cols if c not in drop_cols]

print(f"\nBefore: {len(cont_cols)}  Dropped: {len(drop_cols)}  After: {len(reduced)}")
print(f"Dropped: {drop_cols}")

with open(os.path.join(OUT_DIR, 'reduced_covariate_list.json'), 'w') as f:
    json.dump({
        'n_before': len(cont_cols),
        'n_after': len(reduced),
        'dropped': drop_cols,
        'kept_continuous': reduced,
        'note': 'Add tasseled cap cols and one-hot cols before training'
    }, f, indent=2)

print(f"\nSaved: reduced_covariate_list.json")
print(f"Done. Outputs in {OUT_DIR}")
