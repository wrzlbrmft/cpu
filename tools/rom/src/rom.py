import math
import os
import sys

address_config = {}
data_config_column = None
data_config_bits = None
data_config_control_signals = {}


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


def read_control_signals_file(file_name):
    if os.path.isfile(file_name):
        control_signals = {}

        with open(file_name, 'r') as file:
            for line in file.readlines():
                line = line.strip()
                if line:
                    control_signals[line] = int(math.pow(2, len(control_signals)))
        bits = len(control_signals)

        return bits, control_signals
    else:
        return None, None


def parse_data_config(config_str):
    i = config_str.split(':')

    column = i[0]
    if not column.isdecimal():
        return None, None, None

    bits = None
    control_signals = {}
    if len(i) > 1:
        bits = i[1]
        if not bits.isdecimal():
            control_signals_file_name = bits
            bits, control_signals = read_control_signals_file(control_signals_file_name)

    return column, bits, control_signals


# main


def main():
    global address_config, data_config_column, data_config_bits, data_config_control_signals

    if len(sys.argv) < 5:
        pass
    else:
        csv_file_name = sys.argv[1]
        address_config_str = sys.argv[2]
        data_config_str = sys.argv[3]
        output_format = sys.argv[4]

        address_config = parse_address_config(address_config_str)
        data_config_column, data_config_bits, data_config_control_signals = parse_data_config(data_config_str)


if '__main__' == __name__:
    main()
