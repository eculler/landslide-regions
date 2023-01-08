import logging
import yaml
import shutil, os, sys
import numpy as np
import pandas as pd
import xarray as xr


if __name__ == '__main__':
    slide = pd.read_csv('../data/SLIDE_NASA_GLC/GLC20180821.csv',
                        index_col='OBJECTID')
    origen_x = -125
    origen_y = 32
    res = 0.05

     # Filter Landslides to study area and duration
    slide = slide[slide.latitude > 32]
    slide = slide[slide.latitude < 43]
    slide = slide[slide.longitude > -125]
    slide = slide[slide.longitude < -114]

    # Open climatology files
    climate = xr.merge([
        xr.open_dataarray('data/livneh/prec.mon.ltm.nc'),
        xr.open_dataset('data/livneh/swe.mon.ltm.nc')
    ])

    # Add precipitation to dataframe
    event_dfs = []
    count = 0
    for index, row in slide.iterrows():
        print(count)
        count += 1
        # Pull out precipitation values for location
        event_climate = climate.sel(
            lat = row.latitude,
            lon = row.longitude % 360,
            method='nearest'
        ).to_dataframe()

        # Add location identifier to the index
        event_climate['OBJECTID'] = index
        event_climate = event_climate.set_index(['OBJECTID'], append=True)
        event_dfs.append(event_climate)

    climate_df = pd.concat(event_dfs)

    climate_df.to_csv('glc_climatology.csv')
    print(climate_df.sort_index().head())
