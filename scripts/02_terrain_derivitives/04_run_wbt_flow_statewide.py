#!/usr/bin/env python3
"""
WhiteboxTools flow operations 

PURPOSE
 Computes flow-dependent terrain derivatives (breached
  DEM, D8/DInf flow accumulation, TWI, deviation-from-mean-elevation,
  relative topographic position) 

INPUT
  00_data/covariates_10m/minnesota_dem_10m.tif

OUTPUTS
  breached_dem.tif, d8FlowAccumulation.tif, dInfFlowAccumulation.tif,
  wetnessIndex.tif, devfrommeanelev_{4,8,16}m.tif, diffFromMeanElev.tif,
  relativeTopographicPosition_{4,8,16}m.tif
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
output_dir = "/folder/00_data/covariates_10m"

print("whiteboxtools flow operations")

# Step 1: breach depressions so water can flow continuously across the DEM
breached = f"{output_dir}/breached_dem.tif"
if not os.path.exists(breached):
    print("[1/11] Breach Depressions")
    wbt.breach_depressions(dem, breached)

# Step 2-3: flow accumulation
d8_flow = f"{output_dir}/d8FlowAccumulation.tif"
if not os.path.exists(d8_flow):
    print("[2/11] D8 Flow Accumulation")
    wbt.d8_flow_accumulation(breached, d8_flow, out_type="cells")

dinf_flow = f"{output_dir}/dInfFlowAccumulation.tif"
if not os.path.exists(dinf_flow):
    print("[3/11] DInf Flow Accumulation")
    wbt.d_inf_flow_accumulation(breached, dinf_flow, out_type="Specific Contributing Area")

# Step 4: Topographic Wetness Index = f(flow accumulation, slope)
twi = f"{output_dir}/wetnessIndex.tif"
if not os.path.exists(twi):
    print("[4/11] Wetness Index")
    wbt.wetness_index(dinf_flow, breached, twi)

# Step 5-7: Deviation from mean elevation at three moving-window radii
# (4m, 8m, 16m)
for radius in [4, 8, 16]:
    output = f"{output_dir}/devfrommeanelev_{radius}m.tif"
    if not os.path.exists(output):
        print(f"[{4+radius//4}/11] Dev from Mean Elev {radius}m")
        wbt.dev_from_mean_elev(breached, output, filterx=radius, filtery=radius)

# Step 8: Difference from mean elevation, single fixed 11x11 window.
diff_mean = f"{output_dir}/diffFromMeanElev.tif"
if not os.path.exists(diff_mean):
    print("[8/11] Diff from Mean Elev")
    wbt.diff_from_mean_elev(breached, diff_mean, filterx=11, filtery=11)

# Step 9-11: Relative topographic position at the same three radii.
for radius in [4, 8, 16]:
    output = f"{output_dir}/relativeTopographicPosition_{radius}m.tif"
    if not os.path.exists(output):
        print(f"[{8+radius//4}/11] Relative Topo Position {radius}m")
        wbt.relative_topographic_position(breached, output, filterx=radius, filtery=radius)

print("COMPLETE")
