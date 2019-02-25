def write_raw_file(file_name, data):
    if isinstance(data, list):
        data = {addr_value: data[addr_value] for addr_value in range(0, len(data))}

    with open(file_name, 'w') as raw:
        raw.write('v2.0 raw\n')

        prev_addr_value = -1
        for addr_value in sorted(data.keys()):
            for i in range(prev_addr_value, addr_value - 1):
                raw.write('0\n')

            data_value = data[addr_value]
            data_value = hex(data_value)[2:]
            raw.write(data_value + '\n')

            prev_addr_value = addr_value
