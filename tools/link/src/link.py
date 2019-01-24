import struct

total_errors_count = 0
current_file_name = None
current_file_errors_count = 0

obj_files = {}


def obj_file_exists(file_name):
    return file_name in obj_files


def add_obj_file(file_name):
    if not obj_file_exists(file_name):
        obj_files[file_name] = {
            'symbol_table': [],
            'symbols': {}
        }


def get_obj_file(file_name):
    if obj_file_exists(file_name):
        return obj_files[file_name]
    else:
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
    if str_len > 0:
        values = file.read(str_len)
        if len(values) == str_len:
            return str(values)
        else:
            return None
    else:
        return None


def read_obj_header(obj, errors=None):
    return True


def read_obj_symbol_table(obj, errors=None):
    errors = []

    symbol_table_size = read_value_little_endian(obj)
    if symbol_table_size > 0:
        for i in range(0, symbol_table_size):
            symbol_name = read_str(obj)
            machine_code_size = read_value_little_endian(obj)
            if symbol_name is not None and machine_code_size is not None:
                obj_file = get_obj_file(current_file_name)
                obj_file['symbol_table'].append(symbol_name)
                obj_file['symbols'][symbol_name] = {
                    'machine_code_size': machine_code_size,
                    'machine_code': bytearray(),
                    'relocations': []
                }
            else:
                pass
    else:
        pass

    return not errors


def read_obj_symbols(obj, errors=None):
    errors = []

    obj_file = get_obj_file(current_file_name)
    for symbol_name, symbol in obj_file['symbols'].items():
        relocations_size = read_value_little_endian(obj)
        if relocations_size is not None:
            for i in range(0, relocations_size):
                machine_code_offset = read_value_little_endian(obj)
                symbol_index = read_value_little_endian(obj)
                if machine_code_offset is not None and symbol_index is not None:
                    symbol['relocations'].append({
                        'machine_code_offset': machine_code_offset,
                        'symbol_index': symbol_index
                    })
                else:
                    pass

            if not errors:
                machine_code = obj.read(symbol['machine_code_size'])
                if len(machine_code) == symbol['machine_code_size']:
                    symbol['machine_code'].extend(machine_code)
                else:
                    pass
        else:
            pass

    return not errors


def read_obj_file(file_name):
    global current_file_name, current_file_errors_count

    errors = []

    with open(file_name, 'rb') as obj:
        if obj_file_exists(file_name):
            pass
        else:
            current_file_name = file_name
            current_file_errors_count = 0

            add_obj_file(current_file_name)

            read_obj_header(obj, errors)
            read_obj_symbol_table(obj, errors)
            read_obj_symbols(obj, errors)


def read_obj_files(file_names):
    for file_name in file_names:
        read_obj_file(file_name)


# main


read_obj_files(['test1.obj'])
