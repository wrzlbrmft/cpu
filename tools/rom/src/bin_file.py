import os


def write_bin_file(file_name, data):
    pass


def read_bin_file(file_name, errors=None):
    if os.path.isfile(file_name):
        with open(file_name, 'rb') as _bin:
            return list(_bin.read())
    else:
        if errors is not None:
            errors.append({
                'name': 'FILE_NOT_FOUND',
                'info': [file_name]
            })
        return None
