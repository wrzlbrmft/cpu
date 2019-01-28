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
