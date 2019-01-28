import symbol_table
import symbols

import re
import shlex
import sys

current_asm_file_name = None
current_asm_line_num = 0
current_asm_line_str = None
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


def is_valid_directive(directive):
    return directive in valid_directives


def is_valid_mnemonic(mnemonic):
    return mnemonic in valid_mnemonics


def is_valid_register(register):
    return register in valid_registers.keys()


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


def is_valid_name(name):
    return not is_valid_operand(name) and valid_name_regex.fullmatch(name)


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
    return 0


def mnemonic_lda(operands, errors=None):
    return 0


def mnemonic_sta(operands, errors=None):
    return 0


def mnemonics_push_pop(mnemonic, operands, errors=None):
    return 0


def mnemonics_add_sub_cmp(mnemonic, operands, errors=None):
    return 0


def mnemonics_jmp_jc_jnc_jz_jnz_call_cc_cnc_cz_cnz(mnemonic, operands, errors=None):
    return 0


def mnemonics_ret_rc_rnc_rz_rnz(mnemonic, operands, errors=None):
    return 0


def mnemonics_db_dw(mnemonic, operands, errors=None):
    return 0


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


def parse_asm_line_str(line_str, errors=None):
    directive = None
    symbol_name = None
    mnemonic = None
    operands = []
    operand = ''
    operand_expected = False

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
                operand += ' ' + token
                operand_expected = False
            else:
                mnemonic = token

    # end of line

    if not errors:
        if operand:
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
    global current_asm_file_name, current_asm_line_num, current_asm_line_str, current_symbol_name

    with open(file_name, 'r') as asm:
        current_asm_file_name = file_name
        line_num = 0
        current_asm_line_num = line_num

        for line_str in asm.readlines():
            current_asm_line_str = line_str
            line_num += 1
            current_asm_line_num = line_num

            errors = []

            line = parse_asm_line_str(current_asm_line_str, errors)

            if not errors and line['directive']:
                directive = line['directive']
                directive_lower = directive.lower()

                if not is_valid_directive(directive_lower):
                    errors.append({
                        'name': 'INVALID_DIRECTIVE',
                        'info': [',']
                    })
                elif 'end' == directive_lower:
                    break

            if not errors and line['symbol_name']:
                symbol_name = line['symbol_name']

                if symbols.symbol_exists(symbol_name):
                    errors.append({
                        'name': 'DUPLICATE_SYMBOL',
                        'info': [symbol_name]
                    })
                elif not is_valid_name(symbol_name):
                    errors.append({
                        'name': 'INVALID_SYMBOL_NAME',
                        'info': [symbol_name]
                    })
                elif not line['mnemonic']:
                    errors.append({
                        'name': 'SYMBOL_WITHOUT_INSTRUCTION',
                        'info': []
                    })
                else:
                    current_symbol_name = symbol_name

                    symbol_table.get_index(current_symbol_name)

            if not errors and line['mnemonic']:
                if not current_symbol_name:
                    errors.append({
                        'name': 'INSTRUCTION_WITHOUT_SYMBOL',
                        'info': []
                    })
                else:
                    symbol = symbols.add_symbol(current_symbol_name)


        # end of file


if '__main__' == __name__:
    if len(sys.argv) < 2:
        pass
    else:
        asm_file_name = sys.argv[1]
        assemble_asm_file(asm_file_name)
