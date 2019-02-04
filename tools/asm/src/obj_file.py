# object file format:
#   4 bytes  header
#   ? bytes  symbol table
#   ? bytes  the symbols
#   --- eof ---
#
#
# header:
#   3 bytes  file signature ('MPO')
#   1 byte   file version
#
# symbol table:
#   1 word   number of symbol names in symbol table
#   ? bytes  the symbol names in symbol table
#
# a symbol name in symbol table:
#   1 byte   length of symbol name
#   ? bytes  symbol name
#
# a symbol
#   1 word   size of machine code (0=external)
#   --- if not external ---
#   ? bytes  machine code
#   1 word   number of relocations
#   ? bytes  the relocations
#
# a relocation:
#   1 word   machine code offset
#   1 word   symbol table index

import os

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


def read_obj_file_header(file, errors=None):
    file_signature = fileutils.read_str(file, len(obj_file_signature))
    if file_signature is None:
        if errors is not None:
            errors.append({
                'name': 'UNEXPECTED_EOF',
                'info': []
            })
        return None
    elif file_signature == obj_file_signature:
        obj_file_version = fileutils.read_byte(file)
        if obj_file_version is None:
            if errors is not None:
                errors.append({
                    'name': 'CORRUPT_FILE_HEADER',
                    'info': []
                })
            return None
        elif obj_file_version > max_obj_file_version:
            if errors is not None:
                errors.append({
                    'name': 'INCOMPATIBLE_OBJ_FILE_VERSION',
                    'info': []
                })
            return None
        else:
            return {
                'obj_file_version': obj_file_version
            }
    else:
        if errors is not None:
            errors.append({
                'name': 'NOT_OBJ_FILE',
                'info': []
            })
        return None


def read_obj_file_symbol_table(file, errors=None):
    symbol_table_size = fileutils.read_word_le(file)
    if symbol_table_size is None:
        if errors is not None:
            errors.append({
                'name': 'UNEXPECTED_EOF',
                'info': []
            })
        return None
    else:
        _symbol_table = []
        for i in range(0, symbol_table_size):
            symbol_name = fileutils.read_str(file)
            if symbol_name is None:
                if errors is not None:
                    errors.append({
                        'name': 'CORRUPT_SYMBOL_TABLE',
                        'info': []
                    })
                return None
            elif symbol_table.symbol_exists(symbol_name, _symbol_table):
                if errors is not None:
                    errors.append({
                        'name': 'DUPLICATE_SYMBOL',
                        'info': [symbol_name]
                    })
                return None
            else:
                symbol_table.get_index(symbol_name, _symbol_table)

        return _symbol_table


def read_obj_file_symbols(file, _symbol_table=None, errors=None):
    _symbol_table = symbol_table.get_symbol_table(_symbol_table)

    _symbols = {}
    for symbol_name in _symbol_table:
        machine_code_size = fileutils.read_word_le(file)
        if machine_code_size is None:
            if errors is not None:
                errors.append({
                    'name': 'UNEXPECTED_EOF',
                    'info': []
                })
            return None
        elif machine_code_size:
            symbol = symbols.add_symbol(symbol_name, _symbols)

            machine_code = file.read(machine_code_size)
            if len(machine_code) == machine_code_size:
                symbol['machine_code'].extend(machine_code)
            else:
                if errors is not None:
                    errors.append({
                        'name': 'CORRUPT_MACHINE_CODE',
                        'info': []
                    })
                return None

            relocation_table_size = fileutils.read_word_le(file)
            if relocation_table_size is None:
                if errors is not None:
                    errors.append({
                        'name': 'UNEXPECTED_EOF',
                        'info': []
                    })
                return None
            else:
                for i in range(0, relocation_table_size):
                    machine_code_offset = fileutils.read_word_le(file)
                    symbol_table_index = fileutils.read_word_le(file)
                    if machine_code_offset is None or symbol_table_index is None:
                        if errors is not None:
                            errors.append({
                                'name': 'CORRUPT_RELOCATION_TABLE',
                                'info': []
                            })
                        return None
                    else:
                        symbol['relocation_table'].append({
                            'machine_code_offset': machine_code_offset,
                            'symbol_table_index': symbol_table_index
                        })

    return _symbols


def read_obj_file(file_name, errors=None):
    if os.path.isfile(file_name):
        with open(file_name, 'rb') as obj:
            header = read_obj_file_header(obj, errors)
            _symbol_table = None
            _symbols = None

            if not errors:
                _symbol_table = read_obj_file_symbol_table(obj, errors)

            if not errors:
                _symbols = read_obj_file_symbols(obj, _symbol_table, errors)

            return header, _symbol_table, _symbols
    else:
        if errors is not None:
            errors.append({
                'name': 'FILE_NOT_FOUND',
                'info': [file_name]
            })
        return None, None, None
