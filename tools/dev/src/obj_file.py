import endianness
import fileutils
import symbol_table
import symbols

obj_file_signature = 'MPO'
max_obj_file_version = 0


def build_obj_file_header():
    buffer = bytearray()
    buffer.extend(map(ord, obj_file_signature))
    buffer.append(max_obj_file_version)
    return buffer


def build_obj_file_symbol_table(_symbol_table=None):
    _symbol_table = symbol_table.get_symbol_table(_symbol_table)

    buffer = bytearray()
    symbol_table_size = len(_symbol_table)
    buffer.extend(endianness.word_to_le(symbol_table_size))
    for symbol_name in _symbol_table:
        buffer.append(len(symbol_name))
        buffer.extend(map(ord, symbol_name))
    return buffer


def build_obj_file_symbols(_symbol_table=None, _symbols=None):
    _symbol_table = symbol_table.get_symbol_table(_symbol_table)

    buffer = bytearray()
    for symbol_name in _symbol_table:
        if symbols.symbol_exists(symbol_name, _symbols):
            symbol = symbols.get_symbol(symbol_name, _symbols)

            machine_code_size = len(symbol['machine_code'])
            buffer.extend(endianness.word_to_le(machine_code_size))
            buffer.extend(symbol['machine_code'])

            relocation_table_size = len(symbol['relocation_table'])
            buffer.extend(endianness.word_to_le(relocation_table_size))
            for relocation in symbol['relocation_table']:
                buffer.extend(endianness.word_to_le(relocation['machine_code_offset']))
                buffer.extend(endianness.word_to_le(relocation['symbol_table_index']))
        else:
            buffer.extend([0, 0])
    return buffer


def write_obj_file(file_name, _symbol_table=None, _symbols=None):
    obj_file_header = build_obj_file_header()
    obj_file_symbol_table = build_obj_file_symbol_table(_symbol_table)
    obj_file_symbols = build_obj_file_symbols(_symbol_table, _symbols)

    buffer = bytearray()
    buffer.extend(obj_file_header)
    buffer.extend(obj_file_symbol_table)
    buffer.extend(obj_file_symbols)

    # fileutils.dump_buffer(buffer)

    with open(file_name, 'wb') as obj:
        obj.write(buffer)