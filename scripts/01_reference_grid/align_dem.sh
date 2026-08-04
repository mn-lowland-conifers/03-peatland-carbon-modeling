#!/bin/bash
#SBATCH --job-name=align_dem
#SBATCH --ntasks=1
#SBATCH --mem=64gb
#SBATCH --time=1:00:00
#SBATCH --partition=agsmall
#SBATCH --mail-user=email@gmail.com
#SBATCH -o /folder/align_dem_%j.out
#SBATCH -e /folder/align_dem_%j.err

# PURPOSE
#   Reference grid alignment. Each covariate raster must
#   share the same pixel grid (size, origin, resolution) as the
#   gNATSGO 10m MUKEY raster for pixel extraction and stacking. 
#	This script aligns the statewide DEM to
#   the reference grid.
#
# REFERENCE GRID (gNATSGO 10m MUKEY raster)
#   Size:       66,474 x 75,185 pixels   (-ts)
#   Extent:     -99098.0, 2269539.0, 565642.0, 3021389.0   (-te: xmin ymin xmax ymax)
#   CRS:        EPSG:5070 (NAD83 / Conus Albers Equal Area)
#   Resolution: 10m
#
# INPUT
#   00_data/covariates_10m/minnesota_dem_10m.tif
#
# OUTPUT
#   00_data/covariates_10m/minnesota_dem_10m_ALIGNED.tif

COVAR_DIR="/00_data/covariates_10m"

echo "Aligning grid..."

gdalwarp \
  -ts 66474 75185 \
  -te -99098.0 2269539.0 565642.0 3021389.0 \
  -r bilinear \
  -co COMPRESS=LZW \
  -co TILED=YES \
  -co BIGTIFF=YES \
  ${COVAR_DIR}/minnesota_dem_10m.tif \
  ${COVAR_DIR}/minnesota_dem_10m_ALIGNED.tif

gdalinfo ${COVAR_DIR}/minnesota_dem_10m_ALIGNED.tif | grep "Size\|Origin"
