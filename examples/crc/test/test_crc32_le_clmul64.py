import random
from test_utils import random_byte

from crc_model import crc32_le, CRC32_POLY_LE
from crc32_le_clmul64 import crc32_le_clmul64, crc32_le_clmul64_v2
from bit_manip_utils import byte_assemble


def test_crc32_be_clmul64_random():

    NUM_TESTS = 10000
    for _ in range(NUM_TESTS):
        data_bytes = [random_byte() for _ in range(8)]
        assert len(data_bytes) <= 8
        # assembling data, they byte list needs to be reversed, since the first byte the crc32_be considers
        # is actually the one with highest index in the message
        data = byte_assemble(data_bytes)
        assert data < 2**64
        # First, we compute the reference CRC32_LE value of the single byte data
        ref_crc32_le = crc32_le(0, data_bytes, CRC32_POLY_LE)
        # Then, we compute the same value but using carry-less multiply with the barrett's constant
        clmul64_crc32_le = crc32_le_clmul64(data)

        assert ref_crc32_le == clmul64_crc32_le


def test_crc32_le_clmul64_v2_random():
    random_bytes = lambda: random.randrange(256)

    NUM_TESTS = 10000
    for _ in range(NUM_TESTS):
        data_bytes = [random_bytes() for _ in range(8)]
        assert len(data_bytes) <= 8
        # assembling data, they byte list needs to be reversed, since the first byte the crc32_be considers
        # is actually the one with highest index in the message
        data = byte_assemble(data_bytes)
        assert data < 2**64
        # First, we compute the reference CRC32_LE value of the single byte data
        ref_crc32_le = crc32_le(0, data_bytes, CRC32_POLY_LE)
        # Then, we compute the same value but using carry-less multiply with the barrett's constant
        clmul64_crc32_le = crc32_le_clmul64_v2(data)

        assert ref_crc32_le == clmul64_crc32_le
    
