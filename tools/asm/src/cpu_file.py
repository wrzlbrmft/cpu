# cpu file format:
#   ? bytes  machine code
#   --- eof ---

import binutils
import fileutils
import symbol_table
import symbols

default_link_base = 0x0000


def build_cpu_symbols(errors=None, _symbol_table=None, _symbols=None, link_base=None):
    _symbols = symbols.get_symbols(_symbols)
    if link_base is None:
        link_base = default_link_base

    buffer = bytearray()

    for symbol_name in _symbols.keys():
        symbol = symbols.get_symbol(symbol_name, _symbols)

        machine_code = symbol['machine_code']
        # do the relocation...
        for relocation in symbol['relocation_table']:
            relocation_symbol_name = symbol_table.get_symbol_name(relocation['symbol_table_index'], _symbol_table)
            if symbols.symbol_exists(relocation_symbol_name, _symbols):
                # determine the absolute memory address of the relocated symbol by adding its machine code base to the
                # link base (the machine code base was set when linking the relocated symbol)
                # the link base is the memory address to which a program is loaded before it is executed by the cpu
                relocation_symbol = symbols.get_symbol(relocation_symbol_name, _symbols)
                relocation_symbol_addr = link_base + relocation_symbol['machine_code_base']

                # insert the absolute memory address of the relocated symbol into the machine code of the current symbol
                # at the correct offset
                machine_code[relocation['machine_code_offset']] = binutils.word_to_le(relocation_symbol_addr)[0]
                machine_code[relocation['machine_code_offset'] + 1] = binutils.word_to_le(relocation_symbol_addr)[1]
            else:
                if errors is not None:
                    errors.append({
                        'name': 'UNKNOWN_SYMBOL',
                        'info': [relocation_symbol_name]
                    })
                    return None
        buffer.extend(machine_code)

    return buffer


def write_cpu_file(file_name, errors=None, _symbol_table=None, _symbols=None, link_base=None):
    cpu_symbols = build_cpu_symbols(errors, _symbol_table, _symbols, link_base)

    if not errors:
        buffer = bytearray()
        buffer.extend(cpu_symbols)

        # fileutils.dump_buffer(buffer)

        with open(file_name, 'wb') as cpu:
            cpu.write(buffer)
