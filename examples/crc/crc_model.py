def crc32_be(crc: int, data: list[int], poly: int) -> int:
    """ 32-bit CRC, big-endian mode from initial value @p crc
        of each byte in data, using polynomial @p poly """
    acc = crc
    for byte in data:
        acc = acc ^ (byte << 24)
        for i in range(8):
            if acc & 0x80000000:
                acc = ((acc << 1) ^ poly) & 0xffffffff
            else:
                acc = (acc << 1)
            assert acc < 2**32 # CRC should not exceed 32-bit
    return acc

def crc32_le(crc: int, data: list[int], poly: int) -> int:
    """ 32-bit CRC, little-endian mode from initial value @p crc
        of each byte in data, using polynomial @p poly """
    acc = crc
    for byte in data:
        acc = acc ^ byte
        for i in range(8):
            if acc & 1:
                acc = (acc >> 1) ^ poly
            else:
                acc >>= 1
        assert acc < 2**32 # CRC should not exceed 32-bit
    return acc

def crc32c(crc: int, data: list[int]) -> int:
    """ 32-bit CRC Castagnoli """
    return crc32_le(crc, data, CRC32C_POLY_LE)
    
 # From: https://codebrowser.dev/linux/linux/include/linux/crc32poly.h.html
 # The polynomial used by crc32_le(), in integer form.  See crc32_le().
CRC32_POLY_LE = 0xedb88320
# The polynomial used by crc32_be(), in integer form.  See crc32_be().
CRC32_POLY_BE = 0x04c11db7
# The polynomial used by crc32c(), in integer form.  See crc32c().
CRC32C_POLY_LE = 0x82f63b78

        