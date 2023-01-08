import logging
import yaml
import shutil, os, sys
import numpy as np
import pandas as pd
from osgeo import gdal, osr, ogr
import netCDF4 as nc4

sys.path.append('sediment')
from calibrate import CaseCollection
from utils import CoordProperty
from operation import LatLonToShapefileOp
from sequence import run_cfg
from path import Path

burn_out_fn = 'slide_modisburn.csv'
slide_fn = '../data/SLIDE_NASA_GLC/GLC20180821.csv'
burn_fn = '../data/FIRE_MODIS/MCD64A1.utm{zone}.nc'

def get_values(name, group):
    ds = gdal.Open(name)
    geot = ds.GetGeoTransform()
    origen_x = geot[0]
    origen_y = geot[3]
    res_x = geot[1]
    res_y = geot[5]
    index_x = np.floor( (group['longitude'] - origen_x) / res_x
            ).astype(int)
    index_y = np.floor( (group['latitude'] - origen_y) / res_y
            ).astype(int)
    return ds, index_x, index_y


if __name__ == '__main__':
    # Process DEM
    #case = run_cfg('ca_stat_slope_cfg.yaml')
    slide = pd.read_csv(slide_fn, index_col='OBJECTID')
    #slide = slide[slide.days_before==0]
    #print(len(slide))

    # Filter Landslides to study area and duration
    slide = slide[slide.latitude > 32]
    slide = slide[slide.latitude < 43]
    slide = slide[slide.longitude > -125]
    slide = slide[slide.longitude < -114]
    #print(len(slide))

    slide['event_date'] = pd.to_datetime(
            slide['event_date'], format='%Y/%m/%d %H:%M')
    slide = slide[slide.event_date >= '2007-01-01']
    slide = slide[slide.event_date < '2016-01-01']
    slide['year'] = slide.event_date.dt.year
    slide['month'] = slide.event_date.dt.month
    slide['doy'] = slide.event_date.dt.dayofyear

    # Make sure to get all original columns at the end
    columns = list(slide)

    """
    # Add slope column
    slope_fn_fmt = ( 'data/slope/agg/'
                     'N{abs_min_lat:02d}'
                     'W{abs_min_lon:03d}'
                     '_reprojected_reprojected_0-00028x0-00028'
                     '_slope_slope_reprojected_reprojected_scaled-'
                     'dem_aggregated.gtif')

    slide['abs_min_lat'] = np.abs(np.floor(slide['latitude']))
    slide['abs_min_lon'] = np.abs(np.floor(slide['longitude']))
    slide['slope_fn'] = slide[['abs_min_lat', 'abs_min_lon']].apply(
            lambda x: slope_fn_fmt.format(
                    abs_min_lat= int(x[0]), abs_min_lon=int(x[1])), axis=1)

    grouped = slide.groupby('slope_fn')
    with_slope = []
    for name, group in grouped:
        ds, index_x, index_y = get_values(name, group)
        group['slope'] = ds.GetRasterBand(1).ReadAsArray()[
                index_x, index_y]
        with_slope.append(group)
        del ds
    slide = pd.concat(with_slope)


    # Add percent clay column
    clay_fn_fmt = ( 'data/clay/agg/'
                    'lat{min_lat}{max_lat}_lon{min_lon}{max_lon}'
                    '_scaled-clay_aggregated_0-00028x0-00028.gtif')

    slide['min_lat'] = np.floor(slide['latitude'])
    slide['min_lon'] = np.floor(slide['longitude'])
    slide['max_lat'] = np.ceil(slide['latitude'])
    slide['max_lon'] = np.ceil(slide['longitude'])
    slide['clay_fn'] = slide[['min_lat', 'max_lat', 'min_lon', 'max_lon']
            ].apply(
                    lambda x: clay_fn_fmt.format(
                            min_lat=int(x[0]), max_lat=int(x[1]),
                            min_lon=int(x[2]), max_lon=int(x[3])), axis=1)

    grouped = slide.groupby('clay_fn')
    with_clay = []
    for name, group in grouped:
        ds, index_x, index_y = get_values(name, group)
        group['clay'] = ds.GetRasterBand(1).ReadAsArray()[
                index_x, index_y]
        with_clay.append(group)
        del ds
    slide = pd.concat(with_clay)

    # Add Soil Moisture
    # Open precipitation files and extract variables
    sm_ds = nc4.Dataset('data/noah/NLDAS_NOAH0125_time.nc')

    sm = sm_ds.variables['var86_SOILM']
    sm_time = sm_ds.variables['time']
    print(sm_time)

    origen_x = -125
    origen_y = 32
    res = 0.125
    slide['x'] = np.floor(
            (slide['longitude'] - origen_x) / res ).astype(int)
    slide['y'] = np.floor(
            (slide['latitude'] - origen_y) / res ).astype(int)
    slide['event_date'] = slide.event_date.dt.normalize()
    print(slide[['event_date']].head())

    def get_ind(date):
        try:
            return nc4.date2num(date, sm_time.units, sm_time.calendar)
        except ValueError:
            return np.nan

    slide['sm_ind'] = slide[['event_date']].apply(
        lambda x: get_ind(x[0]), axis=1)
    print(slide[['event_date', 'sm_ind']]).loc[np.isnan(slide.sm_ind)]

    print(sm_ds.dimensions['lat'])
    print(sm_ds.dimensions['lon'])
    slide['soil_moisture'] = slide[['sm_ind', 'x', 'y']].apply(
        lambda x: sm[x[0], x[1], x[2]], axis=1)

    # Add antecedent precipitation column
    precip_fn_fmt = ('NETCDF:"../data/PRECIP_CHIRPS/'
                     'chirps-v2.0.{year}.days_p05.nc":precip')
    slide['precip_fn'] = slide[['year']].apply(
            lambda x: precip_fn_fmt.format(year=x[0]), axis=1)
    slide['precip_prev_fn'] = slide[['year']].apply(
            lambda x: precip_fn_fmt.format(year=x[0]-1), axis=1)
    slide['band'] = (slide.event_date -
                         pd.to_datetime(slide.year.astype(str) + '0101')
                         ).dt.days + 1
    slide['band_prev'] = (
            pd.to_datetime((slide.year - 1).astype(str) + '1231') -
            pd.to_datetime((slide.year - 1).astype(str) + '0101')
                         ).dt.days + 1
    print(slide.head())

    grouped = slide.groupby('precip_fn')
    with_precip = []
    days = 30

    def get_precip(dataset, prev, band_i, index_x, index_y, band, day):
        if band <= day:
            dataset = prev
        return dataset.GetRasterBand(
                band_i).ReadAsArray(index_x, index_y, 1, 1)[0, 0]

    for name, group in grouped:
        print(name)
        ds, index_x, index_y = get_values(name, group)
        ds_prev = gdal.Open(group['precip_prev_fn'].iloc[0])
        group['index_x'] = index_x
        group['index_y'] = index_y
        group['precip'] = 0
        # Read values one at a time - these files are too big
        for day in range(days):
            group['band_i'] = group[['band', 'band_prev']].apply(
                lambda x: x[0] - day if x[0] > day else x[1] + x[0] - day,
                axis=1)
            print(group)
            group['precip'] = (group['precip'] +
                group[['band_i', 'index_x', 'index_y', 'band']].apply(
                lambda x: get_precip(ds, ds_prev,
                                     x[0], x[1], x[2], x[3], day),
                axis=1))
        with_precip.append(group)
        del ds

    slide = pd.concat(with_precip)
    """
    # Define location accuracy masks
    levels = [1, 5, 10, 25, 50, 100]
    masks = {}
    for level in levels:
        radius = level * 1000 / 500
        y, x = np.ogrid[-radius: radius + 1, -radius: radius + 1]
        masks[level] = x**2 + y**2 <= radius**2

    # Indicate UTM zone in dataframe
    slide['zone'] = np.where(slide.longitude < - 120., 10, 11)

    # Define coordinate transformation to match landslide and burn data
    latlon_sr = osr.SpatialReference()
    latlon_sr.ImportFromEPSG(4326)

    for zone, group in slide.groupby('zone'):
        utm_sr = osr.SpatialReference()
        utm_sr.ImportFromEPSG(6329 + zone)
        latlon_to_utm = osr.CoordinateTransformation(latlon_sr, utm_sr)

        # Open burn dataset
        burn_ds = nc4.Dataset(burn_fn.format(zone=zone))

        burn_doy = burn_ds.variables['burn_date']
        burn_month = burn_ds.variables['month']
        burn_east = burn_ds.variables['x'][:]
        burn_north = burn_ds.variables['y'][:]
        x_len = len(burn_east)
        y_len = len(burn_north)
        #print(np.shape(burn_doy))
        #print(x_len, y_len)

        count=1

        for i, row in group.iterrows():
            count += 1

            month = row['month']
            year = row['year']
            date = year * 1000 + row['doy']
            #print i
            #print date

            # Reproject coordinates
            wkt = 'POINT ({lon} {lat})'.format(lon=row['longitude'],
                                               lat=row['latitude'])
            location = ogr.CreateGeometryFromWkt(wkt)
            location.Transform(latlon_to_utm)

            east = location.GetX()
            north = location.GetY()
            #print east, north

            # Get center indices for landslide locations
            x_i = np.argmin(np.abs(burn_east - east))
            y_i = np.argmin(np.abs(burn_north - north))
            #print (north - burn_north[0])/(burn_north[-1] - burn_north[0])
            #print y_i / float(y_len)
            #print (east - burn_east[0])/(burn_east[-1] - burn_east[0])
            #print x_i / float(x_len), '\n'

            # Get min/max month indices for burn dates
            # Include the month when the landslide occurred
            month_max_i = np.searchsorted(
                    burn_month, date, side='right') - 1
            month_min_i = month_max_i - 36
            #print date
            #print month_max_i, month_min_i
            #print burn_doy[month_max_i, x_i, y_i]

            if row['location_accuracy'] in ('exact', 'unknown'):
                burn_values = burn_doy[month_min_i:month_max_i, x_i, y_i]
                # Eliminate burn dates after the landslide
                burn_values[burn_values > row['doy']] = 0
                total = 1.

            else:
                # Get min/max indices for landslide locations
                level = int(row['location_accuracy'][:-2])
                radius = level * 1000 / 500

                x_min_i = x_i - radius if x_i > radius else 0
                x_max_i = x_i + radius if x_i + radius < x_len else x_len
                y_min_i = y_i - radius if y_i > radius else 0
                y_max_i = y_i + radius if y_i + radius < y_len else y_len
                #print x_i, x_min_i, x_max_i
                # Pull data
                burn_values = burn_doy[month_min_i:month_max_i,
                                       x_min_i:x_max_i + 1,
                                       y_min_i:y_max_i + 1]
                #print burn_values

                # Mask
                mask = masks[level]
                #print mask
                # This does not cover edge cases,
                # but the edges are not close to the study area
                total = float(np.count_nonzero(mask))
                burn_values[:,np.invert(mask)] = 0
                #print burn_values

                # Eliminate burn dates after the landslide
                burn_values[-1,:,:][burn_values[-1,:,:] > row['doy']] = 0
                #print burn_values

            # Null fill values
            burn_values[burn_values < 0] = 0
            #print burn_values

            # Collapse burn date to boolean
            burn_values[burn_values > 0] = 1
            #print burn_values

            # Aggregate
            burn_cumulative = np.sum(burn_values) / total
            #print burn_cumulative

            # Store to dataframe
            slide.loc[i, 'burn.cumulative'] = burn_cumulative

    new_cols = ['burn.cumulative']
    burn = slide[new_cols]
    burn.to_csv(burn_out_fn)
    print(burn.head())
