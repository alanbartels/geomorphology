import json

from dotenv import load_dotenv
from os import environ
from pathlib import Path
import c_voxels
import t_import
import logging
import datetime




# Set the logging config
logging.basicConfig(filename=f'F:/UMB/Geomorphology/logs/{datetime.datetime.now():%Y%m%d%H%M%S}.log',
                    filemode='w',
                    format=' %(levelname)s - %(asctime)s - %(message)s',
                    level=logging.DEBUG)


# Make a Grid object
grid = c_voxels.Grid(spec_path=Path(r'F:\UMB\Geomorphology\support\grid_rainsford'))

grid.assess_project_structure(Path(r'F:\UMB\Geomorphology\input\07_top_bot_sliced_trimmed_rotated_pointcloud'))

print(grid.proj_struct)

#grid.derive_change('00')

#dir_path = Path(r'F:\UMB\Geomorphology\output\Rainsford Geomorphology')

#print(Path(dir_path.parents[0], 'Test'))

exit()


# Make a Grid object
grid = c_voxels.Grid(spec_path=Path(r'F:\UMB\Geomorphology\support\grid_rainsford'))

dir_path = Path(r'F:\UMB\Geomorphology\output\Rainsford Geomorphology')

grid.all_jsons_to_visualizations(dir_path)

exit()

#grid.process_point_cloud(file_path)


grid.process_all_point_clouds(Path(r'F:\UMB\Geomorphology\input\07_top_bot_sliced_trimmed_rotated_pointcloud'))

exit()

file_path = Path(r'F:\UMB\Geomorphology\input\Geomorphology_Bartels\test_final_section\00_SP01_TP3.txt')

# Make a Grid object
grid = c_voxels.Grid(spec_path=Path(r'F:\UMB\Geomorphology\support\grid_rainsford'))

grid.process_point_cloud(file_path)

for vox_x in grid.voxels.keys():
    for vox_z in grid.voxels[vox_x].keys():
        curr_vox = grid.voxels[vox_x][vox_z]
        for timepoint in curr_vox.stats_by_timepoint.keys():
            for stats_set in curr_vox.stats_by_timepoint[timepoint].keys():
                # Reference
                results = curr_vox.stats_by_timepoint[timepoint][stats_set]

                print(f'\nResults for {stats_set}, Voxel X: {vox_x}, Z: {vox_z}.\n')

                for attribute in results.__dict__.keys():
                    print(f'{attribute}: {getattr(results, attribute)}')

        input()