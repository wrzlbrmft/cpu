import struct


def word_to_le(value):
    return struct.pack('<H', value)


def word_to_be(value):
    return struct.pack('>H', value)
