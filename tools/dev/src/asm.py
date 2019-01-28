import shlex

current_asm_file_name = None
current_asm_line_num = 0
current_asm_line_str = None


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
        pass

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

            line = parse_asm_line_str(current_asm_line_str)


if '__main__' == __name__:
    pass
