import shlex
import sys

current_asm_file_name = None
current_asm_line_num = 0
current_asm_line_str = None

valid_directives = ['end']


def is_valid_directive(directive):
    return directive in valid_directives


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
        return False
    else:
        return {
            'directive': directive,
            'symbol_name': symbol_name,
            'mnemonic': mnemonic,
            'operands': operands
        }


def assemble_asm_file(file_name):
    global current_asm_file_name, current_asm_line_num, current_asm_line_str

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

            if not errors and line['mnemonic']:
                pass

        # end of file


if '__main__' == __name__:
    if len(sys.argv) < 2:
        pass
    else:
        asm_file_name = sys.argv[1]
        assemble_asm_file(asm_file_name)
