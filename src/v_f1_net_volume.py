import c_voxels
import logging
import datetime
from pathlib import Path
from matplotlib import pyplot as plt
import matplotlib as mpl
import h_nonveg_slice as nv
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

    net_vol = 0
    gross_vol = 0
    gain_count = 0
    loss_count = 0

    # make loop that iterates over all events
    for col_key in grid.voxels.keys():
        for event_key in grid.voxels[col_key].keys():
            curr_event = grid.voxels[col_key][event_key]
            # Check for Missing event, if event is instance of event class
            if isinstance(curr_event, c_voxels.Event):
                if curr_event.is_gain():
                    gain_count += len(list(curr_event.voxels.keys()))
                else:
                    loss_count += len(list(curr_event.voxels.keys()))
                net_vol += curr_event.get_volume()
                gross_vol += abs(curr_event.get_volume())

    print(f'For {first_tp} to {second_tp} there was a net vol_change of {net_vol} m^3.')
    print(f'For {first_tp} to {second_tp} there was a gross vol_change of {gross_vol} m^3.')
    print(f'For {first_tp} to {second_tp} there was gain in {gain_count} voxels.')
    print(f'For {first_tp} to {second_tp} there was loss in {loss_count} voxels.')
    print(f'For {first_tp} to {second_tp} there was change in {gain_count + loss_count} voxels')

# Establishing the necessary paths
spec_path = Path(r'C:\UMB\Geomorphology\support\grid_rainsford')
input_path = Path(r'C:\UMB\Geomorphology\input\07_top_bot_sliced_trimmed_rotated_pointcloud')


timepoint_list = [('TP1', 'TP2'),
                  ('TP1', 'TP3'),
                  ('TP2', 'TP3'),
                  ('TP2', 'TP4'),
                  ('TP3', 'TP4'),
                  ('TP1', 'TP4')]

for timepoint_pair in timepoint_list:
    event_stats(timepoint_pair[0], timepoint_pair[1], spec_path, input_path)