# A Data-driven Evaluation of Post-wildfire Landslide Hazards

Contains the code and configuration files necessary to reproduce a global analysis of landslide-triggering hydrologic conditions. This analysis will be published in the journal NHESS

## Data

This analysis uses the following data with no preprocessing:
  * The NASA Global Landslide Catalog
    - Kirschbaum, D.B., Adler, R., Hong, Y., Hill, S., and Lerner-Lam, A. (2010), A global landslide catalog for hazard applications: method, results, and limitations. Natural Hazards, 52,561-575. doi: 1007/s11069-009-9401-4. 
    - Data accessed from [Global Landslide Catalog Downloadable Products Gallery](https://maps.nccs.nasa.gov/arcgis/apps/MapAndAppGallery/index.html?appid=574f26408683485799d02e857e5d9521)
    - Data should be placed in `00-data` > `raw` > `GLC20201204.csv` to run the `02-analysis` > `glc.Rmd` notebook  without modifications
    
This analysis uses the following data preprocessed to extract values at landslide locations and calculat precipitation percentile:
  * MODIS Burned Area (Global, 2004-2019)
    - Giglio, L., Justice, C., Boschetti, L., Roy, D. (2015). <i>MCD64A1 MODIS/Terra+Aqua Burned Area Monthly L3 Global 500m SIN Grid V006</i> [Data set]. NASA EOSDIS Land Processes DAAC. Accessed 2019-12-04 from https://doi.org/10.5067/MODIS/MCD64A1.006
    - Data accessed from [OPeNDAP](https://lpdaac.usgs.gov/tools/opendap/)
  * CHIRPS Precipitation
    - Funk, C.C., Peterson, P.J., Landsfeld, M.F., Pedreros, D.H., Verdin, J.P., Rowland, J.D., Romero, B.E., Husak, G.J., Michaelsen, J.C., and Verdin, A.P., 2014, A quasi-global precipitation time series for drought monitoring: U.S. Geological Survey Data Series 832, 4 p. ftp://chg-ftpout.geog.ucsb.edu/pub/org/chg/products/CHIRPS-2.0/docs/USGS-DS832.CHIRPS.pdf
    - Data accessed from the [University of California Santa Barbara](https://data.chc.ucsb.edu/products/CHIRPS-2.0/)
  * Daymet Daily Surface Weather Data Precipitation and Snow Water Equivalent (SWE)
    - Thornton, M.M., R. Shrestha, Y. Wei, P.E. Thornton, S-C. Kao, and B.E. Wilson. 2022. Daymet: Daily Surface Weather Data on a 1-km Grid for North America, Version 4 R1. ORNL DAAC, Oak Ridge, Tennessee, USA. https://doi.org/10.3334/ORNLDAAC/2129
    - Data accessed from the [Oak Ridge National Laboratory DAAC](https://daac.ornl.gov/cgi-bin/dsviewer.pl?ds_id=2129)
  
The [preprocessed dataset are available from zenodo](https://doi.org/10.5281/zenodo.7653639) and should be placed in `00-data` > `processed` to runthe `02-analysis` > `glc.Rmd` notebook  without modifications

## To run:

Some preprocessing steps are performed using the land-surface-modeling-utilities package using configuration files in `01-preprocessing/cfg`:
  * Mosaicing, reprojecting, and converting MODIS Burned Area data to netCDF format
  * Downloading Daymet data over THREDDS

Additional pre-processing was performed using command line utilities `cdo`, `ncrcat`, and `ncks`. Instructions are included in `01-preprocessing/bash-instructions`:
  * Clipping, concatenating, and calculating percentiles of CHIRPS data

Python scripts may be run in a docker container duplicated using the supplied `Dockerfile` and `environment.yml`. Example run scripts are provided in `01-preprocessing/bin`:
  * `burn_global.py` determines if a fire has occurred nearby the landslide site
  * `precip_dayment.py` and `precip_global.py` files determine the timeline of antecedent precipitation for various datasets
  * `precip_frequency.py` calculates a rolling window of precipitation frequency
  * `swe_dayment.py` determines the timeline of antecedent SWE at landslide sites
  * `precip_global_monthly.py` determines precipitation climatology at landslide sites

Further analysis of the preprocessed data is performed using an RMarkdown file available at `02-analysis/glc.Rmd`. `02-analysis/glc.html` contains the knitted analysis.

