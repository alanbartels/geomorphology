import c_voxels
import logging
import datetime
from pathlib import Path

# Set the logging config
logging.basicConfig(filename=f'F:/UMB/Geomorphology/logs/{datetime.datetime.now():%Y%m%d%H%M%S}.log',
                    filemode='w',
                    format=' %(levelname)s - %(asctime)s - %(message)s',
                    level=logging.DEBUG)

spec_path = Path(r'F:\UMB\Geomorphology\support\grid_rainsford')
input_path = Path(r'F:\UMB\Geomorphology\input\07_top_bot_sliced_trimmed_rotated_pointcloud')


first_tp = 'TP2'
second_tp = 'TP3'

for slice_num in list(range(0, 23)):

    slice = str(slice_num)

    while len(slice) < 2:
        slice = '0' + slice

    # Make a Grid object
    grid = c_voxels.Grid(spec_path=spec_path,
                         input_path=input_path)

    grid.load_events(slice, first_tp, second_tp)

    grid.get_event_summary(slice, first_tp, second_tp)

    #grid.visualize_events(slice, first_tp, second_tp)

    #grid.visualize_cumulative_profile(list(grid.voxels.keys())[0])

    grid.visualize_change_profile(list(grid.voxels.keys())[0])