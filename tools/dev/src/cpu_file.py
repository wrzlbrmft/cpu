import endianness
import fileutils
import symbol_table
import symbols


def build_cpu_symbols(errors=None, link_base=0, _symbol_table=None, _symbols=None):
    _symbols = symbols.get_symbols(_symbols)

    buffer = bytearray()

    for symbol_name in _symbols.keys():
        symbol = symbols.get_symbol(symbol_name, _symbols)

        machine_code = symbol['machine_code']
        for relocation in symbol['relocation_table']:
            relocation_symbol_name = symbol_table.get_symbol_name(relocation['symbol_table_index'], _symbol_table)
            if symbols.symbol_exists(relocation_symbol_name, _symbols):
                relocation_symbol = symbols.get_symbol(relocation_symbol_name, _symbols)
                relocation_addr = link_base + relocation_symbol['machine_code_base']
                machine_code[relocation['machine_code_offset']] = endianness.word_to_le(relocation_addr)[0]
                machine_code[relocation['machine_code_offset'] + 1] = endianness.word_to_le(relocation_addr)[1]
            else:
                if errors is not None:
                    errors.append({
                        'name': 'UNKNOWN_SYMBOL',
                        'info': [relocation_symbol_name]
                    })
                    return None
        buffer.extend(machine_code)

    return buffer


def write_cpu_file(file_name, errors=None, link_base=0, _symbol_table=None, _symbols=None):
    cpu_symbols = build_cpu_symbols(errors, link_base, _symbol_table, _symbols)

    if not errors:
        buffer = bytearray()
        buffer.extend(cpu_symbols)

        # fileutils.dump_buffer(buffer)

        with open(file_name, 'wb') as cpu:
            cpu.write(buffer)
