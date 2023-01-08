docker build --tag=gis .
docker run --rm -itp 4000:8786 \
  --security-opt seccomp=unconfined \
  -v ~/Documents/landslide/data/SLIDE_NASA_GLC:/gis/data/SLIDE_NASA_GLC \
  -v /mnt/wddata/landslide_data/PRECIP_CHIRPS:/gis/data/PRECIP_CHIRPS \
  -v ~/Documents/landslide/regions/data/processed:/gis/out \
  -t gis:latest \
  gdb -ex r --args python3 src/precip_global.py
