_symbols = {}


def symbol_exists(symbol_name, symbols=None):
    if symbols is None:
        symbols = _symbols

    return symbol_name in symbols.keys()


def get_symbol(symbol_name, symbols=None):
    if symbols is None:
        symbols = _symbols

    if symbol_exists(symbol_name, symbols):
        return symbols[symbol_name]
    else:
        return None


def add_symbol(symbol_name, symbols=None):
    if symbols is None:
        symbols = _symbols

    if not symbol_exists(symbol_name, symbols):
        symbols[symbol_name] = {
            'machine_code': bytearray(),
            'relocation_table': [],
        }
    return get_symbol(symbol_name, symbols)
