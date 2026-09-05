import random
from test_utils import random_byte, random_bytes

from crc_model import crc32_be, CRC32_POLY_BE
from crc32_be_clmul64 import crc32_be_clmul64, crc32_be_clmul64_v2
from crc32_be_clmul_fold import crc32_be_clmul_fold, crc32_be_clmul_fold_v2
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

    NUM_TESTS = 1000
    for _ in range(NUM_TESTS):
        data_bytes = random_bytes(8)
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


def test_crc32_be_clmul64_v2_sanity():
    # Single byte data
    for data in [0x1, 0x80, 0x17]:
        data_bytes = [data]
        # First, we compute the reference CRC32_BE value of the single byte data
        ref_crc32_be = crc32_be(0, data_bytes, CRC32_POLY_BE)
        # Then, we compute the same value but using carry-less multiply with the barrett's constant
        clmul64_crc32_be = crc32_be_clmul64_v2(data)
        assert ref_crc32_be == clmul64_crc32_be


def test_crc32_be_clmul64_v2_random():

    NUM_TESTS = 10000
    for _ in range(NUM_TESTS):
        data_bytes = random_bytes(8)
        assert len(data_bytes) <= 8
        # assembling data, they byte list needs to be reversed, since the first byte the crc32_be considers
        # is actually the one with highest index in the message
        data = byte_assemble(data_bytes[::-1])
        assert data < 2**64
        # First, we compute the reference CRC32_BE value of the single byte data
        ref_crc32_be = crc32_be(0, data_bytes, CRC32_POLY_BE)
        # Then, we compute the same value but using carry-less multiply with the barrett's constant
        clmul64_crc32_be = crc32_be_clmul64_v2(data)
        assert ref_crc32_be == clmul64_crc32_be


def test_crc32_be_clmul_fold_random():

    NUM_TESTS = 1000
    MAX_BUFFER_LEN = 256

    for _ in range(NUM_TESTS):
        data_len = random.randrange(1, MAX_BUFFER_LEN+1)
        data_bytes = random_bytes(data_len)

        # First, we compute the reference CRC32_BE value of the single byte data
        ref_crc32_be = crc32_be(0, data_bytes, CRC32_POLY_BE)
        # Then, we compute the same value but using carry-less multiply with folding method
        clmul_fold_crc32_be = crc32_be_clmul_fold(data_bytes)
        assert ref_crc32_be == clmul_fold_crc32_be


def test_crc32_be_clmul_fold_v2_random():

    NUM_TESTS = 1000
    MAX_BUFFER_LEN = 256

    for _ in range(NUM_TESTS):
        data_len = random.randrange(1, MAX_BUFFER_LEN+1)
        data_bytes = random_bytes(data_len)

        # First, we compute the reference CRC32_BE value of the single byte data
        ref_crc32_be = crc32_be(0, data_bytes, CRC32_POLY_BE)

        # Then, we compute the same value but using carry-less multiply with folding method
        clmul_fold_crc32_be_v2 = crc32_be_clmul_fold_v2(data_bytes)
        assert ref_crc32_be == clmul_fold_crc32_be_v2
    
