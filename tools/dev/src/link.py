import sys

import obj_file

obj_files = {}


def obj_file_exists(file_name):
    return file_name in obj_files


def get_obj_file(file_name):
    if obj_file_exists(file_name):
        return obj_files[file_name]
    else:
        return None


def add_obj_file(file_name):
    if not obj_file_exists(file_name):
        obj_files[file_name] = {
            'symbol_table': [],
            'symbols': {}
        }

    return get_obj_file(file_name)


def read_obj_files(file_names):
    for file_name in file_names:
        if obj_file_exists(file_name):
            pass
        else:
            errors = []

            header, _symbol_table, _symbols = obj_file.read_obj_file(file_name, errors)

            if not errors:
                _obj_file = add_obj_file(file_name)

                _obj_file['symbol_table'] = _symbol_table
                _obj_file['symbols'] = _symbols


# main


def main():
    if len(sys.argv) < 2:
        pass
    else:
        obj_file_names = sys.argv[1:]
        read_obj_files(obj_file_names)


if '__main__' == __name__:
    main()
