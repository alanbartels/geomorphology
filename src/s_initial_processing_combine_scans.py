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


def parallel_process(file_set):
    # Split out the information from the file set
    spec_path = file_set[0][0]
    input_path = file_set[0][1]
    timepoint = file_set[0][2]
    slice = file_set[0][3]

    # Make a Grid object
    grid = c_voxels.Grid(spec_path=spec_path,
                         input_path=input_path)
    # For each scan position in the set
    for scan_position in file_set[1]:
        # Assemble the file path
        file_path = Path(input_path, f'{slice}_{scan_position}_{timepoint}.txt')
        # Log info
        logging.info(f'Processing {file_path}.')
        # Have the grid process the file
        grid.process_point_cloud(file_path, summary_stats=False, export_file=False)
        # Log info
        logging.info(f'Finished processing {file_path}.')
    # Now all scans are done, generate summary stats
    # Iterate over the voxels
    # For each voxel X
    for vox_x in grid.voxels.keys():
        # For each voxel Z
        for vox_z in grid.voxels[vox_x].keys():
            # Reference the voxel object
            curr_voxel = grid.voxels[vox_x][vox_z]
            # Generate summary stats
            curr_voxel.generate_summary_stats()
    # Output directory
    output_dir = Path(f'F:/UMB/Geomorphology/output/{grid.name}/slice_timepoint/')
    # If the output directory for this grid does not exist
    if not exists(output_dir):
        # Make it
        mkdir(output_dir)

    # Output dictionary
    output_dict = {'Grid Name': grid.name,
                   'Timepoint Name': timepoint,
                   'Slice Name': slice,
                   'Voxels': {}}
    # Transfer keys and results
    for vox_x in grid.voxels.keys():
        output_dict['Voxels'][vox_x] = {}
        for vox_z in grid.voxels[vox_x].keys():
            output_dict['Voxels'][vox_x][vox_z] = grid.voxels[vox_x][vox_z].flatten()
    # Assemble the output path
    output_path = Path(output_dir, f'{slice}_{timepoint}.json.')
    # Log before output
    logging.info(f'Exporting to {output_path}')
    # Open output file
    with open(output_path, 'w') as of:
        json.dump(output_dict, of)
    # Log after output
    logging.info(f'Export to {output_path} complete.')


def main(spec_path, input_path):
    # List for file sets
    file_set_list = []
    # Make a Grid object
    grid = c_voxels.Grid(spec_path=Path(spec_path),
                         input_path=Path(input_path))
    # Assess the structure of the project
    grid.assess_project_structure()

    # Specify output directory path
    output_path = Path(f'F:/UMB/Geomorphology/output/{grid.name}/slice_timepoint/')
    # If the path does not exist
    if not exists(output_path):
        # Make it
        mkdir(output_path)
    # For each timepoint
    for timepoint in grid.proj_struct.keys():
        # For each slice
        for slice in grid.proj_struct[timepoint].keys():
            # If the output file already exists
            if exists(Path(output_path, f'{slice}_{timepoint}.json')):
                # Log it
                logging.info(f'Output file {slice}_{timepoint}.json already exists, skipping.')
                # Skip it
                continue
            # Add the file set to the list
            file_set_list.append([(spec_path, input_path, timepoint, slice), grid.proj_struct[timepoint][slice]])

    # Make a process pool executor
    with ProcessPoolExecutor(max_workers=3) as executor:
        executor.map(parallel_process, file_set_list)


if __name__ == '__main__':

    # Specify paths to specification file and input directory (where ASCII point clouds are stored)
    spec_path = Path(r'F:\UMB\Geomorphology\support\grid_rainsford')
    input_path = Path(r'F:\UMB\Geomorphology\input\07_top_bot_sliced_trimmed_rotated_pointcloud')

    # Call the main function
    main(spec_path, input_path)
