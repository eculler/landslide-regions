# A Data-driven Evaluation of Post-wildfire Landslide Hazards

Contains the code and configuration files necessary to reproduce a global analysis of landslide-triggering hydrologic conditions. This analysis will be published in the journal NHESS

## Data

This analysis uses the following data:
  * The NASA Global Landslide Catalog
  * MODIS Burned Area
  * CHIRPS Precipitation
  * Daymet Precipitation and Snow Water Equivalent (SWE)
  
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

