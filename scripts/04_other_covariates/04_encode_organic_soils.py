"""
One-hot encode the gNATSGO organic soils classification column


INPUT
  00_data/processed/peat_depths_with_covariates_v2_fixed.csv
  (column: MN_organic_soils_classified_FIXED, integer class 0-8)

OUTPUT
  00_data/processed/peat_depths_processed_v2.csv
  (MN_organic_soils_classified_FIXED replaced with one binary column per class)
"""

import pandas as pd

df = pd.read_csv("/folder/00_data/processed/peat_depths_with_covariates_v2_fixed.csv", low_memory=False)

# One-hot encode the categorical organic-soils class into binary columns
# (e.g. MN_organic_soils_classified_FIXED_0, ..._1, ... one per class
# present in the data), then drop the original integer column.
dummies = pd.get_dummies(df['MN_organic_soils_classified_FIXED'], prefix='MN_organic_soils_classified_FIXED', dtype=int)
df = pd.concat([df, dummies], axis=1)
df = df.drop(columns=['MN_organic_soils_classified_FIXED'])

# Save
df.to_csv("/folder/00_data/processed/peat_depths_processed_v2.csv", index=False)
print(f"Done Shape: {df.shape}")
