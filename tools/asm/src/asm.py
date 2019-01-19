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
    'INVALID_MNEMONIC': "invalid mnemonic '{}'",
    'INSUFFICIENT_OPERANDS': 'insufficient operands (given: {}, required: {})',
    'TOO_MANY_OPERANDS': 'too many operands (given: {}, required: {})',
    'UNSUPPORTED_OPERAND': "unsupported operand '{}'",
    'INVALID_OPERAND': "invalid operand '{}'",
    'INCOMPATIBLE_REGISTER_SIZE': 'incompatible register size (given: {}-bits, required: {}-bits)',
    'INCOMPATIBLE_DATA_TYPE': 'incompatible data type',
    'INCOMPATIBLE_DATA_SIZE': 'incompatible data size (given: {}-bits, max: {}-bits)',
    'NO_DATA': 'no data'
}

valid_name_regex = re.compile('[_a-z][_a-z0-9]*', re.IGNORECASE)
valid_data_dec_regex = re.compile('[1-9][0-9]*')
valid_data_hex_regex = re.compile('0x[0-9a-f]+', re.IGNORECASE)
valid_data_bin_regex = re.compile('0b[0-1]+', re.IGNORECASE)
valid_data_oct_regex = re.compile('0[0-7]+')
valid_data_chr_regex = re.compile('(\'.\'|\".\")', re.IGNORECASE)
valid_data_str_regex = re.compile('(\'.{2,}\'|\".{2,}\")', re.IGNORECASE)

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
    'a': {'size': 8, 'opcode': 0b000},
    'b': {'size': 8, 'opcode': 0b001},
    'c': {'size': 8, 'opcode': 0b010},
    'd': {'size': 8, 'opcode': 0b011},
    'h': {'size': 8, 'opcode': 0b100},
    'l': {'size': 8, 'opcode': 0b101},
    'hl': {'size': 16, 'opcode': 0b000},
    'ip': {'size': 16, 'opcode': 0b001},
    'sp': {'size': 16, 'opcode': 0b010}
}

valid_operands = list(valid_registers.keys()) + ['m']


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


def is_valid_data_str(data):
    return valid_data_str_regex.fullmatch(data)


def is_valid_data(data):
    return '0' == data or \
        is_valid_data_dec(data) or \
        is_valid_data_hex(data) or \
        is_valid_data_bin(data) or \
        is_valid_data_oct(data) or \
        is_valid_data_chr(data) or \
        is_valid_data_str(data)


def get_data_value(data):
    if '0' == data:
        return 0
    elif is_valid_data_dec(data):
        return int(data)
    elif is_valid_data_hex(data):
        return int(data[2:], 16)
    elif is_valid_data_bin(data):
        return int(data[2:], 2)
    elif is_valid_data_oct(data):
        return int(data[1:], 8)
    elif is_valid_data_chr(data):
        return ord(data[1])
    elif is_valid_data_str(data):
        values = []
        for value in data[1:-1]:
            values.append(ord(value))
        return values
    else:
        return None


def get_data_size(data):
    value = get_data_value(data)
    if isinstance(value, list):
        values = value
        size = 0
        for value in values:
            bits = value.bit_length()
            size = max(size, bits + (8 - bits) % 8)
        return size
    elif value is not None:
        bits = value.bit_length()
        return bits + (8 - bits) % 8
    else:
        return None


def is_valid_directive(directive):
    return directive in valid_directives


def is_valid_mnemonic(mnemonic):
    return mnemonic in valid_mnemonics


def is_valid_register(register):
    return register in valid_registers


def get_register_size(register):
    if is_valid_register(register):
        return valid_registers[register]['size']
    else:
        return None


def get_register_opcode(register):
    if is_valid_register(register):
        return valid_registers[register]['opcode']
    else:
        return None


def is_valid_operand(operand):
    return operand in valid_operands


def validate_operands_count(operands, count_valid, errors=None):
    if len(operands) < count_valid:
        if errors is not None:
            errors.append({
                'name': 'INSUFFICIENT_OPERANDS',
                'info': [len(operands), count_valid]
            })
        return False
    elif len(operands) > count_valid:
        if errors is not None:
            errors.append({
                'name': 'TOO_MANY_OPERANDS',
                'info': [len(operands), count_valid]
            })
        return False
    else:
        return True


def validate_operand_register(operand, errors=None):
    if is_valid_register(operand):
        return True
    elif is_valid_operand(operand):
        if errors is not None:
            errors.append({
                'name': 'UNSUPPORTED_OPERAND',
                'info': [operand]
            })
        return False
    else:
        if errors is not None:
            errors.append({
                'name': 'INVALID_OPERAND',
                'info': [operand]
            })
        return False


def validate_operand_register_size(operand, size_valid, errors=None):
    if validate_operand_register(operand, errors):
        size = get_register_size(operand)
        if size == size_valid:
            return True
        else:
            if errors is not None:
                errors.append({
                    'name': 'INCOMPATIBLE_REGISTER_SIZE',
                    'info': [size, size_valid]
                })
            return False


def validate_operand_data(operand, errors=None):
    if is_valid_data(operand):
        return True
    elif is_valid_operand(operand):
        if errors is not None:
            errors.append({
                'name': 'UNSUPPORTED_OPERAND',
                'info': [operand]
            })
        return False
    else:
        if errors is not None:
            errors.append({
                'name': 'INVALID_OPERAND',
                'info': [operand]
            })
        return False


def validate_operand_data_size(operand, size_valid, errors=None):
    if validate_operand_data(operand, errors):
        size = get_data_size(operand)
        if size <= size_valid:
            return True
        else:
            if errors is not None:
                errors.append({
                    'name': 'INCOMPATIBLE_DATA_SIZE',
                    'info': [size, size_valid]
                })
            return False


def mnemonics_nop_hlt_rst(mnemonic, operands):
    opcode = None
    errors = []

    if validate_operands_count(operands, 0, errors):
        if 'nop' == mnemonic:
            opcode = 0b00000000
        elif 'hlt' == mnemonic:
            opcode = 0b11111111
        elif 'rst' == mnemonic:
            opcode = 0b11111110

    machine_code = bytearray()
    if opcode is not None:
        machine_code.append(opcode)
    return {
        'machine_code': machine_code,
        'references': [],
        'errors': errors
    }


def mnemonic_mov(operands):
    opcode = None
    opcode_operands = bytearray()
    errors = []

    if validate_operands_count(operands, 2, errors):
        operand1 = operands[0].lower()
        operand2 = operands[1].lower()
        if 'm' == operand1:
            register1_opcode = 0b110
            if validate_operand_register_size(operand2, 8, errors):
                register2_opcode = get_register_opcode(operand2)
                opcode = 0b10000000 | (register1_opcode << 4) | (register2_opcode << 1)
        elif validate_operand_register(operand1, errors):
            register1_size = get_register_size(operand1)
            register1_opcode = get_register_opcode(operand1)
            if 8 == register1_size:
                register2_opcode = None
                if 'm' == operand2:
                    register2_opcode = 0b110
                elif is_valid_register(operand2):
                    if validate_operand_register_size(operand2, register1_size, errors):
                        register2_opcode = get_register_opcode(operand2)
                elif is_valid_data_str(operand2):
                    errors.append({
                        'name': 'INCOMPATIBLE_DATA_TYPE',
                        'info': []
                    })
                elif validate_operand_data_size(operand2, register1_size, errors):
                    register2_opcode = 0b111
                    data_value = get_data_value(operand2)
                    opcode_operands.append(data_value)

                if register2_opcode is not None:
                    opcode = 0b10000000 | (register1_opcode << 4) | (register2_opcode << 1)
            elif 16 == register1_size:
                register2_opcode = None
                if is_valid_register(operand2):
                    if validate_operand_register_size(operand2, register1_size, errors):
                        register2_opcode = get_register_opcode(operand2)
                elif is_valid_data_str(operand2):
                    errors.append({
                        'name': 'INCOMPATIBLE_DATA_TYPE',
                        'info': []
                    })
                elif validate_operand_data_size(operand2, register1_size, errors):
                    register2_opcode = 0b111
                    data_value = get_data_value(operand2)
                    opcode_operands.extend(data_value.to_bytes(2, 'little'))

                if register2_opcode is not None:
                    opcode = (register1_opcode << 4) | (register2_opcode << 1)

    machine_code = bytearray()
    if opcode is not None:
        machine_code.append(opcode)
    machine_code.extend(opcode_operands)
    return {
        'machine_code': machine_code,
        'references': [],
        'errors': errors
    }


def mnemonic_lda(operands):
    opcode = None
    opcode_operands = bytearray()
    errors = []

    if validate_operands_count(operands, 2, errors):
        operand1 = operands[0].lower()
        operand2 = operands[1].lower()

    machine_code = bytearray()
    if opcode is not None:
        machine_code.append(opcode)
    machine_code.extend(opcode_operands)
    return {
        'machine_code': machine_code,
        'references': [],
        'errors': errors
    }


def mnemonic_sta(operands):
    opcode = None
    opcode_operands = bytearray()
    errors = []

    if validate_operands_count(operands, 2, errors):
        operand1 = operands[0].lower()
        operand2 = operands[1].lower()

    machine_code = bytearray()
    if opcode is not None:
        machine_code.append(opcode)
    machine_code.extend(opcode_operands)
    return {
        'machine_code': machine_code,
        'references': [],
        'errors': errors
    }


def mnemonics_push_pop(mnemonic, operands):
    opcode = None
    errors = []

    if validate_operands_count(operands, 1, errors):
        operand = operands[0].lower()
        if validate_operand_register_size(operand, 8, errors):
            register_opcode = get_register_opcode(operand)
            opcode = (register_opcode << 4) | (register_opcode << 1)
            if 'push' == mnemonic:
                opcode = 0b10000000 | opcode
            elif 'pop' == mnemonic:
                opcode = 0b10000001 | opcode

    machine_code = bytearray()
    if opcode is not None:
        machine_code.append(opcode)
    return {
        'machine_code': machine_code,
        'references': [],
        'errors': errors
    }


def mnemonics_add_sub_cmp(mnemonic, operands):
    opcode = None
    opcode_operands = bytearray()
    errors = []

    if validate_operands_count(operands, 1, errors):
        operand = operands[0].lower()
        if 'm' == operand:
            opcode = 0b1100
        elif is_valid_register(operand):
            if validate_operand_register_size(operand, 8, errors):
                register_opcode = get_register_opcode(operand)
                opcode = (register_opcode << 1)
        elif is_valid_data_str(operand):
            errors.append({
                'name': 'INCOMPATIBLE_DATA_TYPE',
                'info': []
            })
        elif validate_operand_data_size(operand, 8, errors):
            opcode = 0b1110
            data_value = get_data_value(operand)
            opcode_operands.append(data_value)

        if opcode is not None:
            if 'add' == mnemonic:
                opcode = 0b01100000 | opcode
            elif 'sub' == mnemonic:
                opcode = 0b01100001 | opcode
            elif 'cmp' == mnemonic:
                opcode = 0b01110000 | opcode

    machine_code = bytearray()
    if opcode is not None:
        machine_code.append(opcode)
    machine_code.extend(opcode_operands)
    return {
        'machine_code': machine_code,
        'references': [],
        'errors': errors
    }


def mnemonics_ret_rc_rnc_rz_rnz(mnemonic, operands):
    opcode = None
    errors = []

    if validate_operands_count(operands, 0, errors):
        if 'ret' == mnemonic:
            opcode = 0b11000001
        elif 'rc' == mnemonic:
            opcode = 0b11000011
        elif 'rnc' == mnemonic:
            opcode = 0b11000101
        elif 'rz' == mnemonic:
            opcode = 0b11000111
        elif 'rnz' == mnemonic:
            opcode = 0b11001011

    machine_code = bytearray()
    if opcode is not None:
        machine_code.append(opcode)
    return {
        'machine_code': machine_code,
        'references': [],
        'errors': errors
    }


def mnemonics_db_dw(mnemonic, operands):
    opcode_operands = bytearray()
    errors = []

    if operands:
        if 'db' == mnemonic:
            for operand in operands:
                if validate_operand_data_size(operand, 8, errors):
                    if is_valid_data_str(operand):
                        data_values = get_data_value(operand)
                        for data_value in data_values:
                            opcode_operands.append(data_value)
                    else:
                        data_value = get_data_value(operand)
                        opcode_operands.append(data_value)
                else:
                    opcode_operands.clear()
                    break
        elif 'dw' == mnemonic:
            for operand in operands:
                if validate_operand_data_size(operand, 16, errors):
                    if is_valid_data_str(operand):
                        data_values = get_data_value(operand)
                        for data_value in data_values:
                            opcode_operands.extend(data_value.to_bytes(2, 'little'))
                    else:
                        data_value = get_data_value(operand)
                        opcode_operands.extend(data_value.to_bytes(2, 'little'))
                else:
                    opcode_operands.clear()
                    break
    else:
        errors.append({
            'name': 'NO_DATA',
            'info': []
        })

    return {
        'machine_code': opcode_operands,
        'references': [],
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
    elif mnemonic_lower in ['nop', 'hlt', 'rst']:
        assembly = mnemonics_nop_hlt_rst(mnemonic_lower, line['operands'])
    elif 'mov' == mnemonic_lower:
        assembly = mnemonic_mov(line['operands'])
    elif 'lda' == mnemonic_lower:
        assembly = mnemonic_lda(line['operands'])
    elif 'sta' == mnemonic_lower:
        assembly = mnemonic_sta(line['operands'])
    elif mnemonic_lower in ['push', 'pop']:
        assembly = mnemonics_push_pop(mnemonic_lower, line['operands'])
    elif mnemonic_lower in ['add', 'sub', 'cmp']:
        assembly = mnemonics_add_sub_cmp(mnemonic_lower, line['operands'])
    elif mnemonic_lower in ['ret', 'rc', 'rnc', 'rz', 'rnz']:
        assembly = mnemonics_ret_rc_rnc_rz_rnz(mnemonic_lower, line['operands'])
    elif mnemonic_lower in ['db', 'dw']:
        assembly = mnemonics_db_dw(mnemonic_lower, line['operands'])

    if assembly:
        return assembly
    else:
        return {
            'machine_code': bytearray(),
            'references': [],
            'errors': errors
        }


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
                operands.append(operand[1:])
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
        operands.append(operand[1:])
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

                if symbol in symbols:
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
                elif 'end' == directive_lower:
                    break

            elif line['mnemonic']:
                if not current_symbol:
                    parser_error({
                        'name': 'INSTRUCTION_OUTSIDE_SYMBOL',
                        'info': []
                    })

                assembly = assemble_asm_line(line)

                for error in assembly['errors']:
                    parser_error(error)

                if assembly['machine_code']:
                    print(current_line_str.strip())
                    for byte in assembly['machine_code']:
                        print('', hex(byte)[2:].upper().zfill(2), end='')
                    print()
                    print()

            # end of line

        # end of file


parse_asm_file('test1.asm')
