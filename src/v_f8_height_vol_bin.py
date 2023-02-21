import c_voxels
import logging
import datetime
from pathlib import Path
from matplotlib import pyplot as plt
import matplotlib as mpl
import numpy as np

# Height bin size = voxel_size * BINNING_VARIABLE
BINNING_VARIABLE=20

def get_bin_key(bin_factor, row_key):
    return np.floor(int(row_key)/bin_factor)

def get_plt_var_from_dict(input_dict):
    vol_list = []
    height_list = []

    for height_key in sorted(list(input_dict.keys())):
        vol_list.append(input_dict[height_key])
        height_list.append(height_key - 15.5)
    return vol_list, height_list

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

timepoint_list = [('TP1', 'TP2'),
                  ('TP2', 'TP3'),
                  ('TP3', 'TP4'),
                  ('TP1', 'TP3'),
                  ('TP2', 'TP4'),
                  ('TP1', 'TP4')]

vh_list_gain = []
vh_list_loss = []

for timepoint_pair in timepoint_list:
    binned_dict_loss = {}
    binned_dict_gain = {}
    # Loading all events into grid object
    for slice_num in list(range(0, 23)):
        # Make a Grid object
        grid = c_voxels.Grid(spec_path=spec_path,
                             input_path=input_path)

        slice = str(slice_num)

        while len(slice) < 2:
            slice = '0' + slice
        # method on the grid object
        grid.load_events(slice, timepoint_pair[0], timepoint_pair[1])
        # make loop that iterates over all events
        for col_key in grid.voxels.keys():
            for event_key in grid.voxels[col_key].keys():
                curr_event = grid.voxels[col_key][event_key]
                # Check for Missing event, if event is instance of event class
                if isinstance(curr_event, c_voxels.Event):
                    for vox_row in curr_event.voxels.keys():
                        bin_key = get_bin_key(BINNING_VARIABLE, vox_row)
                        if curr_event.is_gain():
                            if bin_key not in binned_dict_gain.keys():
                                binned_dict_gain[bin_key] = 0
                            # Grabbing median distance
                            binned_dict_gain[bin_key] += grid.get_voxel_volume(curr_event.voxels[vox_row])
                        else:
                            if bin_key not in binned_dict_loss.keys():
                                binned_dict_loss[bin_key] = 0
                            # Grabbing median distance
                            binned_dict_loss[bin_key] += grid.get_voxel_volume(abs(curr_event.voxels[vox_row]))
    vh_list_gain.append(binned_dict_gain)
    vh_list_loss.append(binned_dict_loss)

fig = plt.figure(figsize=(18, 12))

subplot_index = 1
while vh_list_gain:
    ax = fig.add_subplot(2, 3, subplot_index)
    gain_dict = vh_list_gain.pop(0)
    loss_dict = vh_list_loss.pop(0)
    tp_names = timepoint_list.pop(0)

    vol_list, height_list = get_plt_var_from_dict(gain_dict)
    gain_line = ax.plot(vol_list, height_list, color='blue')

    vol_list, height_list = get_plt_var_from_dict(loss_dict)

    loss_line = ax.plot(vol_list, height_list, color='red')

    ax.set_title(f'{tp_names[0]} to {tp_names[1]}')

    if subplot_index == 5:
        ax.set_xlabel('Volume (m^3)')
    if subplot_index == 1:
        ax.set_ylabel('Height (m)')
        #ax.legend([gain_line, loss_line], ['Gain', 'Loss'])
        ax.legend([gain_line, loss_line], ['Gain', 'Loss'])

    subplot_index += 1


plt.show()
