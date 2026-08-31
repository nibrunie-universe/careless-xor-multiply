# -*- coding: utf-8
import random

from bit_manip_utils import byte_assemble, bit_reverse
from carry_less_multiply import carry_less_multiply
from crc_model import CRC32_POLY_BE, CRC32_POLY_LE, crc32_le
from crc_intro import CRC32_BE_INV
from crc32_be_clmul64 import crc32_be_clmul64

def crc32_le_clmul64(rev_data: int) -> int:
    """ carry-less multiply based implementation of crc32_be for 64-bit data """
    assert rev_data < 2**64
    crc32_be_full_poly = (1 << 32) | CRC32_POLY_BE
    MASK_64 = 2**64 - 1

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
    # (M.P_INV << 1) >> 64 = QH
    #
    # rev128(M.P_INV.X) = rev64(M).rev64(P_INV.X) << 1
    # rev128(M.P_INV.X >> 64) = (rev64(M).rev64(P_INV.X) << 1) & (2^64 - 1)
    #                         = (rev_data . (rev64(P_INV.X) << 1) & (2^64 - 1)
    #
    # rev64(M.P_INV.X >> 64) = rev64(QH)
    # rev64(QH) = (rev_data . (rev64(P_INV.X) << 1) & (2^64 - 1)
    # FIXME: the .X -> rev -> .X should cancel out
    p_inv_times_x_rev_times_x = bit_reverse(CRC32_BE_INV << 1, 64) << 1
    q_msb_rev = carry_less_multiply(rev_data, p_inv_times_x_rev_times_x) & MASK_64

    # data_lsb = data ^ q_msb.P
    # rev64(data_lsb) = rev64(data) ^ rev64(q_msb.P)
    #                 = rev64(data) ^ (rev128(q_msb.P) >> 64)
    #                 = rev64(data) ^ ((rev64(q_msb) . rev64(P) << 1) >> 64)
    data_lsb_rev = rev_data ^ (carry_less_multiply(q_msb_rev, bit_reverse(crc32_be_full_poly, 64)) >> 63)

    # OPTIMIZATION:
    #     The right shift by 63 following the carry-less multiply is incovenient, since it would be easier t
    #     directly used the upper 64-bit (actually 63-bit) of a 64x64 carry-less multiply operation
    data_lsb_rev_opt = rev_data ^ (carry_less_multiply(q_msb_rev, bit_reverse(crc32_be_full_poly >> 1, 64)) >> 64)
    # Since (crc32_be_full_poly >> 1) may have discarded a bit which would have corresponded to q_msb_rev.X^64 after
    # the bit-reversal, we need to compensante (if the lsb of crc32_be_full_poly is set) by xor-ing q_msb_rev once
    # again into the upper 64-bit of the carry-less multiply result
    data_lsb_rev_opt ^= q_msb_rev if (crc32_be_full_poly & 1) else 0 
    assert data_lsb_rev_opt == data_lsb_rev


    # q_lsb = (data_lsb . P_INv) >> 31
    # q_lsb_opt = (data_lsb . P_INv . X^33) >> 64
    # rev64(q_lsb_opt) = rev128(data_lsb . P_INV . X^33) & MASK_64 
    #
    # rev128(data_lsb . P_INV . X^33) = (rev64(data_lsb) . rev64(P_INV . X^33)) << 1
    # rev128(data_lsb . P_INV . X^33) = (rev64(data_lsb) . (rev64(P_INV << 33) << 1)
    # rev128(data_lsb . P_INV . X^33) = (rev64(data_lsb) . (rev64(P_INV << 32) >> 1 << 1)
    # rev128(data_lsb . P_INV . X^33) = (rev64(data_lsb) . rev64(P_INV << 32)
    #
    # rev64(q_lsb_opt) = (rev64(data_lsb) . rev64(P_INV << 32) & MASK_64
    q_lsb_opt_rev = carry_less_multiply(data_lsb_rev, bit_reverse(CRC32_BE_INV << 32, 64)) & MASK_64

    # CRC = (data_lsb . X^32) ^ (q_lsb.P)
    # rev64(CRC) = (rev128(data_lsb.X^32) >> 64) ^ (rev128(q_lsb.P) >> 64)
    #            = (rev64(data_lsb) >> 32) ^ (rev64(q_lsb) . rev64(P) >> 63)

    assert data_lsb_rev < 2**64
    remainder_rev = (data_lsb_rev >> 64) ^ (carry_less_multiply(q_lsb_opt_rev, bit_reverse(crc32_be_full_poly, 64)) >> 95)
    assert remainder_rev < 2**32
    # NOTE: the data_lsb_rev is actually useless here: it has no impact on the lower 32 bits of the results,
    #       since it does not exceed 64-bit and gets cancelled out by the right shift by 64
    #      

    # OPTIMIZATION:
    #   The final computation of the CRC can be optimized by multiplying the full CRC32_BE polynomial by X^31 before
    #   the bit reveral (which corresponds to dividing it by X^31 after the reversal), this allows the remainder the be
    #   positioned in the upper 64-bit of the result (which the operands crc32_be_full_poly.X^31 still fits on 64-bit)
    remainder_opt = carry_less_multiply(q_lsb_opt_rev, bit_reverse(crc32_be_full_poly << 31, 64)) >> 64

    assert remainder_opt == remainder_rev

    return remainder_rev


if __name__ == "__main__":
    # Single byte data
    for data in [0xdeadbeefcafebebe]:
        clmul64_crc32_be = crc32_be_clmul64(data)
        clmul64_crc32_le = crc32_le_clmul64(bit_reverse(data, 64))

        assert clmul64_crc32_be == bit_reverse(clmul64_crc32_le, 32)

    random_bytes = lambda: random.randrange(256)

    NUM_TESTS = 100000
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
        clmul64_crc32_le = crc32_le_clmul64(data)
        print(f"crc32_le(0x{data:x} / {data_bytes}) = 0x{ref_crc32_le:x} (ref) vs 0x{clmul64_crc32_le:x} (clmul64)")
        assert ref_crc32_le == clmul64_crc32_le
