
# Results

## Peat Probability

### Random Forest

| Metric | Random CV | Spatial CV |
|--------|-----------|------------|
| AUC | 0.9722 | 0.9567 |
| Average Precision | 0.9193 | 0.8861 |
| F1 (threshold = 0.327) | 0.8445 | 0.8061 |
| n | 57,134 | 57,134 |

The decrease from random cv (AUC=0.972) to spatial cv (AUC=0.957) shows spatial autocorrelation in the training data where observations that are closer to one another are more similar to each other and that random folds are overestimating performance. 

Model experiments testing the benefit of including categorical features resulted in AUC values of 0.9740 (exp407, with categorical) versus 0.9722 (exp410, without categorical) which was determined to be a minimal decrease in performance relative to the visual improvement of the spatial inferences.

The NWI encoding experiments produced AUC 0.956 on the full dataset (exp403-405) and AUC 0.973 on the 0-20cm dropped dataset (exp406-408).

### Gradient Boosting (XGBoost and LightGBM)

| Model | Spatial CV AUC | Avg Precision | F1 | n |
|-------|---------------|---------------|-----|---|
| XGBoost (PROB_XGB_002) | 0.9615 | 0.8892 | 0.8105 | 57,134 |
| LightGBM (PROB_LGBM_002) | 0.9624 | 0.8917 | 0.8152 | 57,134 |

Random cv AUC for the initial run of the LightGBM model (PROB_LGBM_001) was 0.9965 which was an overestimate caused by inclusion of the point_id column in the training data. 

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

The differences between the F1-optimal and Youden's J thresholds between the models shows their differences in probability distributions. For example the GAM, SVM, and CNN require higher decision thresholds to get balanced precision and recall because their predicted probabilities are compressed.

**Add calibration curves and Brier scores**
### Probability Model Selection

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
| CNN 31×31            | Spatial | 0.9375 | 0.8905        | 0.8084 | 0.1107 |
| CNN 31×31 v2         | Spatial | 0.9621 | 0.9302        | 0.8527 | 0.0786 |
| CNN 31×31 focal loss | Spatial | 0.9620 | 0.9303        | 0.8527 | 0.0806 |

**Note that not all of the models have S1 included as a covariate**

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
Random CV R^2 for the gradient boosting models was much higher than the spatial CV values. For example XGBoost's random CV R^2 was 0.6209 compared to the spatial CV R^2 of 0.2898. This shows that depth is more spatially autocorrelated than peat probability.

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

Both of the gradient boosting models outperformed the RF. The largest R^2 gains were in Sapric % and the smallest on Hemic %. Note that the RF model (COMP_RF_001) used the iterative-residual method and a smaller 15 feature RFE set where the Gradient boosting models used all 143 features and independent per-target regression. So part of the gap could reflect the larger feature set or the unconstrained formulation.

## Below ground Carbon



## Above ground Carbon

