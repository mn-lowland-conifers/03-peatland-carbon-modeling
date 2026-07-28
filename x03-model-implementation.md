
# Model Implementation

This section goes over the development and evaluation of models created to predict peat presence and related peat properties. The modeling workflow had four steps: (1) training data curation for each property being modeled. (2) covariate feature selection (3) model training and hyperparameter tuning. (4) model evaluation. 

Six types of models were run and evaluated using Python 3.8 and scikit learn. 

### Overview

#### Cross-Validation

Two cross-validation strategies were used and are reported alongside each models results

#### Random cross-validation
Random cross-validation used stratified k-fold splitting (k=5) and randomly assigned observations to folds. This approach is a standard method but it can create bias when training points that are spatially clustered. Because nearby points tend to have similar covariate values, a randomly held out point may be spatially close to a training point which allows the model to interpolate instead of generalize. This can inflate the metrics used to evaluate the effectiveness of models. 

#### Spatial block cross-validation
Spatial block cross-validation was used to replicate independent validation. The boundary of the spatial model (state of Minnesota) was split into a 50 km x 50 km grid. All training points that shared a block were assigned to the same fold, with blocks allocated to folds in a round robin. When a block is held out for validation the model has never seen any training point within that geographic region forcing the model to generalize across the space instead of making an interpretation using local data. This method produces a lower but more reliable estimate. The performance drop from the random and spatial cross-validation in the models reflects spatial autocorrelation in the training data. 

#### Modeling Decisions

Several decision were consistent across all target properties and model types.

#### Coordinate reference system
All training points and covariates were projected to EPSG:5070 (Albers Equal Area Conic, NAD83) before modeling. Spatial block fold assignment used projected coordinates.

#### Missing Data 
Features with missing values at training point locations were imputed with the column median computed from training data only. This primarily impacted distance based features at edge locations.

#### Negative Prediction Clipping
Depth regression models (XGBoost, LightGBM, GAM, SVM) can produce negative predictions. When predicting a target variable such as peat depth, a negative value is not possible in the real world and should not be reported in the spatial outputs. All negative depth predictions were clipped to zero at inference time. 

***NOTE try Tweedie or Gamma loss function as alternatives

#### Model Catalog
All trained models, their feature sets, parameters, cross-validation metrics, and output file paths are documented in a model catalog (MODEL_CATALOG.csv). Model codes follow the convention
{TARGET}_{ALGORITHM}_{VERSION} (e.g., PROB_RF_001, DEPTH_CNN_002).

## Peat Probability

### Random Forest

#### Training Data
The peat probability models were trained on the peat binary presence/absence dataset compiled from the DNR peat inventory, NASIS, and the MBS. The initial compiled dataset contained ~102,000 points. One of the preprocessing decisions made was to exclude observations that contained an organic layer thickness of 0-20cm. These shallow observations often represent "duff layers" or thin accumulations of organic matter such a leaf litter on the forest floor and do not indicate the presence of a true histosol. After applying this filter the final training dataset contained 57,134 points of which 32% were classified as peat and 68% as non peat.

#### Covariate Development and Categorical Features

The initial covariate stack contained **77** (update with s1, include bands as individual layers??) features including terrain derivatives, satellite imagery, and spatial datasets. Several decision were made during processing that influenced the final feature set.

#### Exclusion of Peat Reference Layers
Early peat probability random forest models (exp201, exp301-303) included peat reference layers as predictive features: histosol rasters, gNATSGO organic component, and NWI wetland layers. These experiments produced inflated AUC values (exp201 AUC=0.994) because the model was learning to reproduce the reference maps instead of independently predicting peat from the landscape covariates. The prevent the model from using circular logic, peat reference maps were excluded from the final feature set. 

#### Categorical Covariates
Early experiments (exp401-408) included categorical raster layers encoded as one-hot features: quaternary geology classification, Pennock landform class, and geopmorphons. These covariates produced visible polygon shaped artifacts in the spatial inferences such as hard geometric edges corresponding to vector boundaries. Because these boundaries reflected mapped units rather than a continuous peat forming process the model learned to abruptly change predictions at polygon edges.

Experiments exp409 and exp410 removed all categorical one-hot features. The visual quality of the inference was improved substantially by removing them. Exp410 was selected as the best RF peat probability model on due to its visual consistency and the marginal performance difference.
#### National Wetlands Inventory Encoding

The NWI vector data was converted and classified to a raster by Cowardin code and separated into 3 groupings: 
0 = Non-wetland
1 = Wetland
2 = Lowland conifer (PFO4, PSS4, PFO2, PSS2, mixed codes containing "/4")

Three NWI strategies were evaluated across experiments exp404-408:
- 3-class encoding (0=non-wetland, 1=wetland, 2=lowland conifer): exp403, 406
- Binary encoding (0=non-wetland, 1=any wetland class): exp404, 407
- NWI excluded entirely: exp405, 408

NWI contributed minimally when tested on the full dataset (exp403-405). On the 0-20cm dropped dataset (exp406-408) the differences between strategies were negligible. Binary encoding was kept in the final random forest model because it preserved meaningful wetland/non-wetland discrimination without creating polygon artifacts. 

#### Recursive Feature elimination

After non-NWI categorical features were dropped, recursive feature elimination was applied to the remaining covariates.

A random forest classifier with 200 trees was trained using 5-fold cross validation. First, the model ran using all covariates as inputs. The feature with the lowest mean importance across folds was dropped. Then, another iteration of the model was run without the dropped covariate. The process continued until AUC was reduced by more then 0.5 points from the maximum. This process reduced the final covariate stack from a total of 77 features to 41.

**THIS LIST HAS CHANGED WITH ADDITION OF NEW COVARITES AND BETTER MODELS**
-All 12 sentinel-2 spring bands
-Selected summer and fall bands
-Tasseled Cap components across all seasons
-Terrain derivatives (DEM, slope, wetness index, flow accumulation, curvature, deviation from mean elevation) 
-PRISM climate normals
NWI binary wetland indicator
-Distance features (to water, streams, roads, waterbody edge)

Exp410 was chosen as the final random forest production model. It used 41 features with 500 trees, square root of features considered at each split, and a minimum of 1 sample per leaf. 

#### Probability Threshold Optimization

When creating a spatial output from the peat probability models, the output must be thresholded to determine what probability range is considered peat and what range is considered non-peat.
Three threshold metrics were evaluated by sweeping 200 equally-spaced values from 0 to 1 across spatial CV out-of-fold predictions:

- F1-optimal: the harmonic mean of precision and recall
- Youden's J: sensitivity + specificity − 1
- G-mean: geometric mean of sensitivity and specificity

The first threshold used after initial random forest inferences were made was 0.50 and did a poor job by underpredicting peat. Areas with identifiable peat from imagery were excluded at this threshold.

The F1-optimal threshold of 0.327 was the final selection. (for random forest model) At this threshold the RF model correctly identifies 85% of true peat observations (sensitivity = 0.85) with a precision of 0.84. The Youden's J threshold (0.186) was tested but not used as it predicted peat too often and had a false positive rate of around 25%.

The F1-optimal threshold of 0.327 was also used as the peat probability mask for the various peat property models that were run exclusively on areas were peat is likely to exist
(depth, organic decomposition)

**add threshold section below other models or keep it here under random forest??** 

### Gradient Boosting (XGBoost and LightGBM)

XGBoost and LightGBM were trained using spatial block cv. Class imbalance was addressed with 'scale_pos_weight' set to the ratio of negative to positive training examples.

#### Point_ID Correction
The first runs of the gradient boosting models (PROB_XGB_001, PROB_LGBM_001) included the point_id column in the feature set. During training, the model assigned high importance to this feature because it correlated with spatial patterns in the training data. When spatial inferences were made, point_id was assigned a constant fill value across all pixels which placed every inference pixel outside the training distribution for one of the model's most important features. This resulted in inflated predictions of 0.98–1.00 in tiles where the RF model had predicted values in the 0.02–0.20 range. 

Corrected models (PROB_XGB_002, PROB_LGBM_002) were retrained using 76 features with point_id dropped. The AUC was essentially the same which confirmed that point_id had no predictive signal and was an error in the inferences. 

### Generalized Additive Model (GAM)

A Logistic GAM was fit using the pygam library with thin-plate spline terms for each of the covariates. Due to high memory needed and issues with the jobs completing on MSI, each cross-validation fold was trained on a subsample of 30,000 observations (15,000 peat, 15,000 non-peat).

### Support Vector Machine

A Support Vector Classifier with RBF kernel standardized with StandardScaler was also run. Because of memory complexity of kernel SVM, each fold used a subsample of the training points 
that included 15,000 training observations (7,500 peat, 7,500 non-peat). Predictions were generated on the full held-out fold.

Hyperparameters: C = 1.0, gamma = 'scale', class_weight = 'balanced'.

### Logistic Regression

The logistic regression model used  L2 regularization as a linear baseline. Fit on all features and standardized with StandardScaler.

Solver: lbfgs, C = 1.0, class_weight = 'balanced'.

### Convolutional Neural Network (CNN))

For the CNN models a dual branch architecture was used. One branch takes a spatial raster patch centered on the training point and a second branch takes the standard tabular covariate stack. Each branch is processed separately and then concatenated before the final prediction layer. Training used spatial block CV and ran on GPU (A100) nodes.

Two patch sizes (15x15 and 31x31) were both tried with additional 31x31 iterations to attempt to improve performance. 

Although the models ran successfully and had comparable metrics to other algorithms, the time and computing issues related to creating spatial inferences stopped further experimentation. 

### Model Selection

All probability models were evaluated on spatial block cross-validation AUC as the primary selection criterion, with F1 at optimal threshold and average precision as secondary metrics.
The performance of each model is shown in the Results section.


## Peat Depth
### Random Forest
#### Training Data and Masking

Early depth models were trained on the full point set including points with a depth of zero which produced deceptively high R^2 values (~0.70). This was misleading as the high R^2 mainly showed the model separating zero from non-zero depth, and had bad accuracy at locations that actually have peat.

To correct this, a two-stage approach was adopted. The peat probability model (exp410, using the F1-optimal 0.327 threshold) is used as a mask, and depth regression is trained and predicted only on pixels the probability model classifies as peat. 

The first two-stage depth model (exp301) produced an R^2 = 0.41 (random CV)
#### Depth Model Experiments

- Adding SSURGO soil survey data as covariates (exp411, exp412)
- Dropping shallow (0-20cm) points (exp415) 
- Log-transforming the depth target (exp413) 
#### Recursive Feature Elimination
RFE was run on the feature set for depth and reduce the amount of features to 15. Performance improved as features were removed from R^2 = 0.4233 at 125 features to a best result of R^2 = 0.484 at 15 features.

### Other Algorithms
#### Gradient Boosting, GAM, SVM, and Linear Baselines
Following the same approach used for peat probability, XGBoost, LightGBM, GAM, a linear SVM, and Ridge regression were evaluated for peat depth. 

Random CV R^2 for the gradient boosting models was substantially higher than their spatial CV R^2 (0.62 vs 0.30), showing that peat depth is even more spatially correlated than peat probability.
#### Convolutional Neural Network
The same dual-branch CNN architecture for peat probability was also built for depth.

## Organic decomposition

#### Target and Training Data
Organic decomposition modeling had a three part approach: determining as a percent the amount of Fibric, Hemic, and Sapric material in the top meter of peat. Training data came from organic_composition_features_extracted.csv which had 10,679 points and was restricted to the same peat probability mask used for depth (exp410 probability with threshold of 0.327). Training used coverage weighting and no categorical layers or peat reference layers were included.

#### Modeling Approaches
Two strategies were used for handling the three part composition target:

1. **Independent target** -- Fibric %, Hemic %, and Sapric % are each modeled as separate targets, with no constraint that they sum to 100%. This is the approach used in exp421 and exp422.

2. **Iterative residual regression** -- Fibric % is predicted first, then Hemic % is predicted as a fraction of the remainder (100% - Fibric), and Sapric % is assigned whatever is left. This means that the total percent at each predicted pixel of Fibric + Hemic + Sapric will sum to 100%. 

XGBoost and LightGBM models were also trained as three independent regressors (one per decomposition state). Both used the full feature set as an input with and 500 trees, versus the 15-feature RFE set used for the RF experiments above.

## Below ground Carbon


## Above ground Carbon


























































