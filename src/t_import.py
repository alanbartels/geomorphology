from os.path import exists
from pathlib import Path
import logging
import c_voxels


def yield_ascii_rows(file_path):

    for row in open(file_path, 'r'):

        yield row


# Takes a pathlib Path object
def parse_ascii_file(file_path):

    # If the path does not exist
    if not exists(file_path):
        # Log an error
        logging.error(f'File import failed. File path {file_path} does not exist.')
        # Exit the function returning None
        return None



