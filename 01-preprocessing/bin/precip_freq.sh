docker build --tag=gis .
docker run --rm -itp 4000:8786 \
  --security-opt seccomp=unconfined \
  -v ~/Documents/landslide/regions/regions_data/processed:/gis/data \
  -v ~/Documents/landslide/regions/data/processed:/gis/out \
  -t gis:latest \
  python3 src/precip_frequency.py
