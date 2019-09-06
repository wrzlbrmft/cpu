# usage: link [obj files...]

import cpu_file
import i18n
import obj_file
import relocation_table
import symbol_table
import symbols

import os
import sys

total_errors_count = 0

current_obj_file_name = None

# object files are a map keyed by the object file name, each object file containing the symbol table and the symbols
obj_files = {}

# this is the memory address to which a program is loaded before it is executed by the cpu
# the value is used when determining the absolute memory address of a relocated symbol
# using the .base directive, the assembler allows setting the link base which is then stored in the object file header
link_base = None

# this is the current size of the byte-stream of machine code of all symbols linked so far
# the value is set as the machine code base of the next symbol to be linked, which is its offset in the byte-stream
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


def link_symbol(symbol_name, file_name=None):
    global link_base, link_offset

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
                'name': 'AMBIGUOUS_SYMBOL',
                'info': [symbol_name]
            })
            return
        elif file_name is None or obj_file_names[0] == file_name:
            # copy the symbol from the object file symbols to the global symbols
            _obj_file = get_obj_file(obj_file_names[0])

            if _obj_file['header']['link_base'] is not None:
                if link_base is not None and _obj_file['header']['link_base'] != link_base:
                    show_error({
                        'name': 'AMBIGUOUS_LINK_BASE',
                        'info': [link_base, obj_file_names[0], _obj_file['header']['link_base']]
                    })
                    return
                else:
                    link_base = _obj_file['header']['link_base']

            obj_file_symbol = symbols.get_symbol(symbol_name, _obj_file['symbols'])

            symbol_table.add_symbol(symbol_name)
            symbol = symbols.add_symbol(symbol_name)

            symbol['machine_code'] = obj_file_symbol['machine_code']
            symbol['relocation_table'] = obj_file_symbol['relocation_table']

            # rebuild the relocation table to use the symbol indexes from the global symbol table
            relocation_table.rebuild(symbol['relocation_table'], _obj_file['symbol_table'])

            # set the machine code base to the current link offset and increment it for the next symbol to be linked
            symbol['machine_code_base'] = link_offset
            link_offset += len(symbol['machine_code'])


def link_obj_file(file_name):
    global current_obj_file_name

    current_obj_file_name = file_name

    _obj_file = get_obj_file(file_name)
    for symbol_name in _obj_file['symbols'].keys():
        link_symbol(symbol_name, file_name)


def link_obj_files(file_names):
    for file_name in file_names:
        link_obj_file(file_name)


# main


def main():
    global current_obj_file_name

    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        pass  # TODO: help
    elif len(sys.argv) < 2:
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
                # if there is one 'main' symbol, then create a cpu file (executable)
                current_obj_file_name = ''

                # link order:
                #   1. the 'main' symbol
                #   2. all other symbols of the object file that contains the 'main' symbol in the given order
                #   3. all symbols of all other object files in the given order
                link_symbol('main')
                link_obj_file(main_obj_file_names[0])
                del obj_files[main_obj_file_names[0]]
                link_obj_files(obj_files.keys())

                if not total_errors_count:
                    errors = []

                    cpu_file_name = os.path.splitext(os.path.basename(main_obj_file_names[0]))[0] + '.cpu'
                    cpu_file.write_cpu_file(cpu_file_name, errors, link_base=link_base)

                    if errors:
                        show_error(errors[0], '')
            else:
                # if there is no 'main' symbol, then create a new object file (library)

                # link order:
                #   - all symbols of all object files in the given order
                link_obj_files(obj_files.keys())

                if not total_errors_count:
                    obj_file_name = 'output.obj'
                    obj_file.write_obj_file(obj_file_name)


if '__main__' == __name__:
    main()

    if total_errors_count:
        sys.exit(1)
