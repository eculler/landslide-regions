import logging
import yaml
import shutil, os, sys
import numpy as np
import pandas as pd
import netCDF4 as nc4

sys.path.append('sediment')
from dataset import GDALDataset

if __name__ == '__main__':
    slide = pd.read_csv('glc_plus_7dayprecip.csv')
    glc_precip = pd.read_csv('glc_precip_no0.csv')
    origen_x = -125
    origen_y = 32
    max_x = -114
    max_y = 43
    res = 0.05
    start_date = pd.to_datetime('2007-01-01', format='%Y-%m-%d')
    end_date = pd.to_datetime('2016-01-01', format='%Y-%m-%d')
    samples = 1
    filename = 'control_precip_wpopnear_log_one_sample.csv'

    # Filter to rainfall induced landslides
    rain_triggers =['rain', 'downpour', 'flooding', 
                    'continuous_rain', 'tropical_cyclone']
    slide = slide.loc[slide['landslide_trigger'].isin(rain_triggers)]
    glc_precip = glc_precip.loc[
        glc_precip['OBJECTID'].isin(slide.OBJECTID)]
    precip_pool = glc_precip[glc_precip.days_before == 0]

    
    # Get allowed coordinates from DEM
    dem_ds = GDALDataset('data/dem/merged-dem_merged_0-00000x0-00000.gtif')    
    dem = dem_ds.array
    lons, lats = np.meshgrid(dem_ds.cgrid.lon, dem_ds.cgrid.lat)
    dem_df = pd.DataFrame({
        'longitude': lons.flatten(),
        'latitude': lats.flatten(),
        'elevation': dem.flatten()
    })
    dem_df = dem_df[dem_df.elevation != 0]
    dem_df = dem_df[np.logical_and(dem_df.longitude > origen_x,
                                   dem_df.longitude < max_x)]
    dem_df = dem_df[np.logical_and(dem_df.latitude > origen_y,
                                   dem_df.latitude < max_y)]
    dem_df = dem_df.set_index(['longitude', 'latitude'])

    # Get weights from population dataset
    pop_ds = GDALDataset(('data/population/slide_weighted_near.tif'))   
    pop = pop_ds.array
    pop[pop < 0] = 0
    lons, lats = np.meshgrid(pop_ds.cgrid.lon, pop_ds.cgrid.lat)
    pop_df = pd.DataFrame({
        'longitude': lons.flatten(),
        'latitude': lats.flatten(),
        'population': pop.flatten()
    })
    pop_df = pop_df.set_index(['longitude', 'latitude'])
    print(pop_df.min())
    dem_df = dem_df.join(pop_df, how='left')
    dem_df = dem_df.reset_index()
    
    # Open precipitation files and extract variables
    precip_ds = nc4.Dataset('data/chirps/chirps-v2.0.days_p05.nc')
    precip_pctl_ds = nc4.Dataset(
            'data/chirps/chirps-v2.0.days_p05_no0_pctl.nc')

    precip = precip_ds.variables['precip']
    precip_pctl = precip_pctl_ds.variables['precip']
    precip_time = precip_ds.variables['time']

    for i in range(samples):
        print(i+1)
        # Select random locations
        dem_samples = dem_df.sample(
            len(precip_pool.index),
            weights='population'
        )[['longitude', 'latitude']]

        # Select random precipitation percentiles
        precip_samples = precip_pool.sample(len(precip_pool)).precip_pctl
        dem_samples['precip_pctl'] = precip_samples.values
    
        # Get indices for landslides
        dem_samples['x'] = np.floor(
            (dem_samples['longitude'] - origen_x) / res ).astype(int)
        dem_samples['y'] = np.floor(
            (dem_samples['latitude'] - origen_y) / res ).astype(int)

        sample_dfs = []
        count = 1
        for index, row in dem_samples.iterrows():
            print(count)
        
            # Get index range of dates
            pctl = int(row['precip_pctl'])
            event_inds = (np.array([]),)

            # Correct for 0 precipitation
            precip_pctl_here = precip_pctl[:, 0, row['y'], row['x']]
            precip_pctl_here[0] = 0

            while event_inds[0].size==0:
                print(pctl)
                if pctl < 0:
                    break
                precip_low = precip_pctl_here[pctl]
                precip_high = precip_pctl_here[pctl + 1]
                print(precip_low, precip_high)

                # Limit event date to study duration
                start_ind = nc4.date2index(start_date, precip_time)
                end_ind = nc4.date2index(end_date, precip_time)
                precip_all = precip[start_ind:end_ind, row['y'], row['x']]
                event_inds = np.where(np.logical_and(
                    precip_all >= precip_low, precip_all < precip_high))
                pctl -= 1

            #Just in case there's a nodata value for precipitation
            if event_inds[0].size==0:
                continue
            event_ind_end = int(
                np.random.choice(event_inds[0])) + start_ind + 1
        
            # 3 years before
            event_ind_beg = event_ind_end - 1095

            # Pull out precipitation values
            event_precip = precip[event_ind_beg:event_ind_end,
                                  row['y'], row['x']]
            print(event_precip[-1])
            event_pctl = np.searchsorted(
                    precip_pctl_here,
                    event_precip, side='right') - 1
            print(event_pctl[-1])

            event_df = pd.DataFrame({
                    'precip': event_precip,
                    'precip_pctl': event_pctl,
                    'days_before': range(1094, -1, -1)})
            event_df['event'] = count
            event_df['sample'] = i + 1
            event_df['longitude'] = row['longitude']
            event_df['latitude'] = row['latitude']
            # Convert number to index
            # Dataset starts on 1981-1-1, but measures time from 1980-1-1
            event_df['event_date'] = nc4.num2date(
                    event_ind_end + 366,
                    precip_time.units, precip_time.calendar)

            sample_dfs.append(event_df)
            event_df.to_csv(filename, mode='a', index=False,
                            header=not(os.path.exists(filename)))
            count += 1
        
        sample = pd.concat(sample_dfs)
        sample.reset_index(drop=True, inplace=True)

        #sample.to_csv(filename)
        print(sample.sort_index().head())
