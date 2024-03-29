import argparse
import bin_file
import data
import i18n
import raw_file

import os
import sys

total_errors_count = 0

# default number of zero-bytes to fill in at the beginning of the raw file
# should match the default memory address to which a program is loaded before it is executed by the cpu
zero_fill_default = 0x0900  # TODO: for the time being...


def show_error(error):
    global total_errors_count

    total_errors_count += 1

    print('error:', i18n.error_messages[error['name']].format(*error['info']))

    print()


def parse_zero_fill(zero_fill_str):
    if data.is_valid(zero_fill_str) and not data.is_valid_str(zero_fill_str):
        return data.get_value(zero_fill_str)
    else:
        show_error({
            'name': 'INVALID_ZERO_FILL',
            'info': [zero_fill_str]
        })
        return None


# main

parser = argparse.ArgumentParser(description='convert binary file to raw file')
parser.add_argument('file', help='binary file to be converted')
parser.add_argument('zeros', nargs='?', default=zero_fill_default, type=int,
                    help='number of zero-bytes to fill in at the beginning of the raw file')
args = parser.parse_args()


def main():
    global args

    input_file_name = args.file
    output_file_name = os.path.splitext(os.path.basename(input_file_name))[0] + '.raw'

    if len(sys.argv) > 2:
        zero_fill = parse_zero_fill(sys.argv[2])

    if not total_errors_count:
        errors = []

        bin_data = bin_file.read_bin_file(input_file_name, errors)

        if errors:
            show_error(errors[0])
        else:
            raw_file.write_raw_file(output_file_name, bin_data, args.zeros)


if '__main__' == __name__:
    main()

    if total_errors_count:
        sys.exit(1)
