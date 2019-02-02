import re
import shlex
import sys

asm_file = 'test.asm'

symbols = {}

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

valid_8bit_registers = ['a', 'b', 'c', 'd', 'h', 'l']
valid_16bit_registers = ['hl', 'ip', 'sp']
valid_registers = valid_8bit_registers + valid_16bit_registers
valid_operands = valid_registers + ['m']

reserved_words = valid_directives + valid_mnemonics + valid_operands

valid_name_chars = 'abcdfeghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.'
valid_name_regex = re.compile('[_a-z][_a-z0-9]*', re.IGNORECASE)
valid_data_dec_regex = re.compile('[1-9][0-9]*')
valid_data_hex_regex = re.compile('0x[0-9a-f]+', re.IGNORECASE)
valid_data_bin_regex = re.compile('0b[0-1]+', re.IGNORECASE)
valid_data_oct_regex = re.compile('0[0-7]+')
valid_data_chr_regex = re.compile('(\'.\'|\".\")')

parser_errors = {
    'DUPLICATE_SYMBOL_DEFINITION': "duplicate symbol definition '{}'",
    'SYMBOL_NAME_EXPECTED': 'symbol name expected',
    'UNEXPECTED': "unexpected '{}'",
    'OPERAND_EXPECTED': 'operand expected',
    'INVALID_DIRECTIVE': "invalid directive '.{}'",
    'INVALID_MNEMONIC': "invalid mnemonic '{}'",
    'INSUFFICIENT_OPERANDS': 'insufficient operands (required={}, given={})',
    'TOO_MANY_OPERANDS': 'too many operands (required={}, given={})',
    'UNSUPPORTED_REGISTER_SIZE': 'unsupported register size',
    'UNSUPPORTED_OPERAND': "unsupported operand '{}'",
    'INVALID_OPERAND': "invalid operand '{}'",
    'MISSING_SYMBOL_DEFINITION': 'missing symbol definition',
    'INCOMPATIBLE_REGISTER_SIZES': 'incompatible register sizes',
    'INVALID_SYMBOL_NAME': "invalid symbol name '{}'",
    'MISUSE_OF_RESERVED_WORD': "misuse of reserved word '{}'",
    'BIT_LENGTH_OVERFLOW': "bit-length overflow '{}'"
}


def parser_error(file, symbol, line_number, line, error, details=()):
    if symbol is not None:
        print(f"{file}: in symbol '{symbol}':")
    print(f'{file}:{line_number}: error: {parser_errors[error].format(*details)}')
    if line is not None:
        print(' ' + line)
    sys.exit(1)


def is_valid_directive(directive):
    return directive in valid_directives


def is_valid_mnemonic(mnemonic):
    return mnemonic in valid_mnemonics


def is_valid_8bit_register(register):
    return register in valid_8bit_registers


def is_valid_16bit_register(register):
    return register in valid_16bit_registers


def is_valid_register(register):
    return register in valid_registers


def is_valid_operand(operand):
    return operand in valid_operands


def is_reserved_word(word):
    return word in reserved_words


def is_valid_name(name):
    return valid_name_regex.fullmatch(name)


def is_valid_data_dec(data):
    return valid_data_dec_regex.fullmatch(data)


def is_valid_data_hex(data):
    return valid_data_hex_regex.fullmatch(data)


def is_valid_data_bin(data):
    return valid_data_bin_regex.fullmatch(data)


def is_valid_data_oct(data):
    return valid_data_oct_regex.fullmatch(data)


def is_valid_data_chr(data):
    return valid_data_chr_regex.fullmatch(data)


def is_valid_data(data):
    return is_valid_data_dec(data) or \
           is_valid_data_hex(data) or \
           is_valid_data_bin(data) or \
           is_valid_data_oct(data) or \
           is_valid_data_chr(data)


def check_number_of_operands(file, symbol, line_number, line, required, operands):
    if len(operands) < required:
        parser_error(file, symbol, line_number, line, 'INSUFFICIENT_OPERANDS', [required, len(operands)])
    elif len(operands) > required:
        parser_error(file, symbol, line_number, line, 'TOO_MANY_OPERANDS', [required, len(operands)])


def get_opcode_register(register):
    # 8-bit registers
    if "a" == register:
        return 0b000
    elif "b" == register:
        return 0b001
    elif "c" == register:
        return 0b010
    elif "d" == register:
        return 0b011
    elif "h" == register:
        return 0b100
    elif "l" == register:
        return 0b101

    # 16-bit registers
    elif "hl" == register:
        return 0b000
    elif "ip" == register:
        return 0b001
    elif "sp" == register:
        return 0b010

    else:
        return None


def get_data_value(data):
    if is_valid_data_dec(data):
        return int(data, 10)
    elif is_valid_data_hex(data):
        return int(data[2:], 16)
    elif is_valid_data_bin(data):
        return int(data[2:], 2)
    elif is_valid_data_oct(data):
        return int(data[1:], 8)
    elif is_valid_data_chr(data):
        return ord(data[1])
    else:
        return None


def get_data_value_hi(data):
    return divmod(data, 256)[0]


def get_data_value_lo(data):
    return divmod(data, 256)[1]


def parse_asm_file(file):
    with open(file) as asm:
        line_number = 0

        symbol = None  # current symbol

        for line in asm.readlines():
            line_number += 1

            line = line.strip()
            if line:
                symbol_definition = False  # whether the current line contains a symbol definition
                mnemonic = ''              # mnemonic of the current line
                operands = []              # list of all operands in the current line (so far)
                operand = ''               # the operand currently being parsed
                operand_expected = False   # set to True after parsing a comma, therefore expecting next operand

                line_parser = shlex.shlex(line)
                line_parser.commenters = ';'  # comments starting with semicolon
                line_parser.wordchars = valid_name_chars

                for line_token in line_parser:
                    if ':' == line_token:
                        if not symbol_definition:
                            if mnemonic and not operand and not operand_expected:
                                # if the current line so far only contains a mnemonic (no operand), then a colon means
                                # that the supposed mnemonic is actually a symbol definition
                                symbol_definition = True
                                symbol = mnemonic
                                mnemonic = ''

                                if not is_valid_name(symbol):
                                    parser_error(file, None, line_number, line, 'INVALID_SYMBOL_NAME', [symbol])
                                elif is_reserved_word(symbol):
                                    parser_error(file, None, line_number, line, 'MISUSE_OF_RESERVED_WORD', [symbol])
                                elif symbol in symbols:
                                    parser_error(file, None, line_number, line, 'DUPLICATE_SYMBOL_DEFINITION', [symbol])

                                symbols[symbol] = {
                                    'code': bytearray()
                                }
                            elif not mnemonic:
                                # colon without a mnemonic? (line started with a colon)
                                parser_error(file, None, line_number, line, 'SYMBOL_NAME_EXPECTED')
                        else:
                            # after a symbol definition no further colons expected
                            parser_error(file, symbol, line_number, line, 'UNEXPECTED', [':'])

                    elif ',' == line_token:
                        if not operand:
                            # only expect commas while parsing an operand (to separate the next operand)
                            parser_error(file, symbol, line_number, line, 'UNEXPECTED', [','])

                        # add current operand to the list of all operands and expect next operand
                        operands.append(operand.strip())
                        operand = ''
                        operand_expected = True

                    else:
                        if not mnemonic:
                            mnemonic = line_token
                        else:
                            # any token after the mnemonic adds to an operand (fulfilling possible expectation)
                            operand += ' ' + line_token
                            operand_expected = False

                # end of line

                # add outstanding operand
                if operand:
                    operands.append(operand.strip())
                    # operand = ''
                    operand_expected = False

                # still expecting next operand? (line ended with a comma)
                if operand_expected:
                    parser_error(file, symbol, line_number, line, 'OPERAND_EXPECTED')

                if mnemonic:
                    mnemonic_lower = mnemonic.lower()

                    # directives
                    if '.' == mnemonic[:1]:
                        directive = mnemonic[1:]
                        directive_lower = directive.lower()

                        if not is_valid_directive(directive_lower):
                            parser_error(file, symbol, line_number, line, 'INVALID_DIRECTIVE', [directive])
                        else:
                            if 'include' == directive_lower:
                                pass  # todo: .include directive (include another file)

                            elif 'define' == directive_lower:
                                pass  # todo: .define directive

                            elif 'undef' == directive_lower:
                                pass  # todo: .undef directive

                            elif 'ifdef' == directive_lower:
                                pass  # todo: .ifdef directive

                            elif 'ifndef' == directive_lower:
                                pass  # todo: .ifndef directive

                            elif 'else' == directive_lower:
                                pass  # todo: .else directive

                            elif 'endif' == directive_lower:
                                pass  # todo: .endif directive

                            elif 'end' == directive_lower:
                                pass  # todo: .end directive (end parsing of current file)

                    # mnemonics
                    else:
                        # no mnemonic without a symbol
                        if symbol is None:
                            parser_error(file, None, line_number, line, 'MISSING_SYMBOL_DEFINITION')

                        if not is_valid_mnemonic(mnemonic_lower):
                            parser_error(file, symbol, line_number, line, 'INVALID_MNEMONIC', [mnemonic])
                        else:
                            code = bytearray()

                            if 'nop' == mnemonic_lower:
                                # no operation
                                check_number_of_operands(file, symbol, line_number, line, 0, operands)
                                code.append(0b00000000)

                            elif 'hlt' == mnemonic_lower:
                                # halt
                                check_number_of_operands(file, symbol, line_number, line, 0, operands)
                                code.append(0b11111111)

                            elif 'rst' == mnemonic_lower:
                                # reset
                                check_number_of_operands(file, symbol, line_number, line, 0, operands)
                                code.append(0b11111110)

                            elif 'mov' == mnemonic_lower:
                                # move
                                check_number_of_operands(file, symbol, line_number, line, 2, operands)
                                operand1 = operands[0].lower()
                                operand2 = operands[1].lower()
                                opcode = None
                                opcode_operands = bytearray()

                                # destination: 8-bit register
                                if is_valid_8bit_register(operand1):
                                    opcode_register1 = get_opcode_register(operand1)

                                    # source: 8-bit register
                                    if is_valid_8bit_register(operand2):
                                        opcode_register2 = get_opcode_register(operand2)
                                        opcode = 0b10000000 | (opcode_register1 << 4) | (opcode_register2 << 1)

                                    # source: 16-bit register
                                    elif is_valid_16bit_register(operand2):
                                        parser_error(file, symbol, line_number, line, 'INCOMPATIBLE_REGISTER_SIZES')

                                    elif is_valid_operand(operand2):
                                        # source: memory
                                        if 'm' == operand2:
                                            opcode_register2 = 0b110
                                            opcode = 0b10000000 | (opcode_register1 << 4) | (opcode_register2 << 1)

                                        # source: any other operand
                                        else:
                                            parser_error(file, symbol, line_number, line, 'UNSUPPORTED_OPERAND',
                                                         [operand2])

                                    # source: data
                                    elif is_valid_data(operand2):
                                        opcode_register2 = 0b111
                                        opcode = 0b10000000 | (opcode_register1 << 4) | (opcode_register2 << 1)

                                        # append data as opcode operand
                                        data_value = get_data_value(operand2)
                                        if data_value.bit_length() > 8:
                                            parser_error(file, symbol, line_number, line, 'BIT_LENGTH_OVERFLOW',
                                                         [operand2])
                                        opcode_operands.append(data_value)

                                    else:
                                        parser_error(file, symbol, line_number, line, 'INVALID_OPERAND', [operand2])

                                # destination: 16-bit register
                                elif is_valid_16bit_register(operand1):
                                    opcode_register1 = get_opcode_register(operand1)

                                    # source: 8-bit register
                                    if is_valid_8bit_register(operand2):
                                        parser_error(file, symbol, line_number, line, 'INCOMPATIBLE_REGISTER_SIZES')

                                    # source: 16-bit register
                                    elif is_valid_16bit_register(operand2):
                                        opcode_register2 = get_opcode_register(operand2)
                                        opcode = (opcode_register1 << 4) | (opcode_register2 << 1)

                                    # source: any operand
                                    elif is_valid_operand(operand2):
                                        parser_error(file, symbol, line_number, line, 'UNSUPPORTED_OPERAND', [operand2])

                                    # source: data
                                    elif is_valid_data(operand2):
                                        opcode_register2 = 0b111
                                        opcode = (opcode_register1 << 4) | (opcode_register2 << 1)

                                        # append data as opcode operand
                                        data_value = get_data_value(operand2)
                                        if data_value.bit_length() > 16:
                                            parser_error(file, symbol, line_number, line, 'BIT_LENGTH_OVERFLOW',
                                                         [operand2])
                                        opcode_operands.append(get_data_value_lo(data_value))  # little-endian
                                        opcode_operands.append(get_data_value_hi(data_value))

                                    else:
                                        parser_error(file, symbol, line_number, line, 'INVALID_OPERAND', [operand2])

                                elif is_valid_operand(operand1):
                                    # destination: memory
                                    if 'm' == operand1:
                                        opcode_register1 = 0b110

                                        # source: 8-bit register
                                        if is_valid_8bit_register(operand2):
                                            opcode_register2 = get_opcode_register(operand2)
                                            opcode = 0b10000000 | (opcode_register1 << 4) | (opcode_register2 << 1)

                                        # source: 16-bit register
                                        elif is_valid_16bit_register(operand2):
                                            parser_error(file, symbol, line_number, line, 'INCOMPATIBLE_REGISTER_SIZES')

                                        # source: any operand
                                        elif is_valid_operand(operand2):
                                            parser_error(file, symbol, line_number, line, 'UNSUPPORTED_OPERAND',
                                                         [operand2])

                                        else:
                                            parser_error(file, symbol, line_number, line, 'INVALID_OPERAND', [operand2])

                                    # destination: any other operand
                                    else:
                                        parser_error(file, symbol, line_number, line, 'UNSUPPORTED_OPERAND', [operand1])

                                else:
                                    parser_error(file, symbol, line_number, line, 'INVALID_OPERAND', [operand1])

                                if opcode is not None:
                                    code.append(opcode)
                                    if opcode_operands:
                                        code.extend(opcode_operands)

                            elif 'lda' == mnemonic_lower:
                                # load from address
                                check_number_of_operands(file, symbol, line_number, line, 2, operands)

                            elif 'sta' == mnemonic_lower:
                                # store to address
                                check_number_of_operands(file, symbol, line_number, line, 2, operands)

                            elif mnemonic_lower in ['push', 'pop']:
                                # push, pop
                                check_number_of_operands(file, symbol, line_number, line, 1, operands)
                                operand = operands[0].lower()
                                opcode = None

                                # 8-bit register
                                if is_valid_8bit_register(operand):
                                    opcode_register = get_opcode_register(operand)
                                    opcode = 0b10000000 | (opcode_register << 4) | (opcode_register << 1)

                                # 16-bit register
                                elif is_valid_16bit_register(operand):
                                    parser_error(file, symbol, line_number, line, 'UNSUPPORTED_REGISTER_SIZE')

                                # any operand
                                elif is_valid_operand(operand):
                                    parser_error(file, symbol, line_number, line, 'UNSUPPORTED_OPERAND', [operand])

                                else:
                                    parser_error(file, symbol, line_number, line, 'INVALID_OPERAND', [operand])

                                if opcode is not None:
                                    if 'push' == mnemonic_lower:
                                        # push
                                        code.append(opcode)

                                    elif 'pop' == mnemonic_lower:
                                        # pop
                                        code.append(0b00000001 | opcode)

                            elif mnemonic_lower in ['add', 'sub', 'cmp']:
                                # add, sub, cmp
                                check_number_of_operands(file, symbol, line_number, line, 1, operands)
                                operand = operands[0].lower()
                                opcode = None
                                opcode_operands = bytearray()

                                # 8-bit register
                                if is_valid_8bit_register(operand):
                                    opcode_register = get_opcode_register(operand)
                                    opcode = (opcode_register << 1)

                                # 16-bit register
                                elif is_valid_16bit_register(operand):
                                    parser_error(file, symbol, line_number, line, 'UNSUPPORTED_REGISTER_SIZE')

                                elif is_valid_operand(operand):
                                    # memory
                                    if 'm' == operand:
                                        opcode = (0b110 << 1)

                                    # any other operand
                                    else:
                                        parser_error(file, symbol, line_number, line, 'UNSUPPORTED_OPERAND', [operand])

                                # data
                                elif is_valid_data(operand):
                                    opcode = (0b111 << 1)

                                    # append data as opcode operand
                                    data_value = get_data_value(operand)
                                    if data_value.bit_length() > 8:
                                        parser_error(file, symbol, line_number, line, 'BIT_LENGTH_OVERFLOW', [operand])
                                    opcode_operands.append(data_value)

                                else:
                                    parser_error(file, symbol, line_number, line, 'INVALID_OPERAND', [operand])

                                if opcode is not None:
                                    if 'add' == mnemonic_lower:
                                        # add
                                        code.append(0b01100000 | opcode)

                                    elif 'sub' == mnemonic_lower:
                                        # subtract
                                        code.append(0b01100001 | opcode)

                                    elif 'cmp' == mnemonic_lower:
                                        # compare
                                        code.append(0b01110000 | opcode)

                                    if opcode_operands:
                                        code.extend(opcode_operands)

                            elif mnemonic_lower in ['jmp', 'jc', 'jnc', 'jz', 'jnz',
                                                    'call', 'cc', 'cnc', 'cz', 'cnz']:
                                # jmp, jc, jnc, jz, jnz, call, cc, cnc, cz, cnz
                                check_number_of_operands(file, symbol, line_number, line, 1, operands)
                                operand = operands[0].lower()

                                if 'm' == operand:
                                    pass

                                elif is_valid_operand(operand):
                                    parser_error(file, symbol, line_number, line, 'UNSUPPORTED_OPERAND', [operand])

                                if 'jmp' == mnemonic_lower:
                                    # jump unconditionally
                                    pass

                                elif 'jc' == mnemonic_lower:
                                    # jump on carry
                                    pass

                                elif 'jnc' == mnemonic_lower:
                                    # jump on no carry
                                    pass

                                elif 'jz' == mnemonic_lower:
                                    # jump on zero
                                    pass

                                elif 'jnz' == mnemonic_lower:
                                    # jump on no zero
                                    pass

                                elif 'call' == mnemonic_lower:
                                    # call unconditionally
                                    pass

                                elif 'cc' == mnemonic_lower:
                                    # call on carry
                                    pass

                                elif 'cnc' == mnemonic_lower:
                                    # call on no carry
                                    pass

                                elif 'cz' == mnemonic_lower:
                                    # call on zero
                                    pass

                                elif 'cnz' == mnemonic_lower:
                                    # call on no zero
                                    pass

                            elif 'ret' == mnemonic_lower:
                                # return unconditionally
                                check_number_of_operands(file, symbol, line_number, line, 0, operands)
                                code.append(0b11000001)

                            elif 'rc' == mnemonic_lower:
                                # return on carry
                                check_number_of_operands(file, symbol, line_number, line, 0, operands)
                                code.append(0b11000011)

                            elif 'rnc' == mnemonic_lower:
                                # return on no carry
                                check_number_of_operands(file, symbol, line_number, line, 0, operands)
                                code.append(0b11000101)

                            elif 'rz' == mnemonic_lower:
                                # return on zero
                                check_number_of_operands(file, symbol, line_number, line, 0, operands)
                                code.append(0b11000111)

                            elif 'rnz' == mnemonic_lower:
                                # return on no zero
                                check_number_of_operands(file, symbol, line_number, line, 0, operands)
                                code.append(0b11001011)

                            elif 'db' == mnemonic_lower:
                                # define byte
                                pass

                            elif 'dw' == mnemonic_lower:
                                # define word
                                pass

                            print(line)
                            for i in code:
                                print(' ' + hex(i), end='')
                            print()


parse_asm_file(asm_file)
