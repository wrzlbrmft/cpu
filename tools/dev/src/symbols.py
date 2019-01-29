_symbols = {}


def get_symbols(symbols=None):
    if symbols is None:
        return _symbols
    else:
        return symbols


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


def add_symbol(symbol_name, symbol=None, symbols=None):
    if symbols is None:
        symbols = _symbols

    if not symbol_exists(symbol_name, symbols):
        if symbol is None:
            symbols[symbol_name] = {
                'machine_code': bytearray(),
                'relocation_table': [],
            }
        else:
            symbols[symbol_name] = symbol
    return get_symbol(symbol_name, symbols)
