#!/usr/bin/env python3
"""
create_mn_50km_grid.py

PURPOSE
  creates a 50km x 50km tile grid over the state of MN.


METHOD
  1. Read the statewide DEM bounds, CRS , and resolution 
  2. Create tiles with 50km spacing starting from the
     DEMs lower left corner
  3. Each tile is given a 500m buffer so adjacent tile inferences
     overlap for mosiacing.
  4. Tiles that don't intersect the MN boundary are
     dropped (reduces 224 grid down to 115 tiles)
  5. Each tile polygon gets a unique tile_id as a row/col
     (example tile_003_007) and non buffered x/y bounds stored as attributes 

INPUT
  00_data/covariates_10m/minnesota_dem_10m.tif        (defines CRS/extent/resolution)
  00_data/boundary/mn_state_boundary_albers.shp        (clip filter)

OUTPUT
  00_data/boundary/mn_50km_grid.shp
"""

import numpy as np
import fiona
from fiona.crs import from_epsg
from shapely.geometry import box, mapping
from shapely.ops import unary_union
from shapely.geometry import shape
import rasterio

DEM_PATH  = '/folder/00_data/covariates_10m/minnesota_dem_10m.tif'
OUT_GRID  = '/folder/00_data/boundary/mn_50km_grid.shp'
TILE_SIZE = 50000   # 50km in meters (EPSG:5070)
BUFFER    = 500     # 500m overlap buffer on each side, resolved during mosaicking

# Get DEM extent and CRS 
with rasterio.open(DEM_PATH) as src:
    bounds = src.bounds
    crs    = src.crs
    res    = src.res[0]
    print(f'DEM bounds : {bounds}')
    print(f'DEM CRS    : {crs}')
    print(f'DEM res    : {res}m')

# Snap grid origin to DEM bounds 
x_min = bounds.left
x_max = bounds.right
y_min = bounds.bottom
y_max = bounds.top

# Generate tile origin coordinates on a regular 50km spacing
xs = np.arange(x_min, x_max, TILE_SIZE)
ys = np.arange(y_min, y_max, TILE_SIZE)

print(f'\nGrid dimensions: {len(xs)} cols x {len(ys)} rows = {len(xs)*len(ys)} tiles')
print(f'Tile size: {TILE_SIZE/1000:.0f}km x {TILE_SIZE/1000:.0f}km + {BUFFER}m buffer')

# MN state boundary for clipping 
try:
    with fiona.open('/folder/00_data/boundary/mn_state_boundary_albers.shp') as shp:
        mn_geom = unary_union([shape(f['geometry']) for f in shp])
    print(f'MN boundary loaded')
    use_mn_clip = True
except Exception as e:
    print(f'Could not load MN boundary')
    use_mn_clip = False

# Write shapefile to store the buffered polygon geometry
# and the unbuffered x/y bounds as attributes 
schema = {
    'geometry': 'Polygon',
    'properties': {
        'tile_id':  'str',
        'col':      'int',
        'row':      'int',
        'x_min':    'float',
        'y_min':    'float',
        'x_max':    'float',
        'y_max':    'float',
    }
}

tile_count = 0
with fiona.open(OUT_GRID, 'w',
                driver='ESRI Shapefile',
                crs=crs.to_wkt(),
                schema=schema) as dst:

    for col_i, x0 in enumerate(xs):
        for row_i, y0 in enumerate(ys):
            x1 = x0 + TILE_SIZE
            y1 = y0 + TILE_SIZE

            # Tile geometry with buffer 
            tile_buf = box(x0 - BUFFER, y0 - BUFFER,
                           x1 + BUFFER, y1 + BUFFER)

            # Skip tiles that don't intersect MN 
            if use_mn_clip and not mn_geom.intersects(tile_buf):
                continue

            tile_id = f'tile_{col_i:03d}_{row_i:03d}'
            dst.write({
                'geometry': mapping(tile_buf),
                'properties': {
                    'tile_id': tile_id,
                    'col':     col_i,
                    'row':     row_i,
                    # Unbuffered bounds
                    'x_min':   x0,
                    'y_min':   y0,
                    'x_max':   x1,
                    'y_max':   y1,
                }
            })
            tile_count += 1

print(f'\nSaved {tile_count} tiles to:\n  {OUT_GRID}')
print(f'\nTile IDs will be used as region names in inference script.')
print(f'Example: tile_000_000, tile_001_000, ...')
