# Results

## Final Model Summary


| Layer | Model | Spatial CV | Random CV | Caveat |
|---|---|---|---|---|
| Probability | PROB_LGBM_V2 (threshold 0.362) | AUC 0.9642 | AUC 0.9766 | Brier 0.0483 spatial, 0.0383 random |
| Depth | DEPTH_LGBM_V2_TUNED (base), deep-tail blend (a075_s60) is the mapped product | R² 0.2925 (blend 0.2581) | R² 0.4273 (blend 0.4078) | Spatial CV values describe the model |
| Fibric | COMP_LGBM_DECLEAN (LightGBM, 35 features) | R² 0.1398 | R² 0.3726 | Retrained without NWI |
| Hemic | COMP_LGBM_DECLEAN (LightGBM, 35 features) | R² 0.0535 | R² 0.3389 | Almost no spatial skill; earlier tuned value 0.216 was not reproduced |
| Sapric | COMP_LGBM_DECLEAN (LightGBM, 35 features) | R² 0.1935 | R² 0.5947 | Retrained without NWI |
| Full-profile carbon | CARBON_FULL_DEPTHCURVE_2026 | R² 0.8623 | R² 0.8673 | Near-tautological, 20.12 kgC/m² intercept |
| 1 m carbon | BD-only RF | R² 0.395 | n/a | Validated, not shipped |
| Aboveground carbon (exploratory RF) | AGC_RF_001 | R² 0.204 | n/a | Not used, the product is the stand inventory / Jenkins overlay |

## Peat Probability

### Random Forest

| Metric | Random CV | Spatial CV |
|--------|-----------|------------|
| AUC | 0.9722 | 0.9567 |
| Average Precision | 0.9193 | 0.8861 |
| F1 (threshold = 0.327) | 0.8445 | 0.8061 |
| n | 57,134 | 57,134 |


### Gradient Boosting (XGBoost and LightGBM)

| Model | Spatial CV AUC | Avg Precision | F1 | n |
|-------|---------------|---------------|-----|---|
| XGBoost (PROB_XGB_002) | 0.9615 | 0.8892 | 0.8105 | 57,134 |
| LightGBM (PROB_LGBM_002) | 0.9624 | 0.8917 | 0.8152 | 57,134 |


### Generalized Additive Model (GAM)

| Metric | Spatial CV |
|--------|------------|
| AUC | 0.9544 |
| Average Precision | 0.8567 |
| F1 (threshold = 0.754) | 0.7957 |

### Support Vector Machine

| Metric | Spatial CV |
|--------|------------|
| AUC | 0.9525 |
| Average Precision | 0.8528 |
| F1 (threshold = 0.764) | 0.8010 |

### Logistic Regression (PROB_LR_001)

| Metric | Spatial CV |
|--------|------------|
| AUC | 0.9454 |
| Average Precision | 0.8139 |
| F1 (threshold = 0.754) | 0.7756 |

### Convolutional Neural Network (CNN)

| Model | Spatial CV AUC | Spatial CV F1 | Opt. Threshold |
|-------|----------------|----------------|-----------------|
| CNN 15x15 (PROB_CNN_001) | 0.8914 | 0.567 | 0.8291 |
| CNN 31x31 v2 (PROB_CNN_002) | 0.9375 | 0.7234 | 0.7638 |


### Probability Threshold Optimization

| Model | F1 Threshold | Youden's J | F1 at Threshold | Sensitivity | Precision |
|-------|-------------|------------|-----------------|-------------|-----------|
| RF | 0.327 | 0.186 | 0.845 | 0.850 | 0.839 |
| XGBoost | 0.598 | 0.342 | 0.816 | 0.828 | 0.804 |
| LightGBM | 0.699 | 0.327 | 0.816 | 0.787 | 0.847 |
| GAM | 0.754 | 0.578 | 0.796 | 0.812 | 0.780 |
| SVM RBF | 0.764 | 0.493 | 0.801 | 0.815 | 0.788 |
| Log. Reg. | 0.754 | 0.578 | 0.776 | 0.788 | 0.764 |
| CNN 15×15 | 0.829 | 0.774 | 0.731 | 0.752 | 0.712 |
| CNN 31×31 v2 | 0.764 | 0.694 | 0.808 | 0.786 | 0.832 |
| CNN 31×31 v3 | 0.764 | 0.694 | 0.853 | 0.853 | 0.853 |

### Probability Model Selection


| Metric | Spatial CV | Random CV |
|--------|-----------|-----------|
| AUC | 0.9642 | 0.9766 |
| Average precision | 0.9002 | 0.9325 |
| Brier score | 0.0483 | 0.0383 |
| F1 at 0.362 | 0.8163 | -- |
| Threshold (median of five metrics) | 0.362 | |
| n | 57,134 | 57,134 |


| Model                | CV      | AUC    | Avg Precision | F1     | Brier  |
| -------------------- | ------- | ------ | ------------- | ------ | ------ |
| RF                   | Random  | 0.9722 | 0.9193        | 0.8445 | 0.0428 |
| RF                   | Spatial | 0.9567 | 0.8861        | 0.8063 | 0.0520 |
| RF + S1 RFE          | Spatial | 0.9583 | 0.8881        | 0.8085 | 0.0516 |
| XGBoost              | Spatial | 0.9615 | 0.8892        | 0.8105 | 0.0556 |
| XGBoost + S1         | Spatial | 0.9628 | 0.8909        | 0.8130 | 0.0549 |
| XGBoost + S1 full    | Spatial | 0.9634 | 0.8917        | 0.8139 | 0.0544 |
| LightGBM             | Spatial | 0.9624 | 0.8917        | 0.8152 | 0.0542 |
| LightGBM + S1        | Spatial | 0.9631 | 0.8939        | 0.8130 | 0.0524 |
| LightGBM + S1 full   | Spatial | 0.9641 | 0.8975        | 0.8172 | 0.0514 |
| GAM                  | Spatial | 0.9544 | 0.8567        | 0.7958 | 0.0819 |
| SVM RBF              | Spatial | 0.9525 | 0.8528        | 0.8010 | 0.0753 |
| Logistic Regression  | Spatial | 0.9454 | 0.8139        | 0.7757 | 0.0918 |
| CNN 15×15            | Spatial | 0.8914 | 0.7690        | 0.7313 | 0.2243 |
| CNN 31×31 v2 (PROB_CNN_002) | Spatial | 0.9375 | 0.8905        | 0.8084 | 0.1107 |
| CNN 31×31 v3 (PROB_CNN_003) | Spatial | 0.9621 | 0.9302        | 0.8527 | 0.0786 |
| CNN 31×31 focal loss (PROB_CNN_004) | Spatial | 0.9620 | 0.9303        | 0.8527 | 0.0806 |

## Peat Depth

### Random Forest Depth models

#### Random Forest Two-stage (Random CV)

| Experiment | Approach                       | R^2   | RMSE    | MAE     | n     |
| ---------- | ------------------------------ | ----- | ------- | ------- | ----- |
| exp301     | Two-stage baseline (peat-only) | 0.41  | 93cm    | 69cm    | 6,829 |
| exp411     | Two-stage, no SSURGO           | 0.413 | 95.18cm | 70.98cm | --    |
| exp412     | Two-stage + SSURGO             | 0.466 | 90.81cm | 66.43cm | --    |
| exp413     | Log-transformed depth          | 0.425 | --      | --      | --    |
| exp415     | 0-20cm dropped                 | 0.450 | --      | --      | --    |

#### RFE-Selected Feature Models (Random CV)

| Experiment | Feature set | Mask | R^2 | RMSE | n |
|---|---|---|---|---|---|
| exp416 | 15 RFE features | depb > 0, exp410 mask | 0.484 | 89.22cm | 7,660 |
| exp417 | 15 RFE features | depb > 40, exp410 mask | 0.443 | 88.09cm | 7,073 |

### Other Depth Models

| Model          | CV      | R2     | MAE_cm | RMSE_cm |
| -------------- | ------- | ------ | ------ | ------- |
| XGBoost        | Random  | 0.6209 | 59.0   | 85.7    |
| LightGBM       | Random  | 0.6206 | 58.4   | 85.7    |
| CNN 31x31 v2   | Spatial | 0.5869 | 58.5   | 87.3    |
| CNN 31x31 (v1) | Spatial | 0.5666 | 59.6   | 89.4    |
| GAM            | Random  | 0.5288 | 68.1   | 95.5    |
| RF             | Random  | 0.4845 | 65.2   | 89.3    |
| RF S1 RFE      | Random  | 0.4819 | 65.5   | 89.3    |
| Ridge          | Spatial | 0.3349 | 77.2   | 102.7   |
| RF             | Spatial | 0.3246 | 77.4   | 103.5   |
| SVM            | Spatial | 0.3092 | 75.7   | 104.7   |
| LightGBM       | Spatial | 0.2991 | 78.8   | 105.4   |
| XGBoost        | Spatial | 0.2898 | 78.5   | 106.1   |
| XGBoost S1     | Spatial | 0.2858 | 78.7   | 104.8   |
| LightGBM S1    | Spatial | 0.2786 | 78.9   | 105.3   |
| GAM            | Spatial | 0.2644 | 80.3   | 108.0   |

### Final depth models (masked, PROB_LGBM_V2 ≥ 0.362, n = 8,223)

| Model | Spatial R² | Random R² | Spatial MAE | Random MAE |
|---|---|---|---|---|
| DEPTH_RF_TUNED | 0.2731 | -- | -- | -- |
| DEPTH_XGB_TUNED | 0.2885 | -- | -- | -- |
| DEPTH_LGBM_V2_TUNED | 0.2925 | 0.4273 | 74.6 cm | 66.1 cm |
| Deep-tail blend (a075_s60) | 0.2581 | 0.4078 | 78.4 cm | 68.3 cm |

### Field validation, 2025 season (123 sites)

| Bias | MAE | RMSE | R² | Pearson r |
|---|---|---|---|---|
| -59.7 cm | 107.6 cm | 150.5 cm | -0.291 | 0.015 |

## Organic decomposition

### Random Forest

#### Feature selection experiments

| Experiment | Feature set | Mean R^2 | Mean RMSE | n |
|---|---|---|---|---|
| exp421 | Full stack, 125 features | 0.4233 | 28.31 | 10,679 |
| exp422 | RFE, 15 features | 0.4341 | 28.03 | 10,679 |
Random cv
#### Composition Comparison 

| Model                | Approach                          | Mean R^2 (avg. of 3 targets) | Mean RMSE |     |
| -------------------- | --------------------------------- | ---------------------------- | --------- | --- |
| exp426 (COMP_RF_001) | Iterative residual (sums to 100%) | 0.3999                       | 21.07     |     |
| exp422               | Independent targets               | 0.4341                       | 28.03     |     |
Random cv
### Gradient Boosting

| Model | Fibric R^2 | Hemic R^2 | Sapric R^2 | Mean R^2 | Features | n |
|---|---|---|---|---|---|---|
| RF baseline (COMP_RF_001 / exp426) | -- | -- | -- | 0.400 | 15 | 10,679 |
| XGBoost (COMP_XGB_001) | 0.507 | 0.581 | 0.670 | 0.583 | 143 | 10,679 |
| LightGBM (COMP_LGBM_001) | 0.515 | 0.580 | 0.674 | 0.589 | 143 | 10,679 |
Random cv

### Spatial cross-validation results by algorithm

| Target | Random Forest | XGBoost | LightGBM |
|---|---|---|---|
| Fibric | 0.105 / 0.38 | 0.08 / 0.41 | 0.156 / 0.436 |
| Hemic | 0.137 / 0.31 | 0.060 / 0.43 | 0.216 / 0.446 |
| Sapric | 0.207 / 0.570 | 0.189 / 0.586 | 0.204 / 0.577 |


## Below ground Carbon

Full-profile carbon stock depth curve, fitted on 1,609 Criterion B pedons: C_stock_full_kgm2 = 0.5043 × max_peat_depth_cm + 20.12.

| Model | Spatial R² | Spatial MAE | Random R² |
|---|---|---|---|
| **Linear (final)** | **0.8623** | **16.14** | 0.8673 |
| RF (depth-only) | 0.8456 | 16.83 | 0.8506 |
