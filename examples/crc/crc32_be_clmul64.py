# -*- coding: utf-8
import random

from bit_manip_utils import byte_assemble
from carry_less_multiply import carry_less_multiply
from crc_intro import CRC32_BE_INV, CRC32_POLY_BE, crc32_be

def crc32_be_clmul64(data: int) -> int:
    """ carry-less multiply based implementation of crc32_be for 64-bit data """
    crc32_be_full_poly = (1 << 32) | CRC32_POLY_BE

    # the quotient is too wide to be determined in a single step.
    # We start by determining the upper part, and use it to cancel its product
    # with the polynomial from the message before determining the lower part
    # M.X^32 = Q.P ^ CRC  
    # M.X^32.P_INV = Q.P.P_INV ^ CRC.P_INV
    #
    # P.P_INV = X^63 ^ R32
    # Q = QH.X^32 ^ QL 
    #
    # M.P_INV.X^32 = (QH.X^32 ^ QL).(X^63 ^ R32)  ^ CRC.P_INV
    #              = (QH.X^95 ^ QH.X^32.R32 ^ QL.X^63 ^ QL.R32)  ^ CRC.P_INV
    #
    # (M.P_INV) >> 63 = QH
    data_times_p_inv = carry_less_multiply(data, CRC32_BE_INV)
    # upper 31-bit of the quotient
    q_msb = data_times_p_inv >> 63
    assert q_msb < 2**32

    # OPTIMIZATION:
    #   The issue with this selection is that it may overlap between the high 64-bit and the low 64-bit
    #   To circumvent this we can multiply CRC32_BE_INV by X before the multiplication
    data_times_p_inv_times_x = carry_less_multiply(data, CRC32_BE_INV << 1)
    q_msb_opt = data_times_p_inv_times_x >> 64
    assert q_msb == q_msb_opt

    data_lsb = data ^ carry_less_multiply(q_msb, crc32_be_full_poly)
    data_lsb_times_p_inv = carry_less_multiply(data_lsb, CRC32_BE_INV)
    q_lsb = data_lsb_times_p_inv >> 31
    assert q_lsb < 2**32

    # OPTIMIZATION:
    #    Multiplying CRC32_BE__INV by X^33 to force selection in the upper 64-bit
    data_lsb_times_p_inv_times_x33 = carry_less_multiply(data_lsb, CRC32_BE_INV << 33)
    q_lsb_opt = data_lsb_times_p_inv_times_x33 >> 64
    assert q_lsb == q_lsb_opt

    remainder = (data_lsb << 32) ^ carry_less_multiply(q_lsb, crc32_be_full_poly)
    assert remainder < 2**32

    return remainder


if __name__ == "__main__":
    # Single byte data
    for data in [0x1, 0x80, 0x17]:
        data_bytes = [data]
        # First, we compute the reference CRC32_BE value of the single byte data
        ref_crc32_be = crc32_be(0, data_bytes, CRC32_POLY_BE)
        # Then, we compute the same value but using carry-less multiply with the barrett's constant
        clmul64_crc32_be = crc32_be_clmul64(data)
        print(f"crc32_be(0x{data:x} / {data_bytes}) = 0x{ref_crc32_be:x} (ref) vs 0x{clmul64_crc32_be:x} (clmul64)")
        assert ref_crc32_be == clmul64_crc32_be

    random_bytes = lambda: random.randrange(256)

    # Multi-byte data (8 bytes)
    for data_bytes in [[0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x1], [random_bytes() for _ in range(8)]]:
        assert len(data_bytes) <= 8
        # assembling data, they byte list needs to be reversed, since the first byte the crc32_be considers
        # is actually the one with highest index in the message
        data = byte_assemble(data_bytes[::-1])
        # First, we compute the reference CRC32_BE value of the single byte data
        ref_crc32_be = crc32_be(0, data_bytes, CRC32_POLY_BE)
        # Then, we compute the same value but using carry-less multiply with the barrett's constant
        clmul64_crc32_be = crc32_be_clmul64(data)
        print(f"crc32_be(0x{data:x} / {data_bytes}) = 0x{ref_crc32_be:x} (ref) vs 0x{clmul64_crc32_be:x} (clmul64)")
        assert ref_crc32_be == clmul64_crc32_be

    NUM_TESTS = 100000
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
        print(f"crc32_be(0x{data:x} / {data_bytes}) = 0x{ref_crc32_be:x} (ref) vs 0x{clmul64_crc32_be:x} (clmul64)")
        assert ref_crc32_be == clmul64_crc32_be

