import yaml
import shutil, os, sys
import numpy as np
import pandas as pd
from osgeo import gdal

sys.path.append('sediment')
from calibrate import CaseCollection
from utils import CoordProperty
from operation import LatLonToShapefileOp
from sequence import run_cfg
from path import Path

if __name__ == '__main__':
    # Process DEM
    case = run_cfg('ca_stat_slope_cfg.yaml')
