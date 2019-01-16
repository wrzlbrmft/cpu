import shlex


def parse_asm_line(line_str):
    symbol = None
    directive = None
    mnemonic = None
    operands = []
    operand = None
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
                            'name': '',  # unexpected ':'
                            'info': []
                        })

                else:
                    errors.append({
                        'name': '',  # symbol name expected
                        'info': []
                    })

            else:
                errors.append({
                    'name': '',  # unexpected ':'
                    'info': []
                })

        elif ',' == token:
            if not operand:
                errors.append({
                    'name': '',  # unexpected ','
                    'info': []
                })

            else:
                operands.append(operand.strip())
                operand = None
                operand_expected = True

        else:
            if not mnemonic:
                mnemonic = token

            else:
                operand += ' ' + token
                operand_expected = False

    # end of line

    if '.' == mnemonic[0]:
        directive = mnemonic[1:]
        mnemonic = None

    if operand:
        operands.append(operand.strip())
        # operand = None
        operand_expected = False

    if operand_expected:
        errors.append({
            'name': '',  # unexpected ','
            'info': []
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

        # end of file


parse_asm_file('test1.asm')
