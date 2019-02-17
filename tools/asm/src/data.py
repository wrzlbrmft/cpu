import re

valid_dec_regex = re.compile('[1-9][0-9]*')
valid_hex_regex = re.compile('0x[0-9a-f]+', re.IGNORECASE)
valid_bin_regex = re.compile('0b[0-1]+', re.IGNORECASE)
valid_oct_regex = re.compile('0[0-7]+')
valid_chr_regex = re.compile('(\'.\'|\".\")', re.IGNORECASE)
valid_str_regex = re.compile('(\'.{2,}\'|\".{2,}\")', re.IGNORECASE)


def is_valid_dec(data):
    return valid_dec_regex.fullmatch(data)


def is_valid_hex(data):
    return valid_hex_regex.fullmatch(data)


def is_valid_bin(data):
    return valid_bin_regex.fullmatch(data)


def is_valid_oct(data):
    return valid_oct_regex.fullmatch(data)


def is_valid_chr(data):
    return valid_chr_regex.fullmatch(data)


def is_valid_str(data):
    return valid_str_regex.fullmatch(data)


def is_valid(data):
    return '0' == data or \
        is_valid_dec(data) or \
        is_valid_hex(data) or \
        is_valid_bin(data) or \
        is_valid_oct(data) or \
        is_valid_chr(data) or \
        is_valid_str(data)


def get_value(data):
    if '0' == data:
        return 0
    elif is_valid_dec(data):
        return int(data)
    elif is_valid_hex(data):
        return int(data[2:], 16)
    elif is_valid_bin(data):
        return int(data[2:], 2)
    elif is_valid_oct(data):
        return int(data[1:], 8)
    elif is_valid_chr(data):
        return ord(data[1])
    elif is_valid_str(data):
        # string data is returned as a tuple containing the ascii codes of the individual characters
        # note: codes can be >255 because of unicode characters
        return tuple(map(ord, data[1:-1]))
    else:
        return None


def get_size(data):
    value = get_value(data)
    if isinstance(value, tuple):
        # for tuples (string data), return the size of the largest item (character)
        # note: size can be >8 bit because of unicode characters
        values = value
        size = 0
        for value in values:
            bits = value.bit_length()
            size = max(size, bits + (8 - bits) % 8)  # multiples of 8-bit
        return size
    elif value is not None:
        bits = value.bit_length()
        return bits + (8 - bits) % 8  # multiples of 8-bit
    else:
        return None
