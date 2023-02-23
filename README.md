# A Data-driven Evaluation of Post-wildfire Landslide Hazards

Contains the code and configuration files necessary to reproduce a global analysis of landslide-triggering hydrologic conditions. This analysis will be published in the journal NHESS.

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

## Software
This analysis uses the following software:
  - Becker OScbRA, Minka ARWRvbRBEbTP, Deckmyn. A (2021). _maps: Draw Geographical Maps_. R package version 3.4.0, <URL: https://CRAN.R-project.org/package=maps>.
  - Bengtsson H (2021). “A Unifying Framework for Parallel and Distributed Processing in R using Futures.” _The R Journal_, *13*(2), 208-227. doi: 10.32614/RJ-2021-048 (URL: https://doi.org/10.32614/RJ-2021-048), <URL: https://doi.org/10.32614/RJ-2021-048>.
  - Grolemund G, Wickham H (2011). “Dates and Times Made Easy with lubridate.” _Journal of Statistical Software_, *40*(3), 1-25. <URL: https://www.jstatsoft.org/v40/i03/>.
  - Henry L, Wickham H (2020). _purrr: Functional Programming Tools_. R package version 0.3.4, <URL: https://CRAN.R-project.org/package=purrr>.
  - Hoyer, S. & Hamman, J., (2017). xarray: N-D labeled Arrays and Datasets in Python. Journal of Open Research Software. 5(1), p.10. DOI: https://doi.org/10.5334/jors.148
  - Maechler M, Rousseeuw P, Struyf A, Hubert M, Hornik K (2022). _cluster: Cluster Analysis Basics and Extensions_. R package version 2.1.3 - For new features, see the 'Changelog' file (in the package source), <URL: https://CRAN.R-project.org/package=cluster>.
  - Makowski D, Lüdecke D, Patil I, Thériault R (2023). “Automated Results Reporting as a Practical Tool to Improve Reproducibility and Methodological Best Practices Adoption.” _CRAN_. <URL: https://easystats.github.io/report/>.
  - McKinney, W., & others. (2010). Data structures for statistical computing in python. In Proceedings of the 9th Python in Science Conference (Vol. 445, pp. 51–56).
  - Müller K, Wickham H (2021). _tibble: Simple Data Frames_. R package version 3.1.5, <URL: https://CRAN.R-project.org/package=tibble>.
  - Neuwirth E (2014). _RColorBrewer: ColorBrewer Palettes_. R package version 1.1-2, <URL: https://CRAN.R-project.org/package=RColorBrewer>.
  - Pebesma E (2018). “Simple Features for R: Standardized Support for Spatial Vector Data.” _The R Journal_, *10*(1), 439-446. doi: 10.32614/RJ-2018-009 (URL: https://doi.org/10.32614/RJ-2018-009), <URL: https://doi.org/10.32614/RJ-2018-009>.
  - R Core Team (2021). _R: A Language and Environment for Statistical Computing_. R Foundation for Statistical Computing, Vienna, Austria. <URL: https://www.R-project.org/>.
  - Robinson D, Hayes A, Couch S (2021). _broom: Convert Statistical Objects into Tidy Tibbles_. R package version 0.7.9, <URL: https://CRAN.R-project.org/package=broom>.
  - Van Rossum, G., & Drake, F. L. (2009). Python 3 Reference Manual. Scotts Valley, CA: CreateSpace.
  - Vaughan D, Dancho M (2022). _furrr: Apply Mapping Functions in Parallel using Futures_. R package version 0.3.1, <URL: https://CRAN.R-project.org/package=furrr>.
  - Walker K (2022). _tigris: Load Census TIGER/Line Shapefiles_. R package version 1.6.1, <URL: https://CRAN.R-project.org/package=tigris>.
  - Wickham H (2016). _ggplot2: Elegant Graphics for Data Analysis_. Springer-Verlag New York. ISBN 978-3-319-24277-4, <URL: https://ggplot2.tidyverse.org>.
  - Wickham H (2019). _stringr: Simple, Consistent Wrappers for Common String Operations_. R package version 1.4.0, <URL: https://CRAN.R-project.org/package=stringr>.
  - Wickham H (2021). _forcats: Tools for Working with Categorical Variables (Factors)_. R package version 0.5.1, <URL: https://CRAN.R-project.org/package=forcats>.
  - Wickham H (2021). _tidyr: Tidy Messy Data_. R package version 1.1.4, <URL: https://CRAN.R-project.org/package=tidyr>.
  - Wickham H, Averick M, Bryan J, Chang W, McGowan LD, François R, Grolemund G, Hayes A, Henry L, Hester J, Kuhn M, Pedersen TL, Miller E, Bache SM, Müller K, Ooms J, Robinson D, Seidel DP, Spinu V, Takahashi K, Vaughan D, Wilke C, Woo K, Yutani H (2019). “Welcome to the tidyverse.” _Journal of Open Source Software_, *4*(43), 1686. doi: 10.21105/joss.01686 (URL: https://doi.org/10.21105/joss.01686).
  - Wickham H, François R, Henry L, Müller K (2021). _dplyr: A Grammar of Data Manipulation_. R package version 1.0.7, <URL: https://CRAN.R-project.org/package=dplyr>.
  - Wickham H, Hester J (2021). _readr: Read Rectangular Text Data_. R package version 2.0.2, <URL: https://CRAN.R-project.org/package=readr>.
  - Wickham H, Pedersen T (2019). _gtable: Arrange 'Grobs' in Tables_. R package version 0.3.0, <URL: https://CRAN.R-project.org/package=gtable>.
  - Wickham H, Seidel D (2020). _scales: Scale Functions for Visualization_. R package version 1.1.1, <URL: https://CRAN.R-project.org/package=scales>.
  - Wilke C (2020). _cowplot: Streamlined Plot Theme and Plot Annotations for 'ggplot2'_. R package version 1.1.1, <URL: https://CRAN.R-project.org/package=cowplot>.
  - Zeileis A, Grothendieck G (2005). “zoo: S3 Infrastructure for Regular and Irregular Time Series.” _Journal of Statistical Software_, *14*(6), 1-27. doi: 10.18637/jss.v014.i06 (URL: https://doi.org/10.18637/jss.v014.i06).


