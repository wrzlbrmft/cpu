import os
import struct
import sys

obj_file_signature = 'MPO'
max_obj_file_version = 0

total_errors_count = 0
current_file_name = None
current_file_errors_count = 0
current_file_version = None
current_symbol_name = None
current_symbol_errors_count = 0

symbol_table = []
symbols = {}

obj_files = {}

link_base = 0
link_offset = 0

error_messages = {
    'NO_OBJ_FILES': 'no object file(s)',
    'DUPLICATE_OBJ_FILE': "duplicate object file '{}'",
    'UNEXPECTED_EOF': 'unexpected end of file',
    'INCOMPATIBLE_OBJ_FILE_VERSION': 'incompatible object file version (given: {}, max: {})',
    'NOT_OBJ_FILE': 'not an object file',
    'INVALID_SYMBOL_TABLE_SIZE': 'invalid symbol table size',
    'CORRUPT_SYMBOL_TABLE': 'corrupt symbol table',
    'DUPLICATE_SYMBOL': "duplicate symbol '{}'",
    'CORRUPT_MACHINE_CODE': 'corrupt machine code',
    'CORRUPT_RELOCATIONS': 'corrupt relocations',
    'UNKNOWN_SYMBOL': "unknown symbol '{}'"
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


def obj_file_get_symbol_index(name, file_name=None):
    if file_name is None:
        file_name = current_file_name

    obj_file = get_obj_file(file_name)
    if name not in obj_file['symbol_table']:
        obj_file['symbol_table'].append(name)
    return obj_file['symbol_table'].index(name)


def obj_file_get_symbol_name(index, file_name=None):
    if file_name is None:
        file_name = current_file_name

    obj_file = get_obj_file(file_name)
    return obj_file['symbol_table'][index]


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
    file_names = []
    for file_name, obj_file in obj_files.items():
        if name in obj_file['symbols'].keys():
            file_names.append(file_name)
    return file_names


def to_little_endian(value):
    return struct.pack('<H', value)


def to_big_endian(value):
    return struct.pack('>H', value)


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


def read_str(file, length=None):
    if length is None:
        length = read_value(file)

    if 0 == length:
        return ''
    elif length > 0:
        values = file.read(length)
        if len(values) == length:
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
    global current_file_version

    file_signature = read_str(obj, len(obj_file_signature))
    if file_signature is None:
        errors.append({
            'name': 'UNEXPECTED_EOF',
            'info': []
        })
    elif file_signature == obj_file_signature:
        obj_file_version = read_value(obj)
        if obj_file_version is None:
            errors.append({
                'name': 'UNEXPECTED_EOF',
                'info': []
            })
        elif obj_file_version > max_obj_file_version:
            errors.append({
                'name': 'INCOMPATIBLE_OBJ_FILE_VERSION',
                'info': [obj_file_version, max_obj_file_version]
            })
        else:
            current_file_version = obj_file_version
    else:
        errors.append({
            'name': 'NOT_OBJ_FILE',
            'info': []
        })


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
            elif symbol_name in obj_file['symbol_table']:
                errors.append({
                    'name': 'DUPLICATE_SYMBOL',
                    'info': [symbol_name]
                })
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
    global current_file_name, current_file_errors_count, current_file_version, current_symbol_name, \
        current_symbol_errors_count

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

            current_file_name = None
            current_file_errors_count = 0
            current_file_version = None
            current_symbol_name = None
            current_symbol_errors_count = 0


def read_obj_files(file_names):
    for file_name in file_names:
        read_obj_file(file_name)


def link_symbol(name):
    global link_offset

    if not symbol_exists(name):
        file_names = find_symbol(name)
        if not file_names:
            show_error({
                'name': 'UNKNOWN_SYMBOL',
                'info': [name]
            })
        elif len(file_names) > 1:
            show_error({
                'name': 'DUPLICATE_SYMBOL',
                'info': [name]
            })
        else:
            file_name = file_names[0]
            obj_file_symbol = obj_file_get_symbol(name, file_name)
            get_symbol_index(name)
            symbol = add_symbol(name)

            symbol['machine_code'] = obj_file_symbol['machine_code']
            for relocation in obj_file_symbol['relocations']:
                symbol['relocations'].append({
                    'machine_code_offset': relocation['machine_code_offset'],
                    'symbol_index': get_symbol_index(obj_file_get_symbol_name(relocation['symbol_index'], file_name))
                })

            symbol['machine_code_base'] = link_offset
            link_offset += len(symbol['machine_code'])


def link_obj_file(file_name):
    obj_file = get_obj_file(file_name)
    for symbol_name in obj_file['symbols'].keys():
        link_symbol(symbol_name)


def link_obj_files(file_names):
    for file_name in file_names:
        link_obj_file(file_name)


def build_obj_header():
    buffer = bytearray()

    buffer.extend(map(ord, obj_file_signature))
    buffer.append(max_obj_file_version)

    return buffer


def build_obj_symbol_table():
    buffer = bytearray()

    buffer.extend(to_little_endian(len(symbol_table)))
    for symbol_name in symbol_table:
        buffer.append(len(symbol_name))
        buffer.extend(map(ord, symbol_name))

    return buffer


def build_obj_symbols():
    buffer = bytearray()

    for symbol_name in symbol_table:
        if symbol_exists(symbol_name):
            symbol = get_symbol(symbol_name)

            machine_code_size = len(symbol['machine_code'])
            buffer.extend(to_little_endian(machine_code_size))
            buffer.extend(symbol['machine_code'])

            relocations_size = len(symbol['relocations'])
            buffer.extend(to_little_endian(relocations_size))
            for relocation in symbol['relocations']:
                buffer.extend(to_little_endian(relocation['machine_code_offset']))
                buffer.extend(to_little_endian(relocation['symbol_index']))
        else:
            buffer.extend([0, 0])

    return buffer


def write_obj_file(file_name):
    with open(file_name, 'wb') as obj:
        obj_header = build_obj_header()
        obj_symbol_table = build_obj_symbol_table()
        obj_symbols = build_obj_symbols()

        buffer = bytearray()
        buffer.extend(obj_header)
        buffer.extend(obj_symbol_table)
        buffer.extend(obj_symbols)

        # dump_buffer(buffer)

        obj.write(buffer)


# main


if len(sys.argv) < 1:
    show_error({
        'name': 'NO_OBJ_FILES',
        'info': []
    })
else:
    obj_file_names = sys.argv[1:]

    read_obj_files(obj_file_names)

    if not total_errors_count:
        main_obj_file_names = find_symbol('main')
        if len(main_obj_file_names) > 1:
            show_error({
                'name': 'DUPLICATE_SYMBOL',
                'info': ['main']
            })
        elif 1 == len(main_obj_file_names):
            link_symbol('main')
            link_obj_file(main_obj_file_names[0])
            del obj_files[main_obj_file_names[0]]
            link_obj_files(obj_files.keys())

            bin_file_name = os.path.splitext(main_obj_file_names[0])[0] + '.bin'
        else:
            link_obj_files(obj_files.keys())

            obj_file_name = 'output.obj'
            write_obj_file(obj_file_name)

    if total_errors_count:
        print(f'{total_errors_count} total error(s)')
