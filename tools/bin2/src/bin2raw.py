import bin_file
import i18n
import raw_file

import os
import sys

total_errors_count = 0


def show_error(error):
    global total_errors_count

    total_errors_count += 1

    print('error:', i18n.error_messages[error['name']].format(*error['info']))

    print()


# main


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        pass  # TODO: help
    elif len(sys.argv) < 2:
        show_error({
            'name': 'NO_INPUT_FILE',
            'info': []
        })
    else:
        input_file_name = sys.argv[1]

        if len(sys.argv) > 2:
            output_file_name = sys.argv[2]
        else:
            output_file_name = os.path.splitext(os.path.basename(input_file_name))[0] + '.raw'

        errors = []

        data = bin_file.read_bin_file(input_file_name, errors)

        if errors:
            show_error(errors[0])
        else:
            raw_file.write_raw_file(output_file_name, data)


if '__main__' == __name__:
    main()
