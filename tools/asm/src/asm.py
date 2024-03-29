import argparse
import binutils
import data
import i18n
import obj_file
import relocation_table
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
current_proc_name = None

valid_directives = ['base', 'proc', 'endproc', 'end']

valid_mnemonics = ['nop', 'hlt', 'rst', 'inchl', 'dechl', 'pushhl', 'pophl', 'pushf', 'popf',
                   'mov',
                   'loda',
                   'stoa',
                   'push', 'pop',
                   'add', 'sub', 'cmp', 'adc', 'sbb', 'and', 'or', 'xor',
                   'jmp', 'jc', 'jnc', 'jz', 'jnz', 'ja', 'jna',
                   'jb', 'jnb', 'je', 'jne', 'jae', 'jnae', 'jbe', 'jnbe',
                   'call', 'cc', 'cnc', 'cz', 'cnz', 'ca', 'cna',
                   'cb', 'cnb', 'ce', 'cne', 'cae', 'cnae', 'cbe', 'cnbe',
                   'ret', 'rc', 'rnc', 'rz', 'rnz', 'ra', 'rna',
                   'rb', 'rnb', 're', 'rne', 'rae', 'rnae', 'rbe', 'rnbe',
                   'iret',
                   'int',
                   'db', 'dw',
                   'inc', 'dec', 'not', 'shl', 'shr']

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

valid_name_regex = re.compile('[@_a-z][_a-z0-9]{,254}', re.IGNORECASE)

# using the .base directive, the assembler allows setting the link base which is then stored in the object file header
link_base = None


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


def expand_local_symbol_name(symbol_name):
    global current_proc_name

    if '@' == symbol_name[0]:
        # if a symbol name starts with an @ sign, the symbol becomes local by automatically putting the current
        # procedure name at the beginning of the symbol name, or at least an underscore
        if current_proc_name is not None:
            symbol_name = current_proc_name + '_' + symbol_name[1:]
        else:
            symbol_name = '_' + symbol_name[1:]

    return symbol_name


def mnemonics_nop_hlt_rst_inchl_dechl_pushhl_pophl_pushf_popf(mnemonic, operands, errors=None):
    opcode = None

    if validate_operands_count(operands, 0, errors):
        if 'nop' == mnemonic:
            opcode = 0b00000000
        elif 'hlt' == mnemonic:
            opcode = 0b11111111
        elif 'rst' == mnemonic:
            opcode = 0b11110111
        elif 'inchl' == mnemonic:
            opcode = 0b10010111
        elif 'dechl' == mnemonic:
            opcode = 0b10100111
        elif 'pushhl' == mnemonic:
            opcode = 0b10010001
        elif 'pophl' == mnemonic:
            opcode = 0b10010101
        elif 'pushf' == mnemonic:
            opcode = 0b10000111
        elif 'popf' == mnemonic:
            opcode = 0b11011001

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
    _relocation_table = []

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
                # single character but no string
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
                # register or using max. 16-bit data or a single character including unicode but no string
                register2_opcode = None
                if is_valid_name(operand2):
                    operand2 = expand_local_symbol_name(operand2)
                    register2_opcode = 0b111
                    opcode_operands.extend([0, 0])
                    _relocation_table.append({
                        'machine_code_offset': 1,
                        'symbol_index': symbol_table.get_index(operand2)
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
                    opcode_operands.extend(binutils.word_to_le(data_value))

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
            'relocation_table': _relocation_table
        }


def mnemonic_loda(operands, errors=None):
    opcode = None
    opcode_operands = bytearray()
    _relocation_table = []

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
                    operand2 = expand_local_symbol_name(operand2)
                    opcode_operands.extend([0, 0])
                    _relocation_table.append({
                        'machine_code_offset': 1,
                        'symbol_index': symbol_table.get_index(operand2)
                    })
                else:
                    opcode_operands.extend(binutils.word_to_le(addr_value))
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
            'relocation_table': _relocation_table
        }


def mnemonic_stoa(operands, errors=None):
    opcode = None
    opcode_operands = bytearray()
    _relocation_table = []

    if validate_operands_count(operands, 2, errors):
        operand1 = operands[0].lower()
        operand2 = operands[1].lower()
        if validate_operand_addr_size(operand1, 16, errors):
            # store to address is supported to an address or a symbol name (using relocation) but only from an 8-bit
            # register
            addr_value = get_addr_value(operand1)
            if addr_value is None:
                operand1 = expand_local_symbol_name(operand1)
                opcode_operands.extend([0, 0])
                _relocation_table.append({
                    'machine_code_offset': 1,
                    'symbol_index': symbol_table.get_index(operand1)
                })
            else:
                opcode_operands.extend(binutils.word_to_le(addr_value))

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
            'relocation_table': _relocation_table
        }


def mnemonics_push_pop(mnemonic, operands, errors=None):
    opcode = None

    if validate_operands_count(operands, 1, errors):
        operand = operands[0].lower()
        if validate_operand_register_size(operand, 8, errors):
            # push and pop are supported with any 8-bit register
            register_opcode = get_register_opcode(operand)
            if 'push' == mnemonic:
                opcode = 0b10000000 | (register_opcode << 4) | (register_opcode << 1)
            elif 'pop' == mnemonic:
                opcode = 0b10000001 | (register_opcode << 4) | (register_opcode << 1)

    if errors:
        return None
    else:
        machine_code = bytearray()
        machine_code.append(opcode)
        return {
            'machine_code': machine_code,
            'relocation_table': []
        }


def mnemonics_add_sub_cmp_adc_sbb_and_or_xor(mnemonic, operands, errors=None):
    opcode = None
    opcode_operands = bytearray()

    if validate_operands_count(operands, 1, errors):
        # add (with carry), subtract (with borrow), compare, and, or and xor are supported with M, any 8-bit register or
        # max. 8-bit data or a single character but no string
        operand = operands[0].lower()
        if 'm' == operand:
            opcode = 0b110
        elif is_valid_register(operand):
            if validate_operand_register_size(operand, 8, errors):
                register_opcode = get_register_opcode(operand)
                opcode = register_opcode
        elif data.is_valid_str(operand):
            if errors is not None:
                errors.append({
                    'name': 'INCOMPATIBLE_DATA_TYPE',
                    'info': []
                })
        elif validate_operand_data_size(operand, 8, errors):
            opcode = 0b111
            data_value = data.get_value(operand)
            opcode_operands.append(data_value)

        if opcode is not None:
            if 'add' == mnemonic:
                opcode = 0b01100000 | (opcode << 1)
            elif 'sub' == mnemonic:
                opcode = 0b01100001 | (opcode << 1)
            elif 'cmp' == mnemonic:
                opcode = 0b01110000 | (opcode << 1)
            elif 'adc' == mnemonic:
                opcode = 0b01010000 | opcode
            elif 'sbb' == mnemonic:
                opcode = 0b01011000 | opcode
            elif 'and' == mnemonic:
                opcode = 0b00110000 | opcode
            elif 'or' == mnemonic:
                opcode = 0b00111000 | opcode
            elif 'xor' == mnemonic:
                opcode = 0b01000000 | opcode

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


def mnemonics_jmps_calls(mnemonic, operands, errors=None):
    opcode = None
    opcode_operands = bytearray()
    _relocation_table = []

    if validate_operands_count(operands, 1, errors):
        # jumps and calls are supported to M, an address or a symbol name (using
        # relocation); note: M vs. address/symbol name is distinguished using a
        # flip-bit in the opcode
        operand = operands[0].lower()
        if 'm' == operand:
            opcode = 0b0
        elif validate_operand_addr_size(operand, 16, errors):
            opcode = 0b1
            addr_value = get_addr_value(operand)
            if addr_value is None:
                operand = expand_local_symbol_name(operand)
                opcode_operands.extend([0, 0])
                _relocation_table.append({
                    'machine_code_offset': 1,
                    'symbol_index': symbol_table.get_index(operand)
                })
            else:
                opcode_operands.extend(binutils.word_to_le(addr_value))

        # optimized usage of opcodes ...and flip the bit for M vs. address/symbol name
        if opcode is not None:
            if 'jmp' == mnemonic:
                opcode = 0b01110101 | (opcode << 1)
            elif mnemonic in ['jc', 'jb', 'jnae']:
                opcode = 0b01111001 | (opcode << 1)
            elif mnemonic in ['jnc', 'jnb', 'jae']:
                opcode = 0b01111101 | (opcode << 1)
            elif mnemonic in ['jz', 'je']:
                opcode = 0b10001111 | (opcode << 4)
            elif mnemonic in ['jnz', 'jne']:
                opcode = 0b10101111 | (opcode << 4)
            elif mnemonic in ['ja', 'jnbe']:
                opcode = 0b00000001 | (opcode << 1)
            elif mnemonic in ['jna', 'jbe']:
                opcode = 0b00000110 | opcode

            elif 'call' == mnemonic:
                opcode = 0b11000001 | (opcode << 1)
            elif mnemonic in ['cc', 'cb', 'cnae']:
                opcode = 0b11000101 | (opcode << 1)
            elif mnemonic in ['cnc', 'cnb', 'cae']:
                opcode = 0b11001011 | (opcode << 2)
            elif mnemonic in ['cz', 'ce']:
                opcode = 0b11010001 | (opcode << 1)
            elif mnemonic in ['cnz', 'cne']:
                opcode = 0b11010101 | (opcode << 1)
            elif mnemonic in ['ca', 'cnbe']:
                opcode = 0b00010010 | opcode
            elif mnemonic in ['cna', 'cbe']:
                opcode = 0b00010110 | opcode

    if errors:
        return None
    else:
        machine_code = bytearray()
        machine_code.append(opcode)
        machine_code.extend(opcode_operands)
        return {
            'machine_code': machine_code,
            'relocation_table': _relocation_table
        }


def mnemonics_rets_iret(mnemonic, operands, errors=None):
    opcode = None

    if validate_operands_count(operands, 0, errors):
        if 'ret' == mnemonic:
            opcode = 0b00000101
        elif mnemonic in ['rc', 'rb', 'rnae']:
            opcode = 0b00010001
        elif mnemonic in ['rnc', 'rnb', 'rae']:
            opcode = 0b00010101
        elif mnemonic in ['rz', 're']:
            opcode = 0b00100001
        elif mnemonic in ['rnz', 'rne']:
            opcode = 0b00100011
        elif mnemonic in ['ra', 'rnbe']:
            opcode = 0b10000011
        elif mnemonic in ['rna', 'rbe']:
            opcode = 0b10000101
        elif 'iret' == mnemonic:
            opcode = 0b10110101

    if errors:
        return None
    else:
        machine_code = bytearray()
        machine_code.append(opcode)
        return {
            'machine_code': machine_code,
            'relocation_table': []
        }


def mnemonic_int(operands, errors=None):
    opcode = None
    opcode_operands = bytearray()

    if validate_operands_count(operands, 1, errors):
        operand = operands[0].lower()
        if data.is_valid_str(operand) or data.is_valid_chr(operand):
            if errors is not None:
                errors.append({
                    'name': 'UNSUPPORTED_OPERAND',
                    'info': [operand]
                })
        elif validate_operand_data_size(operand, 8, errors):
            # call interrupt is supported with max. 8-bit data with a value up to 63 (for 64 interrupts)
            opcode = 0b11011111
            data_value = data.get_value(operand)
            if data_value > 63:
                if errors is not None:
                    errors.append({
                        'name': 'INVALID_INT',
                        'info': [data_value]
                    })
            else:
                opcode_operands.append(data_value)

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


def mnemonics_db_dw(mnemonic, operands, errors=None):
    opcode_operands = bytearray()
    _relocation_table = []

    if operands:
        for operand in operands:
            operand_splits = operand.rsplit(None, 3)
            if len(operand_splits) == 4 and '(' == operand_splits[-3] and ')' == operand_splits[-1]:
                operand = operand_splits[0]
                multiplier = operand_splits[-2]
                if data.is_valid_str(multiplier) or data.is_valid_chr(multiplier):
                    if errors is not None:
                        errors.append({
                            'name': 'UNSUPPORTED_MULTIPLIER',
                            'info': [multiplier]
                        })
                    opcode_operands.clear()
                    break
                elif data.get_size(multiplier) is None or data.get_value(multiplier) < 1:
                    if errors is not None:
                        errors.append({
                            'name': 'INVALID_MULTIPLIER',
                            'info': [multiplier]
                        })
                    opcode_operands.clear()
                    break
                elif data.get_size(multiplier) > 16:
                    if errors is not None:
                        errors.append({
                            'name': 'UNSUPPORTED_MULTIPLIER_SIZE',
                            'info': [data.get_size(multiplier), 16]
                        })
                    opcode_operands.clear()
                    break
                multiplier_value = data.get_value(multiplier)
            else:
                multiplier_value = 1

            if 'db' == mnemonic:
                # bytes support max. 8-bit data, a single character or a string
                if validate_operand_data_size(operand, 8, errors):
                    if data.is_valid_str(operand):
                        data_values = data.get_value(operand) * multiplier_value
                        opcode_operands.extend(data_values)
                    else:
                        data_value = data.get_value(operand)
                        opcode_operands.extend([data_value] * multiplier_value)
                else:
                    opcode_operands.clear()
                    break
            elif 'dw' == mnemonic:
                # words support a symbol name (using relocation), max. 16-bit data, a single character or a string both
                # including unicode
                if is_valid_name(operand):
                    operand = expand_local_symbol_name(operand)
                    opcode_operands.extend([0, 0])
                    _relocation_table.append({
                        'machine_code_offset': len(opcode_operands) - 2,
                        'symbol_index': symbol_table.get_index(operand)
                    })
                elif validate_operand_data_size(operand, 16, errors):
                    if data.is_valid_str(operand):
                        data_values = data.get_value(operand) * multiplier_value
                        for data_value in data_values:
                            opcode_operands.extend(binutils.word_to_le(data_value))
                    else:
                        data_value = data.get_value(operand)
                        opcode_operands.extend(binutils.word_to_le(data_value) * multiplier_value)
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
            'relocation_table': _relocation_table
        }


def mnemonics_inc_dec_not_shl_shr(mnemonic, operands, errors=None):
    opcode = None

    if validate_operands_count(operands, 1, errors):
        # increment, decrement, not, shift left and shift right are supported with M or any 8-bit register
        operand = operands[0].lower()
        if 'm' == operand:
            if mnemonic in ['not', 'shl', 'shr']:
                opcode = 0b111  # note: for not, shift left and shift right M is 111, instead of the usual 110
            else:
                opcode = 0b110
        elif validate_operand_register_size(operand, 8, errors):
            register_opcode = get_register_opcode(operand)
            opcode = register_opcode

        if opcode is not None:
            if 'inc' == mnemonic:
                opcode = 0b11110000 | opcode
            elif 'dec' == mnemonic:
                opcode = 0b11111000 | opcode
            elif 'not' == mnemonic:
                opcode = 0b00001000 | opcode
            elif 'shl' == mnemonic:
                opcode = 0b00011000 | opcode
            elif 'shr' == mnemonic:
                opcode = 0b00101000 | opcode

    if errors:
        return None
    else:
        machine_code = bytearray()
        machine_code.append(opcode)
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
        print(f"^ {symbol_table.get_symbol_name(relocation['symbol_index'])}")


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
    elif mnemonic_lower in ['nop', 'hlt', 'rst', 'inchl', 'dechl', 'pushhl', 'pophl', 'pushf', 'popf']:
        assembly = mnemonics_nop_hlt_rst_inchl_dechl_pushhl_pophl_pushf_popf(mnemonic_lower, line['operands'], errors)
    elif 'mov' == mnemonic_lower:
        assembly = mnemonic_mov(line['operands'], errors)
    elif 'loda' == mnemonic_lower:
        assembly = mnemonic_loda(line['operands'], errors)
    elif 'stoa' == mnemonic_lower:
        assembly = mnemonic_stoa(line['operands'], errors)
    elif mnemonic_lower in ['push', 'pop']:
        assembly = mnemonics_push_pop(mnemonic_lower, line['operands'], errors)
    elif mnemonic_lower in ['add', 'sub', 'cmp', 'adc', 'sbb', 'and', 'or', 'xor']:
        assembly = mnemonics_add_sub_cmp_adc_sbb_and_or_xor(mnemonic_lower, line['operands'], errors)
    elif mnemonic_lower in ['jmp', 'jc', 'jnc', 'jz', 'jnz', 'ja', 'jna',
                            'jb', 'jnb', 'je', 'jne', 'jae', 'jnae', 'jbe', 'jnbe',
                            'call', 'cc', 'cnc', 'cz', 'cnz', 'ca', 'cna',
                            'cb', 'cnb', 'ce', 'cne', 'cae', 'cnae', 'cbe', 'cnbe']:
        assembly = mnemonics_jmps_calls(mnemonic_lower, line['operands'], errors)
    elif mnemonic_lower in ['ret', 'rc', 'rnc', 'rz', 'rnz', 'ra', 'rna',
                            'rb', 'rnb', 're', 'rne', 'rae', 'rnae', 'rbe', 'rnbe',
                            'iret']:
        assembly = mnemonics_rets_iret(mnemonic_lower, line['operands'], errors)
    elif 'int' == mnemonic_lower:
        assembly = mnemonic_int(line['operands'], errors)
    elif mnemonic_lower in ['db', 'dw']:
        assembly = mnemonics_db_dw(mnemonic_lower, line['operands'], errors)
    elif mnemonic_lower in ['inc', 'dec', 'not', 'shl', 'shr']:
        assembly = mnemonics_inc_dec_not_shl_shr(mnemonic_lower, line['operands'], errors)

    if errors:
        return None
    else:
        return assembly


def directive_base(operands, errors=None):
    global link_base

    if link_base is not None:
        if errors is not None:
            errors.append({
                'name': 'DUPLICATE_DIRECTIVE',
                'info': ['base']
            })
    elif validate_operands_count(operands, 1, errors):
        operand = operands[0]
        if is_valid_name(operand):
            if errors is not None:
                errors.append({
                    'name': 'UNSUPPORTED_OPERAND',
                    'info': [operand]
                })
        elif validate_operand_addr_size(operand, 16, errors):
            link_base = data.get_value(operand)


def directive_proc(operands, errors=None):
    if validate_operands_count(operands, 1, errors):
        operand = operands[0]
        if is_valid_name(operand) and '@' != operand[0]:
            return operand
        else:
            if errors is not None:
                errors.append({
                    'name': 'INVALID_PROC_NAME',
                    'info': [operand]
                })
            return None
    else:
        return None


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
    parser.wordchars += '.:@'

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
            elif '@' in token:
                if errors is not None:
                    errors.append({
                        'name': 'UNEXPECTED',
                        'info': ['@']
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
            elif '@' in token[1:]:
                if errors is not None:
                    errors.append({
                        'name': 'UNEXPECTED',
                        'info': ['@']
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
            elif '@' in token[1:]:
                if errors is not None:
                    errors.append({
                        'name': 'UNEXPECTED',
                        'info': ['@']
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


def assemble_asm_file(file_name, dump=False):
    global current_file_name, current_line_num, current_line_str, current_symbol_name, current_proc_name

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
                            'info': [directive]
                        })
                        return
                    elif 'base' == directive_lower:
                        directive_base(line['operands'], errors)
                    elif 'proc' == directive_lower:
                        if current_proc_name is None:
                            current_proc_name = directive_proc(line['operands'], errors)
                            if not errors:
                                line['symbol_name'] = current_proc_name
                        else:
                            show_error({
                                'name': 'UNEXPECTED_PROC',
                                'info': []
                            })
                            return
                    elif 'endproc' == directive_lower:
                        if current_proc_name is not None:
                            current_proc_name = None
                            current_symbol_name = None
                        else:
                            show_error({
                                'name': 'UNEXPECTED_ENDPROC',
                                'info': []
                            })
                            return
                    elif 'end' == directive_lower:
                        # the .end directive simply exists the line-by-line loop (skipping the rest of the file)
                        break

                if not errors and line['symbol_name']:
                    symbol_name = line['symbol_name']

                    if not is_valid_name(symbol_name):
                        show_error({
                            'name': 'INVALID_SYMBOL_NAME',
                            'info': [symbol_name]
                        }, '')
                        return

                    symbol_name = expand_local_symbol_name(symbol_name)

                    if symbols.symbol_exists(symbol_name):
                        show_error({
                            'name': 'DUPLICATE_SYMBOL',
                            'info': [symbol_name]
                        }, '')
                        return
                    else:
                        current_symbol_name = symbol_name

                        if symbol_table.symbol_exists(current_symbol_name):
                            # if the current symbol was already used as an operand (hence it already exists in the
                            # symbol table, but with a lower index), move it to the end of the symbol table to keep
                            # the symbols in the order of their definition
                            old_symbol_table = symbol_table.get_symbol_table().copy()
                            symbol_table.remove_symbol(current_symbol_name)
                            symbol_table.add_symbol(current_symbol_name)

                            # rebuild all symbols to use the new symbol indexes
                            _symbols = symbols.get_symbols()
                            for symbol in _symbols.values():
                                # procedure
                                proc_name = symbol_table.get_symbol_name(symbol['proc_index'], old_symbol_table)
                                symbol['proc_index'] = symbol_table.get_index(proc_name)

                                # relocation table
                                relocation_table.rebuild(symbol['relocation_table'], old_symbol_table)
                        else:
                            symbol_table.add_symbol(current_symbol_name)

                        symbols.add_symbol(current_symbol_name, current_proc_name)

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
                            if dump:
                                dump_assembly(assembly)

                            symbol = symbols.get_symbol(current_symbol_name)

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

parser = argparse.ArgumentParser(description='the assembler')
parser.add_argument('file', help='source file to be assembled')
parser.add_argument('-d', '--dump', action='store_true', help='dump line-by-line instructions and assembly output')
args = parser.parse_args()


def main():
    asm_file_name = args.file
    assemble_asm_file(asm_file_name, args.dump)

    if not total_errors_count:
        obj_file_name = os.path.splitext(os.path.basename(asm_file_name))[0] + '.obj'
        obj_file.write_obj_file(obj_file_name, link_base=link_base)


if '__main__' == __name__:
    main()

    if total_errors_count:
        sys.exit(1)
