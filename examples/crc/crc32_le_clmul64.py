# -*- coding: utf-8
import random

from bit_manip_utils import byte_assemble, bit_reverse
from carry_less_multiply import carry_less_multiply
from crc_intro import CRC32_BE_INV, CRC32_POLY_BE, crc32_be
from crc32_be_clmul64 import crc32_be_clmul64

def crc32_le_clmul64(rev_data: int) -> int:
    """ carry-less multiply based implementation of crc32_be for 64-bit data """
    assert rev_data < 2**64
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
    # (M.P_INV << 1) >> 64 = QH
    #
    # rev128(M.P_INV.X) = rev64(M).rev64(P_INV.X) << 1
    # rev128(M.P_INV.X >> 64) = (rev64(M).rev64(P_INV.X) << 1) & (2^64 - 1)
    #                         = (rev_data . (rev64(P_INV.X) << 1) & (2^64 - 1)
    #
    # rev64(M.P_INV.X >> 64) = rev64(QH)
    # rev64(QH) = (rev_data . (rev64(P_INV.X) << 1) & (2^64 - 1)
    MASK_64 = 2**64 - 1
    # FIXME: the .X -> rev -> .X should cancel out
    p_inv_times_x_rev_times_x = bit_reverse(CRC32_BE_INV << 1, 64) << 1
    q_msb_rev = carry_less_multiply(rev_data, p_inv_times_x_rev_times_x) & MASK_64
    print(f"q_msb_rev={hex(q_msb_rev)} and rev64(q_msb_rev)={hex(bit_reverse(q_msb_rev, 64))}")

    # data_lsb = data ^ q_msb.P
    # rev64(data_lsb) = rev64(data) ^ rev64(q_msb.P)
    #                 = rev64(data) ^ (rev128(q_msb.P) >> 64)
    #                 = rev64(data) ^ ((rev64(q_msb) . rev64(P) << 1) >> 64)
    data_lsb_rev = rev_data ^ (carry_less_multiply(q_msb_rev, bit_reverse(crc32_be_full_poly, 64)) >> 63)
    print(f"data_lsb_rev={hex(data_lsb_rev)} and rev64={hex(bit_reverse(data_lsb_rev, 64))}")
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
    print(f"q_lsb_opt_rev={hex(q_lsb_opt_rev)} and rev64 = {hex(bit_reverse(q_lsb_opt_rev, 64))}")

    # CRC = (data_lsb . X^32) ^ (q_lsb.P)
    # rev64(CRC) = (rev128(data_lsb.X^32) >> 64) ^ (rev128(q_lsb.P) >> 64)
    #            = (rev64(data_lsb) >> 32) ^ (rev64(q_lsb) . rev64(P) >> 63)
    remainder_rev = (data_lsb_rev >> 32) ^ (carry_less_multiply(q_lsb_opt_rev, bit_reverse(crc32_be_full_poly, 64)) >> 63)
    remainder_rev >>= 32
    print(f"crc_le={hex(remainder_rev)} and rev32={hex(bit_reverse(remainder_rev, 32))}")

    return remainder_rev


if __name__ == "__main__":
    # Single byte data
    for data in [0xdeadbeefcafebebe]:
        clmul64_crc32_be = crc32_be_clmul64(data)
        clmul64_crc32_le = crc32_le_clmul64(bit_reverse(data, 64))
