import os
import struct
import sys

total_errors_count = 0
current_file_name = None
current_file_errors_count = 0
current_symbol_name = None
current_symbol_errors_count = 0

symbol_table = []
symbols = {}

obj_files = {}

error_messages = {
    'DUPLICATE_OBJ_FILE': "duplicate object file '{}'",
    'UNEXPECTED_EOF': 'unexpected end of file',
    'INVALID_SYMBOL_TABLE_SIZE': 'invalid symbol table size',
    'CORRUPT_SYMBOL_TABLE': 'corrupt symbol table',
    'DUPLICATE_SYMBOL': "duplicate symbol '{}'",
    'CORRUPT_MACHINE_CODE': 'corrupt machine code',
    'CORRUPT_RELOCATIONS': 'corrupt relocations'
}


def get_symbol_index(name):
    if name not in symbol_table:
        symbol_table.append(name)
    return symbol_table.index(name)


def get_symbol_name(index):
    return symbol_table[index]


def symbol_exists(name):
    return name in symbols.keys()


def get_symbol(name):
    if symbol_exists(name):
        return symbols[name]
    else:
        return None


def get_current_symbol():
    return get_symbol(current_symbol_name)


def add_symbol(name):
    if not symbol_exists(name):
        symbols[name] = {
            'machine_code': bytearray(),
            'relocations': []
        }

    return get_symbol(name)


def obj_file_exists(file_name):
    return file_name in obj_files.keys()


def get_obj_file(file_name):
    if obj_file_exists(file_name):
        return obj_files[file_name]
    else:
        return None


def get_current_obj_file():
    return get_obj_file(current_file_name)


def add_obj_file(file_name):
    if not obj_file_exists(file_name):
        obj_files[file_name] = {
            'symbol_table': [],
            'symbols': {}
        }

    return get_obj_file(file_name)


def obj_file_symbol_exists(name, file_name=None):
    if file_name is None:
        file_name = current_file_name

    obj_file = get_obj_file(file_name)
    return name in obj_file['symbols'].keys()


def obj_file_get_symbol(name, file_name=None):
    if file_name is None:
        file_name = current_file_name

    if obj_file_symbol_exists(name, file_name):
        obj_file = get_obj_file(file_name)
        return obj_file['symbols'][name]
    else:
        return None


def obj_file_add_symbol(name, file_name=None):
    if file_name is None:
        file_name = current_file_name

    if not obj_file_symbol_exists(name, file_name):
        obj_file = get_obj_file(file_name)
        obj_file['symbols'][name] = {
            'machine_code': bytearray(),
            'relocations': []
        }

    return obj_file_get_symbol(name, file_name)


def find_symbol(name):
    for file_name, obj_file in obj_files.items():
        if name in obj_file['symbols'].keys():
            return file_name
    return None


def from_little_endian(values):
    return struct.unpack('<H', values)[0]


def from_big_endian(values):
    return struct.unpack('>H', values)[0]


def read_value_little_endian(file):
    values = file.read(2)
    if 2 == len(values):
        return from_little_endian(values)
    else:
        return None


def read_value_big_endian(file):
    values = file.read(2)
    if 2 == len(values):
        return from_big_endian(values)
    else:
        return None


def read_value(file):
    value = file.read(1)
    if 1 == len(value):
        return value[0]
    else:
        return None


def read_str(file):
    str_len = read_value(file)
    if 0 == str_len:
        return ''
    elif str_len > 0:
        values = file.read(str_len)
        if len(values) == str_len:
            return values.decode('ascii')
        else:
            return None
    else:
        return None


def show_error(error):
    global total_errors_count, current_file_errors_count, current_symbol_errors_count

    total_errors_count += 1

    if current_symbol_name and not current_symbol_errors_count:
        current_symbol_errors_count += 1
        if current_file_name:
            print(f'{current_file_name}: ', end='')
        print(f"in symbol '{current_symbol_name}':")

    if current_file_name:
        current_file_errors_count += 1
        print(f'{current_file_name}: ', end='')

    print('error:', error_messages[error['name']].format(*error['info']))

    print()


def read_obj_header(obj, errors=None):
    pass


def read_obj_symbol_table(obj, errors=None):
    symbol_table_size = read_value_little_endian(obj)
    if symbol_table_size is None:
        errors.append({
            'name': 'UNEXPECTED_EOF',
            'info': []
        })
    elif 0 == symbol_table_size:
        errors.append({
            'name': 'INVALID_SYMBOL_TABLE_SIZE',
            'info': []
        })
    else:
        obj_file = get_current_obj_file()
        for i in range(0, symbol_table_size):
            symbol_name = read_str(obj)
            if symbol_name is None:
                errors.append({
                    'name': 'CORRUPT_SYMBOL_TABLE',
                    'info': []
                })
                break
            else:
                obj_file['symbol_table'].append(symbol_name)


def read_obj_symbols(obj, errors=None):
    global current_symbol_name, current_symbol_errors_count

    obj_file = get_current_obj_file()
    for symbol_name in obj_file['symbol_table']:
        current_symbol_name = symbol_name
        current_symbol_errors_count = 0

        machine_code_size = read_value_little_endian(obj)
        if machine_code_size is None:
            errors.append({
                'name': 'UNEXPECTED_EOF',
                'info': []
            })
        elif machine_code_size:
            if symbol_exists(symbol_name):
                errors.append({
                    'name': 'DUPLICATE_SYMBOL',
                    'info': [symbol_name]
                })
            else:
                add_symbol(symbol_name)
                symbol = obj_file_add_symbol(symbol_name)

                machine_code = obj.read(machine_code_size)
                if len(machine_code) == machine_code_size:
                    symbol['machine_code'].extend(machine_code)
                else:
                    errors.append({
                        'name': 'CORRUPT_MACHINE_CODE',
                        'info': []
                    })

                relocations_size = read_value_little_endian(obj)
                if relocations_size is None:
                    errors.append({
                        'name': 'UNEXPECTED_EOF',
                        'info': []
                    })
                else:
                    for i in range(0, relocations_size):
                        machine_code_offset = read_value_little_endian(obj)
                        symbol_index = read_value_little_endian(obj)
                        if machine_code_offset is None or symbol_index is None:
                            errors.append({
                                'name': 'CORRUPT_RELOCATIONS',
                                'info': []
                            })
                            break
                        else:
                            symbol['relocations'].append({
                                'machine_code_offset': machine_code_offset,
                                'symbol_index': symbol_index
                            })


def read_obj_file(file_name):
    global current_file_name, current_file_errors_count

    if obj_file_exists(file_name):
        show_error({
            'name': 'DUPLICATE_OBJ_FILE',
            'info': [file_name]
        })
    else:
        with open(file_name, 'rb') as obj:
            current_file_name = file_name
            current_file_errors_count = 0

            add_obj_file(current_file_name)

            errors = []
            read_obj_header(obj, errors)
            read_obj_symbol_table(obj, errors)
            read_obj_symbols(obj, errors)

            for error in errors:
                show_error(error)

            # end of file

            if current_file_errors_count:
                print(f'{current_file_name}: {current_file_errors_count} error(s)')


def read_obj_files(file_names):
    for file_name in file_names:
        read_obj_file(file_name)


def link_symbol(name):
    pass


# main


read_obj_files(['bounce.obj'])

if not total_errors_count:
    current_file_name = None
    current_file_errors_count = 0
    current_symbol_name = None
    current_symbol_errors_count = 0

    # symbol_table.clear()
    symbols.clear()

    if find_symbol('main'):
        link_symbol('main')
    else:
        pass

if total_errors_count:
    print(f'{total_errors_count} total error(s)')
