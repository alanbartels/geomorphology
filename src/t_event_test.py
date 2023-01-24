from concurrent.futures import ProcessPoolExecutor
from os import walk, mkdir
from os.path import exists
from pathlib import Path
import logging
import datetime
import c_voxels
import json

# Set the logging config
logging.basicConfig(filename=f'F:/UMB/Geomorphology/logs/{datetime.datetime.now():%Y%m%d%H%M%S}.log',
                    filemode='w',
                    format=' %(levelname)s - %(asctime)s - %(message)s',
                    level=logging.DEBUG)


def test(slice_list):
    # Split out the information from the file set
    spec_path = slice_list[0][0]
    input_path = slice_list[0][1]
    slice = slice_list[0][2]


    # Make a Grid object
    grid = c_voxels.Grid(spec_path=spec_path,
                         input_path=input_path)

    # Log info
    logging.info(f'Processing Slice {slice}.')

    # Derive events for the slice
    grid.derive_all_events_for_slice(slice, slice_list[1])

    # Log info
    logging.info(f'Finished processing Slice {slice}.')

def main(spec_path, input_path):
    # List for slices
    slice_list = []
    # Make a Grid object
    grid = c_voxels.Grid(spec_path=Path(spec_path),
                         input_path=Path(input_path))
    # Assess the structure of the project
    grid.assess_project_structure()
    # Assemble the file directory
    dir_path = Path(grid.input_path.parents[1], 'output', grid.name, 'change')
    # If the output direction does not exist
    if not exists(dir_path):
        # Make it
        mkdir(dir_path)
    # Dictionary for slices
    slices = {}
    # For each timepoint
    for timepoint in grid.proj_struct.keys():
        # For each slice
        for slice in grid.proj_struct[timepoint].keys():
            # If the slice is not in the list
            if slice not in slices:
                # Add it
                slices[slice] = []
            # Add the timepoint to the slice
            slices[slice].append(timepoint)
    # For each slice
    for slice in slices.keys():
        slice_list.append([(spec_path, input_path, slice), slices[slice]])

    test(slice_list[0])


if __name__ == '__main__':

    # Specify paths to specification file and input directory (where ASCII point clouds are stored)
    spec_path = Path(r'F:\UMB\Geomorphology\support\grid_rainsford')
    input_path = Path(r'F:\UMB\Geomorphology\input\07_top_bot_sliced_trimmed_rotated_pointcloud')

    # Call the main function
    main(spec_path, input_path)