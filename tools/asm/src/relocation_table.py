def adjust_symbol_table_index(old_symbol_table_index, new_symbol_table_index, relocation_table):
    if new_symbol_table_index != old_symbol_table_index:
        for relocation in relocation_table:
            if relocation['symbol_table_index'] == old_symbol_table_index:
                relocation['symbol_table_index'] = new_symbol_table_index
