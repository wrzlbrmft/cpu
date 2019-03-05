# a symbol table is an array of symbol names
# note: relocation tables are using the array index of the symbol name as the reference

_symbol_table = []


def get_symbol_table(symbol_table=None):
    if symbol_table is None:
        return _symbol_table
    else:
        return symbol_table


def set_symbol_table(symbol_table):
    global _symbol_table

    _symbol_table = symbol_table


def symbol_exists(symbol_name, symbol_table=None):
    symbol_table = get_symbol_table(symbol_table)

    return symbol_name in symbol_table


def get_index(symbol_name, symbol_table=None):
    symbol_table = get_symbol_table(symbol_table)

    # add the symbol if it does not exist yet
    if not symbol_exists(symbol_name, symbol_table):
        symbol_table.append(symbol_name)

    return symbol_table.index(symbol_name)


def get_symbol_name(index, symbol_table=None):
    symbol_table = get_symbol_table(symbol_table)

    if index < len(symbol_table):
        return symbol_table[index]
    else:
        return None


def add_symbol(symbol_name, symbol_table=None):
    get_index(symbol_name, symbol_table)


def remove_symbol(symbol_name, symbol_table=None):
    symbol_table = get_symbol_table(symbol_table)
    symbol_table.remove(symbol_name)
