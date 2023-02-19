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

# Function to sum gross and net
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

    event_vol = []
    event_height = []


    # make loop that iterates over all events
    for col_key in grid.voxels.keys():
        for event_key in grid.voxels[col_key].keys():
            curr_event = grid.voxels[col_key][event_key]
            # Check for Missing event, if event is instance of event class
            if isinstance(curr_event, c_voxels.Event):
                event_vol.append(curr_event.get_volume())
                event_height.append(curr_event.get_mean_height())
    return [event_vol, event_height]


# Establishing the necessary paths
spec_path = Path(r'C:\UMB\Geomorphology\support\grid_rainsford')
input_path = Path(r'C:\UMB\Geomorphology\input\07_top_bot_sliced_trimmed_rotated_pointcloud')


# timepoint_list = [('TP1', 'TP2'),
#                   ('TP1', 'TP3'),
#                   ('TP2', 'TP3'),
#                   ('TP2', 'TP4'),
#                   ('TP3', 'TP4'),
#                   ('TP1', 'TP4')]
timepoint_test = [('TP1', 'TP2')]

for timepoint_pair in timepoint_test:
    event_stats(timepoint_pair[0], timepoint_pair[1], spec_path, input_path)