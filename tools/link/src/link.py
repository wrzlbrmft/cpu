obj_files = []


def obj_file_exists(file_name):
    return file_name in obj_files


def add_obj_file(file_name):
    if not obj_file_exists(file_name):
        obj_files[file_name] = {
            'symbol_table': [],
            'symbols': {}
        }


def read_obj_header(obj, errors=None):
    return True


def read_obj_symbol_table(obj, errors=None):
    return True


def read_obj_file(file_name):
    errors = []

    with open(file_name, 'rb') as obj:
        read_obj_header(obj, errors)
        read_obj_symbol_table(obj, errors)


def read_obj_files(file_names):
    for file_name in file_names:
        read_obj_file(file_name)


# main


read_obj_files(['test1.obj'])
