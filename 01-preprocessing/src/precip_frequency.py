import dask
import logging
import shutil, os, sys
from multiprocessing.pool import ThreadPool
import numpy as np
import pandas as pd
import yaml

precip_fn = '/gis/data/glc_precip_global.csv'
out_fn = '/gis/out/glc_precip_frequency.csv'

def window_frequency(yday, event_precip):
    # Select 30-day window
    wet = event_precip.loc[((yday - event_precip.yday) % 365) <= 31]['wet']
    # compute frequency
    return wet.sum() / wet.values.apply(len)

def event_frequencies(grp):
    # Get all values for percentile computation
    # Initialize frequency dataframe
    freq = pd.DataFrame(index = wet.yday.unique())
    freq['end_yday'] = freq.index + 15
    print(freq)

    # Calculate wet days
    grp['wet'] = grp.precip > 0
    freq['wet'] = freq.end_yday.apply(window_frequency, event_precip=grp)

    return freq

if __name__ == '__main__':
    with dask.config.set(scheduler='threads'):
        if not os.path.exists(os.path.dirname(out_fn)):
            raise FileNotFoundError(
                'Directory does not exist: {}'.format(out_fn))

        # Open precipitation files
        print('Load precipitation data')
        precip = pd.read_csv(precip_fn, usecols=[1, 2, 3])
        print(precip)
        precip = pd.concat(list(precip.groupby('OBJECTID'))[:3])
        print(precip)

        # Calculate the number of wet days on each yearday
        wet = precip.group_by(['OBJECTID', 'yday']).sum()
        wet.group_by('OBJECTID').apply(event_frequencies)





        # Add location identifier to the index
        event_precip['OBJECTID'] = index
        event_precip = event_precip.set_index(['OBJECTID'], append=True)

        event_precip.to_csv(out_fn, mode='a', header=count==1)
        print(event_precip.sort_index().head())
