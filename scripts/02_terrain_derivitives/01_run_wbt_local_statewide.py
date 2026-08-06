#!/usr/bin/env python3
"""
Run whitebox tools on full Minnesota DEM

PURPOSE
  Computes the terrain derivatives on a statewide basis per covariate curation methods section
  (derivatives that only require local information and do not depend on upstream drainage)

INPUT
  00_data/covariates_10m/minnesota_dem_10m.tif

OUTPUT (one raster per operation)
  slope.tif, aspect.tif, hillshade.tif,
  planCurvature.tif, profileCurvature.tif, meanCurvature.tif, maximalCurvature.tif
"""

import sys
import os

# Setup WBT
wbt_dir = '/users/7/ocon0444/software/whitebox/WhiteboxTools_linux_amd64/WBT'
sys.path.insert(0, wbt_dir)
os.chdir(wbt_dir)

import whitebox_tools

# Create WBT instance
wbt = whitebox_tools.WhiteboxTools()
wbt.set_verbose_mode(True)
wbt.set_compress_rasters(True)

# Paths
dem = "/folder/00_data/covariates_10m/minnesota_dem_10m.tif"
output_dir = "/folder/00_data/covariates_10m"

print("="*80)
print("whitebox tools statewide")
print("="*80)
print(f"Input DEM: {dem}")
print(f"Output dir: {output_dir}")
print()

# Each tuple is(output filename stem, human-readable label).
operations = [
    ("slope", "Slope"),
    ("aspect", "Aspect"),
    ("hillshade", "Hillshade"),
    ("planCurvature", "Plan Curvature"),
    ("profileCurvature", "Profile Curvature"),
    ("meanCurvature", "Mean Curvature"),
    ("maximalCurvature", "Maximal Curvature"),
]

for fname, display in operations:
    output = f"{output_dir}/{fname}.tif"

    print(f"\n{'='*60}")
    print(f"{display}")
    print('='*60)

    if os.path.exists(output):
        print("  \u26a0 Already exists, skipping")
        continue

    try:
        if fname == "slope":
            wbt.slope(dem, output, units="degrees")
        elif fname == "aspect":
            wbt.aspect(dem, output)
        elif fname == "hillshade":
            wbt.hillshade(dem, output, azimuth=315.0, altitude=45.0)
        elif fname == "planCurvature":
            wbt.plan_curvature(dem, output)
        elif fname == "profileCurvature":
            wbt.profile_curvature(dem, output)
        elif fname == "meanCurvature":
            wbt.mean_curvature(dem, output)
        elif fname == "maximalCurvature":
            wbt.maximal_curvature(dem, output)

        print(f"  \u2713 Complete")
    except Exception as e:
        print(f"  \u2717 Error: {e}")

print("\n" + "="*80)
print("COMPLETE")
print("="*80)
