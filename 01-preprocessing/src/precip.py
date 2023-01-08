import logging
import yaml
import shutil, os, sys
import numpy as np
import pandas as pd
import netCDF4 as nc4


if __name__ == '__main__':
    slide = pd.read_csv('../data/SLIDE_NASA_GLC/GLC20180821.csv')
    origen_x = -125
    origen_y = 32
    res = 0.05

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
    precip_ds = nc4.Dataset('data/chirps/chirps-v2.0.days_p05.nc')
    precip_pctl_ds = nc4.Dataset(
            'data/chirps/chirps-v2.0.days_p05_no0_pctl.nc')

    precip = precip_ds.variables['precip']
    precip_pctl = precip_pctl_ds.variables['precip']
    precip_time = precip_ds.variables['time']

    # Get indices for landslides
    slide['x'] = np.floor( (slide['longitude'] - origen_x) / res
            ).astype(int)
    slide['y'] = np.floor( (slide['latitude'] - origen_y) / res
            ).astype(int)

    event_dfs = []
    count = 1
    for index, row in slide.iterrows():
        count += 1
        # Get index of date
        event_ind = nc4.date2index(row[['event_date']], precip_time)


        # Pull out precipitation values
        event_precip = precip[:, row['y'],row['x']]
        # Eliminate null values
        if np.count_nonzero(event_precip < 0) > 10:
            continue
        event_precip[event_precip < 0] = 0

        # Correct for 0 precipitation
        precip_pctl_here = precip_pctl[:, 0, row['y'], row['x']]
        precip_pctl_here[0] = 0

        event_pctl = np.searchsorted(
                    precip_pctl_here,
                    event_precip, side='right') - 1

        # Maximum value is still the 99th percentile
        event_pctl[event_pctl==100] = 99

        event_df = pd.DataFrame({'precip': event_precip,
                                 'precip_pctl': event_pctl,
                                 'days_before': event_ind - len(event_precip)})
        event_df['OBJECTID'] = row['OBJECTID']

        event_dfs.append(event_df)

    precip = pd.concat(event_dfs)
    precip.reset_index(drop=True, inplace=True)

    precip.to_csv('glc_precip_alldates.csv', index=False)
    print(precip.sort_index().head())
