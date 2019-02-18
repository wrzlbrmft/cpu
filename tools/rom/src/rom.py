import sys

address_config = {}
data_config_column = None
data_config_bits = None
control_signals = {}


def parse_address_config(config_str):
    config = {}

    for i in config_str.split(','):
        j = i.split(':')

        column = j[0]
        if not column.isdecimal():
            return None

        bits = None
        if len(j) > 1:
            bits = j[1]
            if not bits.isdecimal():
                return None

        config[column] = bits

    return config


# main


def main():
    global address_config

    if len(sys.argv) < 5:
        pass
    else:
        csv_file_name = sys.argv[1]
        address_config_str = sys.argv[2]
        data_config_str = sys.argv[3]
        output_format = sys.argv[4]

        address_config = parse_address_config(address_config_str)
        print(address_config)


if '__main__' == __name__:
    main()
