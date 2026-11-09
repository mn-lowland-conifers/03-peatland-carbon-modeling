# Preface

This e-book documents the methods and workflow for the peatland carbon modeling component of the MN School Trust Legislative Directive to UMN Department of Forest Resources and UMN Department of Soil, Water and Climate.

## Project Description

This project produces 10m raster maps of peatland extent and characteristics across Minnesota. Point observations from the Minnesota DNR Peat Inventory, National Soil Information System (NASIS), and Minnesota Biological Survey data, along with a stack of 172 candidate covariates were used to develop gradient-boosting models to predict (1) the probability of peat presence, (2) peat depth, and (3) the proportions of fibric, hemic, and sapric material in the upper meter of the profile. The probability model, which maps  ~7.85 million acres of peatland  at a threshold of 0.362, defines the spatial mask used by the depth and composition models. Peat depth is then converted to a full-profile carbon stock using a depth-to-carbon relationship fitted to Peat Inventory pedons. Models were evaluated with 50 km spatial block cross-validation as well as random cross-validation. This ebook documents the data, methods, and results of that mapping workflow.

## Key Personnel

- Nic Jelinski; Associate Professor, SWAC, Co-PI
- Marcella Windmuller-Campione; Associate Professor, FR, Co-PI
- Kellen O'Connor; Research Professional 2, SWAC
- Laura Reuling; Research Professional?, FR
- Basil Nadolski; Research Professional ?, FR

