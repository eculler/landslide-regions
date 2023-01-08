import copy
import dask
import geopandas as gpd
import glob
import logging
from scipy.spatial import cKDTree
import shapely
import shutil, os, sys
import threading
import numpy as np
import pandas as pd
import time
import xarray as xr

data_path = '/gis/data/daymet/prcp/daymet_v3_prcp_*_na.nc'
slide_path = '/gis/data/SLIDE_NASA_GLC/GLC20180821.csv'
out_file = '/gis/out/glc_precip_daymet.csv'

if __name__ == '__main__':

    if not os.path.exists(os.path.dirname(out_file)):
        raise FileNotFoundError('Directory does not exist: {}'.format(out_file))
    # Filter Landslides to study area and duration
    # Set study region
    latlon_crs = {'init': 'epsg:4326'}
    #-125., 32., -114., 43.
    bbox = gpd.GeoDataFrame(
        pd.DataFrame(),
        geometry=[shapely.geometry.box(-125., 32., -114., 43.)],
        crs = latlon_crs)

    # Load landslide data
    slide_df = pd.read_csv(slide_path, index_col='OBJECTID')
    slide = gpd.GeoDataFrame(
        slide_df,
        crs=latlon_crs,
        geometry = [
            shapely.geometry.Point(xy)
            for xy in zip(slide_df.longitude, slide_df.latitude)])
    slide = slide.loc[slide.geometry.within(bbox.geometry[0])]


    slide['event_date'] = pd.to_datetime(
            slide['event_date'], format='%Y/%m/%d %H:%M')
    slide['event_date'] = slide['event_date'].dt.normalize()
    slide = slide[slide.event_date >= '2004-01-01']
    slide = slide[slide.event_date < '2016-01-01']

    # Open files
    files = glob.glob(data_path)
    files.sort()
    precip = xr.open_mfdataset(
        files, combine='nested', concat_dim='time', coords='minimal')

    # Build KD-Tree
    locs = list(zip(precip.lon.isel(time=0).values.flatten(),
                    precip.lat.isel(time=0).values.flatten()))
    kdt = cKDTree(locs)
    xv, yv = np.meshgrid(precip.x.values, precip.y.values)
    xv = xv.flatten()
    yv = yv.flatten()
    xi, yi = np.indices((precip.sizes['x'], precip.sizes['y']))
    xi = xi.flatten()
    yi = yi.flatten()

    # Add precip to dataframe
    event_dfs = []
    count = 0
    for index, row in slide.iterrows():
        print(count)
        count += 1

        # Find index of closest location
        loc_i = kdt.query((row.longitude, row.latitude))[1]

        # Pull buffer
        in_radius = not row['location_accuracy'] in ('exact', 'unknown')
        if in_radius:
            level = int(row['location_accuracy'][:-2])
            radius = level # 1-km grid

            # Clip
            event_precip = precip.isel(
                x=slice(xi[loc_i] - (radius + 1), xi[loc_i] + (radius + 1)),
                y=slice(yi[loc_i] - (radius + 1), yi[loc_i] + (radius + 1)))

            # Pull data
            event_precip = event_precip.where(
                ((precip.x - xv[loc_i])**2 +
                 (precip.y - yv[loc_i])**2) <= radius**2,
                drop=True)
            in_radius = event_precip.prcp.size > 0

            # Take the closest value if the radius contains no data
            if in_radius:
                event_precip = event_precip.mean(dim=['x', 'y'])

        if not in_radius:
            event_precip = precip.sel(x = xv[loc_i], y = yv[loc_i])


        # To DataFrame
        event_precip.prcp.chunk({'time': 'auto'})
        event_precip = pd.DataFrame(
            {'precip': event_precip.prcp.values},
            index = event_precip.time.values)

        # Get all values for percentile computation
        event_precip['yday'] = event_precip.index.dayofyear
        distro = pd.DataFrame(index = event_precip.yday.unique())
        distro['end_doy'] = distro.index + 15

        # Calculate rolling percentiles
        for window in range(1, 8):
            precip_name = 'precip_mm_{}'.format(window)
            pctl_name = 'precip_pctl_{}'.format(window)

            # Calculate rolling sum
            event_precip[
                precip_name] = event_precip.precip.rolling(window).sum()

            # Extract precipitation values from window
            sorted = event_precip[
                event_precip[precip_name] > 0].sort_values(by=precip_name)
            distro['vals'] = distro.end_doy.apply(
                lambda x: sorted.loc[((x - sorted.yday) % 365) <= 31][
                    precip_name].values)
            distro['length'] = distro.vals.apply(len)

            # Compute percentile
            event_precip[pctl_name] = event_precip.groupby(
                'yday')[precip_name].transform(
                    lambda grp: (
                        np.searchsorted(distro.loc[grp.name].vals, grp) /
                        distro.loc[grp.name].length)
            )

        # Add location identifier to the index
        event_precip['OBJECTID'] = index
        event_precip = event_precip.set_index(['OBJECTID'], append=True)
        event_dfs.append(event_precip)

    precip_df = pd.concat(event_dfs)

    precip_df.to_csv(out_file)
    print(precip_df.sort_index().head())
