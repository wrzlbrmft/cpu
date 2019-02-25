import struct


def word_to_le(value):
    return struct.pack('<H', value)


def word_to_be(value):
    return struct.pack('>H', value)


def le_to_word(values):
    return struct.unpack('<H', values)[0]


def be_to_word(values):
    return struct.unpack('>H', values)[0]


def byte_length(value):
    bits = value.bit_length()
    bits = bits + (8 - bits) % 8  # multiples of 8-bit
    return bits // 8
