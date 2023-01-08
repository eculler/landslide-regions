import geopandas a gpd
import logging
import yaml
import shutil, os, sys
import Nio
import numpy as np
import ogr
import pandas as pd
import netCDF4 as nc4
import xarray as xr

burn_out_fn = 'out/slide_modisburndate.csv'
data_dir = '/projects/elcu4811/burn.preprocess/data/'
slide_fn = os.path.join(data_dir, 'SLIDE_NASA_GLC/GLC20180821.csv')
burn_fn = os.path.join('out/netcdf/MCD64A1.utm.nc')



def add_month_to_dataset(ds):
    month = int(os.path.basename(ds.encoding['source'])[9:16])
    ds.expand_dims({'month': [month]})

def extract_buffer(row):
    # Find index of closest location
    loc_i = kdt.query((row.longitude, row.latitude))[1]
    print('Location index: {}'.format(loc_i))
    print('Location: {}, {}'.format(row.longitude, row.latitude))
    print('Closest cell: {}, {}'.format(xv[loc_i], yv[loc_i]))
    print('Closest index: {}, {}'.format(xi[loc_i], yi[loc_i]))

    # Pull buffer
    in_radius = row.location_accuracy == 0
    if in_radius:
        radius = row.location_accuracy
        clip_radius = int(np.floor(radius / 500)) # km -> grid

        # Clip
        event_burn = burn.isel(
            longitude=slice(xi[loc_i] - (clip_radius + 2),
                            xi[loc_i] + (clip_radius + 2)),
            latitude=slice(yi[loc_i] - (clip_radius + 2),
                           yi[loc_i] + (clip_radius + 2)))


        # Find points within radius using flat earth approximation
        r = 6356
        event_precip = event_precip.where(
            ((r * (burn.y  - yv[loc_i]) * np.pi / 180)**2 +
             (r * (burn.x - xv[loc_i]) * np.pi / 180 * np.cos(burn.y))**2)
            <= radius**2,
            drop=True)

        in_radius = (event_burn.sizes['x'] > 1 or
                     event_burn.sizes['y'] > 1)

        if in_radius:
            # Calculate total number of grid cells in radius
            burn_array = event_burn.isel(month=0).Band1
            total = np.count_nonzero(~np.isnan(burn_array))

    # Get the nearest grid cell if the radius does not include any
    if not in_radius:
        event_burn = burn.sel(
            longitude = xv[loc_i], latitude = yv[loc_i])
        total = 1.

    event_burn = event_burn.where(event_burn.Band1 >= 1, drop=True)
    event_burn = event_burn.to_dataframe().dropna(subset=['Band1'])

    # Aggregate
    event_burn.reset_index(inplace=True)
    fraction = event_burn.groupby(['month', 'burn_date']).size() / total
    fraction = fraction.to_frame('fraction')

    # Add location identifier to the index
    fraction['OBJECTID'] = i
    fraction = fraction.set_index(['OBJECTID'], append=True)
    event_dfs.append(fraction)

if __name__ == '__main__':
    if not os.path.exists(os.path.dirname(burn_out_fn)):
        raise FileNotFoundError(
            'Directory does not exist: {}'.format(burn_out_fn))

    # Load landslide data
    slide_df = pd.read_csv(slide_fn)
    slide = gpd.GeoDataFrame(
        slide_df.drop(['longitude', 'latitude'], axis=1),
        crs={'init': 'epsg:4326'},
        geometry = [
            shapely.geometry.Point(xy)
            for xy in zip(slide_df.longitude, slide_df.latitude)])
    slide = slide.loc[slide.geometry.within(bbox.geometry[0])]

     # Filter Landslides to study area
    slide = slide[slide.latitude > -50]
    slide = slide[slide.latitude < 50]

    # Open burn dataset
    files = glob.glob(burn_fn)
    files.sort()
    burn = xr.open_mfdataset(
        files, combine='nested', concat_dim='month', coords='minimal',
        chunks={'latitude': 50, 'longitude': 50},
        preprocess = add_month_to_dataset)

    # Build KD-Tree
    xv, yv = np.meshgrid(burn.x.values, burn.y.values)
    xv = xv.flatten()
    yv = yv.flatten()
    xi, yi = np.indices((burn.sizes['x'],
                         burn.sizes['y']))
    xi = xi.flatten('F')
    yi = yi.flatten('F')

    kdt = cKDTree(np.dstack((xv, yv))[0])

    event_dfs = []

    pool = multiprocessing.Pool()
    pool.map(extract_buffer, slide.iterrows())

    event_df = pd.concat(event_dfs)

    event_df.to_csv(burn_out_fn)
    print(event_df.sort_index().head())
