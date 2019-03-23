# symbols are a map keyed by the symbol name, each symbol is a map containing the machine code and the relocation table

import symbol_table

_symbols = {}


def get_symbols(symbols=None):
    if symbols is None:
        return _symbols
    else:
        return symbols


def symbol_exists(symbol_name, symbols=None):
    symbols = get_symbols(symbols)

    return symbol_name in symbols.keys()


def get_symbol(symbol_name, symbols=None):
    symbols = get_symbols(symbols)

    if symbol_exists(symbol_name, symbols):
        return symbols[symbol_name]
    else:
        return None


def add_symbol(symbol_name, proc_name=None, symbols=None, _symbol_table=None):
    symbols = get_symbols(symbols)

    if not symbol_exists(symbol_name, symbols):
        symbols[symbol_name] = {
            'proc_index': symbol_table.get_index(proc_name, _symbol_table),
            'machine_code': bytearray(),
            'relocation_table': [],
        }

    return get_symbol(symbol_name, symbols)
