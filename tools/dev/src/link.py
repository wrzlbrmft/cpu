import sys

import i18n
import obj_file

total_errors_count = 0

current_obj_file_name = None

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


def show_error(error, obj_file_name=None):
    global total_errors_count

    if obj_file_name is None:
        obj_file_name = current_obj_file_name

    total_errors_count += 1

    if obj_file_name:
        print(f'{obj_file_name}: ', end='')

    print('error:', i18n.error_messages[error['name']].format(*error['info']))

    print()


def read_obj_files(file_names):
    global current_obj_file_name

    for file_name in file_names:
        current_obj_file_name = file_name

        if obj_file_exists(file_name):
            show_error({
                'name': 'DUPLICATE_OBJ_FILE',
                'info': [current_obj_file_name]
            }, '')
            return
        else:
            errors = []

            header, _symbol_table, _symbols = obj_file.read_obj_file(current_obj_file_name, errors)

            if not errors:
                _obj_file = add_obj_file(current_obj_file_name)

                _obj_file['symbol_table'] = _symbol_table
                _obj_file['symbols'] = _symbols

            if errors:
                show_error(errors[0])


# main


def main():
    if len(sys.argv) < 2:
        show_error({
            'name': 'NO_OBJ_FILES',
            'info': []
        })
    else:
        obj_file_names = sys.argv[1:]
        read_obj_files(obj_file_names)

        if not total_errors_count:
            pass


if '__main__' == __name__:
    main()
