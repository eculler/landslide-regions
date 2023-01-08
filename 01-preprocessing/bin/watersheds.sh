docker build --tag=gis .
docker run --rm -i \
  -v ~/Documents/landslide/data/SLIDE_NASA_GLC:/gis/data/SLIDE_NASA_GLC \
  -v /Volumes/LabShare/GAGESII_reorganize:/gis/data/GAGESII \
  -v ~/Documents/landslide/regions/data/processed:/gis/out \
  -t gis:latest \
  python3 src/watershed.py
