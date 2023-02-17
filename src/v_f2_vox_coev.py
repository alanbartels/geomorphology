import c_voxels
import logging
import datetime
from pathlib import Path
from matplotlib import pyplot as plt
import matplotlib as mpl
import numpy as np

# Set matplotlib defaults for fonts
mpl.rc('font', family='Times New Roman')
mpl.rc('axes', labelsize=14)
mpl.rc('axes', titlesize=14)
mpl.rc('xtick', labelsize=12)
mpl.rc('ytick', labelsize=12)

# Set the logging config
logging.basicConfig(filename=f'C:/UMB/Geomorphology/logs/{datetime.datetime.now():%Y%m%d%H%M%S}.log',
                    filemode='w',
                    format=' %(levelname)s - %(asctime)s - %(message)s',
                    level=logging.DEBUG)

# Establishing the necessary paths
spec_path = Path(r'C:\UMB\Geomorphology\support\grid_rainsford')
input_path = Path(r'C:\UMB\Geomorphology\input\07_top_bot_sliced_trimmed_rotated_pointcloud')

first_tp = 'TP1'
second_tp = 'TP2'

# Make a Grid object
grid = c_voxels.Grid(spec_path=spec_path,
                     input_path=input_path)

for slice_num in list(range(0, 23)):

    slice = str(slice_num)

    while len(slice) < 2:
        slice = '0' + slice

    grid.load_events(slice, first_tp, second_tp)


# Event counts
tp1_tp2_event_counts = []
# For each column
for col_key in grid.voxels.keys():
    tp1_tp2_event_counts.append(len(list(grid.voxels[col_key].keys())))

print(f'For TP1 to TP2 there was a mean of {grid.get_mean_event_count_per_col()} events per voxel column.')

first_tp = 'TP1'
second_tp = 'TP4'

# Make a Grid object
grid = c_voxels.Grid(spec_path=spec_path,
                     input_path=input_path)

for slice_num in list(range(0, 23)):

    slice = str(slice_num)

    while len(slice) < 2:
        slice = '0' + slice

    grid.load_events(slice, first_tp, second_tp)


# Event counts
tp1_tp4_event_counts = []
# For each column
for col_key in grid.voxels.keys():
    tp1_tp4_event_counts.append(len(list(grid.voxels[col_key].keys())))