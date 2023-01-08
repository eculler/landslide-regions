cd ~/Documents/lsmutils && docker build --tag=lsmutils ~/Documents/lsmutils
docker run --rm -it \
  --security-opt seccomp=unconfined \
  -v ~/Documents/landslide/data/SLIDE_NASA_GLC:/lsmutils/data/SLIDE_NASA_GLC \
  -v ~/Documents/landslide/data/FIRE_MODIS:/lsmutils/data/FIRE_MODIS \
  -v /mnt/wddata/FIRE_MODIS:/lsmutils/out \
  -v ~/Documents/landslide/regions/preprocessing/cfg:/lsmutils/cfg \
  -t lsmutils:latest \
  conda run -n lsmutils python -m lsmutils /lsmutils/cfg/burn.cfg.yaml
