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

    gain_event_vol = []
    gain_event_height = []
    gain_count = 0

    loss_event_vol = []
    loss_event_height = []
    loss_count = 0

    # make loop that iterates over all events
    for col_key in grid.voxels.keys():
        for event_key in grid.voxels[col_key].keys():
            curr_event = grid.voxels[col_key][event_key]
            # Check for Missing event, if event is instance of event class
            if isinstance(curr_event, c_voxels.Event):
                if curr_event.is_gain():
                    gain_event_vol.append(abs(curr_event.get_volume()))
                    # Subtracting 15.5 to set min height to 0
                    gain_event_height.append(curr_event.get_mean_height() - 15.5)
                    gain_count += len(list(curr_event.voxels.keys()))
                else:
                    loss_event_vol.append(abs(curr_event.get_volume()))
                    # Subtracting 15.5 to set min height to 0
                    loss_event_height.append(curr_event.get_mean_height() - 15.5)
                    loss_count += len(list(curr_event.voxels.keys()))
    return [gain_event_vol, loss_event_vol], [gain_event_height, loss_event_height], [gain_count, loss_count]


# Establishing the necessary paths
spec_path = Path(r'C:\UMB\Geomorphology\support\grid_rainsford')
input_path = Path(r'C:\UMB\Geomorphology\input\07_top_bot_sliced_trimmed_rotated_pointcloud')


timepoint_list = [('TP1', 'TP2'),
                  ('TP2', 'TP3'),
                  ('TP3', 'TP4'),
                  ('TP1', 'TP3'),
                  ('TP2', 'TP4'),
                  ('TP1', 'TP4')]

x_labels = ['1-2 Gain', '1-2 Loss', '2-3 Gain', '2-3 Loss', '3-4 Gain', '3-4 Loss',
            '1-3 Gain', '1-3 Loss', '2-4 Gain', '2-4 Loss', '1-4 Gain', '1-4 Loss']
#timepoint_test = [('TP1', 'TP2')]

vol_list = []
height_list = []
count_list = []

for timepoint_pair in timepoint_list:
    tp_vol_list, tp_height_list, tp_count_list = event_stats(timepoint_pair[0], timepoint_pair[1], spec_path, input_path)
    vol_list.extend(tp_vol_list)
    height_list.extend(tp_height_list)
    count_list.extend(tp_count_list)

# Start a plot
fig = plt.figure(figsize=(15, 12))

ax = fig.add_subplot(2, 1, 1)

box_dict = ax.boxplot(vol_list)
outlier_percent_list = []
outlier_max_list = []

for box, voxel_total in zip(box_dict['fliers'], count_list):
    #print(len(box.get_ydata(orig=True)))
    outlier_percent_list.append((len(box.get_ydata(orig=True)) / voxel_total) * 100)
    outlier_max_list.append((np.max(box.get_ydata(orig=True))))
ax.remove()

ax = fig.add_subplot(2, 1, 1)

box_dict = ax.boxplot(vol_list, showfliers=False)
# Printing out median volumes to timepoint pairs
for medline in box_dict['medians']:
    linedata = medline.get_ydata()
    median = linedata[0]
    print(f'The median volume is {median}')

ax.set_title('Absolute Volume of Events per Timepoint Pair')
ax.set_ylabel('Volume (m^3)')
ax.set_xlabel('Timepoint Pair')
ax.set_xticklabels(x_labels)

#ax.yaxis.set_major_formatter(mpl.ticker.FormatStrFormatter('%.2e'))
(y_min, y_max) = ax.get_ylim()
ax.set_ylim((y_min, y_max + 0.005))


skip = True
for whisker in box_dict['whiskers']:
    if skip:
        skip = False
        continue
    else:
        skip = True
    #print(whisker.get_ydata())
    ax.text(whisker.get_xdata()[0],
            whisker.get_ydata()[1] + 0.0002,
            f'Outliers:\n{np.around(outlier_percent_list.pop(0), decimals=2)}'
            f'% of N\nMax: {np.around(outlier_max_list.pop(0), decimals=2)}',
            horizontalalignment='center')

ax2 = fig.add_subplot(2, 1, 2)

ax2.boxplot(height_list)
box_dict2 = ax2.boxplot(height_list, showfliers=False)

# Printing out median event height of timepoint pairs
for medline in box_dict2['medians']:
    linedata = medline.get_ydata()
    median = linedata[0]
    print(f'The median event height is {median}')

ax2.set_title('Height of Events per Timepoint Pair')
ax2.set_ylabel('Height (m) ')
ax2.set_xlabel('Timepoint Pair')
ax2.set_xticklabels(x_labels)
plt.show()

# START OF FIGURE 2 Height vs. Volume Comparision

fig = plt.figure(figsize=(18, 12))
subplot_index = 1
while vol_list:
    ax = fig.add_subplot(2, 3, subplot_index)
    gain_vol = vol_list.pop(0)
    loss_vol = vol_list.pop(0)
    tp_names = timepoint_list.pop(0)

    gain_height = height_list.pop(0)
    loss_height = height_list.pop(0)
    ax.scatter(gain_vol, gain_height, s=2, color='b', marker='.')
    ax.scatter(loss_vol, loss_height, s=2, color='r', marker='.')

    ax.set_title(f'{tp_names[0]} to {tp_names[1]}')

    if subplot_index == 5:
        ax.set_xlabel('Volume (m^3)')
    if subplot_index == 1:
        ax.set_ylabel('Height (m)')

    subplot_index += 1

plt.show()