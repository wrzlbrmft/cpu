import i18n

import math
import os
import sys

total_errors_count = 0

current_file_name = None
current_line_num = 0
current_line_str = None

address_config = {}
data_config_column = None
data_config_bits = None
data_config_control_signals = {}


def show_error(error, line_str=None, line_num=None, file_name=None):
    global total_errors_count

    if line_str is None:
        line_str = current_line_str

    if line_num is None:
        line_num = current_line_num

    if file_name is None:
        file_name = current_file_name

    total_errors_count += 1

    if file_name:
        print(f'{file_name}:', end='')
        if line_num:
            print(f'{line_num}:', end='')
        print(' ', end='')

    print('error:', i18n.error_messages[error['name']].format(*error['info']))

    if line_str:
        print('', line_str.strip())

    print()


def parse_address_config(config_str):
    config = {}

    for i in config_str.split(','):
        j = i.split(':')

        column = j[0]
        if not column.isdecimal():
            show_error({
                'name': '',  # todo
                'info': [column]
            })
            return None

        bits = None
        if len(j) > 1:
            bits = j[1]
            if not bits.isdecimal():
                show_error({
                    'name': '',  # todo
                    'info': [bits]
                })
                return None

        config[column] = bits

    return config


def read_control_signals_file(file_name, errors=None):
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
        if errors is not None:
            errors.append({
                'name': 'FILE_NOT_FOUND',
                'info': [file_name]
            })
        return None, None


def parse_data_config(config_str):
    i = config_str.split(':')

    column = i[0]
    if not column.isdecimal():
        show_error({
            'name': '',  # todo
            'info': [column]
        })
        return None, None, None

    bits = None
    control_signals = {}
    if len(i) > 1:
        bits = i[1]
        if not bits.isdecimal():
            control_signals_file_name = bits

            errors = []

            bits, control_signals = read_control_signals_file(control_signals_file_name, errors)

            if errors:
                show_error(errors[0])
                return None, None, None

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

        if not total_errors_count:
            data_config_column, data_config_bits, data_config_control_signals = parse_data_config(data_config_str)


if '__main__' == __name__:
    main()
