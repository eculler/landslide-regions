from dask.distributed import Client
from functools import partial
import glob
import logging
import Nio
import multiprocessing
import numpy as np
import ogr
import os
import pandas as pd
import netCDF4 as nc4
import shapely.geometry
import shutil
import sys
import xarray as xr
import yaml

data_dir = 'gis/data/burn'
burn_out_fn = os.path.join(data_dir, 'out/slide_modisburndate.csv')
slide_fn = os.path.join(data_dir, 'data/SLIDE_NASA_GLC/GLC20180821.csv')
burn_fn = os.path.join(data_dir, 'out/netcdf/MCD64A1.*.nc')



def add_month_to_dataset(ds):
    month = int(os.path.basename(ds.encoding['source'])[9:16])
    return ds.expand_dims({'month': [month]})

def extract_buffer(row, ds, nslide):
    i = row[0]
    row = row[1]
    objectid = row.OBJECTID

    # Find index of closest location
    xi = np.argmin(np.abs(ds.lon.values - row.longitude))
    yi = np.argmin(np.abs(ds.lat.values - row.latitude))
    logging.info('Extracting landslide {} of {} with ID {}'.format(
            i, nslide, objectid))
    logging.debug('Location: {}, {}'.format(row.longitude, row.latitude))
    logging.debug('Closest index: {}, {}'.format(xi, yi))
    logging.debug('Closest cell: {}, {}'.format(
        ds.lon.values[xi], ds.lat.values[yi]))
    logging.debug('Location accuracy: {} km'.format(row.location_accuracy))

    # Pull buffer
    in_radius = (row.location_accuracy > 0)
    if in_radius:
        radius = row.location_accuracy
        clip_radius = int(np.floor(radius*2)) # km -> grid

        # Clip
        event_ds = ds.isel(
            lon=slice(xi - (clip_radius + 2),
                      xi + (clip_radius + 2)),
            lat=slice(yi - (clip_radius + 2),
                      yi + (clip_radius + 2)))

        # Find points within radius using flat earth approximation
        event_ds = event_ds.where(
            ( (event_ds.lat - ds.lat.values[yi]) * np.pi / 180)**2 +
            ( (event_ds.lon - ds.lon.values[xi]) * np.pi / 180 * 
                   np.cos(ds.lat.values[yi]) )**2
            <= radius**2,
            drop=True)

        in_radius = (event_ds.sizes['lon'] > 1 or
                     event_ds.sizes['lat'] > 1)
        if in_radius:
            # Calculate total number of grid cells in radius
            ds_array = event_ds.isel(month=0).Band1
            total = np.count_nonzero(~np.isnan(ds_array))

    # Get the nearest grid cell if the radius does not include any
    if not in_radius:
        event_ds = ds.isel(lon = xi, lat = yi)
        total = 1.

    event_ds = event_ds.where(event_ds.Band1 >= 1, drop=True)
    event_ds = event_ds.to_dataframe().dropna(subset=['Band1'])

    # Aggregate
    event_ds.reset_index(inplace=True)
    fraction = event_ds.groupby(['month', 'Band1']).size() / total
    fraction = fraction.to_frame('fraction')

    # Add location identifier to the index
    fraction['OBJECTID'] = objectid
    fraction = fraction.set_index(['OBJECTID'], append=True)

    # Save results
    logging.debug(fraction)
    fraction.to_csv(burn_out_fn, mode='a', header=False)


if __name__ == '__main__':
    start = int(sys.argv[-1])
    end = start + 225
    if not os.path.exists(os.path.dirname(burn_out_fn)):
        raise FileNotFoundError(
            'Directory does not exist: {}'.format(burn_out_fn))

    logging.basicConfig(
        level=logging.DEBUG, 
        format="%(asctime)s:%(levelname)s:%(name)s:%(message)s")

    # Load landslide data
    logging.info('Opening landslide dataset')
    slide = pd.read_csv(slide_fn)
    slide.location_accuracy = slide.location_accuracy.apply(
        lambda s: int(s[:-2]) if str(s).endswith('km') else 0
    )

    # Filter Landslides to study requirements
    slide = slide[slide.latitude > 0]
    slide = slide[slide.latitude < 50]
    slide = slide[slide.longitude > -19]
    slide = slide[slide.location_accuracy < 25]
    rain_triggers = ['rain', 'downpour', 'flooding', 'continuous_rain']
    slide = slide[slide.landslide_trigger.isin(rain_triggers)]
    slide['event_date'] = pd.to_datetime(
            slide['event_date'], format='%Y/%m/%d %H:%M')
    slide['event_date'] = slide['event_date'].dt.normalize()
    slide = slide[slide.event_date >= '2003-11-01']
    slide = slide.reset_index(drop=True)

    # Open burn dataset
    logging.info('Opening burn dataset')
    files = glob.glob(burn_fn)
    files.sort()
    logging.debug('\n    '.join(files[0:10]))
    #client = Client()
    burn = xr.open_mfdataset(
        files, combine='nested', concat_dim='month', coords='minimal',
        chunks={'lat': 200, 'lon': 200},
        preprocess = add_month_to_dataset,
        parallel=True)

    # Clear output file
    if not os.path.exists(burn_out_fn):
        with open(burn_out_fn, 'w') as burn_out_file:
            burn_out_file.write('month,burn_date,OBJECTID,fraction\n')
 
    # Extract buffers
    logging.info('Extracting burn values at landslide locations')
    i = 0
    nslide = len(slide.index)

    for i, row in slide.iloc[start:end].iterrows():
        extract_buffer((i, row), ds=burn, nslide=nslide)
