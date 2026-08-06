"""
Hydrological conditioning - minnesota dem

PURPOSE
  Conditions the statewide DEM for hydrological analysis by removing
  artificial depressions and burning in the known stream network, then
  derives flow accumulation, DInf flow, and TWI from the conditioned DEM.

INPUT
  00_data/covariates_10m/minnesota_dem_10m.tif
  00_data/vector_data/RiversStreams_5070.shp

OUTPUT
  00_data/covariates_10m/breached_dem_conditioned.tif
  00_data/covariates_10m/d8FlowAccumulation_conditioned.tif
  00_data/covariates_10m/dInfFlowAccumulation_conditioned.tif
  00_data/covariates_10m/wetnessIndex_conditioned.tif
"""

import sys
import os
import time

# Setup WBT 
wbt_dir = '/users/7/ocon0444/software/whitebox/WhiteboxTools_linux_amd64/WBT'
sys.path.insert(0, wbt_dir)
os.chdir(wbt_dir)

import whitebox_tools

# Paths
base_dir = "/folder/00_data/covariates_10m"
temp_dir = os.path.join(base_dir, "temp_hydro")
os.makedirs(temp_dir, exist_ok=True)

# Inputs
dem = os.path.join(base_dir, "minnesota_dem_10m.tif")
streams = "/folder/00_data/vector_data/RiversStreams_5070.shp"

# Temp files (intermediate conditioning outputs, not final covariates)
fscp = os.path.join(temp_dir, "fscp.tif")
bdlc = os.path.join(temp_dir, "bdlc.tif")
fscp2 = os.path.join(temp_dir, "fscp2.tif")
streams_raster = os.path.join(temp_dir, "streams_rasterized.tif")

# Output covariates
breached_dem = os.path.join(base_dir, "breached_dem_conditioned.tif")
d8_accum = os.path.join(base_dir, "d8FlowAccumulation_conditioned.tif")
dinf_accum = os.path.join(base_dir, "dInfFlowAccumulation_conditioned.tif")
wetness = os.path.join(base_dir, "wetnessIndex_conditioned.tif")
slope = os.path.join(base_dir, "slope.tif")  # already exists, reuse for wetness

start_time = time.time()

wbt = whitebox_tools.WhiteboxTools()

print("="*60)
print("HYDROLOGICAL CONDITIONING")
print("="*60)

# Step 1: Fill single-cell pits 
print(f"\n[{time.strftime('%H:%M:%S')}] Step 1/7: Fill single cell pits...")
wbt.fill_single_cell_pits(dem, fscp)
print(f"[{time.strftime('%H:%M:%S')}] \u2713 Complete: {fscp}")

# Step 2: Breach depressions (least-cost path), dist=10 cells (100m at
# 10m resolution), max_cost=1.0m 
print(f"\n[{time.strftime('%H:%M:%S')}] Step 2/7: Breach depressions least cost...")
wbt.breach_depressions_least_cost(fscp, bdlc, dist=10, max_cost=1.0)
print(f"[{time.strftime('%H:%M:%S')}] \u2713 Complete: {bdlc}")

# Step 3: Fill single-cell pits again to clean up any new single-cell
# artifacts introduced by the breaching step.
print(f"\n[{time.strftime('%H:%M:%S')}] Step 3/7: Fill single cell pits (second pass)...")
wbt.fill_single_cell_pits(bdlc, fscp2)
print(f"[{time.strftime('%H:%M:%S')}] \u2713 Complete: {fscp2}")

# Step 4: Rasterize the DNR stream-network vector layer onto the DEM grid
# so it can be burned in during the next step.
print(f"\n[{time.strftime('%H:%M:%S')}] Step 4/7: Rasterizing streams...")
wbt.vector_lines_to_raster(
    i=streams,
    output=streams_raster,
    field="FID",
    nodata=True,
    base=fscp2
)
print(f"[{time.strftime('%H:%M:%S')}] \u2713 Complete: {streams_raster}")

# Step 5: Burn the rasterized stream network into the DEM at road
# crossings so that road embankments don't block mapped stream flow.
print(f"\n[{time.strftime('%H:%M:%S')}] Step 5/7: Burning streams into DEM...")
wbt.burn_streams_at_roads(
    dem=fscp2,
    streams=streams_raster,
    output=breached_dem
)
print(f"[{time.strftime('%H:%M:%S')}] \u2713 Complete: {breached_dem}")

# Step 6: Flow accumulation from the conditioned DEM, both algorithms.
print(f"\n[{time.strftime('%H:%M:%S')}] Step 6/7: D8 flow accumulation...")
wbt.d8_flow_accumulation(breached_dem, d8_accum, out_type='specific contributing area')
print(f"[{time.strftime('%H:%M:%S')}] \u2713 Complete: {d8_accum}")

print(f"\n[{time.strftime('%H:%M:%S')}] Step 6b/7: DInf flow accumulation...")
wbt.d_inf_flow_accumulation(breached_dem, dinf_accum, out_type='specific contributing area')
print(f"[{time.strftime('%H:%M:%S')}] \u2713 Complete: {dinf_accum}")

# Step 7: Wetness index, reusing the statewide slope.tif produced by
# run_wbt_local_statewide.py rather than recomputing slope here.
print(f"\n[{time.strftime('%H:%M:%S')}] Step 7/7: Wetness index...")
wbt.wetness_index(dinf_accum, slope, wetness)
print(f"[{time.strftime('%H:%M:%S')}] \u2713 Complete: {wetness}")

elapsed = time.time() - start_time
print("\n" + "="*60)
print(f"COMPLETE")
print(f"Total time: {elapsed/3600:.2f} hours")
print("="*60)
print("\nOutput covariates:")
print(f"  {breached_dem}")
print(f"  {d8_accum}")
print(f"  {dinf_accum}")
print(f"  {wetness}")
print(f"\nTemp files in: {temp_dir}")
print("(delete temp folder when done)")
