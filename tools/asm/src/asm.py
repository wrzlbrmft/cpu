import re
import shlex

symbol_table = []
symbols = {}
current_symbol = None
current_symbol_has_errors = False

parser_errors = {
    'UNEXPECTED': "unexpected '{}'",
    'SYMBOL_NAME_EXPECTED': 'symbol name expected',
    'DUPLICATE_SYMBOL': "duplicate symbol '{}'",
    'INVALID_SYMBOL_NAME': "invalid symbol name '{}'",
    'INVALID_DIRECTIVE': "invalid directive '{}'",
    'INVALID_MNEMONIC': "invalid mnemonic '{}'"
}

valid_name_regex = re.compile('[_a-z][_a-z0-9]*', re.IGNORECASE)

valid_directives = ['include',
                    'define', 'undef', 'ifdef', 'ifndef', 'else', 'endif',
                    'end']

valid_mnemonics = ['nop', 'hlt', 'rst',
                   'mov', 'lda', 'sta', 'push', 'pop',
                   'add', 'sub', 'cmp',
                   'jmp', 'jc', 'jnc', 'jz', 'jnz',
                   'call', 'cc', 'cnc', 'cz', 'cnz',
                   'ret', 'rc', 'rnc', 'rz', 'rnz',
                   'db', 'dw']

valid_registers = {
    'a': 8, 'b': 8, 'c': 8, 'd': 8, 'h': 8, 'l': 8,
    'hl': 16, 'ip': 16, 'sp': 16
}

valid_operands = list(valid_registers) + ['m']


def is_valid_name(name):
    return valid_name_regex.fullmatch(name)


def is_valid_directive(directive):
    return directive in valid_directives


def is_valid_mnemonic(mnemonic):
    return mnemonic in valid_mnemonics


def is_valid_register(register):
    return register in valid_registers


def is_valid_operand(operand):
    return operand in valid_operands


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
            if symbol:
                errors.append({
                    'name': 'UNEXPECTED',
                    'info': [':']
                })
            else:
                if mnemonic:
                    if operand or operand_expected:
                        errors.append({
                            'name': 'UNEXPECTED',
                            'info': [':']
                        })
                    else:
                        symbol = mnemonic
                        mnemonic = None
                else:
                    errors.append({
                        'name': 'SYMBOL_NAME_EXPECTED',
                        'info': []
                    })

        elif ',' == token:
            if operand:
                operands.append(operand.strip())
                operand = ''
                operand_expected = True
            else:
                errors.append({
                    'name': 'UNEXPECTED',
                    'info': [',']
                })

        else:
            if mnemonic:
                operand += ' ' + token
                operand_expected = False
            else:
                mnemonic = token

    # end of line

    if mnemonic and '.' == mnemonic[0]:
        directive = mnemonic[1:]
        mnemonic = None

    if operand:
        operands.append(operand.strip())
        # operand = ''
        # operand_expected = False
    elif operand_expected:
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
                elif not is_valid_name(symbol):
                    parser_error({
                        'name': 'INVALID_SYMBOL_NAME',
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

            if line['directive']:
                directive = line['directive']
                directive_lower = directive.lower()

                if not is_valid_directive(directive_lower):
                    parser_error({
                        'name': 'INVALID_DIRECTIVE',
                        'info': [directive]
                    }, file, line_number, line_str)
                else:
                    pass

            elif line['mnemonic']:
                mnemonic = line['mnemonic']
                mnemonic_lower = mnemonic.lower()

                if not is_valid_mnemonic(mnemonic_lower):
                    parser_error({
                        'name': 'INVALID_MNEMONIC',
                        'info': [mnemonic]
                    }, file, line_number, line_str)
                else:
                    pass

        # end of file


parse_asm_file('test1.asm')
