import i18n

import os
import sys

total_errors_count = 0

data_config_bits = 0


def show_error(error):
    global total_errors_count

    total_errors_count += 1

    print('error:', i18n.error_messages[error['name']].format(*error['info']))

    print()


def parse_extract_bits(bits_str):
    i = bits_str.split('-')

    bits_from = i[0]
    if not bits_from.isdecimal() or int(bits_from) < 0:
        show_error({
            'name': 'INVALID_EXTRACT_BITS',
            'info': [bits_from]
        })
        return None, None
    else:
        bits_from = int(bits_from)

    if len(i) > 1:
        bits_to = i[1]
        if not bits_to.isdecimal() or int(bits_to) < 0:
            show_error({
                'name': 'INVALID_EXTRACT_BITS',
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


# main


def main():
    global data_config_bits

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
            data_config_bits = sys.argv[2]
            if not data_config_bits.isdecimal() or int(data_config_bits) < 1:
                show_error({
                    'name': 'INVALID_BIT_WIDTH',
                    'info': [data_config_bits]
                })
            else:
                data_config_bits = int(data_config_bits)
        else:
            data_config_bits = 8

        if not total_errors_count and len(sys.argv) > 3:
            output_file_name = sys.argv[3]
        else:
            output_file_name = os.path.splitext(os.path.basename(input_file_name))[0] + '.raw'

        if not total_errors_count and len(sys.argv) > 4:
            extract_bits_from, extract_bits_to = parse_extract_bits(sys.argv[4])

        if not total_errors_count:
            if os.path.isfile(input_file_name):
                with open(input_file_name, 'rb') as input_file:
                    with open(output_file_name, 'w') as output_file:
                        output_file.write('v2.0 raw\n')
            else:
                show_error({
                    'name': 'FILE_NOT_FOUND',
                    'info': [input_file_name]
                })


if '__main__' == __name__:
    main()
