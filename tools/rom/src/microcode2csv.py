import math

valid_control_signals = {
    'hlt':             int(math.pow(2,  0)),
    'srst':            int(math.pow(2,  1)),
    'nxt':             int(math.pow(2,  2)),
    'data_to_ir':      int(math.pow(2,  3)),
    'data_to_a':       int(math.pow(2,  4)),
    'a_to_data':       int(math.pow(2,  5)),
    'a_to_x':          int(math.pow(2,  6)),
    'data_to_y':       int(math.pow(2,  7)),

    'sub':             int(math.pow(2,  8)),
    'flags':           int(math.pow(2,  9)),
    'z_to_data':       int(math.pow(2, 10)),
    'data_to_b':       int(math.pow(2, 11)),
    'b_to_data':       int(math.pow(2, 12)),
    'data_to_c':       int(math.pow(2, 13)),
    'c_to_data':       int(math.pow(2, 14)),
    'data_to_d':       int(math.pow(2, 15)),

    'd_to_data':       int(math.pow(2, 16)),
    'addr_to_ip':      int(math.pow(2, 17)),
    'ip_to_addr':      int(math.pow(2, 18)),
    'ip_inc':          int(math.pow(2, 19)),
    'addr_to_mar':     int(math.pow(2, 20)),
    'mar_inc':         int(math.pow(2, 21)),
    'data_to_mdr':     int(math.pow(2, 22)),
    'mdr_to_data':     int(math.pow(2, 23)),

    'addr_to_hl':      int(math.pow(2, 24)),
    'hl_to_addr':      int(math.pow(2, 25)),
    'addr_to_t':       int(math.pow(2, 26)),
    't_to_addr':       int(math.pow(2, 27)),
    'addr_to_sp':      int(math.pow(2, 28)),
    'sp_to_addr':      int(math.pow(2, 29)),
    'sp_inc':          int(math.pow(2, 30)),
    'sp_dec':          int(math.pow(2, 31)),

    'addr_hi_to_data': int(math.pow(2, 32)),
    'data_to_addr_hi': int(math.pow(2, 33)),
    'addr_lo_to_data': int(math.pow(2, 34)),
    'data_to_addr_lo': int(math.pow(2, 35))
}


def is_valid_control_signal(control_signal):
    return control_signal in valid_control_signals.keys()


# main


def main():
    print('microcode2csv')


if '__main__' == __name__:
    main()
