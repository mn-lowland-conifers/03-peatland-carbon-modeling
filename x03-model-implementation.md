# Model Implementation

This section covers the development and evaluation of models created to predict peat presence and other characteristics. The modeling workflow has four steps: (1) curation of the training data for each property that is being modeled. (2) covariate feature selection. (3) model training and hyperparameter tuning. (4) model evaluation. 

In total, four statewide raster maps were produced including the probability of peat presence, peat depth, the composition of the upper meter of peat as fibric, hemic, and sapric percent, and carbon stock. The final probability, depth, and composition models use a LightGBM algorithm. The carbon stock map was then calculated from the depth map using a linear depth–carbon stock curve. Earlier model versions and other algorithms that were tested are documented alongside the selected production models.

## Overview

### Cross-Validation

Cross-validation is a method used in machine learning to evaluate the performance of a model. Two cross-validation strategies were used in development and are reported with each model’s results.

#### Random cross-validation
Random cross-validation used stratified k-fold splitting (k=5) and randomly assigned observations to folds. This approach is a standard method in machine learning but it can create bias when training points that are clustered. Because nearby points often have similar covariate values, a randomly held out point may be geographically close to a training point which allows the model to interpolate on nearby data. This can inflate the metrics used to evaluate the effectiveness of models. 

#### Spatial block cross-validation
Spatial block cross-validation was used to replicate independent validation. The boundary of the project area (Minnesota) was split into a 50 km x 50 km grid. All training points that shared a block were assigned to the same fold and then blocks were allocated to folds in a round robin fashion. When a block is held out for validation, the model has never seen any training point within that geographic area forcing generalization across space. This method produces a lower but more reliable estimate. The performance drop from the random to spatial cross-validation in the results shows spatial autocorrelation that is occurring in the training data. 

### Shared Modeling Decisions

Some decisions made in the modeling workflow were consistent across all target properties and model types:

1) CRS - All training points and covariates are projected to Albers Equal Area Conic NAD83 (EPSG:5070)

2) Missing Data - Covariate features with missing data at training point locations were imputed with the column median from training data only. This affected distance features at edge locations and Sentinel-1 features where coverage was incomplete.

3) Negative prediction clipping - The depth regression models tested (XGBoost, LightGBM, GAM, SVM) can sometimes produce negative predictions which is unrealistic because peat depth can not be negative. All negative predictions were clipped to zero.

4) Output encoding - Raster map inferences were written as Cloud-Optimized GeoTIFFs (COGs) at a 10m resolution. Percentage outputs rasters are stored as `uint8` (value × 0.5 = percent) and the depth raster as `uint16` (1cm per unit)

## Peat Probability

The peat probability modeling workflow has two distinct versions. The first version (V1) was a random forest. The second (V2) used a gradient boosting algorithm (LightGBM) and produced the final model used to create the map displayed in the MNLCC viewer. The random forest work is kept within this documentation because it informs training data decisions and because the comparison algorithms were tested alongside it. 

### Training Data

The peat probability models were trained on the peat binary presence/absence dataset compiled from the MN DNR Peat Inventory, NASIS, and the MBS. The initial compiled dataset contained ~102,000 points. After shallow, non-histosol points with organic material depths of 1-20 cm were excluded, the final training dataset contained 57,134 points with 18.2% coded as peat and 81.8% as non peat.

### Covariate Development and Categorical Features

The initial V1 covariate stack was made up of 172 candidate features. To limit the redundancy of predictors in the random forest model, a Pearson correlation filter was applied using a threshold of |r| ≥ 0.90. Each pair of correlated features meeting that threshold had the lower variance feature dropped from the stack. This filtering reduced the set to 143 covariates.

#### Exclusion of Peat Reference Layers

Early model runs (exp201, exp301-303) included peat reference layers as predictive features  such as the Potentially Wet Histosol layer and gNATSGO organic components. These experiments resulted in inflated AUC values (exp201 AUC=0.994) because the model was learning to reproduce the reference maps instead of independently predicting
peat presence from the covariates. To prevent the model from using circular logic the peat reference maps were ultimately excluded from the feature set.

#### Categorical covariates and polygon artifacts

Other early experiments (exp401-408) included categorical raster layers encoded as one-hot features: quaternary geology classification, Pennock landform class, and geomorphons. The inclusion of these covariates in the model resulted in visible polygon shaped artifacts in the output inferences such as hard geometric edges that corresponded to vector boundaries. Because the boundaries were showing mapped units rather than a continuous peat forming process, the model learned to abruptly change predictions at polygon edges.

In exp409 and exp410, all categorical one-hot features were removed. This cost minimal AUC (0.974 with categoricals, 0.9722 without) and substantially improved the visual quality of the inference map. Exp410 was selected as the production RF peat probability model because of its metric scores as well as visual coherence.

#### National Wetlands Inventory Encoding

Three NWI encoding strategies were evaluated across RF model experiments 
- 3-class encoding (0=non-wetland, 1=wetland, 2=lowland conifer) 403, 406
- Binary encoding (0=non-wetland, 1=any wetland class) 404, 407
- NWI excluded entirely 405, 408

NWI contributed minimally to the overall model AUC on experiments using the original full point dataset. On the revised 1-20 cm dropped point dataset the AUC differences were negligible between NWI encoding strategies (AUC 0.973 versus 0.974). NWI Binary encoding was selected to be kept in the final RF model because it preserved visually meaningful wetland versus non-wetland discrimination without creating artifacts.

### Random Forest (V1)

#### Recursive Feature elimination

After the Pearson coefficient was applied and categorical features were dropped (excluding NWI binary) recursive feature elimination (RFE) was applied to reduce the remaining covariates used in the model. A random forest classifier with 200 trees was trained using 5-fold cross validation. Iterations of the model were run and the feature with the lowest mean impurity-based importance across folds was dropped each time. This process was continued until AUC was reduced by more than 0.5 points from the maximum, resulting in a final stack of 41 features to be used in the RF model.

The set of the 41 final features includes:

- All 12 sentinel-2 spring bands
- Selected summer and fall bands
- Tasseled Cap components for all seasons
- Terrain derivatives (DEM, slope, wetness index, flow accumulation, curvature, deviation from mean elevation)
- PRISM climate normals
- NWI binary wetland indicator
- Distance features (to water, streams, roads, waterbody edge)

Exp410 was chosen as the final random forest production model. It used the 41 features with 500 trees and a minimum of 1 sample per leaf.

| Metric | Random CV | Spatial CV |
|--------|-----------|------------|
| AUC | 0.9722 | 0.9567 |
| Average Precision | 0.9193 | 0.8861 |
| F1 (threshold = 0.327) | 0.8445 | 0.8061 |
| n | 57,134 | 57,134 |

The decrease from random cv (AUC=0.972) to spatial cv (AUC=0.957) shows spatial autocorrelation in the training data where nearby observations are more similar and random folds are overestimating performance.


### Gradient Boosting (V2)

Version 2 of the peat probability modeling process used gradient boosting algorithms. Gradient boosting builds a model as a sequence of decision trees where each new tree is trained to correct the errors by the trees before it. Gradient boosting can fit complicated patterns between covariates more closely than a random forest, but is prone to overfitting if settings and tuning are not controlled.

Two boosting implementations were tested in this project, XGBoost and LightGBM. Both were trained on the covariates that remained after the Pearson correlation filter (|r| ≥ 0.90) was applied. Recursive feature elimination was not used for the boosting models. It is only needed for the random forest because the boosted models select correlated covariates as trees are built.

The peat present points are the minority class in the training data (18.2% of the 57,134 points). Because of this, weighted and unweighted versions of both boosting algorithms were compared. In the weighted version of the model runs, the peat class has more influence in the training. The ‘scale_pos_weight’ setting was set at 4.495 which is the ratio of non-peat to peat points so that they have an equal total weight. This helps the model identify the less common class, in this case peat presence, but can overestimate the likelihood of that class. In the unweighted versions each point counts equally and the model learns the natural frequency. The imbalance is then handled afterward when a probability threshold is selected.
Weighting had little effect on the overall model performance. Spatial AUC scores were almost the same between weighted and unweighted models for both XGBoost (0.9730 vs. 0.9738) and LightGBM (0.9744 vs. 0.9739). However, the unweighted models had better Brier scores and higher F1 scores for both algorithms. Because the final maps show predicted probabilities and the classification threshold is applied afterward, unweighted models were used for all final probability maps. 





# Everything below is still being edited


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


























































