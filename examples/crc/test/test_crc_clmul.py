from crc_model import CRC32_POLY_BE, crc32_be, CRC32_POLY_LE, crc32_le, crc32c, CRC32C_POLY_LE
from crc_intro import crc32_be_clmul
from crc32_le_clmul import crc32_le_clmul_generic, crc32_le_clmul, crc32c_clmul
from bit_manip_utils import byte_assemble
import random


random_bytes = lambda: random.randrange(256)

def test_crc32_be_clmul_sanity():
    # Single byte data
    for data in [0x1, 0x80, 0x17]:
        data_bytes = [data]
        # First, we compute the reference CRC32_BE value of the single byte data
        ref_crc32_be = crc32_be(0, data_bytes, CRC32_POLY_BE)
        # Then, we compute the same value but using carry-less multiply with the barrett's constant
        clmul_crc32_be = crc32_be_clmul(data)
        assert ref_crc32_be == clmul_crc32_be


def test_crc32_be_clmul_extended():
    # Multi-byte data (4 bytes, corresponding to the CRC width)
    for data_bytes in [[0x0, 0x0, 0x0, 0x1], [0x1, 0x0, 0x0, 0x0], [random_bytes() for _ in range(4)]]:
        assert len(data_bytes) <= 4
        # assembling data, they byte list needs to be reversed, since the first byte the crc32_be considers
        # is actually the one with highest index in the message
        data = byte_assemble(data_bytes[::-1])
        # First, we compute the reference CRC32_BE value of the single byte data
        ref_crc32_be = crc32_be(0, data_bytes, CRC32_POLY_BE)
        # Then, we compute the same value but using carry-less multiply with the barrett's constant
        clmul_crc32_be = crc32_be_clmul(data)
        assert ref_crc32_be == clmul_crc32_be


def test_crc32_le_clmul_sanity():
    # Single byte data
    for data_rev in [0x08, 0x80, 0x1, 0x71]:
        data_bytes_rev = [data_rev] + [0, 0, 0]

        # First, we compute the reference CRC32_LE value of the single byte data
        ref_crc32_le = crc32_le(0, data_bytes_rev, CRC32_POLY_LE)
        # Then, we compute the same value but using carry-less multiply with the barrett's constant
        clmul_crc32_le = crc32_le_clmul(data_rev)
        assert ref_crc32_le == clmul_crc32_le


def test_crc32_le_clmul_random():
    # Multi-byte data (4 bytes, corresponding to the CRC width)
    for data_bytes_rev in [[0x0, 0x0, 0x0, 0x1], [0x1, 0x0, 0x0, 0x0], [random_bytes() for _ in range(4)]]:
        data_rev = byte_assemble(data_bytes_rev)

        # First, we compute the reference CRC32_LE value of the multi byte data
        ref_crc32_le = crc32_le(0, data_bytes_rev, CRC32_POLY_LE)
        # Then, we compute the same value but using carry-less multiply with the barrett's constant
        clmul_crc32_le = crc32_le_clmul(data_rev)
        assert ref_crc32_le == clmul_crc32_le


def test_crc32c_clmul_random():
    # Multi-byte data (4 bytes, corresponding to the CRC width)
    # FOR CRC32C
    for data_bytes_rev in [[0, 0, 0, 0], [0x0, 0x0, 0x0, 0x1], [0x1, 0x0, 0x0, 0x0], [random_bytes() for _ in range(4)]]:
        data_rev = byte_assemble(data_bytes_rev)

        # First, we compute the reference CRC32_LE value of the multi byte data
        ref_crc32c_le = crc32c(0, data_bytes_rev)
        # Then, we compute the same value but using carry-less multiply with the barrett's constant
        clmul_crc32c_le = crc32_le_clmul_generic(data_rev, CRC32C_POLY_LE)
        assert ref_crc32c_le == clmul_crc32c_le

        clmul_crc32c = crc32c_clmul(data_rev)
        assert ref_crc32c_le == clmul_crc32c


def test_crc32c_clmul_extended():
    # More agressive CRC32C testing
    NUM_TESTS = 1000
    for data_bytes_rev in [[random_bytes() for _ in range(4)] for _ in range(NUM_TESTS)]:
        data_rev = byte_assemble(data_bytes_rev)

        # First, we compute the reference CRC32_LE value of the multi byte data
        ref_crc32c_le = crc32c(0, data_bytes_rev)
        # Then, we compute the same value but using carry-less multiply with the barrett's constant
        clmul_crc32c = crc32c_clmul(data_rev)

        # checks
        assert ref_crc32c_le == clmul_crc32c