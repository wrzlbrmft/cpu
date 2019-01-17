import re
import shlex

current_file = None
current_line_num = 0
current_line_str = None
current_symbol = None
current_symbol_errors_count = 0

symbol_table = []
symbols = {}

parser_errors = {
    'UNEXPECTED': "unexpected '{}'",
    'SYMBOL_NAME_EXPECTED': 'symbol name expected',
    'DUPLICATE_SYMBOL': "duplicate symbol '{}'",
    'INVALID_SYMBOL_NAME': "invalid symbol name '{}'",
    'INVALID_DIRECTIVE': "invalid directive '{}'",
    'INSTRUCTION_OUTSIDE_SYMBOL': 'instruction outside of a symbol',
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


def parser_error(error):
    global current_symbol_errors_count

    if current_symbol and not current_symbol_errors_count:
        if current_file:
            print(f'{current_file}: ', end='')
        print(f"in symbol '{current_symbol}':")
        current_symbol_errors_count += 1

    if current_file:
        print(f'{current_file}:', end='')
        if current_line_num:
            print(f'{current_line_num}:', end='')
        print(' ', end='')

    print('error:', parser_errors[error['name']].format(*error['info']))

    if current_line_str:
        print('', current_line_str.strip())

    print()


def parse_asm_line_str(line_str):
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


def mnemonic_nop(operands):
    opcode = 0b00000000
    errors = []

    return {
        'opcode': opcode,
        'errors': errors
    }


def assemble_asm_line(line):
    assembly = None
    errors = []

    mnemonic = line['mnemonic']
    mnemonic_lower = mnemonic.lower()

    if not is_valid_mnemonic(mnemonic_lower):
        errors.append({
            'name': 'INVALID_MNEMONIC',
            'info': [mnemonic]
        })
    elif 'nop' == mnemonic_lower:
        assembly = mnemonic_nop(line['operands'])

    if assembly:
        return assembly
    else:
        return {
            'errors': errors
        }


def parse_asm_file(file):
    global current_file, current_line_num, current_line_str, current_symbol, current_symbol_errors_count

    with open(file) as asm:
        current_file = file
        line_num = 0
        current_line_num = line_num

        for line_str in asm.readlines():
            current_line_str = line_str
            line_num += 1
            current_line_num = line_num

            line = parse_asm_line_str(current_line_str)

            if line['symbol']:
                symbol = line['symbol']

                if symbol in symbol_table:
                    parser_error({
                        'name': 'DUPLICATE_SYMBOL',
                        'info': [symbol]
                    })
                elif not is_valid_name(symbol):
                    parser_error({
                        'name': 'INVALID_SYMBOL_NAME',
                        'info': [symbol]
                    })
                else:
                    current_symbol = symbol
                    current_symbol_errors_count = 0

                    symbol_table.append(current_symbol)
                    symbols[current_symbol] = {
                        'machine_code': bytearray(),
                        'references': []
                    }

            for error in line['errors']:
                parser_error(error)

            if line['directive']:
                directive = line['directive']
                directive_lower = directive.lower()

                if not is_valid_directive(directive_lower):
                    parser_error({
                        'name': 'INVALID_DIRECTIVE',
                        'info': [directive]
                    })
                else:
                    pass

            elif line['mnemonic']:
                if not current_symbol:
                    parser_error({
                        'name': 'INSTRUCTION_OUTSIDE_SYMBOL',
                        'info': []
                    })

                assembly = assemble_asm_line(line)

                for error in assembly['errors']:
                    parser_error(error)

        # end of file


parse_asm_file('test1.asm')
