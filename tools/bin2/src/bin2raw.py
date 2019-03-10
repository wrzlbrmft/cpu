import bin_file
import data
import i18n
import raw_file

import os
import sys

total_errors_count = 0

# number of zero-bytes to fill in at the beginning of the raw file
zero_fill = 0x0800  # TODO: for the time being...


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


def main():
    global zero_fill

    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        pass  # TODO: help
    elif len(sys.argv) < 2:
        show_error({
            'name': 'NO_INPUT_FILE',
            'info': []
        })
    else:
        input_file_name = sys.argv[1]
        output_file_name = os.path.splitext(os.path.basename(input_file_name))[0] + '.raw'

        if len(sys.argv) > 2:
            zero_fill = parse_zero_fill(sys.argv[2])

        if not total_errors_count:
            errors = []

            bin_data = bin_file.read_bin_file(input_file_name, errors)

            if errors:
                show_error(errors[0])
            else:
                raw_file.write_raw_file(output_file_name, bin_data, zero_fill)


if '__main__' == __name__:
    main()
