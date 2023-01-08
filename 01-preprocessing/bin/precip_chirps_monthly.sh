docker run --rm -it \
  --security-opt seccomp=unconfined \
  -v  C:\Users\ecull\Google` Drive\research\regions\regions_data\glc:/gis/data/glc \
  -v  C:\Users\ecull\Google` Drive\research\regions\region_data\precip_chirps_monthly:/gis/data/precip_chirps_monthly \
  -v  C:\Users\ecull\Google` Drive\research\regions\regions_data\processed:/gis/out \
  -t eculler/glc_preprocessing \
  gdb -ex r --args python3 src/precip_global.py
