# 4. Model Implementation

This section covers the development and evaluation of models created to predict peat presence and other characteristics. The modeling workflow has four steps: (1) curation of the training data for each property that is being modeled. (2) covariate feature selection. (3) model training and hyperparameter tuning. (4) model evaluation. 

In total, four statewide raster maps were produced including the probability of peat presence, peat depth, the composition of the upper meter of peat as fibric, hemic, and sapric percent, and carbon stock. The final probability, depth, and composition models use a LightGBM algorithm. The carbon stock map was then calculated from the depth map using a linear depth–carbon stock curve. Earlier model versions and other algorithms that were tested are documented alongside the selected production models.

## 4.1 Overview

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

## 4.2 Peat Probability

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

### Generalized Additive Model (GAM)

A generalized additive model (GAM) fits a curve for each covariate and then adds those curves together. For the target of peat presence, a logistic GAM was used. A GAM can identify patterns occurring in a single covariate such as peat presence becoming more likely below a certain slope. However, unlike a random forest or boosted models, a standard GAM does not identify interactions between covariates.


A logistic GAM was built using the pygam library with thin-plate spline terms, which allow the model to fit smooth curves to individual covariates. A GAM with this many smooth terms requires a lot of memory, so each cross-validation fold was trained on a balanced subsample of 30,000 observations (15,000 peat, 15,000 non-peat).

| Metric | Spatial CV |
|--------|------------|
| AUC | 0.9544 |
| Average Precision | 0.8567 |
| F1 (threshold = 0.754) | 0.7957 |

### Support Vector Machine

A support vector machine (SVM) identifies the boundary that separates peat and non-peat observations that have the widest margin. A radial basis function (RBF) kernel was used which allows the boundary to be a curve rather than a straight line. Because SVM uses distances between observations, StandardScaler was used to standardize covariates so that no variable would have an advantage on the model. A large amount of memory is required to run these models which increases with the number of training points, so each fold used a subsample that included 15,000 observations (7,500 peat, 7,500 non-peat). Predictions were then generated on the full held-out fold. Hyperparameters were C = 1.0, gamma = 'scale' and class_weight = 'balanced'.

| Metric | Spatial CV |
|--------|------------|
| AUC | 0.9525 |
| Average Precision | 0.8528 |
| F1 (threshold = 0.764) | 0.8010 |

### Logistic Regression

Logistic regression predicts the likelihood of peat presence based on a weighted combination of the covariates. It assumes each covariate has a straight-line relationship with peat presence and does not account for thresholds. In this case, logistic regression was used primarily as a baseline to compare to the more complex models. The model is standardized with StandardScaler, uses the lbfgs solver, C = 1.0 and class_weight = 'balanced'.

| Metric | Spatial CV |
|--------|------------|
| AUC | 0.9454 |
| Average Precision | 0.8139 |
| F1 (threshold = 0.754) | 0.7756 |

### Convolutional Neural Network (CNN)

A convolutional neural network (CNN) is a type of neural network commonly used with images and other spatial data. It learns patterns such as edges and textures and then combines those patterns to make a prediction. In this project the raster covariates acted as a “landscape” surrounding the points to then be used to predict from rather than using individual pixel values.
The model used two inputs; 1) a raster patch on each training point and 2) the covariate values inside of the patch. These inputs were processed separately and then combined to make a prediction. Two patch sizes were tested (15 × 15 and 31 × 31) which changed the amount of pixels the model saw surrounding the points. The best CNN model had a spatial CV AUC of 0.962 which was similar to the boosted models.
The CNN was not chosen as the production model because it required large compute and compute time. Mapping was also more complex because the spatial inference requires a full raster patch around every pixel. 

### Final Model: LightGBM 

After all of the above models were tested, LightGBM was selected as the best performing based on its spatial AUC score and Brier score. 

#### Model settings

The final hyperparameters came from Optuna tuning of the LightGBM model. In the tuning process the largest gains in performance came from slower learning rates and stronger larger minimum leaf sizes. The final settings of the LightGBM peat probability model are:

- 620 trees (`n_estimators`) with a learning rate of 0.0166 so each tree makes only a small correction
- up to 282 leaves per tree with a maximum depth of 15, and at least 92 points in each leaf (`min_child_samples`)
- each tree uses 56% of the rows (`subsample`) and 72% of the features (`colsample_bytree`)
- L1 regularization (`reg_alpha`) of 3.38 and L2 regularization (`reg_lambda`) of 0.71, which penalizes large leaf values
- trained unweighted, on all 57,134 points

#### Covariates

The final model uses 57 covariates:

- terrain: slope, aspect, hillshade, three curvatures, breached DEM, D-infinity flow accumulation, deviation from mean elevation and relative topographic position (at three scales each)
- distance to water and streams (roads was removed due to artifacts)
- PRISM climate normals 
- Sentinel-2 bands and Tasseled Cap brightness, greenness and wetness
- Sentinel-1 combined VV, VH and VV/VH ratio composites
- the NWI wetland classes

#### Performance

Spatial cross-validation gives the performance that can be expected in areas without training points:

| Metric | Spatial CV | Random CV |
|--------|-----------|------------|
| AUC | 0.9642 | 0.9766 |
| Average precision | 0.9002 | 0.9325 |
| Brier score | 0.0483 | 0.0383 |

At the selected threshold (0.362), the spatial out-of-fold predictions found 8,551 of the 10,397 peat points (recall 0.822) and labeled 2,003 of the 46,737 non-peat points as peat (4.3%). Of all points that were predicted as peat, 81% were peat (precision 0.810), giving an F1 score of 0.816 and an overall accuracy of 93.3%. 

#### Variable importance

Two measures of importance were calculated for the probability model, split counts and gain. The split counts show how often the model uses a covariate and gain shows how much the covariate improves the model's fit. By split count the most used covariates were two PRISM climate layers (precipitation and January minimum temperature) along with the breached DEM and the distances to water and streams. Using gain, slope is the most important covariate by a large margin (over four times the second) followed by NWI non-wetland class and PRISM January minimum temperature.

**add in table of covariate importance**

### Threshold Selection

The final probability model produces a value between 0 and 1 for every pixel in the map raster. To convert this product into a binary peat or non-peat mask, a threshold needs to be selected. The threshold is the cutoff value of which pixel values that are higher are assigned a value of peat present and values below that threshold turn into peat absent. Moving the threshold changes the total area of peatlands mapped. For example, moving the threshold from 0.25 to 0.50 changes the mapped peatland area from around 9.2 million to 6.3 million acres.

#### Final threshold 

Using a single metric to derive a threshold can favor one kind of error so the final threshold uses five metrics. The out-of-fold predictions were swept across 500 cutoffs (0.01–0.99) and the optimal threshold of each metric was found:

| Metric | Optimal threshold |
|---|---|
| Youden's J | 0.161 |
| Balanced accuracy | 0.161 |
| F1 | 0.362 |
| Accuracy | 0.466 |
| Matthews correlation coefficient (MCC) | 0.466 |

The range in optimal threshold from the above metrics range because they weigh mistakes differently. Youden's J and balanced accuracy count the peat and non-peat classes equally so they favor a low threshold that catches a majority of peat but with a higher amount of false positives. Accuracy and MCC are more influenced by the more prevalent non-peat classes and favor a higher threshold. F1 is in the middle because it looks at how well the peat class itself is predicted. Taking the median of the five, **0.362**, avoids committing to either extreme. 

The 0.362 threshold is then used to produce the statewide peat mask. The mapped peatland extent within Minnesota is 7,553,829 acres (3,056,926 ha; 30,569 km²). 

| Probability threshold | Mapped acres |
|---|---|
| ≥ 0.25 | 9,189,405 |
| ≥ 0.33 | 7,910,744 |
| **≥ 0.362 (final)** | **7,553,829** |
| ≥ 0.45 | 6,726,459 |
| ≥ 0.50 | 6,302,600 |

## 4.3 Peat Depth

The peat depth model predicts the thickness of peat in centimeters at every pixel inside the peat mask from the probability model. The target (`depb`), is the maximum peat depth measured at a point. Because depth is a regression problem the model predicts a continuous number and not a class. Depth is an important property in this project because below ground carbon depends on how much peat is present, and the final below ground carbon stock map is calculated directly from the depth map.

Peat depth is a harder variable to predict than peat presence. The covariate stack used are surface properties that can describe peat presence well but the thickness of peat underground is only indirectly related to them. Depth is also strongly clustered in space which can be seen in the gap between random and spatial cross-validation. Two measures are reported for the depth models:

*R²* - the share of the variation in depth that the model explains
*Mean Absolute Error (MAE)* - The average miss in centimeters.

### Training Data and Masking

Early depth models were trained on the full point set which included points that had a depth of zero. This produced deceptively high R² values (~0.70), a misleading result because the high R² mainly showed the model separating zero from non-zero depth, and the model had bad accuracy at locations that actually have peat.

To correct this problem a two-stage approach was used. First, the peat probability model is used as a mask, and depth regression is trained and predicted only on locations the probability model classifies as peat. For a depth point to be included in the training data it must meet both of the criterion `depb > 0` AND `PROB_LGBM ≥ 0.362`. This filter resulted in 8,223 training points.

### Early Random Forest Experiments

The depth modeling originally used a random forest model. Experiments that were tested included adding SSURGO soil survey data as a covariate, dropping shallow peat (1-20 cm) points from the training data, and log-transforming the depth target. Recursive feature elimination reduced the feature set to 15 with performance improving as features were removed. The random CV R² started at 0.4233 with 125 features and increased to 0.484 with 15 features.

### Other Algorithms

XGBoost, LightGBM, GAM, a linear SVM and Ridge regression were also evaluated for depth in the same way as probability. On spatial CV the models performed similarly with an R² between 0.26 and 0.33. The random CV R² of the gradient boosting models was much higher than their spatial CV R² (0.62 versus 0.30) showing that peat depth is even more spatially correlated than peat probability. 

### Final Base Model: LightGBM

The depth pipeline followed the same steps as probability. First a correlation filter reduced 172 features down to 143.  RFE was run for the random forest only (143 reduced to 37). Baseline training of the models and then tuning with Optuna (TPE sampler, 50 trials per model, optimizing spatial CV R²). No class weighting was needed for a regression target.

LightGBM was the best performing model before and after tuning. The untuned spatial R² values were 0.27 (random forest), 0.28 (XGBoost) and 0.29 (LightGBM), and after tuning they were 0.2731, 0.2885 and 0.2925. The final base model, `DEPTH_LGBM_TUNED`, has a spatial R² of 0.2925 and MAE of 74.6 cm, a random R² of 0.4273 and MAE of 66.1 cm, and was trained on 8,223 points. 

The depth model uses the same covariate exclusion list as probability with one difference. The SSURGO organic soil classes are kept for depth. They are a peat classification product, so they would be circular for predicting whether peat exists, but because depth is only trained inside the peat present mask using this layer for peat depth it is not circular, and it improved the depth models. 

### Deep-Tail Blend

#### Predicting Deep Peat

The base LGBM model underpredicted deep peat. Training point data has depths up to 900 cm with 677 points deeper than 366 cm and 179 points deeper than 490 cm, which made up about 10% of the training set. Because a LightGBM model predicts the mean of the training points in each leaf, the rare deep observations get averaged together with shallower neighbors, which causes the model to underestimate areas where deep peat exists.

























































