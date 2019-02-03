_symbol_table = []


def get_symbol_table(symbol_table=None):
    if symbol_table is None:
        return _symbol_table
    else:
        return symbol_table


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
