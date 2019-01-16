import shlex

symbol_table = []
symbols = {}
current_symbol = None
current_symbol_has_errors = False

parser_errors = {
    'UNEXPECTED': "unexpected '{}'",
    'SYMBOL_NAME_EXPECTED': 'symbol name expected',
    'DUPLICATE_SYMBOL': "duplicate symbol '{}'"
}


def parser_error(error, file=None, line_number=None, line_str=None):
    global current_symbol_has_errors
    if current_symbol and not current_symbol_has_errors:
        if file:
            print(f'{file}: ', end='')
        print(f"in symbol '{current_symbol}':")
        current_symbol_has_errors = True

    if file:
        print(f'{file}:', end='')
        if line_number:
            print(f'{line_number}:', end='')
        print(' ', end='')

    print('error:', parser_errors[error['name']].format(*error['info']))

    if line_str:
        print('', line_str.strip())

    print()


def parse_asm_line(line_str):
    symbol = None
    directive = None
    mnemonic = None
    operands = []
    operand = ''
    operand_expected = False
    errors = []

    parser = shlex.shlex(line_str)
    parser.commenters = ';'
    parser.wordchars += '.'

    for token in parser:
        if ':' == token:
            if not symbol:
                if mnemonic:
                    if not operand and not operand_expected:
                        symbol = mnemonic
                        mnemonic = None

                    else:
                        errors.append({
                            'name': 'UNEXPECTED',
                            'info': [':']
                        })

                else:
                    errors.append({
                        'name': 'SYMBOL_NAME_EXPECTED',
                        'info': []
                    })

            else:
                errors.append({
                    'name': 'UNEXPECTED',
                    'info': [':']
                })

        elif ',' == token:
            if not operand:
                errors.append({
                    'name': 'UNEXPECTED',
                    'info': [',']
                })

            else:
                operands.append(operand.strip())
                operand = ''
                operand_expected = True

        else:
            if not mnemonic:
                mnemonic = token

            else:
                operand += ' ' + token
                operand_expected = False

    # end of line

    if mnemonic and '.' == mnemonic[0]:
        directive = mnemonic[1:]
        mnemonic = None

    if operand:
        operands.append(operand.strip())
        # operand = ''
        operand_expected = False

    if operand_expected:
        errors.append({
            'name': 'UNEXPECTED',
            'info': [',']
        })

    return {
        'symbol': symbol,
        'directive': directive,
        'mnemonic': mnemonic,
        'operands': operands,
        'errors': errors
    }


def parse_asm_file(file):
    with open(file) as asm:
        line_number = 0

        for line_str in asm.readlines():
            line_number += 1

            line = parse_asm_line(line_str)

            if line['symbol']:
                symbol = line['symbol']

                if symbol in symbol_table:
                    parser_error({
                        'name': 'DUPLICATE_SYMBOL',
                        'info': [symbol]
                    }, file, line_number, line_str)

                else:
                    symbol_table.append(symbol)
                    symbols[symbol] = {
                        'machine_code': bytearray(),
                        'references': []
                    }
                    global current_symbol, current_symbol_has_errors
                    current_symbol = symbol
                    current_symbol_has_errors = False

            for error in line['errors']:
                parser_error(error, file, line_number, line_str)

        # end of file


parse_asm_file('test1.asm')
