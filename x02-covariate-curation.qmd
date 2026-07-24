# Covariate Curation

## Computing Environment
Processing of covariates was done on the Minnesota Supercomputing Institute (MSI) Agate AMD EPYC Linux cluster. A majority of scripts were run using SLURM batch scheduling. A custom conda environment (gdalenvgeospat) was created on MSI to run packages including GDAL, rasterio, fiona, geopandas, and WhiteboxTools. Standard MSI environments were not used to process rasters because of conflicts between system GDAL and the conda installed GDAL (ABI mismatches, missing libpoppler, libtiff version conflicts). 
## Reference Grid
All rasters were aligned to the gNATSGO grid before modeling. This process was done using gdalwarp with -ts 66474 75185 (target size) and -te (target extent) flags. Bilinear resampling was used for continuous data and nearest neighbor was used for categorical data.
Reference raster: gNATSGO 10m MUKEY raster
Dimensions: 66,474 × 75,185 pixels
CRS: EPSG:5070 (NAD83 / Conus Albers Equal Area)
Origin: −99,098, 3,021,389
Resolution: 10m
### Digital Elevation Model
Source: USGS 3D Elevation Program (3DEP), 10m resolution
Download: National Map Downloader, https://apps.nationalmap.gov/downloader/
Tiles mosaicked into a single statewide raster and clipped to the Minnesota state boundary using GDAL warp with output CRS forced to EPSG:5070
minnesota_dem_10m.tif

### Terrain Derivatives (WhiteboxTools)
WhiteboxTools v2.4.0 was accessed through Python API with a conda kernel configured on MSI. Standard Python/GDAL environments on MSI did not include WhiteboxTools so the gdalenvgeospat environment was used. 
Multiprocessing parallelization (multiprocessing.Pool) was used to run terrain derivatives at the same time to speed up the process.
### Processing Strategy
Two approaches were used depending if the derivative is affected by watershed context:
Statewide: Computed directly on the statewide mosaicked DEM. These derivatives only require local information and do not depend on upstream drainage areas.
slope, aspect, hillshade
planCurvature, profileCurvature, meanCurvature, maximalCurvature
geomorphons, pennockLandformClass
devfrommeanelev (4m, 8m, 16m), diffFromMeanElev
relativeTopographicPosition (4m, 8m, 16m)
By HUC8 watershed: For derivatives that are impacted by flow patterns, a different approach was used. Minnesota was divided into 127 HUC8 watersheds and a 5km buffer was applied around each HUC8. This was done to prevent potential edge effects from occurring. Derivatives were computed on each buffered watershed tile independently with individual SLURM jobs (one per HUC8), then mosaicked back together with the overlapping buffer zones removed.
breached_dem (hydrologically conditioned DEM)
d8FlowAccumulation, dInfFlowAccumulation
wetnessIndex (TWI)
### Hydrological Modification
Minnesota peatlands often exist in low-lying poorly drained areas. When preparing a DEM for hydrological analysis, artificial depressions in the DEM are removed so that waterflow can run continuously throughout the landscape. A breaching approach was used to carve channels through barriers blocking drainage versus raising the surface itself. This allows water to flow continuously through the model, producing more accurate flow accumulation and wetness index values.
Modification workflow by HUC8 watershed:
Step
Tool
Output
Purpose
1
FillSingleCellPits
_01_fscp.tif
Remove single-cell LiDAR artifacts
2
FlattenLakes
_02_flat.tif
Flatten lake surfaces to minimum elevation
3
TopologicalBreachBurn
_03_tbb.tif
Burn stream network into DEM
4
BreachDepressionsLeastCost
_04_bdlc.tif
Breach through road embankments and barriers
5
FillSingleCellPits
_05_fel.tif
Final cleanup

Parameters:
TopologicalBreachBurn snap = 2.0m (2-cell tolerance at 1m resolution for stream/DEM alignment)
BreachDepressionsLeastCost dist = 100 cells (100m max breach length), max_cost = 1.0m
Input datasets:
Lakes: DNR HydroFeatures (polygons)
Streams: DNR RiversStreams (lines)
Roads: MnDOT Roadway Routes (lines)
Final terrain derivatives: slope.tif, aspect.tif, hillshade.tif, planCurvature.tif, profileCurvature.tif, maximalCurvature.tif, breached_dem.tif, d8FlowAccumulation.tif, dInfFlowAccumulation.tif, wetnessIndex.tif, devfrommeanelev_4m.tif, devfrommeanelev_8m.tif, devfrommeanelev_16m.tif, diffFromMeanElev.tif, relativeTopographicPosition_4m.tif, relativeTopographicPosition_8m.tif, relativeTopographicPosition_16m.tif, geomorphons.tif, pennockLandformClass.tif

## Sentinel-2 Imagery
Source: COPERNICUS/S2_SR_HARMONIZED from Google Earth Engine
Dates: 2019–2024
Extent: Minnesota state boundary (TIGER/2018/States)
Seasonal Compositing
Three seasonal median composites were generated:
Spring (April–May): cloud and snow masked
Summer (June–August): cloud masked 
Fall (September–October): cloud and snow masked
Cloud masking used SCL layer excluding: cloud shadows (class 3), medium cloud (class 8), high cloud (class 9), thin cirrus (class 10). Per-image pre-filter excluded scenes >30% cloud cover. Snow/ice (class 11) masked for spring and fall.

In total there were 10 bands per season: B02, B03, B04, B05, B06, B07, B08, B8A, B11, B12 and 2 additional bands were calculated:
NDVI = (B08 − B04) / (B08 + B04) Normalized Difference Vegetation Index to quantify vegetation health and density
SWDI = from Green (B03) and Red Edge 1 (B05) Soil Water Deficit Index sensitive to surface moisture
Bands that were originally at a 20m resolution (B05–B08A, B11, B12) were resampled to 10m during the GEE export.

### Sentinel 2 export and mosaicking

GEE automatically tiled the whole state exports. Tiles were downloaded from google drive to local machine then uploaded into the MSI project. Once in MSI, tiles were mosaicked into a single multiband tiff file using gdal_merge.py. LZW compression, internal tiling, and BIGTIFF were used to merge the outputs.

### Tasseled Cap 

Tasseled Cap Transformation compresses multiband data into single bands that can better track soils, urban areas, and vegetation (source). The three components used in this project were the Brightness (TCB), greenness(TCG), and wetness(TCW). These bands are computed by applying a coefficient to existing S2 bands (Nedkov, 2017). Tasseled cap bands were computed on MSI and validated on expected correlation patterns (positive Brightness–Greenness, negative Brightness–Wetness, stronger Greenness–Wetness correlation in summer vs. spring/fall)

### Sentinel-1 

**Still in the works***
Original export from GEE separated ascending and descending passes and had incomplete coverage in ascending data. Only 43% of points in the model had S1 coverage. However, while limited, S1 survived RFE and increased R2 values
Changes in the export (combining ascending and descending runs, extending date range) will hopefully fill the missing data:
Three bands per composite: VV (dB), VH (dB), VV/VH ratio.
Exported as INT16 scaled ×100, converted to float32 /100 during mosaicking.

## PRISM Climate data
Source: PRISM Climate Group, 30-year normals at 800m
Layers: Annual precipitation, mean July max temp, mean annual temp, mean January min temp

PRISM data was reprojected to EPSG:5070, clipped to the DEM extent, and resampled to 10m (bilinear) during alignment to the reference grid.

## National Wetlands Inventory (NWI) 
Source: NWI geodatabase (https://www.mngeo.state.mn.us/chouse/water_wetlands.html)

The NWI vector data was converted and classified to a raster on MSI using fiona and rasterio with chunked processing to manage the large amount of features (1,000,000+) Polygons were classified by their cowardin code and separated into 3 distinct groupings: 
0 = Non-wetland (background)
1 = Wetland
2 = Lowland conifer (PFO4, PSS4, PFO2, PSS2, mixed codes containing "/4")

The encoding variants of the raster was evaluated during initial random forest experiments and the 3-class classification was found to give no measurable improvement. The final raster used was split into a binary encoding where 0 = non-wetland, 1 = any wetland

## Distance Features
Source: Minnesota statewide vector datasets
Roads: MnDOT Roadway Routes
Streams/rivers: DNR RiversStreams
Water bodies: DNR HydroFeatures

Euclidean distance rasters were computed from vector layers using GDAL proximity on MSI.

## gNATSGO Organic Soils
Source: gNATSGO for Minnesota 

gNATSGO (gridded National Soil Survey Geographic Database) is the USDAs Natural Resource Conservation Service's soils product. It merges SSURGO withs STATSGO into one database per state. The 10m MUKEY raster was used to pull organic soils classified in Minnesota and then split into 8 separate classes based on soil taxonomy:
0: Non-organic
1: Shallow Peat (histic epipedon, non-Histosol, 20–40cm organic)
2: Terric Saprists
3: Terric Hemists
4: Terric Fibrists
5: Typic Saprists
6: Typic Hemists
7: Typic Fibrists
8: Sphagno Histosols

A binary variant of this raster was also created that flags any mukey containing an organic component regardless of dominance. 

Both gNATSGO derived layers ended up being excluded from probability model training as predictors because they are peat classification products and including them caused circular logic. They were retained as refernce/validation layers and used selectively in other peat property models. 

## Categorical Layers

These layers produced visible polygon shaped artifacts such as hard geometric edges in the spatial inferences. Because the models learned to change predictions on polygon edges from these rasters rather than responding to environmental gradients they were excluded. 

10m_quaternary_geology.tif — Quaternary Geology classification
pennockLandformClass.tif — Pennock Landform Class
geomorphons.tif — geomorphon landform classification

These were tested in experiments exp401–exp408 and removed in exp409/exp410. AUC cost was minimal (~0.002) and the visual output quality improved substantially.
 


