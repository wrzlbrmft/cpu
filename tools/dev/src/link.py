import os
import sys

import cpu_file
import i18n
import obj_file
import symbol_table
import symbols

total_errors_count = 0

current_obj_file_name = None

# object files are a map keyed by the object file name, each object file containing a symbol table and symbols
obj_files = {}

# keeps track of the byte count when linking symbols by adding up the sizes of their machine code
# used for relocation when writing a cpu file
link_offset = 0


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


def get_symbol_obj_file_names(symbol_name):
    file_names = []
    for file_name in obj_files.keys():
        _obj_file = get_obj_file(file_name)
        if symbols.symbol_exists(symbol_name, _obj_file['symbols']):
            file_names.append(file_name)

    return file_names


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

                _obj_file['header'] = header
                _obj_file['symbol_table'] = _symbol_table
                _obj_file['symbols'] = _symbols

            if errors:
                show_error(errors[0])


def link_symbol(symbol_name):
    global link_offset

    if not symbols.symbol_exists(symbol_name):
        obj_file_names = get_symbol_obj_file_names(symbol_name)
        if not obj_file_names:
            show_error({
                'name': 'UNKNOWN_SYMBOL',
                'info': [symbol_name]
            })
            return
        elif len(obj_file_names) > 1:
            show_error({
                'name': 'DUPLICATE_SYMBOL',
                'info': [symbol_name]
            })
            return
        else:
            # copy symbol from object file symbols to global symbols
            _obj_file = get_obj_file(obj_file_names[0])
            obj_file_symbol = symbols.get_symbol(symbol_name, _obj_file['symbols'])

            symbol_table.get_index(symbol_name)
            symbol = symbols.add_symbol(symbol_name)

            symbol['machine_code'] = obj_file_symbol['machine_code']
            for relocation in obj_file_symbol['relocation_table']:
                # adjust symbol table index from object file symbol table to global symbol table
                relocation_symbol_name = symbol_table.get_symbol_name(relocation['symbol_table_index'],
                                                                      _obj_file['symbol_table'])
                symbol['relocation_table'].append({
                    'machine_code_offset': relocation['machine_code_offset'],
                    'symbol_table_index': symbol_table.get_index(relocation_symbol_name)
                })

            # set of the machine code base (derived from the link offset)
            # used for relocation when writing a cpu file
            symbol['machine_code_base'] = link_offset
            link_offset += len(symbol['machine_code'])


def link_obj_file(file_name):
    global current_obj_file_name

    current_obj_file_name = file_name

    _obj_file = get_obj_file(file_name)
    for symbol_name in _obj_file['symbols'].keys():
        link_symbol(symbol_name)


def link_obj_files(file_names):
    for file_name in file_names:
        link_obj_file(file_name)


# main


def main():
    global current_obj_file_name

    if len(sys.argv) < 2:
        show_error({
            'name': 'NO_OBJ_FILES',
            'info': []
        })
    else:
        obj_file_names = sys.argv[1:]
        read_obj_files(obj_file_names)

        if not total_errors_count:
            main_obj_file_names = get_symbol_obj_file_names('main')
            if len(main_obj_file_names) > 1:
                # there can only be one 'main' symbol
                show_error({
                    'name': 'DUPLICATE_SYMBOL',
                    'info': ['main']
                }, '')
            elif 1 == len(main_obj_file_names):
                # if there is one 'main' symbol, then create a cpu file
                current_obj_file_name = ''

                # link order:
                # 1. 'main' symbol
                # 2. all symbols of the object file that contains the 'main' symbol in the order of their appearance
                # 3. all symbols of all other object files in the order of their appearance
                link_symbol('main')
                link_obj_file(main_obj_file_names[0])
                del obj_files[main_obj_file_names[0]]
                link_obj_files(obj_files.keys())

                if not total_errors_count:
                    errors = []

                    cpu_file_name = os.path.splitext(os.path.basename(main_obj_file_names[0]))[0] + '.cpu'
                    cpu_file.write_cpu_file(cpu_file_name, errors, 0)  # link_base=0

                    if errors:
                        show_error(errors[0], '')
            else:
                # if there is no 'main' symbol, then create a combined object file (library)

                # link order:
                # - all symbols of all object files in the order of their appearance
                link_obj_files(obj_files.keys())

                if not total_errors_count:
                    obj_file_name = 'output.obj'
                    obj_file.write_obj_file(obj_file_name)


if '__main__' == __name__:
    main()
