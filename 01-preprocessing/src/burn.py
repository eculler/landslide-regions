import logging
import yaml
import shutil, os, sys
import numpy as np
import ogr, osr
import pandas as pd
import netCDF4 as nc4
import xarray as xr

burn_out_fn = 'processed/slide_modisburndate.csv'
slide_fn = '../data/SLIDE_NASA_GLC/GLC20180821.csv'
burn_fn = '../data/FIRE_MODIS/MCD64A1.utm{zone}.nc'

if __name__ == '__main__':
    if not os.path.exists(os.path.dirname(burn_out_fn)):
        raise FileNotFoundError(
            'Directory does not exist: {}'.format(burn_out_fn))
    slide = pd.read_csv(slide_fn, index_col='OBJECTID')

     # Filter Landslides to study area and duration
    slide = slide[slide.latitude > 32]
    slide = slide[slide.latitude < 43]
    slide = slide[slide.longitude > -125]
    slide = slide[slide.longitude < -114]

    slide['event_date'] = pd.to_datetime(
            slide['event_date'], format='%Y/%m/%d %H:%M')
    slide['event_date'] = slide['event_date'].dt.normalize()
    slide = slide[slide.event_date >= '2004-01-01']
    slide = slide[slide.event_date < '2016-01-01']

    # Indicate UTM zone in dataframe
    slide['zone'] = np.where(slide.longitude < - 120., 10, 11)

    # Define coordinate transformation to match landslide and burn data
    latlon_sr = osr.SpatialReference()
    latlon_sr.ImportFromEPSG(4326)

    event_dfs = []
    count=1
    for zone, group in slide.groupby('zone'):
        utm_sr = osr.SpatialReference()
        utm_sr.ImportFromEPSG(6329 + zone)
        latlon_to_utm = osr.CoordinateTransformation(latlon_sr, utm_sr)

        # Open burn dataset
        burn_ds = xr.open_dataset(burn_fn.format(zone=zone))

        burn_doy = burn_ds.variables['burn_date']
        burn_month = burn_ds.variables['month']
        burn_east = burn_ds.variables['x'][:]
        burn_north = burn_ds.variables['y'][:]

        for i, row in group.iterrows():
            print(count)
            count += 1

            month = row['month']
            year = row['year']

            # Reproject coordinates
            wkt = 'POINT ({lon} {lat})'.format(lon=row['longitude'],
                                               lat=row['latitude'])
            location = ogr.CreateGeometryFromWkt(wkt)
            location.Transform(latlon_to_utm)
            slide_x = location.GetX()
            slide_y = location.GetY()

            if row['location_accuracy'] in ('exact', 'unknown'):
                event_burn = burn_ds.sel(
                    x=slide_x, y=slide_y, method='nearest')
                total = 1.
            else:
                level = int(row['location_accuracy'][:-2])
                radius = level * 1000

                # Pull data
                event_burn = burn_ds.where(
                    ((burn_ds.x - slide_x)**2 +
                     (burn_ds.y - slide_y)**2 <= radius**2),
                    drop=True)

                # This does not cover edge cases,
                # but the edges are not close to the study area
                burn_array = event_burn.isel(month=0).burn_date
                total = np.count_nonzero(~np.isnan(burn_array))

            event_burn = event_burn.where(event_burn.burn_date >= 1, drop=True)
            event_burn = event_burn.to_dataframe().dropna(subset=['burn_date'])

            # Aggregate
            event_burn.reset_index(inplace=True)
            fraction = event_burn.groupby(['month', 'burn_date']).size() / total
            fraction = fraction.to_frame('fraction')

            # Add location identifier to the index
            fraction['OBJECTID'] = i
            fraction = fraction.set_index(['OBJECTID'], append=True)
            event_dfs.append(fraction)

    event_df = pd.concat(event_dfs)

    event_df.to_csv(burn_out_fn)
    print(event_df.sort_index().head())
