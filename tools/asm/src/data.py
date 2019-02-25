import binary

import re

valid_dec_regex = re.compile('[1-9][0-9]*')
valid_hex_regex = re.compile('0x[0-9a-f]+', re.IGNORECASE)
valid_bin_regex = re.compile('0b[0-1]+', re.IGNORECASE)
valid_oct_regex = re.compile('0o[0-7]+')
valid_chr_regex = re.compile('(\'.\'|\".\")', re.IGNORECASE)
valid_str_regex = re.compile('(\'.{2,}\'|\".{2,}\")', re.IGNORECASE)


def is_valid_dec(s):
    return valid_dec_regex.fullmatch(s)


def is_valid_hex(s):
    return valid_hex_regex.fullmatch(s)


def is_valid_bin(s):
    return valid_bin_regex.fullmatch(s)


def is_valid_oct(s):
    return valid_oct_regex.fullmatch(s)


def is_valid_chr(s):
    return valid_chr_regex.fullmatch(s)


def is_valid_str(s):
    return valid_str_regex.fullmatch(s)


def is_valid(s):
    return '0' == s or \
        is_valid_dec(s) or \
        is_valid_hex(s) or \
        is_valid_bin(s) or \
        is_valid_oct(s) or \
        is_valid_chr(s) or \
        is_valid_str(s)


def get_value(s):
    if '0' == s:
        return 0
    elif is_valid_dec(s):
        return int(s)
    elif is_valid_hex(s):
        return int(s[2:], 16)
    elif is_valid_bin(s):
        return int(s[2:], 2)
    elif is_valid_oct(s):
        return int(s[1:], 8)
    elif is_valid_chr(s):
        return ord(s[1])
    elif is_valid_str(s):
        # string data is returned as a tuple containing the ascii codes of the individual characters
        # note: codes can be >255 because of unicode characters
        return tuple(map(ord, s[1:-1]))
    else:
        return None


def get_size(s):
    value = get_value(s)
    if isinstance(value, tuple):
        # for tuples (string data), return the size of the largest item (character)
        # note: size can be >8 bit because of unicode characters
        values = value
        size = 0
        for value in values:
            size = max(size, binary.byte_length(value) * 8)  # multiples of 8-bit
        return size
    elif value is not None:
        return binary.byte_length(value) * 8  # multiples of 8-bit
    else:
        return None
