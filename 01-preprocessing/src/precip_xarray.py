import logging
import yaml
import shutil, os, sys
import numpy as np
import pandas as pd
import xarray as xr

slide_fn = '../data/SLIDE_NASA_GLC/GLC20180821.csv'
out_fn = 'processed/glc_precip_buffer.csv'

if __name__ == '__main__':
    if not os.path.exists(os.path.dirname(out_fn)):
        raise FileNotFoundError(
            'Directory does not exist: {}'.format(out_fn))
    slide = pd.read_csv(slide_fn,
                        index_col='OBJECTID')

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

    # Open precipitation files
    precip = xr.open_dataset('data/chirps/chirps-v2.0.days_p05.nc')

    # Add precipitation to dataframe
    event_dfs = []
    count = 0
    for index, row in slide.iterrows():
        print(count)
        count += 1

        # Pull out precipitation values for location
        event_precip = precip.sel(
            latitude = row.latitude,
            longitude = row.longitude,
            method='nearest'
        ).to_dataframe()

        if row['location_accuracy'] in ('exact', 'unknown'):
            in_radius = False
        else:
            level = int(row['location_accuracy'][:-2])
            radius = level / 111.5 # convert km to degrees

            # Pull data
            event_precip = precip.where(
                ((precip.longitude - row['longitude'])**2 +
                 (precip.latitude - row['latitude'])**2 <= radius**2),
                drop=True)

            in_radius = event_precip.precip.size > 0


        if not in_radius:
            event_precip = precip.sel(
                latitude = row.latitude,
                longitude = row.longitude,
                method='nearest'
            )

        # Aggregate
        event_precip = event_precip.to_dataframe().groupby(['time']).mean()

        # Eliminate null values
        event_precip[event_precip.precip < 0] = np.nan

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

    precip = pd.concat(event_dfs)
    precip.to_csv(out_fn)
    print(precip.sort_index().head())
