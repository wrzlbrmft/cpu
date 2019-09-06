def write_raw_file(file_name, data, zero_fill=0):
    # if data is a list (e.g. from bin2raw), convert it into a dict by adding a
    # numeric key like an array index
    if isinstance(data, list):
        data = {addr_value: data[addr_value] for addr_value in range(len(data))}

    with open(file_name, 'w') as raw:
        raw.write('v2.0 raw\n')

        for i in range(zero_fill):
            raw.write('0\n')

        prev_addr_value = -1
        for addr_value in sorted(data.keys()):
            data_value = data[addr_value]

            if data_value:
                for i in range(prev_addr_value, addr_value - 1):
                    raw.write('0\n')

                data_value = hex(data_value)[2:]
                raw.write(data_value + '\n')

                prev_addr_value = addr_value
