import dask
import glob
import logging
from scipy.spatial import cKDTree
import shutil, os, sys
from multiprocessing.pool import ThreadPool
import numpy as np
import pandas as pd
import xarray as xr
import yaml

slide_fn = '/gis/data/SLIDE_NASA_GLC/GLC20180821.csv'
precip_fn = '/gis/data/PRECIP_CHIRPS/chirps-v2.0.*.days_p05.nc'
out_fn = '/gis/out/glc_precip_global.csv'

if __name__ == '__main__':
    with dask.config.set(scheduler='threads'):
        if not os.path.exists(os.path.dirname(out_fn)):
            raise FileNotFoundError(
                'Directory does not exist: {}'.format(out_fn))

        # Load landslide data
        print('Load landslide data')
        slide = pd.read_csv(
            slide_fn, index_col='OBJECTID', parse_dates=['event_date'])
        slide.location_accuracy = slide.location_accuracy.apply(
            lambda s: int(s[:-2]) if str(s).endswith('km') else 0
        )

        # Filter landslides to match precipitation extent
        slide = slide[slide.latitude > -50]
        slide = slide[slide.latitude < 50]

        # Open precipitation files
        print('Load precipitation data')
        files = glob.glob(precip_fn)
        files.sort()
        precip = xr.open_mfdataset(
            files, combine='nested', concat_dim='time', coords='minimal',
            chunks={'latitude': 10, 'longitude': 10})

        # Build KD-Tree
        print('Build KD-Tree')
        xv, yv = np.meshgrid(precip.longitude.values, precip.latitude.values)
        xv = xv.flatten()
        yv = yv.flatten()
        xi, yi = np.indices((precip.sizes['longitude'],
                             precip.sizes['latitude']))
        xi = xi.flatten('F')
        yi = yi.flatten('F')

        kdt = cKDTree(np.dstack((xv, yv))[0])

        # Add precipitation to dataframe
        event_dfs = []
        count = 0
        for index, row in slide.iterrows():
            print('Selecting location {}'.format(count))
            count += 1

            # Find index of closest location
            loc_i = kdt.query((row.longitude, row.latitude))[1]
            print('Location index: {}'.format(loc_i))
            print('Location: {}, {}'.format(row.longitude, row.latitude))
            print('Closest cell: {}, {}'.format(xv[loc_i], yv[loc_i]))
            print('Closest index: {}, {}'.format(xi[loc_i], yi[loc_i]))

            # Pull buffer
            in_radius = row.location_accuracy > 0
            if in_radius:
                radius = row.location_accuracy / 111.5 # convert km to degrees
                clip_radius = int(np.floor(radius * 20)) # convert degrees to grid

                # Clip
                event_precip = precip.isel(
                    longitude=slice(xi[loc_i] - (clip_radius + 1),
                                    xi[loc_i] + (clip_radius + 1)),
                    latitude=slice(yi[loc_i] - (clip_radius + 1),
                                   yi[loc_i] + (clip_radius + 1)))

                # Pull data
                event_precip = event_precip.where(
                    ((precip.longitude - xv[loc_i])**2 +
                     (precip.latitude - yv[loc_i])**2) <= radius**2,
                    drop=True)

                in_radius = (event_precip.sizes['longitude'] > 1 or
                             event_precip.sizes['latitude'] > 1)

                # Take the closest value if the radius contains no data
                if in_radius:
                    event_precip = event_precip.mean(
                        dim=['longitude', 'latitude'],
                        keep_attrs=True)

            if not in_radius:
                event_precip = precip.sel(
                    longitude = xv[loc_i], latitude = yv[loc_i])

            # To DataFrame
            event_precip = event_precip.chunk({'time': 'auto'})
            event_precip = pd.DataFrame(
                {'precip': event_precip.precip.values},
                index = event_precip.time.values)


            # Get all values for percentile computation
            event_precip['yday'] = event_precip.index.dayofyear
            distro = pd.DataFrame(index = event_precip.yday.unique())
            distro['end_doy'] = distro.index + 15

            for window in range(1, 8):
                precip_name = 'precip_mm_{}'.format(window)
                pctl_name = 'precip_pctl_{}'.format(window)

                # Calculate rolling sum
                event_precip[
                    precip_name] = event_precip.precip.rolling(window).sum()

                # Put values in order to facilitate percentile
                # Percentile value excludes 0
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

            event_precip.to_csv(out_fn, mode='a', header=count==1)
            print(event_precip.sort_index().head())
