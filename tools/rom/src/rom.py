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

output_bits_from = None
output_bits_to = None

rom = {}


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


def parse_output_bits(bits):
    i = bits.split('-')

    bits_from = i[0]
    if not bits_from.isdecimal() or int(bits_from) < 0:
        show_error({
            'name': 'INVALID_OUTPUT_BIT',
            'info': [bits_from]
        })
        return None, None
    else:
        bits_from = int(bits_from)

    if len(i) > 1:
        bits_to = i[1]
        if not bits_to.isdecimal() or int(bits_to) < 0:
            show_error({
                'name': 'INVALID_OUTPUT_BIT',
                'info': [bits_from]
            })
            return None, None
        else:
            bits_to = int(bits_to)

        if bits_to < bits_from:
            # change e.g. 7-0 to 0-7
            bits_from, bits_to = bits_to, bits_from
    else:
        bits_to = bits_from

    return bits_from, bits_to


def parse_addr_config(config_str):
    config = {}
    config_bits = 0

    for i in config_str.split(','):
        j = i.split(':')

        column = j[0]
        if not column.isdecimal() or int(column) < 1:
            show_error({
                'name': 'INVALID_COLUMN_NUMBER',
                'info': [column]
            })
            return None, None
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
                return None, None
            else:
                bits = int(bits)

        config[column] = bits

        if config_bits is not None:
            if bits is not None:
                config_bits += bits
            else:
                config_bits = None

    return config, config_bits


def read_flags_file(file_name, errors=None):
    global current_file_name, current_line_num, current_line_str

    if os.path.isfile(file_name):
        flags = {}
        flags_bits = 0

        with open(file_name, 'r') as file:
            current_file_name = file_name
            line_num = 0
            current_line_num = line_num

            for line_str in file.readlines():
                current_line_str = line_str
                line_num += 1
                current_line_num = line_num

                line_str = line_str.strip()
                if line_str:
                    i = line_str.split(';')

                    flag_name = i[0]
                    if is_valid_name(flag_name):
                        if len(i) > 1:
                            flag_value = i[1]
                            if data.is_valid(flag_value) and not data.is_valid_str(flag_value):
                                flag_value = data.get_value(flag_value)
                            else:
                                if errors is not None:
                                    errors.append({
                                        'name': 'INVALID_FLAG_VALUE',
                                        'info': [flag_value]
                                    })
                                return None, None
                        else:
                            flag_value = int(math.pow(2, flags_bits))

                        flags[flag_name] = flag_value
                        flags_bits = max(flags_bits, flag_value.bit_length())
                    else:
                        if errors is not None:
                            errors.append({
                                'name': 'INVALID_FLAG_NAME',
                                'info': [flag_name]
                            })
                        return None, None

        return flags, flags_bits
    else:
        if errors is not None:
            errors.append({
                'name': 'FILE_NOT_FOUND',
                'info': [file_name]
            })
        return None, None


def parse_data_config(config_str):
    global current_file_name, current_line_num, current_line_str

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

            flags, flags_bits = read_flags_file(flags_file_name, errors)

            if errors:
                show_error(errors[0])
                return None, None, None
            else:
                current_file_name = None
                current_line_num = 0
                current_line_str = None

                if len(i) > 2:
                    bits = i[2]
                    if not bits.isdecimal() or int(bits) < 1:
                        show_error({
                            'name': 'INVALID_BIT_WIDTH',
                            'info': [bits]
                        })
                        return None, None, None
                    else:
                        bits = int(bits)

                    if flags_bits > bits:
                        show_error({
                            'name': 'FLAGS_EXCEEDING_BIT_WIDTH',
                            'info': [flags_bits, bits]
                        })
                        return None, None, None
                else:
                    bits = flags_bits
        elif int(bits) < 1:
            show_error({
                'name': 'INVALID_BIT_WIDTH',
                'info': [bits]
            })
            return None, None, None
        else:
            bits = int(bits)

    return column, bits, flags


def flag_exists(flag_name):
    return flag_name in data_config_flags.keys()


def get_flag_value(flag_name):
    if flag_exists(flag_name):
        return data_config_flags[flag_name]
    else:
        return None


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
        elif data_config_flags:
            flag_names = column_value.split(',')
            column_value = 0
            for flag_name in flag_names:
                flag_name = flag_name.strip()
                if flag_exists(flag_name):
                    column_value |= get_flag_value(flag_name)
                else:
                    if errors is not None:
                        errors.append({
                            'name': 'UNKNOWN_FLAG',
                            'info': [flag_name]
                        })
                    return None, None
            column_value = format(column_value, 'b').zfill(data_config_bits)
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


def get_value_bits(value, bits_from, bits_to):
    value = format(value, 'b').zfill(bits_to + 1)
    if data_config_bits:
        value = value.zfill(data_config_bits)

    value = value[len(value) - bits_to - 1:len(value) - bits_from]
    value = int(value, 2)

    return value


def add_to_rom(addr_value, data_value):
    global rom

    addr_value = addr_value.split('x', 1)
    if len(addr_value) > 1:
        add_to_rom('0'.join(addr_value), data_value)
        add_to_rom('1'.join(addr_value), data_value)
    else:
        data_value = int(data_value, 2)

        if output_bits_from is not None and output_bits_to is not None:
            data_value = get_value_bits(data_value, output_bits_from, output_bits_to)

        if data_value:
            addr_value = int(addr_value[0], 2)
            rom[addr_value] = data_value


def read_csv_file(file_name):
    global current_file_name, current_line_num, current_line_str

    if os.path.isfile(file_name):
        with open(file_name, 'r') as csv:
            current_file_name = file_name
            line_num = 0
            current_line_num = line_num

            for line_str in csv.readlines():
                current_line_str = line_str
                line_num += 1
                current_line_num = line_num

                line_str = line_str.strip()
                if line_str:
                    errors = []

                    addr_value, data_value = parse_csv_line(line_str, errors)

                    if not errors:
                        add_to_rom(addr_value, data_value)

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

    current_file_name = None
    current_line_num = 0
    current_line_str = None


def write_raw_file(file_name):
    with open(file_name, 'w') as raw:
        raw.write('v2.0 raw\n')

        prev_addr_value = -1
        for addr_value in sorted(rom.keys()):
            for i in range(prev_addr_value, addr_value - 1):
                raw.write('0\n')

            data_value = rom[addr_value]
            data_value = hex(data_value)[2:]
            raw.write(data_value + '\n')

            prev_addr_value = addr_value


def write_img_file(file_name):
    pass


# main


def main():
    global addr_config, addr_config_bits, data_config_column, data_config_bits, data_config_flags, output_bits_from, \
        output_bits_to

    if len(sys.argv) < 5:
        show_error({
            'name': 'INSUFFICIENT_ARGUMENTS',
            'info': [len(sys.argv) - 1, 4]
        })
    else:
        csv_file_name = sys.argv[1]
        addr_config_str = sys.argv[2]
        data_config_str = sys.argv[3]

        output_file_name = sys.argv[4]
        output_file_extension = os.path.splitext(output_file_name)[1][1:]
        output_file_extension_lower = output_file_extension.lower()
        if not output_file_extension:
            show_error({
                'name': 'MISSING_OUTPUT_FILE_EXTENSION',
                'info': [output_file_name]
            })
        elif output_file_extension_lower not in ['raw', 'img']:
            show_error({
                'name': 'INVALID_OUTPUT_FILE_EXTENSION',
                'info': [output_file_extension]
            })

        if len(sys.argv) > 5:
            output_bits_from, output_bits_to = parse_output_bits(sys.argv[5])

        if not total_errors_count:
            addr_config, addr_config_bits = parse_addr_config(addr_config_str)

        if not total_errors_count:
            data_config_column, data_config_bits, data_config_flags = parse_data_config(data_config_str)

        if not total_errors_count:
            read_csv_file(csv_file_name)

        if not total_errors_count:
            if 'raw' == output_file_extension_lower:
                write_raw_file(output_file_name)
            elif 'img' == output_file_extension_lower:
                write_img_file(output_file_name)


if '__main__' == __name__:
    main()
