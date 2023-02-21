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


def event_stats(first_tp, second_tp, spec_path, input_path):
    # Make a Grid object
    grid = c_voxels.Grid(spec_path=spec_path,
                         input_path=input_path)

    # Loading all events into grid object
    for slice_num in list(range(0, 23)):

        slice = str(slice_num)

        while len(slice) < 2:
            slice = '0' + slice
        # method on the grid object
        grid.load_events(slice, first_tp, second_tp)

    event_count_list = []
    for col_key in grid.voxels.keys():
        event_count_list.append(len(list(grid.voxels[col_key].keys())))
    print(
        f'For {first_tp} to {second_tp} there was a mean of {grid.get_mean_event_count_per_col()} events per voxel column.')

    return event_count_list

# Establishing the necessary paths
spec_path = Path(r'C:\UMB\Geomorphology\support\grid_rainsford')
input_path = Path(r'C:\UMB\Geomorphology\input\07_top_bot_sliced_trimmed_rotated_pointcloud')

timepoint_list = [('TP1', 'TP2'),
                  ('TP2', 'TP3'),
                  ('TP3', 'TP4'),
                  ('TP1', 'TP3'),
                  ('TP2', 'TP4'),
                  ('TP1', 'TP4')]

x_labels = ['TP1 to TP2', 'TP2 to TP3', 'TP3 to TP4', 'TP1 to TP3', 'TP2 to TP4', 'TP1 to TP4']
#timepoint_test = [('TP1', 'TP2')]

count_list = []

for timepoint_pair in timepoint_list:
    tp_count_list = event_stats(timepoint_pair[0], timepoint_pair[1], spec_path, input_path)
    count_list.extend(tp_count_list)

# Start a plot
fig = plt.figure(figsize=(10, 6))

# SUBPLOT 1: Number of Events BAR CHART TP2 - TP1
ax = fig.add_subplot(1, 1, 1)


ax.boxplot(count_list, showfliers=False)

ax.set_title('Absolute Volume of Events per Timepoint Pair')
ax.set_ylabel('Volume (m^3)')
ax.set_xlabel('Timepoint Pair')
ax.set_xticklabels(x_labels)

# SHOW THE PLOT

plt.show()