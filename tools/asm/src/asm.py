import data
import endianness
import i18n
import obj_file
import symbol_table
import symbols

import os
import re
import shlex
import sys

total_errors_count = 0

current_file_name = None
current_line_num = 0
current_line_str = None
current_symbol_name = None

valid_directives = ['end']

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

valid_name_regex = re.compile('[_a-z][_a-z0-9]{,254}', re.IGNORECASE)


def is_valid_directive(s):
    return s in valid_directives


def is_valid_mnemonic(s):
    return s in valid_mnemonics


def is_valid_register(s):
    return s in valid_registers.keys()


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


def is_valid_operand(s):
    return s in valid_operands


def is_valid_name(s):
    return not is_valid_operand(s) and valid_name_regex.fullmatch(s)


def is_valid_addr(s):
    # a symbol name is always a valid address (the linker will determine the address during relocation)
    return is_valid_name(s) or (data.is_valid(s) and not data.is_valid_chr(s) and not data.is_valid_str(s))


def get_addr_value(addr):
    if is_valid_name(addr):
        return None  # this will then add an item to the relocation table
    elif is_valid_addr(addr):
        return data.get_value(addr)
    else:
        return None


def get_addr_size(addr):
    if is_valid_name(addr):
        return 16  # for symbol names, the linker will determine a 16-bit address during relocation
    elif is_valid_addr(addr):
        return data.get_size(addr)
    else:
        return None


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
    else:
        return False


def validate_operand_data(operand, errors=None):
    if data.is_valid(operand):
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
        size = data.get_size(operand)
        if size <= size_valid:
            # data just has to fit in
            return True
        else:
            if errors is not None:
                errors.append({
                    'name': 'INCOMPATIBLE_DATA_SIZE',
                    'info': [size, size_valid]
                })
            return False
    else:
        return False


def validate_operand_addr(operand, errors=None):
    if is_valid_addr(operand):
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


def validate_operand_addr_size(operand, size_valid, errors=None):
    if validate_operand_addr(operand, errors):
        size = get_addr_size(operand)
        if size <= size_valid:
            # an address just has to fit it
            return True
        else:
            if errors is not None:
                errors.append({
                    'name': 'INCOMPATIBLE_ADDR_SIZE',
                    'info': [size, size_valid]
                })
            return False
    else:
        return False


def mnemonics_nop_hlt_rst(mnemonic, operands, errors=None):
    opcode = None

    if validate_operands_count(operands, 0, errors):
        if 'nop' == mnemonic:
            opcode = 0b00000000
        elif 'hlt' == mnemonic:
            opcode = 0b11111111
        elif 'rst' == mnemonic:
            opcode = 0b11111110

    if errors:
        return None
    else:
        machine_code = bytearray()
        machine_code.append(opcode)
        return {
            'machine_code': machine_code,
            'relocation_table': []
        }


def mnemonic_mov(operands, errors=None):
    opcode = None
    opcode_operands = bytearray()
    relocation_table = []

    if validate_operands_count(operands, 2, errors):
        operand1 = operands[0].lower()
        operand2 = operands[1].lower()
        if 'm' == operand1:
            # move into M is only supported from an 8-bit register
            register1_opcode = 0b110
            if validate_operand_register_size(operand2, 8, errors):
                register2_opcode = get_register_opcode(operand2)
                opcode = 0b10000000 | (register1_opcode << 4) | (register2_opcode << 1)
        elif validate_operand_register(operand1, errors):
            register1_size = get_register_size(operand1)
            register1_opcode = get_register_opcode(operand1)
            if 8 == register1_size:
                # move into an 8-bit register is supported from M, another 8-bit register or using max. 8-bit data or a
                # single character (no string)
                register2_opcode = None
                if 'm' == operand2:
                    register2_opcode = 0b110
                elif is_valid_register(operand2):
                    if validate_operand_register_size(operand2, register1_size, errors):
                        register2_opcode = get_register_opcode(operand2)
                elif data.is_valid_str(operand2):
                    if errors is not None:
                        errors.append({
                            'name': 'INCOMPATIBLE_DATA_TYPE',
                            'info': []
                        })
                elif validate_operand_data_size(operand2, register1_size, errors):
                    register2_opcode = 0b111
                    data_value = data.get_value(operand2)
                    opcode_operands.append(data_value)

                if register2_opcode is not None:
                    opcode = 0b10000000 | (register1_opcode << 4) | (register2_opcode << 1)
            elif 16 == register1_size:
                # move into a 16-bit register is supported from a symbol name (using relocation), another 16-bit
                # register or using max. 16-bit data or a single character including unicode (no string)
                register2_opcode = None
                if is_valid_name(operand2):
                    register2_opcode = 0b111
                    opcode_operands.extend([0, 0])
                    relocation_table.append({
                        'machine_code_offset': 1,
                        'symbol_table_index': symbol_table.get_index(operand2)
                    })
                elif is_valid_register(operand2):
                    if validate_operand_register_size(operand2, register1_size, errors):
                        register2_opcode = get_register_opcode(operand2)
                elif data.is_valid_str(operand2):
                    errors.append({
                        'name': 'INCOMPATIBLE_DATA_TYPE',
                        'info': []
                    })
                elif validate_operand_data_size(operand2, register1_size, errors):
                    register2_opcode = 0b111
                    data_value = data.get_value(operand2)
                    opcode_operands.extend(endianness.word_to_le(data_value))

                if register2_opcode is not None:
                    opcode = (register1_opcode << 4) | (register2_opcode << 1)

    if errors:
        return None
    else:
        machine_code = bytearray()
        machine_code.append(opcode)
        machine_code.extend(opcode_operands)
        return {
            'machine_code': machine_code,
            'relocation_table': relocation_table
        }


def mnemonic_lda(operands, errors=None):
    opcode = None
    opcode_operands = bytearray()
    relocation_table = []

    if validate_operands_count(operands, 2, errors):
        operand1 = operands[0].lower()
        operand2 = operands[1].lower()
        if validate_operand_register_size(operand1, 8, errors):
            # load from address into an 8-bit register is supported from an address or a symbol name (using relocation)
            register_opcode = get_register_opcode(operand1)
            opcode = 0b10001101 | (register_opcode << 4)
            if validate_operand_addr_size(operand2, 16, errors):
                addr_value = get_addr_value(operand2)
                if addr_value is None:
                    opcode_operands.extend([0, 0])
                    relocation_table.append({
                        'machine_code_offset': 1,
                        'symbol_table_index': symbol_table.get_index(operand2)
                    })
                else:
                    opcode_operands.extend(endianness.word_to_le(addr_value))
            else:
                opcode = None

    if errors:
        return None
    else:
        machine_code = bytearray()
        machine_code.append(opcode)
        machine_code.extend(opcode_operands)
        return {
            'machine_code': machine_code,
            'relocation_table': relocation_table
        }


def mnemonic_sta(operands, errors=None):
    opcode = None
    opcode_operands = bytearray()
    relocation_table = []

    if validate_operands_count(operands, 2, errors):
        operand1 = operands[0].lower()
        operand2 = operands[1].lower()
        if validate_operand_addr_size(operand1, 16, errors):
            # store to address is supported to an address or a symbol name (using relocation) but only from an 8-bit
            # register
            addr_value = get_addr_value(operand1)
            if addr_value is None:
                opcode_operands.extend([0, 0])
                relocation_table.append({
                    'machine_code_offset': 1,
                    'symbol_table_index': symbol_table.get_index(operand1)
                })
            else:
                opcode_operands.extend(endianness.word_to_le(addr_value))

            if validate_operand_register_size(operand2, 8, errors):
                register_opcode = get_register_opcode(operand2)
                opcode = 0b11100001 | (register_opcode << 1)
            else:
                opcode_operands.clear()

    if errors:
        return None
    else:
        machine_code = bytearray()
        machine_code.append(opcode)
        machine_code.extend(opcode_operands)
        return {
            'machine_code': machine_code,
            'relocation_table': relocation_table
        }


def mnemonics_push_pop(mnemonic, operands, errors=None):
    opcode = None

    if validate_operands_count(operands, 1, errors):
        operand = operands[0].lower()
        if validate_operand_register_size(operand, 8, errors):
            # push or pop are supported with any 8-bit register
            register_opcode = get_register_opcode(operand)
            opcode = (register_opcode << 4) | (register_opcode << 1)
            if 'push' == mnemonic:
                opcode = 0b10000000 | opcode
            elif 'pop' == mnemonic:
                opcode = 0b10000001 | opcode

    if errors:
        return None
    else:
        machine_code = bytearray()
        machine_code.append(opcode)
        return {
            'machine_code': machine_code,
            'relocation_table': []
        }


def mnemonics_add_sub_cmp(mnemonic, operands, errors=None):
    opcode = None
    opcode_operands = bytearray()

    if validate_operands_count(operands, 1, errors):
        # add, subtract and compare are supported with M, any 8-bit register or max. 8-bit data or a single character
        # (no string)
        operand = operands[0].lower()
        if 'm' == operand:
            opcode = 0b1100
        elif is_valid_register(operand):
            if validate_operand_register_size(operand, 8, errors):
                register_opcode = get_register_opcode(operand)
                opcode = (register_opcode << 1)
        elif data.is_valid_str(operand):
            if errors is not None:
                errors.append({
                    'name': 'INCOMPATIBLE_DATA_TYPE',
                    'info': []
                })
        elif validate_operand_data_size(operand, 8, errors):
            opcode = 0b1110
            data_value = data.get_value(operand)
            opcode_operands.append(data_value)

        if opcode is not None:
            if 'add' == mnemonic:
                opcode = 0b01100000 | opcode
            elif 'sub' == mnemonic:
                opcode = 0b01100001 | opcode
            elif 'cmp' == mnemonic:
                opcode = 0b01110000 | opcode

    if errors:
        return None
    else:
        machine_code = bytearray()
        machine_code.append(opcode)
        machine_code.extend(opcode_operands)
        return {
            'machine_code': machine_code,
            'relocation_table': []
        }


def mnemonics_jmp_jc_jnc_jz_jnz_call_cc_cnc_cz_cnz(mnemonic, operands, errors=None):
    opcode = None
    opcode_operands = bytearray()
    relocation_table = []

    if validate_operands_count(operands, 1, errors):
        # jumps are supported to M, an address or a symbol name (using relocation)
        # note: M vs. address/symbol name is distinguished using one bit in the opcode
        operand = operands[0].lower()
        if 'm' == operand:
            opcode = 0b0
        elif validate_operand_addr_size(operand, 16, errors):
            opcode = 0b1
            addr_value = get_addr_value(operand)
            if addr_value is None:
                opcode_operands.extend([0, 0])
                relocation_table.append({
                    'machine_code_offset': 1,
                    'symbol_table_index': symbol_table.get_index(operand)
                })
            else:
                opcode_operands.extend(endianness.word_to_le(addr_value))

        # optimized usage of opcodes ...and adjust the bit for M vs. address/symbol name
        if opcode is not None:
            if 'jmp' == mnemonic:
                opcode = 0b01110101 | (opcode << 1)
            elif 'jc' == mnemonic:
                opcode = 0b01111001 | (opcode << 1)
            elif 'jnc' == mnemonic:
                opcode = 0b01111101 | (opcode << 1)
            elif 'jz' == mnemonic:
                opcode = 0b10001111 | (opcode << 4)
            elif 'jnz' == mnemonic:
                opcode = 0b10101111 | (opcode << 4)
            elif 'call' == mnemonic:
                opcode = 0b11000001 | (opcode << 1)
            elif 'cc' == mnemonic:
                opcode = 0b11000101 | (opcode << 1)
            elif 'cnc' == mnemonic:
                opcode = 0b11001011 | (opcode << 2)
            elif 'cz' == mnemonic:
                opcode = 0b11010001 | (opcode << 1)
            elif 'cnz' == mnemonic:
                opcode = 0b11010101 | (opcode << 1)

    if errors:
        return None
    else:
        machine_code = bytearray()
        machine_code.append(opcode)
        machine_code.extend(opcode_operands)
        return {
            'machine_code': machine_code,
            'relocation_table': relocation_table
        }


def mnemonics_ret_rc_rnc_rz_rnz(mnemonic, operands, errors=None):
    opcode = None

    if validate_operands_count(operands, 0, errors):
        if 'ret' == mnemonic:
            opcode = 0b00000101
        elif 'rc' == mnemonic:
            opcode = 0b00001111
        elif 'rnc' == mnemonic:
            opcode = 0b00010001
        elif 'rz' == mnemonic:
            opcode = 0b00010101
        elif 'rnz' == mnemonic:
            opcode = 0b00011111

    if errors:
        return None
    else:
        machine_code = bytearray()
        machine_code.append(opcode)
        return {
            'machine_code': machine_code,
            'relocation_table': []
        }


def mnemonics_db_dw(mnemonic, operands, errors=None):
    opcode_operands = bytearray()

    if operands:
        if 'db' == mnemonic:
            # bytes support max. 8-bit data, a single character or a string
            for operand in operands:
                if validate_operand_data_size(operand, 8, errors):
                    if data.is_valid_str(operand):
                        data_values = data.get_value(operand)
                        for data_value in data_values:
                            opcode_operands.append(data_value)
                    else:
                        data_value = data.get_value(operand)
                        opcode_operands.append(data_value)
                else:
                    opcode_operands.clear()
                    break
        elif 'dw' == mnemonic:
            # words support max. 16-bit data, a single character or a string both including unicode
            for operand in operands:
                if validate_operand_data_size(operand, 16, errors):
                    if data.is_valid_str(operand):
                        data_values = data.get_value(operand)
                        for data_value in data_values:
                            opcode_operands.extend(endianness.word_to_le(data_value))
                    else:
                        data_value = data.get_value(operand)
                        opcode_operands.extend(endianness.word_to_le(data_value))
                else:
                    opcode_operands.clear()
                    break
    else:
        if errors is not None:
            errors.append({
                'name': 'NO_DATA',
                'info': []
            })

    if errors:
        return None
    else:
        machine_code = bytearray()
        machine_code.extend(opcode_operands)
        return {
            'machine_code': machine_code,
            'relocation_table': []
        }


def dump_assembly(assembly):
    for byte in assembly['machine_code']:
        print(hex(byte)[2:].upper().zfill(2), '', end='')
    print('   ' * (3 - len(assembly['machine_code'])), '  ', end='')
    print(current_line_str.strip())
    for relocation in assembly['relocation_table']:
        print('   ' * relocation['machine_code_offset'], end='')
        print(f"^ {relocation['symbol_table_index']}: {symbol_table.get_symbol_name(relocation['symbol_table_index'])}")


def assemble_asm_line(line, errors=None):
    assembly = None

    mnemonic = line['mnemonic']
    mnemonic_lower = mnemonic.lower()

    if not is_valid_mnemonic(mnemonic_lower):
        if errors is not None:
            errors.append({
                'name': 'INVALID_MNEMONIC',
                'info': [mnemonic]
            })
    elif mnemonic_lower in ['nop', 'hlt', 'rst']:
        assembly = mnemonics_nop_hlt_rst(mnemonic_lower, line['operands'], errors)
    elif 'mov' == mnemonic_lower:
        assembly = mnemonic_mov(line['operands'], errors)
    elif 'lda' == mnemonic_lower:
        assembly = mnemonic_lda(line['operands'], errors)
    elif 'sta' == mnemonic_lower:
        assembly = mnemonic_sta(line['operands'], errors)
    elif mnemonic_lower in ['push', 'pop']:
        assembly = mnemonics_push_pop(mnemonic_lower, line['operands'], errors)
    elif mnemonic_lower in ['add', 'sub', 'cmp']:
        assembly = mnemonics_add_sub_cmp(mnemonic_lower, line['operands'], errors)
    elif mnemonic_lower in ['jmp', 'jc', 'jnc', 'jz', 'jnz', 'call', 'cc', 'cnc', 'cz', 'cnz']:
        assembly = mnemonics_jmp_jc_jnc_jz_jnz_call_cc_cnc_cz_cnz(mnemonic_lower, line['operands'], errors)
    elif mnemonic_lower in ['ret', 'rc', 'rnc', 'rz', 'rnz']:
        assembly = mnemonics_ret_rc_rnc_rz_rnz(mnemonic_lower, line['operands'], errors)
    elif mnemonic_lower in ['db', 'dw']:
        assembly = mnemonics_db_dw(mnemonic_lower, line['operands'], errors)

    if errors:
        return None
    else:
        return assembly


def show_error(error, symbol_name=None, line_str=None, line_num=None, file_name=None):
    global total_errors_count

    if symbol_name is None:
        symbol_name = current_symbol_name

    if line_str is None:
        line_str = current_line_str

    if line_num is None:
        line_num = current_line_num

    if file_name is None:
        file_name = current_file_name

    total_errors_count += 1

    if symbol_name:
        if file_name:
            print(f'{file_name}: ', end='')
        print(f"in symbol '{symbol_name}':")

    if file_name:
        print(f'{file_name}:', end='')
        if line_num:
            print(f'{line_num}:', end='')
        print(' ', end='')

    print('error:', i18n.error_messages[error['name']].format(*error['info']))

    if line_str:
        print('', line_str.strip())

    print()


def parse_asm_line_str(line_str, errors=None):
    directive = None
    symbol_name = None
    mnemonic = None
    operands = []
    operand = ''              # the current operand
    operand_expected = False  # whether another operand is expected (after a comma)

    parser = shlex.shlex(line_str)
    parser.commenters = ';'
    parser.wordchars += '.:'

    for token in parser:
        if '.' == token[0]:
            if 1 == len(token) or directive or symbol_name or mnemonic:
                if errors is not None:
                    errors.append({
                        'name': 'UNEXPECTED',
                        'info': ['.']
                    })
                break
            elif ':' in token:
                if errors is not None:
                    errors.append({
                        'name': 'UNEXPECTED',
                        'info': [':']
                    })
                break
            else:
                directive = token[1:]

        elif ':' == token[-1]:
            if 1 == len(token) or directive or symbol_name or mnemonic:
                if errors is not None:
                    errors.append({
                        'name': 'UNEXPECTED',
                        'info': [':']
                    })
                break
            elif '.' in token:
                if errors is not None:
                    errors.append({
                        'name': 'UNEXPECTED',
                        'info': ['.']
                    })
                break
            else:
                symbol_name = token[:-1]

        elif ',' == token:
            if operand:
                # finish the current operand and expect another one
                operands.append(operand[1:])
                operand = ''
                operand_expected = True
            else:
                if errors is not None:
                    errors.append({
                        'name': 'UNEXPECTED',
                        'info': [',']
                    })
                break

        else:
            if '.' in token:
                if errors is not None:
                    errors.append({
                        'name': 'UNEXPECTED',
                        'info': ['.']
                    })
                break
            elif ':' in token:
                if errors is not None:
                    errors.append({
                        'name': 'UNEXPECTED',
                        'info': [':']
                    })
                break
            elif directive or mnemonic:
                # everything after the directive or mnemonic is an operand
                operand += ' ' + token
                operand_expected = False
            else:
                mnemonic = token

    # end of line

    if not errors:
        if operand:
            # finish the last operand
            operands.append(operand[1:])
            # operand = ''
            # operand_expected = False
        elif operand_expected:
            if errors is not None:
                errors.append({
                    'name': 'UNEXPECTED',
                    'info': [',']
                })

    if errors:
        return None
    else:
        return {
            'directive': directive,
            'symbol_name': symbol_name,
            'mnemonic': mnemonic,
            'operands': operands
        }


def assemble_asm_file(file_name):
    global current_file_name, current_line_num, current_line_str, current_symbol_name

    if os.path.isfile(file_name):
        with open(file_name, 'r') as asm:
            current_file_name = file_name
            line_num = 0
            current_line_num = line_num

            for line_str in asm.readlines():
                current_line_str = line_str
                line_num += 1
                current_line_num = line_num

                errors = []

                line = parse_asm_line_str(current_line_str, errors)

                if not errors and line['directive']:
                    directive = line['directive']
                    directive_lower = directive.lower()

                    if not is_valid_directive(directive_lower):
                        show_error({
                            'name': 'INVALID_DIRECTIVE',
                            'info': [',']
                        })
                        return
                    elif 'end' == directive_lower:
                        # the .end directive simply exists the line-by-line loop (skipping the rest of the file)
                        break
                else:
                    if not errors and line['symbol_name']:
                        symbol_name = line['symbol_name']

                        if not is_valid_name(symbol_name):
                            show_error({
                                'name': 'INVALID_SYMBOL_NAME',
                                'info': [symbol_name]
                            }, '')
                            return
                        elif symbols.symbol_exists(symbol_name):
                            show_error({
                                'name': 'DUPLICATE_SYMBOL',
                                'info': [symbol_name]
                            }, '')
                            return
                        elif not line['mnemonic']:
                            show_error({
                                'name': 'SYMBOL_WITHOUT_INSTRUCTION',
                                'info': []
                            })
                            return
                        else:
                            current_symbol_name = symbol_name

                            # adds the symbol name to the symbol table
                            symbol_table.get_index(current_symbol_name)

                    if not errors and line['mnemonic']:
                        if not current_symbol_name:
                            show_error({
                                'name': 'INSTRUCTION_WITHOUT_SYMBOL',
                                'info': []
                            })
                            return
                        else:
                            assembly = assemble_asm_line(line, errors)

                            if not errors:
                                # dump_assembly(assembly)

                                symbol = symbols.add_symbol(current_symbol_name)

                                for relocation in assembly['relocation_table']:
                                    # adjust the machine code offset to be relative to the current symbol
                                    relocation['machine_code_offset'] += len(symbol['machine_code'])
                                symbol['relocation_table'].extend(assembly['relocation_table'])
                                symbol['machine_code'].extend(assembly['machine_code'])

                # end of line

                if errors:
                    show_error(errors[0])
                    break

            # end of file
    else:
        show_error({
            'name': 'FILE_NOT_FOUND',
            'info': [file_name]
        })


# main


def main():
    if len(sys.argv) < 2:
        show_error({
            'name': 'NO_ASM_FILE',
            'info': []
        })
    else:
        asm_file_name = sys.argv[1]
        assemble_asm_file(asm_file_name)

        if not total_errors_count:
            obj_file_name = os.path.splitext(os.path.basename(asm_file_name))[0] + '.obj'
            obj_file.write_obj_file(obj_file_name)


if '__main__' == __name__:
    main()
