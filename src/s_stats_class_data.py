from pathlib import Path
from os import walk
from os.path import exists
import c_voxels

class TimepointStats:

    def __init__(self, timepoint):

        self.name = timepoint.name
        self.voxels = {}

    def add_voxel(self, voxel):

        if voxel.x not in self.voxels.keys():
            self.voxels[voxel.x] = {}
        self.voxels[voxel.x][voxel.z] = {'point_count': len(voxel.stats_by_timepoint[self.name]['distance'].values),
                                         'scan_count': len(voxel.scans)}

# Specify directory path for files to process
dir_path = Path(r'F:\UMB\Geomorphology\input\07_top_bot_sliced_trimmed_rotated_pointcloud')

# List of slices
slice_list = ['02', '11', '20']

# For each slice
for slice in slice_list:
    # If the output file already exists
    if exists(
            Path(
                f'F:/UMB/Geomorphology/output/stats_project/{slice}.csv')):
        # Skip it
        continue
    # Grid object dictionary
    grid_objs = {}
    # For each timepoint
    for timepoint in ['TP1', 'TP4']:
        # Key for timepoint in dictionary and new Grid object
        grid_objs[timepoint] = {'Grid': c_voxels.Grid(spec_path=Path(r'F:\UMB\Geomorphology\support\grid_rainsford')),
                                'Timepoint Stats': None}
        # Reference current timepoint
        curr_grid = grid_objs[timepoint]['Grid']
        # Generate a list of files to process
        file_list = []
        # Walk the directory
        for root, dirs, files in walk(dir_path):
            # Iterate over files
            for file in files:
                # If the file is an ascii file to be processed
                if '.txt' in file:
                    # If the file is the correct slice
                    if f'{slice}_SP' in file:
                        # If the file is the correct timepoint
                        if f'{timepoint}.txt' in file:
                            # Get the components of the file
                            slice_name, scan_name, timepoint_name = curr_grid.get_file_name_components(file)
                            # Otherwise (needs processing), add to list
                            file_list.append(Path(f'{root}/{file}'))
        # For file in file list
        for file in file_list:
            # Have the grid process the file
            curr_grid.process_point_cloud(file, summary_stats=False, export_file=False)
        # Retrieve Timepoint object
        timepoint_key = list(curr_grid.timepoints.keys())[0]
        timepoint_obj = curr_grid.timepoints[timepoint_key]

        # Make a new timepoint stats object in the grid object dictionary
        grid_objs[timepoint]['Timepoint Stats'] = TimepointStats(timepoint_obj)
        # Reference it
        tp_stats = grid_objs[timepoint]['Timepoint Stats']
        # Get the results and write a file
        # Iterate over the voxels
        # For each voxel X
        for vox_x in curr_grid.voxels.keys():
            # For each voxel Z
            for vox_z in curr_grid.voxels[vox_x].keys():
                # Reference the voxel object
                curr_voxel = curr_grid.voxels[vox_x][vox_z]
                # Add the voxel's stats to the TimepointStats object
                tp_stats.add_voxel(curr_voxel)
                # Generate summary stats
                curr_voxel.generate_summary_stats()
    # Reference TP 1 and TP 4 grids and stats
    tp1_grid = grid_objs['TP1']['Grid']
    tp1_stats = grid_objs['TP1']['Timepoint Stats']
    tp4_grid = grid_objs['TP4']['Grid']
    tp4_stats = grid_objs['TP4']['Timepoint Stats']

    # Open a file for writing.

    with open(Path(f'F:/UMB/Geomorphology/output/stats_project/{slice}.csv'), 'w') as of:
        # Write header line
        #of.write('Change in Mean (TP4 - TP1), Change in Median (TP4 - TP1), Height, Mean Point Count, Mean Scan Count, Proportional Mean Reflectance Change')
        of.write(
            'Change in Mean (TP4 - TP1), Change in Median (TP4 - TP1), Height, Mean Point Count, Mean Scan Count')
        # Iterate over voxels in TP1
        # For each voxel X
        for vox_x in tp1_grid.voxels.keys():
            # For each voxel Z
            for vox_z in tp1_grid.voxels[vox_x].keys():
                # Check if the voxel exists in TP4
                if vox_x in tp4_grid.voxels.keys():
                    if vox_z in tp4_grid.voxels[vox_x].keys():
                        change_in_mean = tp4_grid.voxels[vox_x][vox_z].stats_by_timepoint['TP4']['distance'].mean - \
                                         tp1_grid.voxels[vox_x][vox_z].stats_by_timepoint['TP1']['distance'].mean
                        change_in_median = tp4_grid.voxels[vox_x][vox_z].stats_by_timepoint['TP4']['distance'].median - \
                                         tp1_grid.voxels[vox_x][vox_z].stats_by_timepoint['TP1']['distance'].median
                        mean_points = (tp4_stats.voxels[vox_x][vox_z]['point_count'] + tp1_stats.voxels[vox_x][vox_z]['point_count']) / 2
                        mean_scans = (tp4_stats.voxels[vox_x][vox_z]['scan_count'] + tp1_stats.voxels[vox_x][vox_z]['scan_count']) / 2

                        # If reflectance is None (bad export from CloudCompare)
                        #if not tp1_grid.voxels[vox_x][vox_z].stats_by_timepoint['TP1']['reflectance'].mean or not tp4_grid.voxels[vox_x][vox_z].stats_by_timepoint['TP4']['reflectance'].mean:
                            # Skip it
                            #continue

                        #prop_ref_change = (tp4_grid.voxels[vox_x][vox_z].stats_by_timepoint['TP4']['reflectance'].mean -
                                           #tp1_grid.voxels[vox_x][vox_z].stats_by_timepoint['TP1']['reflectance'].mean) / tp1_grid.voxels[vox_x][vox_z].stats_by_timepoint['TP1']['reflectance'].mean
                        #of.write(f'\n{change_in_mean}, {change_in_median}, {vox_z * tp1_grid.voxel_size}, {mean_points}, {mean_scans}, {prop_ref_change}')
                        of.write(
                            f'\n{change_in_mean}, {change_in_median}, {vox_z * tp1_grid.voxel_size}, {mean_points}, {mean_scans}')