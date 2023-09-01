import json
from datetime import date
from os.path import exists
from os import environ, walk, mkdir
from dotenv import load_dotenv
from pathlib import Path
from numpy import floor
import numpy as np
import logging
from matplotlib import pyplot as plt
import matplotlib as mpl


class Grid:

    def __init__(self, spec_path=None, input_path=None):

        # Name of the grid (project)
        self.name = None
        # Path to project specification
        self.spec_path = spec_path
        # Path to input files (ASCII point clouds)
        self.input_path = input_path
        # Dictionary for project structure
        self.proj_struct = None
        # Global offsets for the grid
        self.x_offset = None
        self.y_offset = None
        self.z_offset = None
        # Size of each voxel in the grid
        self.voxel_size = None
        # Dictionary of timepoints
        self.timepoints = {}
        # Dictionary of voxels. Nested keys [X][Z]
        self.voxels = {}
        # Dictionary of events
        self.events = {}

        # If a path to a grid specification file was provided
        if self.spec_path:
            # Load the specification
            self.load_spec()

    def load_spec(self):
        # If the spec path is not a Path object
        if not isinstance(self.spec_path, Path):
            # Try and convert it
            try:
                self.spec_path = Path(self.spec_path)
            # If it doesn't work
            except:
                # Log an error
                logging.error(f'Grid specification import failed. {self.spec_path} could not be converted to Path object.')
        # Check if the specification path exists
        if not exists(self.spec_path):
            # Log an error
            logging.error(f'Grid specification import failed. File path {self.spec_path} does not exist.')
        # Otherwise (path exists)
        else:
            # Load the content of the spec an environment variables
            load_dotenv(self.spec_path)
            # For each spec entry
            for spec_entry in ['voxel_size', 'name', 'x_offset', 'y_offset', 'z_offset']:
                # See if the spec contained the entry
                try:
                    environ[spec_entry]
                # Exception for missing key
                except KeyError:
                    # Log information
                    logging.info(f'No {spec_entry} was found in grid specification {self.spec_path}.')
                    # Skip to next entry
                    continue
                # Otherwise, unless it's one of the string entries
                if spec_entry != 'name':
                    # set the attribute (float conversion)
                    setattr(self, spec_entry, float(environ[spec_entry]))
                # Otherwise
                else:
                    # set the attribute (leave as string)
                    setattr(self, spec_entry, environ[spec_entry])

    # Add a timepoint
    def add_timepoint(self, name):
        # If the timepoint name already exists
        if name in self.timepoints.keys():
            # Log a warning
            #logging.warning(f'Timepoint {name} already exists in grid {self.name}. Skipping creation.')
            # End the process
            return
        # Otherwise, create a timepoint object
        new_timepoint = Timepoint(name)
        new_timepoint.grid = self
        self.timepoints[name] = new_timepoint

    # Process all point clouds in a directory
    def process_all_point_clouds(self, combine_scans=True):
        # Assess the project structure
        self.assess_project_structure()
        # For each timepoint
        for timepoint in self.proj_struct.keys():
            # For each slice
            for slice in self.proj_struct[timepoint].keys():
                # For each scan position
                for scan in self.proj_struct[timepoint][slice]:
                    # If combining scans
                    if combine_scans:
                        # Process point cloud
                        self.process_point_cloud(Path(self.input_path, f'{slice}_{scan}_{timepoint}.txt'), summary_stats=False, export_file=False)
                    # Otherwise (not combining scans)
                    else:
                        # Process the point cloud
                        self.process_point_cloud(Path(self.input_path, f'{slice}_{scan}_{timepoint}.txt'))
                # If combining scans
                if combine_scans:
                    continue

    # Process a point cloud file to get Voxel-level statistics for distance and reflectance
    def process_point_cloud(self, file_path, summary_stats=True, export_file=True):
        # If the file path is not a Path object
        if not isinstance(file_path, Path):
            # Try and convert it
            try:
                file_path = Path(file_path)
            # If it doesn't work
            except:
                # Log an error
                logging.error(f'Point cloud import failed. {file_path} could not be converted to Path object.')
                # Stop here
                return
        # If the path does not exist
        if not exists(file_path):
            # Log an error
            logging.error(f'File import failed. File path {file_path} does not exist.')
            # Exit the function returning None
            return
        # Get the components from the file name from the path
        slice_name, scan_name, timepoint_name = self.get_file_name_components(file_path)

        # Create Timepoint
        self.add_timepoint(timepoint_name)
        # Add a scan to the Timepoint object
        self.timepoints[timepoint_name].add_scan(scan_name)

        # Iterate over the rows in the file
        for row in self.yield_ascii_rows(file_path):
            values = row.strip().split(',')
            x_co = float(values[0])
            y_co = float(values[1])
            z_co = float(values[2])
            # Get the voxel coordinates
            vox_x, _, vox_z = self.get_voxel_coords(x_co, y_co, z_co)
            # Add a voxel (if necessary)
            self.add_voxel(vox_x, vox_z)
            # Reference the current voxel
            curr_voxel = self.voxels[vox_x][vox_z]
            # Add timepoint to the voxel
            curr_voxel.add_timepoint_stats(self.timepoints[timepoint_name])
            # Add the distance and reflectance values to the relevant stat generators
            curr_voxel.stats_by_timepoint[timepoint_name]['distance'].values.append(float(values[1]))
            # Check whether the reflectance properties were exported from Cloud Compare (by counting cols)
            if len(values) == 10:
                # If so, add the reflectance value
                curr_voxel.stats_by_timepoint[timepoint_name]['reflectance'].values.append(float(values[4]))
            # Check if the scan was already noted as contributing to the voxel
            if scan_name not in curr_voxel.scans:
                # Add it
                curr_voxel.scans[scan_name] = 0
            # Add to the point count for the scan
            curr_voxel.scans[scan_name] += 1

        # If generating summary stats
        if summary_stats:
            # Iterate over the voxels
            # For each voxel X
            for vox_x in self.voxels.keys():
                # For each voxel Z
                for vox_z in self.voxels[vox_x].keys():
                    # Reference the voxel object
                    curr_voxel = self.voxels[vox_x][vox_z]
                    # Generate summary stats
                    curr_voxel.generate_summary_stats()

        # If exporting the file
        if export_file:
            # Export the results (save to disk)
            self.initial_export(timepoint_name, scan_name, slice_name)

    # Add a voxel to the grid
    def add_voxel(self, vox_x, vox_z):
        # If there is no vox_x key in the dictionary
        if vox_x not in self.voxels.keys():
            # Add a subdictionary
            self.voxels[vox_x] = {}
        # If there is no vox_z key in the subdictionary
        if vox_z not in self.voxels[vox_x].keys():
            # Add a Voxel object
            self.voxels[vox_x][vox_z] = Voxel(x=vox_x, z=vox_z)

    # Get the voxel coordinates from X, Y, Z point positions
    def get_voxel_coords(self, x_co, y_co, z_co):
        # <> Include the offsets to 0,0 the grid
        vox_x = int(floor(x_co / self.voxel_size))
        vox_y = int(floor(y_co / self.voxel_size))
        vox_z = int(floor(z_co / self.voxel_size))
        return vox_x, vox_y, vox_z

    def get_file_name_components(self, file_name):
        # Convert to Path
        file_path = Path(file_name)
        # Get the file name as the last component of the Path
        file_name = file_path.parts[-1]
        # Convert to string
        file_name = str(file_name)
        # Split on the underscores
        file_name = file_name.split('_')
        # Return Slice, Scan, and Timepoint
        return file_name[0], file_name[1], file_name[2].split('.')[0]

    def yield_ascii_rows(self, file_path, skip_first=True):
        row_count = 0
        for row in open(file_path, 'r'):
            if row_count == 0:
                if skip_first:
                    row_count += 1
                continue
            row_count += 1
            yield row

    # Initial export of results
    def initial_export(self, timepoint_name, scan_name, slice_name):
        dir_name = f'F:/UMB/Geomorphology/output/{self.name}'
        # Check if output directory for this grid exists
        if not exists(dir_name):
            # Make it
            mkdir(dir_name)

        # Output dictionary
        output_dict = {'Grid Name': self.name,
                       'Timepoint Name': timepoint_name,
                       'Scan Name': scan_name,
                       'Slice Name': slice_name,
                       'Voxels': {}}
        # Transfer keys and results
        for vox_x in self.voxels.keys():
            output_dict['Voxels'][vox_x] = {}
            for vox_z in self.voxels[vox_x].keys():
                output_dict['Voxels'][vox_x][vox_z] = self.voxels[vox_x][vox_z].flatten()
        # Log before output
        logging.info(f'Exporting to {slice_name}_{scan_name}_{timepoint_name}.json.')
        # Open output file
        with open(Path(f'F:/UMB/Geomorphology/output/{self.name}/{slice_name}_{scan_name}_{timepoint_name}.json'), 'w') as of:
            json.dump(output_dict, of)
        # Log after output
        logging.info(f'Exporting to {slice_name}_{scan_name}_{timepoint_name}.json complete.')

    # Assess project structure from ASCII files
    def assess_project_structure(self):
        # Make empty dictionary
        self.proj_struct = {}
        # Walk the directory
        for root, dirs, files in walk(self.input_path):
            # Iterate over files
            for file in files:
                # If the file is an ascii text file to be processed
                if '.txt' in file:
                    # Get the components of the file
                    slice_name, scan_name, timepoint_name = self.get_file_name_components(file)
                    # If the timepoint is not in the dictionary
                    if timepoint_name not in self.proj_struct.keys():
                        # Add it with a subdict
                        self.proj_struct[timepoint_name] = {}
                    # If the slice is not in the timepoint subdict
                    if slice_name not in self.proj_struct[timepoint_name].keys():
                        # Add it with a sublist
                        self.proj_struct[timepoint_name][slice_name] = []
                    # Add the scan point to the slice sublist
                    self.proj_struct[timepoint_name][slice_name].append(scan_name)

    # Derive all loss & gain events from all slices
    def derive_all_events(self):
        # Assemble the file directory
        dir_path = Path(self.input_path.parents[1], 'output', self.name, 'change')
        # If the output direction does not exist
        if not exists(dir_path):
            # Make it
            mkdir(dir_path)
        # Dictionary for slices
        slices = {}
        # For each timepoint
        for timepoint in self.proj_struct.keys():
            # For each slice
            for slice in self.proj_struct[timepoint].keys():
                # If the slice is not in the list
                if slice not in slices:
                    # Add it
                    slices[slice] = []
                # Add the timepoint to the slice
                slices[slice].append(timepoint)
        # For each slice
        for slice in slices.keys():
            # Derive the events
            self.derive_all_events_for_slice(slice, slices[slice])

    # Derive all loss & gain events from all pairs of timepoints in a slice
    def derive_all_events_for_slice(self, slice, timepoints):
        # Empty the timepoints
        self.timepoints = {}
        # Assemble output directory
        output_dir = Path(self.input_path.parents[1], 'output', self.name, 'change', 'slice_timepoint_pairs')
        # If the directory does not exist
        if not exists(output_dir):
            # Make it
            mkdir(output_dir)
        # Assemble the file directory
        dir_path = Path(self.input_path.parents[1], 'output', self.name, 'slice_timepoint')
        # For each timepoint
        for timepoint in timepoints:
            # Add a timepoint object
            self.add_timepoint(timepoint)
            # Assemble the file path
            file_path = Path(dir_path, f'{slice}_{timepoint}.json')
            # Open the file
            with open(file_path, 'r') as f:
                # Load the input dictionary
                input_dict = json.load(f)
            # Transfer the dictionary
            self.timepoints[timepoint].voxels = input_dict['Voxels']
        # List of timepoint pairs for the slice
        timepoint_pairs = [(a, b) for idx, a in enumerate(timepoints) for b in timepoints[idx + 1:]]
        # For each timepoint pair
        for timepoint_pair in timepoint_pairs:
            # Assemble output path
            output_path = Path(output_dir, f'{slice}_{timepoint_pair[0]}_{timepoint_pair[1]}.json')
            # If the file already exists
            if exists(output_path):
                # Skip it
                continue
            # If the first timepoint in the pair is the lower number (earlier) timepoint
            if int(timepoint_pair[0][2:]) < int(timepoint_pair[1][2:]):
                # Derive the events
                pair_results = self.derive_events_from_timepoints(timepoint_pair[0], timepoint_pair[1])
            # Otherwise (second timepoint is before first)
            else:
                # Derive the events
                pair_results = self.derive_events_from_timepoints(timepoint_pair[1], timepoint_pair[0])
            # Open output file
            with open(output_path, 'w') as of:
                json.dump(pair_results, of)

    def order_timepoints(self, first_tp, second_tp):
        if int(first_tp[2:]) < int(second_tp[2:]):
            return first_tp, second_tp
        else:
            return second_tp, first_tp

    # Derive all loss & gain events from a pair or timepoints
    def derive_events_from_timepoints(self, first_tp, second_tp):
        # Dictionary for results
        results_dict = {}
        # List of all X coordinates from both timepoints
        vox_x_list = []
        # For each timepoint
        for timepoint in [first_tp, second_tp]:
            # For each voxel x in the timepoint
            for vox_x in self.timepoints[timepoint].voxels.keys():
                # If the key is not in the list
                if vox_x not in vox_x_list:
                    # Add it
                    vox_x_list.append(vox_x)
        # Sorted voxel list
        sorted_vox_x = sorted(vox_x_list, key=int)
        # First (leftmost) voxel
        curr_vox_x = int(sorted_vox_x[0]) - 1
        # Iterate through the voxel xs
        for vox_x in sorted_vox_x[1:]:
            # Increment the current column
            curr_vox_x += 1
            # While curr voxel is less than the voxel minus one
            while curr_vox_x < int(vox_x) - 1:
                # Add a record of the missing column
                results_dict[str(curr_vox_x + 1)] = [first_tp, second_tp]
                # Increment the current column
                curr_vox_x += 1
        # Iterate through the voxel xs
        for vox_x in sorted_vox_x[1:]:
            # Set up a list for the column
            results_dict[vox_x] = []
            # For each timepoint
            for timepoint in [first_tp, second_tp]:
                # If the column is not in the timepoint
                if vox_x not in self.timepoints[timepoint].voxels.keys():
                    # Add it to the missing data
                    results_dict[vox_x].append(timepoint)
            # If both timepoints have data for the column
            if len(results_dict[vox_x]) == 0:
                # Proceed
                column_results = self.derive_events_from_column(first_tp,
                                                                second_tp,
                                                                self.timepoints[first_tp].voxels[vox_x],
                                                                self.timepoints[second_tp].voxels[vox_x])
                # Store the results for the column
                results_dict[vox_x] = column_results
        # Return the results dictionary
        return results_dict

    # Derive loss & gain events from a column of voxels
    def derive_events_from_column(self, first_tp, second_tp, first_col, second_col):
        # Dictionary for results
        results_dict = {}
        # List of all Z coordinates from both timepoints
        vox_z_list = []
        # For each timepoint
        for timepoint in [first_col, second_col]:
            # For each voxel z in the timepoint
            for vox_z in timepoint.keys():
                # If the key is not in the list
                if vox_z not in vox_z_list:
                    # Add it as integer
                    vox_z_list.append(int(vox_z))

        # Starting current event
        curr_event = EventParser()

        # Sorted voxel list
        sorted_vox_z = list(range(max(vox_z_list), min(vox_z_list) + 1, -1))

        # First voxel switch
        first_voxel = True
        last_missing = False

        while sorted_vox_z:
            # Pop the next value
            curr_vox_z = str(sorted_vox_z.pop(0))
            # If the row is not in both timepoints
            if curr_vox_z not in first_col.keys() or curr_vox_z not in second_col.keys():
                # If this is the first voxel
                if first_voxel:
                    # Flip switch
                    first_voxel = False
                # Otherwise (not first voxel)
                else:
                    # Increment event counter
                    curr_event.count += 1
                # If there is no dictionary for the event
                if curr_event.count not in results_dict.keys():
                    # Set up a dictionary for it
                    results_dict[curr_event.count] = {}
                results_dict[curr_event.count][curr_vox_z] = []
                # If the row is not in the timepoint 1
                if curr_vox_z not in first_col.keys():
                    # Append the timepoint
                    results_dict[curr_event.count][curr_vox_z].append(first_tp)
                # If the row is not in the timepoint 2
                if curr_vox_z not in second_col.keys():
                    # Append the timepoint
                    results_dict[curr_event.count][curr_vox_z].append(second_tp)
                # (Re)set change to None
                curr_event.type = None
                # Set Last Missing to True
                last_missing = True
                # Skip the rest of the loop
                continue
            # Derive the change
            change = second_col[curr_vox_z][0][2] - first_col[curr_vox_z][0][2]
            # If the ongoing event matches the change
            if self.event_matches_change(curr_event, change):
                # If the last change was missing value(s)
                if last_missing:
                    # Flip switch
                    last_missing = False
                    # Increment event
                    curr_event.count += 1
                # If there is no dictionary for the event
                if curr_event.count not in results_dict.keys():
                    # Set up a dictionary for it
                    results_dict[curr_event.count] = {}
                # Record the voxel and change to the event
                results_dict[curr_event.count][curr_vox_z] = change
            # Otherwise (ongoing event does not match change)
            else:
                # If this is the first voxel
                if first_voxel:
                    # Flip switch
                    first_voxel = False
                # Otherwise (not first voxel)
                else:
                    # Increment event counter
                    curr_event.count += 1
                # If there is no dictionary for the event
                if curr_event.count not in results_dict.keys():
                    # Set up a dictionary for it
                    results_dict[curr_event.count] = {}
                # Add the voxel and change to the current event
                results_dict[curr_event.count][curr_vox_z] = change
            # If first voxel still active
            if first_voxel:
                # Flip switch
                first_voxel = False
        # Return the results dictionary
        return results_dict

    def event_matches_change(self, event, change):

        is_gain = self.is_gain(change)

        if is_gain is None:
            return True
        if is_gain and event.type is not False:
            event.type = True
            return True
        if is_gain is False and event.type is not True:
            event.type = False
            return True
        if event.type is False:
            event.type = True
            return False
        if event.type is True:
            event.type = False
            return False
        return False

    def is_gain(self, change):
        if change > 0:
            return True
        elif change < 0:
            return False
        else:
            return None

    def all_jsons_to_visualizations(self, dir_path):

        # Walk the directory
        for root, dirs, files in walk(dir_path):
            # Iterate over files
            for file in files:
                # If the file is a json file to be processed
                if '.json' in file:
                    self.json_to_visualization_file(Path(f'{root}/{file}'))

    def json_to_visualization_file(self, file_path):

        with open(file_path, 'r') as f:
            input_dict = json.load(f)

        # Visualization directory path
        vis_dir = Path(f'F:/UMB/Geomorphology/output/visualization')

        if not exists(vis_dir):
            mkdir(vis_dir)

        vis_dir = str(vis_dir)

        # Grid visualization directory path
        vis_dir += f'/{self.name}'

        if not exists(Path(vis_dir)):
            mkdir(Path(vis_dir))

        for stat_ind, stat in enumerate(['min', 'max', 'mean', 'median']):
            output_file = str(file_path.parts[-1]).replace('.json', f'_{stat}.txt')
            output_path = Path(str(vis_dir) + '/' + output_file)

            with open(output_path, 'w') as of:
                # Write header line
                of.write(f'X, Y, Z, stdev, covar')
                # For each voxel x
                for vox_x in input_dict['Voxels'].keys():
                    for vox_z in input_dict['Voxels'][vox_x].keys():
                        distance_stats = input_dict['Voxels'][vox_x][vox_z][0]
                        # write the line
                        of.write(f'\n{(int(vox_x) * self.voxel_size) + (self.voxel_size / 2)}, '
                                 f'{distance_stats[stat_ind]}, '
                                 f'{(int(vox_z) * self.voxel_size) + (self.voxel_size / 2)}, '
                                 f'{distance_stats[4]}, {distance_stats[4] / distance_stats[2]}')

    def load_events(self, slice, first_tp, second_tp):
        # Order the timepoints correctly
        first_tp, second_tp = self.order_timepoints(first_tp, second_tp)
        # Assemble the directory path
        dir_path = Path(self.input_path.parents[1], 'output', self.name, 'change', 'slice_timepoint_pairs')
        # Assemble the file path
        file_path = Path(dir_path, f'{slice}_{first_tp}_{second_tp}.json')
        # Open the file
        with open(file_path, mode='r') as f:
            # Retrieve the dictionary
            input_dict = json.load(f)
        # For each column in the input dictionary
        for col in input_dict.keys():
            # For each event in the column
            for event_number in input_dict[col].keys():
                # Get the first voxel key
                first_voxel_key = list(input_dict[col][event_number].keys())[0]
                # If there is a list in the event (i.e. there were missing data)
                if isinstance(input_dict[col][event_number][first_voxel_key], list):
                    # Create a MissingObservation object
                    new_obs = MissingObservation()
                    # Transfer the values
                    new_obs.voxels = input_dict[col][event_number]
                    # Store the object
                    if col not in self.voxels.keys():
                        self.voxels[col] = {}
                    self.voxels[col][event_number] = new_obs
                # If it was a gain or loss event
                else:
                    # Create an Event object
                    new_event = Event()
                    # Transfer the values
                    new_event.voxels = input_dict[col][event_number]
                    new_event.grid = self
                    new_event.timepoints = [first_tp, second_tp]
                    # If it is a gain event
                    if new_event.voxels[first_voxel_key] > 0:
                        new_event.type = 'Gain'
                    elif new_event.voxels[first_voxel_key] < 0:
                        new_event.type = 'Loss'
                    else:
                        new_event.type = 'No Change'
                    # Store the object
                    if col not in self.voxels.keys():
                        self.voxels[col] = {}
                    self.voxels[col][event_number] = new_event

    def get_mean_event_count_per_col(self):
        # Event counts
        event_counts = []
        # For each column
        for col_key in self.voxels.keys():
            event_counts.append(len(list(self.voxels[col_key].keys())))
        # Return the mean
        return np.mean(event_counts)

    def get_median_event_count_per_col(self):
        # Event counts
        event_counts = []
        # For each column
        for col_key in self.voxels.keys():
            event_counts.append(len(list(self.voxels[col_key].keys())))
        # Return the median
        return np.median(event_counts)

    def get_event_summary(self, slice, first_tp, second_tp):
        # Make sure the timepoints are ordered correctly
        first_tp, second_tp = self.order_timepoints(first_tp, second_tp)
        # Counts
        gain_count = 0
        loss_count = 0
        no_change_count = 0
        missing_data_count = 0
        # For each col
        for col in self.voxels.keys():
            # For each event number
            for event_number in self.voxels[col].keys():
                # Get event obj
                curr_event = self.voxels[col][event_number]
                # If it's a MissingObservation obj
                if isinstance(curr_event, MissingObservation):
                    missing_data_count += len(list(curr_event.voxels.keys()))
                    # Skip the rest of the loop
                    continue
                # If it's gain
                if curr_event.type == 'Gain':
                    gain_count += 1
                elif curr_event.type == 'Loss':
                    loss_count += 1
                elif curr_event.type == 'No Change':
                    no_change_count += 1

        # Print a summary
        print(f'For slice {slice} change ({second_tp} - {first_tp}).')
        print(f'There were {gain_count} Gain events, {loss_count} Loss events, and {no_change_count} No Change events.')
        print(f'There were {missing_data_count} voxels with missing data.')

    def visualize_events(self, slice, first_tp, second_tp):
        # Make sure the timepoints are ordered correctly
        first_tp, second_tp = self.order_timepoints(first_tp, second_tp)
        # Mins and maxes
        min_row = None
        max_row = None
        min_col = None
        max_col = None

        # Get row and col extents
        for col in self.voxels.keys():
            if min_col is None:
                min_col = int(col)
            elif int(col) < min_col:
                min_col = int(col)
            if max_col is None:
                max_col = int(col)
            elif int(col) > max_col:
                max_col = int(col)
            for event_number in self.voxels[col].keys():
                for row in self.voxels[col][event_number].voxels.keys():
                    if min_row is None:
                        min_row = int(row)
                    elif int(row) < min_row:
                        min_row = int(row)
                    if max_row is None:
                        max_row = int(row)
                    elif int(row) > max_row:
                        max_row = int(row)

        # Visualization array
        vis_arr = np.zeros(((max_row - min_row) + 1, (max_col - min_col) + 1))

        change_arr = np.zeros(((max_row - min_row) + 1, (max_col - min_col) + 1))

        # Get row and col extents
        for col in self.voxels.keys():
            for event_number in self.voxels[col].keys():
                # Get the object
                curr_obj = self.voxels[col][event_number]
                if isinstance(curr_obj, Event):
                    for row in self.voxels[col][event_number].voxels.keys():
                        array_row = (max_row - min_row) - (int(row) - min_row)
                        array_col = int(col) - min_col
                        if curr_obj.type == 'Gain':
                            vis_arr[array_row, array_col] = 1
                        elif curr_obj.type == 'Loss':
                            vis_arr[array_row, array_col] = -1
                        else:
                            vis_arr[array_row, array_col] = 0
                        change_arr[array_row, array_col] = curr_obj.voxels[row]
        # Make a figure
        fig = plt.figure(figsize=(12, 12))
        # Make some space between the subplots4.
        # plt.subplots_adjust(hspace=0.3)
        # Start a subplot
        ax = fig.add_subplot(1, 2, 1)
        # Scatter the night time lights against the "days of study"
        array_map = ax.imshow(vis_arr)
        #color_m = Colormap()
        #ax.plot([0, 0], [0, 15], c='k')
        ax.set_ylabel('Rows')
        ax.set_xlabel('Columns')
        ax.set_title(f'Change for Slice {slice} ({second_tp} - {first_tp})')
        plt.colorbar(array_map)

        ax = fig.add_subplot(1, 2, 2)

        norm = mpl.colors.Normalize(vmin=-2, vmax=2)
        # Make a scalar mappable (including color map)
        my_cmap = mpl.cm.ScalarMappable(norm=norm, cmap='RdYlBu')
        # Scatter the night time lights against the "days of study"
        array_map = ax.imshow(change_arr, cmap=my_cmap.cmap, norm=norm)

        plt.colorbar(array_map)
        # color_m = Colormap()
        # ax.plot([0, 0], [0, 15], c='k')
        ax.set_ylabel('Rows')
        ax.set_xlabel('Columns')
        ax.set_title(f'Change for Slice {slice} ({second_tp} - {first_tp})')

        plt.show()

    def visualize_change_profile(self, x_co):
        # Make a figure
        fig = plt.figure(figsize=(12, 12))
        # Start a subplot
        ax = fig.add_subplot(1, 1, 1)

        max_row = None
        min_row = None

        # For each event in the col
        for event_number in self.voxels[x_co].keys():
            # Reference the event
            curr_event = self.voxels[x_co][event_number]
            # If the event is a missing observation
            if isinstance(curr_event, MissingObservation):
                # Set the color for the patch
                color = 'k'
                # Skip it
                continue

            elif isinstance(curr_event, Event):
                # For each voxel in the path (row)
                for row in curr_event.voxels.keys():
                    if max_row is None:
                        max_row = int(row)
                    elif int(row) > max_row:
                        max_row = int(row)
                    if min_row is None:
                        min_row = int(row)
                    elif int(row) < min_row:
                        min_row = int(row)
                    # Get change volume
                    curr_vol = self.get_voxel_volume(curr_event.voxels[row])
                    # If event is a gain
                    if curr_event.type == 'Gain':
                        # Add the patch to the plot
                        curr_patch = mpl.patches.Rectangle((0, int(row) - 0.5),
                                                           width=curr_vol,
                                                           height=1,
                                                           fill=True,
                                                           facecolor='b')
                    # Otherwise, if it's a loss
                    elif curr_event.type == 'Loss':
                        # Add the patch to the plot
                        curr_patch = mpl.patches.Rectangle((0 + curr_vol, int(row) - 0.5),
                                                           width=abs(curr_vol),
                                                           height=1,
                                                           fill=True,
                                                           facecolor='r')
                    ax.add_patch(curr_patch)

        ax.plot((0, 0), (max_row, min_row), 'k')

        plt.show()

    def visualize_cumulative_profile(self, x_co):

        # Make a figure
        fig = plt.figure(figsize=(12, 12))
        # Start a subplot
        ax = fig.add_subplot(1, 1, 1)

        max_row = None
        min_row = None

        # Current cumulative change
        curr_change = 0

        # For each event in the col
        for event_number in sorted(self.voxels[x_co].keys(), key=int):
            # Reference the event
            curr_event = self.voxels[x_co][event_number]
            # If the event is a missing observation
            if isinstance(curr_event, MissingObservation):
                # Set the color for the patch
                color = 'k'
                # Skip it
                continue

            elif isinstance(curr_event, Event):
                # For each voxel in the path (row)
                for row in curr_event.voxels.keys():
                    if max_row is None:
                        max_row = int(row)
                    elif int(row) > max_row:
                        max_row = int(row)
                    if min_row is None:
                        min_row = int(row)
                    elif int(row) < min_row:
                        min_row = int(row)
                # For each row (sorted top to bottom)
                for row in sorted(curr_event.voxels.keys(), key=int, reverse=True):
                    # Update current change
                    curr_change += curr_event.voxels[row]
                    # Get volume
                    curr_vol = self.get_voxel_volume(curr_change)
                    # If we are in cumulative gain (change > 0)
                    if curr_change > 0:
                        # Add the patch to the plot
                        curr_patch = mpl.patches.Rectangle((0, int(row) - 0.5),
                                                           width=curr_vol,
                                                           height=1,
                                                           fill=True,
                                                           facecolor='b')
                    # Otherwise, if it's a loss
                    elif curr_change < 0:
                        # Add the patch to the plot
                        curr_patch = mpl.patches.Rectangle((0 + curr_vol, int(row) - 0.5),
                                                           width=abs(curr_vol),
                                                           height=1,
                                                           fill=True,
                                                           facecolor='r')
                    ax.add_patch(curr_patch)

        ax.plot((0, 0), (max_row, min_row), 'k')

        plt.show()

    def get_voxel_volume(self, dimension):
        return dimension * (self.voxel_size ** 2)


class Timepoint:

    def __init__(self, name):

        # Name for the timepoint
        self.name = name
        # Dictionary of scans for the timepoint
        self.scans = {}
        self.voxels = None
        self.grid = None

    # Add a scan (with a name)
    def add_scan(self, name):
        # If the scan name already exists
        if name in self.scans.keys():
            # Log a warning
            #logging.warning(f'Scan {name} already exists in timepoint {self.name}. Skipping creation.')
            # End the process
            return
        # Otherwise, create a Scan object, reference the timepoint, and add to dictionary
        new_scan = Scan(name)
        new_scan.timepoint = self
        self.scans[name] = new_scan


class Scan:

    def __init__(self, name):

        self.timepoint = None
        self.name = name
        # Voxel dict with nested keys [X][Z]: Voxel
        self.voxel_dict = {}


class Voxel:

    def __init__(self, x=None, y=None, z=None):

        # Reference to the grid object to which this voxel belongs
        self.grid = None
        # X, Y and Z coordinates of this voxel
        self.x = x
        self.y = y
        self.z = z
        # Stats objects in dictionary with timepoint as key
        self.stats_by_timepoint = {}
        # Scans contributing points to this voxel
        self.scans = {}

    # Add the statistics from a Timepoint object
    def add_timepoint_stats(self, timepoint):
        # If the timepoint name already exists in the dictionary
        if timepoint.name in self.stats_by_timepoint.keys():
            # Log a warning
            #logging.warning(f'Timepoint {timepoint.name} already exists in voxel X:{self.x}, Z:{self.z}. Skipping it.')
            # End the process
            return
        # Otherwise, add a subdictionary for distance and reflectance
        self.stats_by_timepoint[timepoint.name] = {'distance': VoxelStatsGenerator(),
                                                   'reflectance': VoxelStatsGenerator()}

    # Generate summary statistics from the VoxelStatsGenerator objects
    def generate_summary_stats(self):
        # For each timepoint in the voxel
        for timepoint in self.stats_by_timepoint.keys():
            # For each set of stats
            for stats_set in self.stats_by_timepoint[timepoint].keys():
                # If the stats has no entries (the file had no reflectance)
                if len(self.stats_by_timepoint[timepoint][stats_set].values) == 0:
                    # Point to None
                    self.stats_by_timepoint[timepoint][stats_set] = None
                    # Skip the loop
                    continue
                # Create a new VoxelStats object
                vox_stats = VoxelStats()
                # Populate the stats object
                vox_stats.populate(self.stats_by_timepoint[timepoint][stats_set])
                # Replace the reference to the object
                self.stats_by_timepoint[timepoint][stats_set] = vox_stats

    # Flatten for export to JSON
    def flatten(self):
        # Get the timepoint key
        timepoint_key = list(self.stats_by_timepoint.keys())[0]
        # If there were no reflectance results
        if not self.stats_by_timepoint[timepoint_key]['reflectance']:
            # Return distance results, and None
            return [self.stats_by_timepoint[timepoint_key]['distance'].flatten(),
                    None]
        # Otherwise (there were reflectance data), return the results
        return [self.stats_by_timepoint[timepoint_key]['distance'].flatten(),
                self.stats_by_timepoint[timepoint_key]['reflectance'].flatten(),
                self.scans]


class Point:

    def __init__(self):

        self.voxel = None
        self.x = None
        self.y = None
        self.z = None
        self.intensity = None


class VoxelStatsGenerator:

    def __init__(self):

        self.values = []


class VoxelStats:

    def __init__(self):

        self.min = None
        self.max = None
        self.mean = None
        self.median = None
        self.stdev = None

    def coefficient_variation(self):

        return self.stdev / self.mean

    # Populate the statistics based on a VoxelStatsGenerator object as input
    def populate(self, stats_generator):
        self.min = np.nanmin(stats_generator.values)
        self.max = np.nanmax(stats_generator.values)
        self.mean = np.nanmean(stats_generator.values)
        self.median = np.nanmedian(stats_generator.values)
        self.stdev = np.nanstd(stats_generator.values)

    # Flatten for export to JSON
    def flatten(self):

        return [self.min, self.max, self.mean, self.median, self.stdev]


class EventParser:

    def __init__(self):

        # Event counter
        self.count = 0
        # Event type
        self.type = None


class ChangeVoxel:

    def __init__(self):

        self.value = None
        self.type = None
        self.timepoints = []


class MissingObservation:

    def __init__(self):

        self.voxels = {}


class Event:

    def __init__(self):

        self.voxels = {}
        self.timepoints = None
        self.grid = None
        self.type = None
        self.volume = None

    def set_volume(self):

        # Set volume to 0
        self.volume = 0
        # For each row
        for row in self.voxels.keys():
            # Add the change
            self.volume += self.voxels[row]
        self.volume = self.grid.get_voxel_volume(self.volume)

    def get_volume(self):
        # If volume is not set
        if not self.volume:
            # Set it
            self.set_volume()
        # Return the volume
        return self.volume

    def is_gain(self):
        if self.type == 'Gain':
            return True
        elif self.type == 'Loss':
            return False

    # Return the mean height of voxels for the event
    def get_mean_height(self):
        row_total = 0
        # For each row key
        for row_key in self.voxels.keys():
            # Add to total
            row_total += int(row_key)
        # Return the mean
        return (row_total / len(list(self.voxels.keys()))) * self.grid.voxel_size

    def get_min_height(self):
        return int(sorted(list(self.voxels.keys()), key=int)[0]) * self.grid.voxel_size

    def get_max_height(self):
        return int(sorted(list(self.voxels.keys()), key=int)[-1]) * self.grid.voxel_size

    def get_height_range(self):
        return self.get_max_height() - self.get_min_height()

    def get_coeff_var(self):
        # Values for event
        event_values = []
        # For row key
        for row_key in self.voxels.keys():
            event_values.append(self.voxels[row_key])
        # Return STDev/Mean
        return np.std(event_values) / np.mean(event_values)

    def get_row_change_plot_vars(self):
        # Lists for plotting variable
        rows = []
        change = []
        # For each row (sorted top to bottom)
        for row in sorted(self.voxels.keys(), key=int, reverse=True):
            # Store the values
            rows.append(int(row))
            change.append(self.voxels[row])
        # Return the plotting variables
        return rows, change

    def get_cumulative_change_plot_vars(self):
        # Lists for plotting variable
        rows = []
        change = []
        # Current cumulative change
        curr_change = 0
        # For each row (sorted top to bottom)
        for row in sorted(self.voxels.keys(), key=int, reverse=True):
            # Update current change
            curr_change += self.voxels[row]
            # Store the values
            rows.append(int(row))
            change.append(curr_change)
        # Return the plotting variables
        return rows, change