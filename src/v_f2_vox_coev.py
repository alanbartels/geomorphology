import json
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
input_path = Path(r'C:\UMB\Geomorphology\output\Rainsford Geomorphology\slice_timepoint')
# iterate over timepoints, then slices, and then range of coefficient of variations within each timepoint
# for each timepoint, code is under

timepoint_list = ['TP1', 'TP2', 'TP3', 'TP4']
# box_plot_stats = [min, l_quart, med, u_quart, max]
cv_list = []
total_voxel_list = []

for timepoint in timepoint_list:
    tp_cv_list = []
    tp_voxel_count = 0
    for slice_num in list(range(0, 23)):
        slice = str(slice_num)

        while len(slice) < 2:
            slice = '0' + slice
        file_path = Path(input_path, f'{slice}_{timepoint}.json')

        with open(file_path, 'r') as f:
            # Load input dictionary
            input_dict = json.load(f)
        for col_key in input_dict['Voxels']:
            for row_key in input_dict['Voxels'][col_key].keys():
                voxel_values = input_dict['Voxels'][col_key][row_key][0]
                if len(input_dict['Voxels'][col_key][row_key]) > 2:
                    scan_pos = input_dict['Voxels'][col_key][row_key][2]
                    # If more than 1 key in dictionary or if there is only one scan position, does it have more than one point
                    if len(list(scan_pos.keys())) > 1 or scan_pos[list(scan_pos.keys())[0]] > 1:
                        voxel_cv = voxel_values[-1]/voxel_values[2]
                        tp_cv_list.append(voxel_cv)
                        tp_voxel_count += 1
                elif voxel_values[0] != voxel_values[1]:
                    voxel_cv = voxel_values[-1] / voxel_values[2]
                    tp_cv_list.append(voxel_cv)
                    tp_voxel_count += 1
    cv_list.append(tp_cv_list)
    total_voxel_list.append(tp_voxel_count)

# Start a plot
fig = plt.figure(figsize=(10, 6))

# SUBPLOT 1: Number of Events BAR CHART TP2 - TP1
ax = fig.add_subplot(1, 1, 1)

box_dict = ax.boxplot(cv_list)
outlier_percent_list = []
outlier_max_list = []

for box, voxel_total in zip(box_dict['fliers'], total_voxel_list):
    print(len(box.get_ydata(orig=True)))
    outlier_percent_list.append((len(box.get_ydata(orig=True)) / voxel_total) * 100)
    outlier_max_list.append((np.max(box.get_ydata(orig=True))))
ax.remove()

ax = fig.add_subplot(1, 1, 1)

box_dict = ax.boxplot(cv_list, showfliers=False)
for medline in box_dict['medians']:
    linedata = medline.get_ydata()
    median = linedata[0]
    print(f'The median CV is {median}')

ax.set_title('CV of Point Y-Position within Voxels per Timepoint')
ax.set_ylabel('Coefficient of Variation')
ax.set_xlabel('Timepoint')
ax.yaxis.set_major_formatter(mpl.ticker.FormatStrFormatter('%.2e'))
(y_min, y_max) = ax.get_ylim()
ax.set_ylim((y_min, y_max + 0.00025))


skip = True
for whisker in box_dict['whiskers']:
    if skip:
        skip = False
        continue
    else:
        skip = True
    #print(whisker.get_ydata())
    ax.text(whisker.get_xdata()[0],
            whisker.get_ydata()[1] + 0.00002,
            f'Outliers:\n{np.around(outlier_percent_list.pop(0), decimals=2)}'
            f'% of N\nMax: {np.around(outlier_max_list.pop(0), decimals=2)}',
            horizontalalignment='center')
#for whisker, timepoint in zip(box_dict['whiskers'], timepoint_list):
#   print(whisker.get_ydata(orig=True))

plt.show()

