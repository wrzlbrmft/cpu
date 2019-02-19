import data
import i18n

import math
import os
import re
import sys

total_errors_count = 0

current_file_name = None
current_line_num = 0
current_line_str = None

addr_config = {}
addr_config_bits = 0
data_config_column = 0
data_config_bits = 0
data_config_flags = {}

valid_name_regex = re.compile('[_a-z][_a-z0-9]*', re.IGNORECASE)
valid_bits_regex = re.compile('0b[0-1x]+', re.IGNORECASE)


def is_valid_name(s):
    return valid_name_regex.fullmatch(s)


def is_valid_bits(s):
    return valid_bits_regex.fullmatch(s)


def get_bits_value(s):
    if is_valid_bits(s):
        return s[2:]
    else:
        return None


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


def parse_addr_config(config_str):
    global addr_config_bits

    config = {}

    for i in config_str.split(','):
        j = i.split(':')

        column = j[0]
        if not column.isdecimal() or int(column) < 1:
            show_error({
                'name': 'INVALID_COLUMN_NUMBER',
                'info': [column]
            })
            return None
        else:
            column = int(column)

        bits = None
        if len(j) > 1:
            bits = j[1]
            if not bits.isdecimal() or int(bits) < 1:
                show_error({
                    'name': 'INVALID_BIT_WIDTH',
                    'info': [bits]
                })
                return None
            else:
                bits = int(bits)

        config[column] = bits

        if addr_config_bits is not None:
            if bits is not None:
                addr_config_bits += bits
            else:
                addr_config_bits = None

    return config


def read_flags_file(file_name, errors=None):
    if os.path.isfile(file_name):
        flags = {}

        with open(file_name, 'r') as file:
            for line_str in file.readlines():
                line_str = line_str.strip()
                if line_str:
                    if is_valid_name(line_str):
                        flags[line_str] = int(math.pow(2, len(flags)))
                    else:
                        if errors is not None:
                            errors.append({
                                'name': 'INVALID_FLAG_NAME',
                                'info': [line_str]
                            })
                        return None, None

        bits = len(flags)

        return bits, flags
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
    if not column.isdecimal() or int(column) < 1:
        show_error({
            'name': 'INVALID_COLUMN_NUMBER',
            'info': [column]
        })
        return None, None, None
    else:
        column = int(column)

    bits = None
    flags = {}
    if len(i) > 1:
        bits = i[1]
        if not bits.isdecimal():
            flags_file_name = bits

            errors = []

            bits, flags = read_flags_file(flags_file_name, errors)

            if errors:
                show_error(errors[0])
                return None, None, None
        elif int(bits) < 1:
            show_error({
                'name': 'INVALID_BIT_WIDTH',
                'info': [bits]
            })
            return None, None, None
        else:
            bits = int(bits)

    return column, bits, flags


def parse_csv_line(line_str, errors=None):
    columns = line_str.split(';')

    addr_value = ''
    data_value = ''

    for column, bits in addr_config.items():
        if column <= len(columns):
            column_value = columns[column - 1]
            if data.is_valid(column_value) and not data.is_valid_str(column_value):
                column_value = format(data.get_value(column_value), 'b')
                if bits is not None:
                    column_value = column_value.zfill(bits)
            elif is_valid_bits(column_value):
                column_value = get_bits_value(column_value)
                if bits is not None:
                    column_value = column_value.zfill(bits)
            else:
                if errors is not None:
                    errors.append({
                        'name': 'INVALID_ADDR_VALUE',
                        'info': [column_value]
                    })
                return None, None
            addr_value += column_value
        else:
            if errors is not None:
                errors.append({
                    'name': 'ADDR_COLUMN_NOT_FOUND',
                    'info': [column]
                })
                return None, None

    if addr_config_bits is not None and len(addr_value) > addr_config_bits:
        if errors is not None:
            errors.append({
                'name': 'INCOMPATIBLE_ADDR_SIZE',
                'info': [len(addr_value), addr_config_bits]
            })
            return None, None

    if data_config_column <= len(columns):
        column_value = columns[data_config_column - 1]
        if data.is_valid(column_value) and not data.is_valid_str(column_value):
            column_value = format(data.get_value(column_value), 'b')
            if data_config_bits is not None:
                column_value = column_value.zfill(data_config_bits)
        else:
            if errors is not None:
                errors.append({
                    'name': 'INVALID_DATA_VALUE',
                    'info': [column_value]
                })
            return None, None
        data_value = column_value
    else:
        if errors is not None:
            errors.append({
                'name': 'DATA_COLUMN_NOT_FOUND',
                'info': [data_config_column]
            })
            return None, None

    if data_config_bits is not None and len(data_value) > data_config_bits:
        if errors is not None:
            errors.append({
                'name': 'INCOMPATIBLE_DATA_SIZE',
                'info': [len(data_value), data_config_bits]
            })
            return None, None

    return addr_value, data_value


def read_csv_file(file_name):
    if os.path.isfile(file_name):
        with open(file_name, 'r') as csv:
            for line_str in csv.readlines():
                line_str = line_str.strip()
                if line_str:
                    errors = []

                    addr_value, data_value = parse_csv_line(line_str, errors)

                    if not errors:
                        print(addr_value, data_value)

                    # end of line

                    if errors:
                        show_error(errors[0])
                        break

            # end of file
    else:
        show_error({
            'name': 'FILE_NOT_FOUND',
            'info': [file_name]
        })


# main


def main():
    global addr_config, data_config_column, data_config_bits, data_config_flags

    if len(sys.argv) < 5:
        show_error({
            'name': 'INSUFFICIENT_ARGUMENTS',
            'info': [len(sys.argv) - 1, 4]
        })
    else:
        csv_file_name = sys.argv[1]
        addr_config_str = sys.argv[2]
        data_config_str = sys.argv[3]
        output_format = sys.argv[4]

        addr_config = parse_addr_config(addr_config_str)

        if not total_errors_count:
            data_config_column, data_config_bits, data_config_flags = parse_data_config(data_config_str)

        if not total_errors_count:
            read_csv_file(csv_file_name)


if '__main__' == __name__:
    main()
