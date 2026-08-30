import random

from crc_model import crc32_be, CRC32_POLY_BE
from crc32_be_clmul64 import crc32_be_clmul64
from bit_manip_utils import byte_assemble


def test_crc32_be_clmul64_sanity():
    # Single byte data
    for data in [0x1, 0x80, 0x17]:
        data_bytes = [data]
        # First, we compute the reference CRC32_BE value of the single byte data
        ref_crc32_be = crc32_be(0, data_bytes, CRC32_POLY_BE)
        # Then, we compute the same value but using carry-less multiply with the barrett's constant
        clmul64_crc32_be = crc32_be_clmul64(data)
        assert ref_crc32_be == clmul64_crc32_be


def test_crc32_be_clmul64_random():
    random_bytes = lambda: random.randrange(256)

    NUM_TESTS = 1000
    for _ in range(NUM_TESTS):
        data_bytes = [random_bytes() for _ in range(8)]
        assert len(data_bytes) <= 8
        # assembling data, they byte list needs to be reversed, since the first byte the crc32_be considers
        # is actually the one with highest index in the message
        data = byte_assemble(data_bytes[::-1])
        assert data < 2**64
        # First, we compute the reference CRC32_BE value of the single byte data
        ref_crc32_be = crc32_be(0, data_bytes, CRC32_POLY_BE)
        # Then, we compute the same value but using carry-less multiply with the barrett's constant
        clmul64_crc32_be = crc32_be_clmul64(data)
        assert ref_crc32_be == clmul64_crc32_be


    
