from crc_model import crc32_be, crc32_le, CRC32_POLY_LE, CRC32_POLY_BE
from bit_manip_utils import bit_reverse


def test_crc32_be():
    assert crc32_be(0, [0x00], CRC32_POLY_BE) == 0x00000000
    assert crc32_be(0, [0x01], CRC32_POLY_BE) == CRC32_POLY_BE
    assert crc32_be(0xcafebeef, [], CRC32_POLY_BE) == 0xcafebeef

def test_crc32_le():
    assert crc32_le(0, [0x00], CRC32_POLY_LE) == 0x00000000
    assert crc32_le(0, [0x80], CRC32_POLY_LE) == CRC32_POLY_LE

def test_crc32():
    byte = 0x37
    byte_rev = bit_reverse(byte, 8)
    # the CRC32BE is equivalent to the CRC32LE with each byte being bit reverse
    # (while keeping the bytes in the same order) and bit reversing the final result
    assert crc32_be(0, [byte], CRC32_POLY_BE) == bit_reverse(crc32_le(0, [byte_rev], CRC32_POLY_LE), 32)
    data = [0x11, 0x22, 0x33, 0x44]
    data_rev = [bit_reverse(byte, 8) for byte in data]
    assert crc32_be(0, data, CRC32_POLY_BE) == bit_reverse(crc32_le(0, data_rev, CRC32_POLY_LE), 32)
    

    