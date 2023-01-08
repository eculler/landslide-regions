docker build --tag=gis .
docker run --rm -itp 4000:8786 \
  -v ~/Documents/landslide/data/SLIDE_NASA_GLC:/gis/data/SLIDE_NASA_GLC \
  -v ~/Documents/landslide/regions/data/raw/daymet/prcp:/gis/data/daymet/prcp \
  -v ~/Documents/landslide/regions/data/processed:/gis/out \
  -t gis:latest \
  python3 src/precip_daymet.py
