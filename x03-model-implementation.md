# Model Implementation

This section goes over the development and evaluation of models created to predict peat presence and related peat properties. The modeling workflow had four steps: (1) training data curation for each property being modeled.
(2) feature selection using recursive feature elimination. (3) model training and hyperparameter tuning. (4) model evaluation using both random and spatial cross validation. Six types of models 
were evaluated and coded using Python 3.8 using scikit learn. 

### Overview

#### Cross-Validation

Two cross-validation strategies were used in model development and are reported alongside each models results

#### Random cross-validation
Random cross-validation used stratified k-fold splitting (k=5) and randomly assigned observations to folds. This approach is standard in machine learning but it can create bias when training 
points that are spatially clustered. Because nearby points tend to have similar covariate values, a randomly held out point may be geographically adjacent to a training point which allows the model to interpolate instead
of generalize. This can inflate the metrics used to evaluate the effectiveness of models. 

#### Spatial block cross-validation
Spatial block cross-validation was used to replicate ture independant validation. The boundary of the spatial model (state of Minnesota) was split into a 50 xm x 50 km grid. All training points that shared a block were 
assigned to the same fold, with blocks allocated to folds in a round robin. When a block is held out for validation the model has never seen any training point with that geographic region forcing the model to generalize 
across the space instead of making an interpretation using local data. This method produces a lower but more reliable performance estimate and is the primary reported metric for models. The performance drop between the 
random and spatial cross-validation observed across the models reflects spatial autocorrelation in the training data. 

#### Shared Modeling Decisions

Several decision were consistant across all target properties and model types.

#### Coordinate reference system
All training points and covariates were projected to EPSG:5070 (Albers Equal Area Conic, NAD83) before modeling. Spatial block fold assignment used projected coordinates.

#### Missing Data 
Features with missing values at training point locations were imputed with the column median computed from training data only. This primarily impacted distance based features at edge locations and Sentinel-1 backscatter
features where coverage was incomplete (~45% of training points). 

#### Negative prediction clipping
Depth regression models (XGBoost, LightGBM, GAM, SVM) can produce negative predictions. This mainly impacted the peat depth model. All negative depth predictions were clipped to zero at inference time. 

***NOTE have not ran other approaches to get non-negative outputs. (ie Tweedie or Gamma loss function)

#### Model Catalog
All trained models, their feature sets, parameters, cross-validation metrics, and output file paths are documented in a model catalog (MODEL_CATALOG.csv). Model codes follow the convention
{TARGET}_{ALGORITHM}_{VERSION} (e.g., PROB_RF_001, DEPTH_CNN_002).

## Peat Probability

### Random Forest

#### Training Data
The peat probability models were trained on the peat binary presence/absence dataset compiled from the DNR peat inventory, NASIS, and the MBS. The initial compiled dataset contained ~102,000 points. One of the preprocessing
decisions made was to exclude observations that contained an organic layer thickness of 0-20cm. These shallow observations often represent 'duff layers,' or thin accumulations of organic matter such a leaf litter on the
forest floor and often do not indicate the presence of a true histosol. After applying this filter the final training dataset contained 57,134 points of which 32% were peat and 68% as non peat.

#### Covariate Development and Categorical Features

The initial covariate stack contained 77 features including terrain derivatives, satellite imagery, and spatial datasets. Several decision were made during processing that influenced the final feature set.

#### Exclusion of Peat Refernce Layers
Early models (exp201, exp301-303) included peat reference layers as predictive features; histosol rasters, gNATSGO organic component classifications, National Peatland Classification peatland
indicators, and NWI wetland layers. These experiments produces inflated AUC values (exp201 AUC=0.994) because the model was learning to reproduce the reference maps instead of independently predicting
peat from the landscape covariates. The prevent the model from using circular logic peat reference maps were excluded from the feature set. 

#### Categorical one-hot covariates and polygon artifacts
Early experiments (exp401-408) included categorical raster layers encoded as one-hot features: quaternary geology classification, Pennock landform class, and geopmorphons. These covariates produced
visible polygon shaped artifacts in the output inferences such as hard geometric edges corresponding to vector boundaries. Because these boundaries reflected mapped units rather than a continuous
peat forming process the model learned to abruptly change predictions at polygon edges.

Experiments exp409 and exp410 removed all categorical one-hot features. The AUC cost was minimal (exp407 with categoricals: 0.9740, exp410 without: 0.9722), but the visual quality of the inference
was improved substantially. Exp410 was selected as the best RF peat probability model on due to its visual coherence and marginal AUC difference. 

#### National Wetlands Inventory Encoding

Three NWI encoding strategies were evaluated across experiments exp404-408:
- 3-class encoding (0=upland, 1-palustrine, 2=lacustrine/riverine): exp403, 406
- Binary encoding (0=non-wetland, 1=any wetland class): exp404, 407
- NWI excluded entirely: exp405, 408

NWI contributed minimally when tested on the full dataset (exp403-405, AUC ~0.955-0.957). On the 0-20cm dropped dataset (exp406-408, AUC 0.973-0.974) the differences were negligible between strategies.
Binary encoding was kept in the final rf model because it preserved meaningful wetland/non-wetland discrimination without creating polygon artifacts. 

#### Recursive Feature elimination

After categorical features were dropped, excluding NWI binary,  recursive feature elimination was applied to reduce the amount of covariates used in the model. A random forest classifier with
200 trees was trained using 5-fold cross validation at each iteration. The feature with the lowest mean impurity-based importance across folds was dropped at each iteration. The process continued 
until AUC was reduced by more then 0.5 points from the maximum. This process reduced the final covariate stack from a total of 77 features to 41.

The set of 41 retained:
-All 12 sentinel-2 spring bands
-Selected summer and fall bands
-Tasseled Cap componentes across all seasons
-Terrain derivatives (DEM, slope, wetness index, flow accumulation, curvature, deviation from mean elevation) 
-PRISM climate normals
NWI binary wetland indicator
-Distance features (to water, streams, roads, waterbody edge)

Exp410 was chosen as the final random forest production model. It used 41 features with 500 trees, square root of features considered at each split, and a minimum of 1 sample per leaf. 

| Metric | Random CV | Spatial CV |
|--------|-----------|------------|
| AUC | 0.9722 | 0.9567 |
| Average Precision | 0.9193 | 0.8861 |
| F1 (threshold = 0.327) | 0.8445 | 0.8061 |
| n | 57,134 | 57,134 |

The decrease from random cv (AUC=0.972) to spatial cv (AUC=0.957) shows spatial autocorrelation in the training data where nearby observations are more similar and random folds
overestimate performance. 

## Gradient Boosting (XGBoost and LightGBM)

XGBoost and LightGBM were trained using spatial block cv. Class imbalance was addressed with 'scale_pos_weight' set on the ratio of negative to positive training examples.

#### Point_ID Correction
The first runs of the gradient boosting models (PROB_XGB_001, PROB_LGBM_001) included 'point_id' in the feature set. During spatial inference the point_id feature was assigned a constant fill
value (0 or column median) across all pixels, which placed predictions far outside the training distribution for the feature the model had as high performance. This resulted in overconfidence of 
the model and peat probability predictions were 0.98-1.00 in tiles where the RF model predicted in the 0.20 range. 

Corrected models (PROB_XGB_002, PROB_LGBM_002) were retrained using 76 features with point_id dropped. Cross-validated AUC was essentially the same confirming that point_id had no predictive signal.

| Model | Spatial CV AUC | Avg Precision | F1 | n |
|-------|---------------|---------------|-----|---|
| XGBoost (PROB_XGB_002) | 0.9615 | 0.8892 | 0.8105 | 57,134 |
| LightGBM (PROB_LGBM_002) | 0.9624 | 0.8917 | 0.8152 | 57,134 |

Random cv AUC for LightGBM (PROB_LGBM_001) was 0.9965 which was an overestimate caused by spatial autocorrelation and point_id leakage. 

## Generalized Additive Model (GAM)
A Logistic GAM was fit using the pygam library with thin-plate spline terms for each of the 76 features. Due to the high memory complexity needed  every
cross-validation fold was trained on a balanced subsample of 30,000 observations (15,000 peat, 15,000 non-peat).

| Metric | Spatial CV |
|--------|------------|
| AUC | 0.9544 |
| Average Precision | 0.8567 |
| F1 (threshold = 0.754) | 0.7957 |

## Support Vector Machine

A Support Vector Classifier with RBF kernel standardized with StandardScaler was also run. Because of memory complexity of kernel SVM, each fold used a subsample of the training points 
that included 15,000 training observations (7,500 peat, 7,500 non-peat) with predictions generated on the full held-out fold.
Hyperparameters: C = 1.0, gamma = 'scale', class_weight = 'balanced'.

| Metric | Spatial CV |
|--------|------------|
| AUC | 0.9525 |
| Average Precision | 0.8528 |
| F1 (threshold = 0.764) | 0.8010 |

## Logistic Regression (PROB_LR_001)

Logistic regression model with L2 regularization as a linear baseline. Fit on the 76 features and standardized with StandardScaler.
Solver: lbfgs, C = 1.0, class_weight = 'balanced'.

| Metric | Spatial CV |
|--------|------------|
| AUC | 0.9454 |
| Average Precision | 0.8139 |
| F1 (threshold = 0.754) | 0.7756 |

## Convolutional Neural Network (CNN))


### Probability Threshold Optimization

When creating a spatial output from the peat probability models, the output must be thresholded to determine what probability range is considered peat and what range is considered non-peat.
Three threshold metrics were evaluated by sweeping 200 equally-spaced values from 0 to 1 across spatial CV out-of-fold predictions:

- F1-optimal: maximizes the harmonic mean of precision and recall
- Youden's J: maximizes sensitivity + specificity − 1
- G-mean: geometric mean of sensitivity and specificity (resulted in identical results to Youden's J)

The first threshold used after initial inferences were made was 0.50 and did a poor job visually by underpredicting peat. Areas identifiable from aerial imagery were excluded at this threshold.
The F1-optimal threshold of 0.327 was the final selection. At this threshold the RF model correctly identifies 85% of true peat observations
(sensitivity = 0.85) with a precision of 0.84. The Youden's J threshold (0.186) was tested but not used as it predicted peat too often and had a false positive rate of ~25%.

The F1-optimal threshold of 0.327 was also used as the peat probability mask for the various peat property models that were run exclusively on areas were peat is likely to exist
(depth, organic decomposition)


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

The large difference between F1-optimal and Youden's J thresholds for GAM, SVM, and CNN models shows their compressed probability distributions. Each of these models require high thresholds
to get balanced precision/recall because their outputs are not calibrated to the true class prevalence.

### Model Selection

All probability models were evaluated on spatial block cross-validation AUC as the primary selection criterion, with F1 at optimal threshold and average precision as secondary metrics.
The performance of each model is shown below.

| Model | Spatial AUC | Random AUC | Avg Precision | F1 |
|-------|------------|------------|---------------|-----|
| RF (PROB_RF_001) | 0.9567 | 0.9722 | 0.8861 | 0.8061 |
| XGBoost (PROB_XGB_002) | 0.9615 | — | 0.8892 | 0.8105 |
| LightGBM (PROB_LGBM_002) | 0.9624 | — | 0.8917 | 0.8152 |
| GAM (PROB_GAM_001) | 0.9544 | — | 0.8567 | 0.7957 |
| SVM RBF (PROB_SVM_001) | 0.9525 | — | 0.8528 | 0.8010 |
| Log. Reg. (PROB_LR_001) | 0.9454 | — | 0.8139 | 0.7756 |
| CNN 15×15 (PROB_CNN_001) | 0.8914 | — | 0.7690 | 0.7313 |
| CNN 31×31 (PROB_CNN_003) | 0.9621 | — | 0.9302 | 0.8527 |





























































# Peat Depth

# Organic decomposition

# Below ground Carbon

# Above ground Carbon
