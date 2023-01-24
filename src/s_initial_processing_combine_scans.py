from concurrent.futures import ProcessPoolExecutor
from os import walk
from os.path import exists
from pathlib import Path
import logging
import datetime
import c_voxels

# Set the logging config
logging.basicConfig(filename=f'F:/UMB/Geomorphology/logs/{datetime.datetime.now():%Y%m%d%H%M%S}.log',
                    filemode='w',
                    format=' %(levelname)s - %(asctime)s - %(message)s',
                    level=logging.DEBUG)


def parallel_process(file_path):
    # Make a Grid object
    grid = c_voxels.Grid(spec_path=Path(r'F:\UMB\Geomorphology\support\grid_rainsford'))
    # Log info
    logging.info(f'Processing {file_path}.')
    # Have the grid process the file
    grid.process_point_cloud(file_path)
    # Log info
    logging.info(f'Finished processing {file_path}.')


def main(dir_path):
    # Make a Grid object
    grid = c_voxels.Grid(spec_path=Path(r'F:\UMB\Geomorphology\support\grid_rainsford'))
    # Generate a list of files to process
    file_list = []
    # Walk the directory
    for root, dirs, files in walk(dir_path):
        # Iterate over files
        for file in files:
            # If the file is an ascii file to be processed
            if '.txt' in file:
                # Get the components of the file
                slice_name, scan_name, timepoint_name = grid.get_file_name_components(file)
                # If the output file already exists
                if exists(
                        Path(
                            f'F:/UMB/Geomorphology/output/{grid.name}/{slice_name}_{scan_name}_{timepoint_name}.json')):
                    # Log it
                    logging.info(f'Output file for {slice_name}_{scan_name}_{timepoint_name} already exists, skipping.')
                    # Skip it
                    continue
                # Otherwise (needs processing), add to list
                file_list.append(Path(f'{root}/{file}'))

    # Make a process pool executor
    with ProcessPoolExecutor(max_workers=3) as executor:
        executor.map(parallel_process, file_list)


if __name__ == '__main__':

    # Specify directory path for files to process
    dir_path = Path(r'F:\UMB\Geomorphology\input\07_top_bot_sliced_trimmed_rotated_pointcloud')

    # Call the main function
    main(dir_path)
