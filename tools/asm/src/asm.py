import shlex

parser_errors = {
    'UNEXPECTED': "unexpected '{}'",
    'SYMBOL_NAME_EXPECTED': 'symbol name expected'
}


def parser_error(error, file=None, line_number=None, line_str=None):
    if file:
        print(f'{file}:', end='')
        if line_number:
            print(f'{line_number}:', end='')
        print(' ', end='')

    print('error:', parser_errors[error['name']].format(*error['info']))

    if line_str:
        print('', line_str.strip())


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

            for error in line['errors']:
                parser_error(error, file, line_number, line_str)

        # end of file


parse_asm_file('test1.asm')
