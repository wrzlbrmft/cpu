# a relocation table is an array of relocations, each relocation is a map containing the machine code offset and the
# array index of the symbol name in the corresponding symbol table

import symbol_table


def rebuild(relocation_table, old_symbol_table, new_symbol_table=None):
    new_symbol_table = symbol_table.get_symbol_table(new_symbol_table)

    for relocation in relocation_table:
        symbol_name = symbol_table.get_symbol_name(relocation['symbol_index'], old_symbol_table)
        relocation['symbol_index'] = symbol_table.get_index(symbol_name, new_symbol_table)
