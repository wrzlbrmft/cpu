import endianness


def dump_buffer(buffer):
    row = 0
    col = 0

    for i in range(0, len(buffer)):
        if 0 == col:
            print(hex(row)[2:].upper().zfill(4), '   ', end='')

        byte = buffer[i]
        print(hex(byte)[2:].upper().zfill(2), '', end='')
        col += 1

        if 8 == col or i == len(buffer) - 1:
            print('   ' * (8 - col), '  ', end='')
            for j in range(row, row + col):
                byte = buffer[j]
                if byte not in range(33, 126):
                    byte = 46  # .
                print(chr(byte), end='')
            print('')
            row += col
            col = 0


def read_byte(file):
    value = file.read(1)
    if 1 == len(value):
        return value[0]
    else:
        return None


def read_word_le(file):
    values = file.read(2)
    if 2 == len(values):
        return endianness.le_to_word(values)
    else:
        return None


def read_word_be(file):
    values = file.read(2)
    if 2 == len(values):
        return endianness.be_to_word(values)
    else:
        return None


def read_str(file, length=None):
    # if no string length is given, read one byte containing the string length
    if length is None:
        length = read_byte(file)

    if 0 == length:
        return ''
    elif length > 0:
        values = file.read(length)
        if len(values) == length:
            return values.decode('ascii')
        else:
            return None
    else:
        return None
