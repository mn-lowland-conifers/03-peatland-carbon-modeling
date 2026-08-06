"""
Create geomorphons landform classification raster

PURPOSE
  Computes the geomorphons landform classification 

INPUT
  00_data/covariates_10m/minnesota_dem_10m.tif

OUTPUT
  00_data/covariates_10m/geomorphons.tif
"""

import sys
import os

wbt_dir = '/users/7/ocon0444/software/whitebox/WhiteboxTools_linux_amd64/WBT'
sys.path.insert(0, wbt_dir)
os.chdir(wbt_dir)

import whitebox_tools

wbt = whitebox_tools.WhiteboxTools()
wbt.set_verbose_mode(True)
wbt.set_compress_rasters(True)

dem = "/folder/00_data/covariates_10m/minnesota_dem_10m.tif"
output = "/folder/00_data/covariates_10m/geomorphons.tif"

print("Creating geomorphons...")
print(f"Input: {dem}")
print(f"Output: {output}")

# search: max lookup distance (cells) used to compute line-of-sight
# visibility in each direction around a pixel
# threshold: minimum flatness angle (degrees) to consider two directions
# "similar" -- 0.0 means no flatness tolerance
# fdist / skip: forward/skip distance parameters left at WBT defaults
# forms=True: output the 10-class landform typology rather than raw pattern codes
wbt.geomorphons(dem, output, search=50, threshold=0.0, fdist=0, skip=0, forms=True)

print("Complete")
