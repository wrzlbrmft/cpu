import sys

address_config = {}
data_config_column = None
data_config_bits = None
control_signals = {}


# main


def main():
    if len(sys.argv) < 5:
        pass
    else:
        csv_file_name = sys.argv[1]
        address_config_str = sys.argv[2]
        data_config_str = sys.argv[3]
        output_format = sys.argv[4]


if '__main__' == __name__:
    main()
