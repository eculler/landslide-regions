import fiona, fiona.crs
import geopandas as gpd
import shapely.geometry
import shapely.speedups
import pandas as pd
import matplotlib.pyplot as plt
import os
import pyproj

out_fn = 'out/watersheds.csv'
gagesii_path = 'data/GAGESII/CONUS/bas_all_us.shp'
slide_path = 'data/SLIDE_NASA_GLC/GLC20180821.csv'

def buffer_slide(row):
    if row.location_accuracy in ['exact', 'unknown']:
        return row.geometry.buffer(1)
    radius = int(row.location_accuracy[:-2]) * 1000
    return row.geometry.buffer(radius)


def remove_nested(group):
    done = []
    keep = []
    inds = group.sort_values('AREA', ascending=False).index
    for i in inds[:-1]:
        intersection = gpd.overlay(
            group.loc[[i]], group.drop([i] + done), how='intersection')

        if intersection.empty:
            keep.append(i)
        else:
            diff = group.at[i, 'geometry'].difference(intersection.unary_union)
            if diff:
                keep.append(i)

        done.append(i)

    keep.append(inds[-1])
    # Always include smallest watershed
    return group.loc[keep]

if not os.path.exists(os.path.dirname(out_fn)):
    raise FileNotFoundError(
        'Directory does not exist: {}'.format(out_fn))

# Speed up set operations
shapely.speedups.enable()

# Set study region
latlon_crs = {'init': 'epsg:4326'}
#-125., 32., -114., 43.
bbox = gpd.GeoDataFrame(
    pd.DataFrame(),
    geometry=[shapely.geometry.box(-125., 32., -114., 43.)],
    crs = latlon_crs)

# Load landslide data
slide_df = pd.read_csv(slide_path)
slide = gpd.GeoDataFrame(
    slide_df.drop(['longitude', 'latitude'], axis=1),
    crs=latlon_crs,
    geometry = [
        shapely.geometry.Point(xy)
        for xy in zip(slide_df.longitude, slide_df.latitude)])
slide = slide.loc[slide.geometry.within(bbox.geometry[0])]

# Load basin data
gagesii = gpd.read_file(gagesii_path, bbox=bbox)
gagesii['GAGE_ID'] = pd.to_numeric(gagesii['GAGE_ID'])
# Filter basins with active record
# (skip this before downloading discharge records)
active = pd.read_csv('data/gages_active.txt', index_col='site_no')
gagesii = gagesii.join(active, on='GAGE_ID', how='inner')

# Match projections
slide = slide.to_crs(gagesii.crs)

# Buffer landslide locations
slide['geometry'] = slide.apply(buffer_slide, axis=1)

# Find basins overlapping the buffer
watersheds = gpd.overlay(slide, gagesii, how='intersection')

# Remove nested watersheds
watersheds = watersheds.groupby('OBJECTID').apply(remove_nested)

# Save results
pd.DataFrame(watersheds).to_csv(
    out_fn, columns=['OBJECTID', 'GAGE_ID'], index=False)
