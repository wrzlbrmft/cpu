import sys

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


# main


if '__main__' == __name__:
    if len(sys.argv) < 2:
        pass
    else:
        obj_file_names = sys.argv[1:]
