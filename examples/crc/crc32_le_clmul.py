from bit_manip_utils import byte_split
from crc_model import CRC32C_POLY_LE
from carry_less_multiply import carry_less_multiply, carry_less_divide
import random

from bit_manip_utils import bit_reverse, byte_assemble
from crc_model import CRC32_POLY_LE, crc32_le, crc32c, CRC32C_POLY_LE
from crc_intro import CRC32_BE_INV

CRC32_BE_INV_REV = bit_reverse(CRC32_BE_INV, 32)

def crc32_le_clmul(rev_data: int) -> int:
    return crc32_le_clmul_generic(rev_data, CRC32_POLY_LE)

def crc32_le_clmul_generic(rev_data: int, poly_le: int) -> int:
    assert rev_data < 2**32
    # building normal form poly from reverse (le) polynomial
    poly_be = bit_reverse(poly_le, 32)
    # computing normal form barrett's coefficient X^63 / poly
    poly_inv = carry_less_divide(1 << 63, (1 << 32) ^ poly_be)
    # computing reverse form barrett's coefficient
    poly_inv_rev = bit_reverse(poly_inv, 32)

    # Theory for CRC32BE:
    # data.X^32 = Q*P ^ crc
    # data.CRC32_BE_INV.x^32 = Q.(P.CRC32_BE_INV) ^ crc
    # data.CRC32_BE_INV.x^32 = Q.(X^63 ^ R32) ^ crc; R32 is a degree 31 polynomial
    # data.CRC32_BE_INV.x^32 = Q.X^63 ^ Q.R32 ^ crc
    #
    # Q = (data . CRC32_BE_INV) >> 63
    #
    # For CRC32LE, the polynomial P is bit reversed, and so is the final CRC
    # rev64 stands for 64-bit bit reverse
    #    P = (1 << 32) ^ CRC32_POLY_BE
    #    rev64(data.X^32) = rev64(Q*P ^ crc)
    #    rev32(data) = rev64(Q.P) ^ (rev32(crc) << 32)
    #
    #    rev64(Q.P) = rev64(Q . (X^ 32 ^ CRC32_POLY_BE))
    #               = rev64(Q.X^32 ^ Q.CRC32_POLY_BE)
    #               = rev64(Q.X^32) ^ rev64(Q.CRC32_POLY_BE)
    #               = rev32(Q) ^ ((rev32(Q).CRC32_POLY_LE) << 1)
    #
    #    rev32(Q) = rev32((data . CRC32_BE_INV) >> 31) 
    #
    #     rev32(data) . rev32(CRC32_BE_INV) = rev64(data . CRC32_BE_INV) >> 1
    #     rev32(data) . CRC32_BE_INV_REV = rev64(data . CRC32_BE_INV) >> 1
    # 
    # data . CRC32_BE_INV = Q . X^31 ^ R31 where R31 is a 31-bit remainder (degree at most 30)
    # rev64(data . CRC32_BE_INV) = rev64(Q . X^31 ^ R31)
    #                            = rev64(Q . X^31) ^ (rev31(R31) << 33)
    #                            = rev33(Q) ^ (rev31(R31) << 33)
    #                            = (rev32(Q) << 1) ^ (rev31(R31) << 33)
    #
    # rev64(data . CRC32_BE_INV) >> 1 = (rev32(Q)) ^ (rev31(R31) << 32)
    # rev32(data) . CRC32_BE_INV_REV  = (rev32(Q)) ^ (rev31(R31) << 32)
    # rev32(Q) corresponds to the least 32 bits of rev32(data) . CRC32_BE_INV_REV
    rev32_q = carry_less_multiply(rev_data, poly_inv_rev) & 0xffffffff

    # computing the remainder
    #    rev64(data.X^32) = rev64(Q*P ^ crc)
    #    rev32(data) = rev64(Q.P) ^ (rev32(crc) << 32)
    #    rev32(crc) is the upper 32 bits of rev64(Q.P) (since rev32(data) has no upper 32 bits)
    #
    #    rev64(Q.P) = rev32(Q) ^ (rev32(Q).CRC32_POLY_LE) << 1 
    #    rev64(Q.P) >> 32 = (rev32(Q).CRC32_POLY_LE) >> 31 
    remainder_rev = carry_less_multiply(rev32_q, poly_le) >> 31
    return remainder_rev

def crc32c_clmul(rev_data: int) -> int:
    assert rev_data < 2**32
    # the polynomial forms can be statically evaluated
    # building normal form poly from reverse (le) polynomial
    poly_be = bit_reverse(CRC32C_POLY_LE, 32)
    # computing normal form barrett's coefficient X^63 / poly
    poly_inv = carry_less_divide(1 << 63, (1 << 32) ^ poly_be)
    # computing reverse form barrett's coefficient
    poly_inv_rev = bit_reverse(poly_inv, 32)
    assert poly_inv_rev < 2**32

    # computing the quotient (see crc32_le_clmul_generic for formula details)
    rev32_q = carry_less_multiply(rev_data, poly_inv_rev) & 0xffffffff
    # computing the remainder (a.k.a. CRC), (see crc32_le_clmul_generic for formula details)
    remainder_rev = carry_less_multiply(rev32_q, CRC32C_POLY_LE) >> 31

    # CRC32C_POLY_LE = 0x82f63b78
    # (rev32(Q) . CRC32C_POLY_LE) >> 31 = rev32(Q) . (CRC32C_POLY_LE . X) >> 32
    #
    # The issue is that (CRC32C_POLY_LE . X) exceeds 32 bits
    # but can be exposed as (X^32 ^ ((CRC32_POLY_LE << 1) & 0xffffffff) = X^32 + P'
    # rev32(Q) . (X^32 ^ P') >> 32 = rev32(Q) ^ (rev32(Q) . P') >> 32
    p_prime = (CRC32C_POLY_LE << 1) & 0xffffffff # can be statically evaluated
    remainder_opt = rev32_q ^ (carry_less_multiply(rev32_q, p_prime) >> 32)
    # and now the carry-less part directly corresponds to the upper 32-bit part of
    # a possibly 64-bit carry-less
    assert remainder_rev == remainder_opt

    return remainder_opt


if __name__ == "__main__":
    data = random.randrange(2**32)
    placeholder_q = random.randrange(2**32)
    placeholder_crc = random.randrange(2**32)
    rev64 = lambda v: bit_reverse(v, 64)
    rev32 = lambda v: bit_reverse(v, 32)
    assert rev64(data << 32) == rev32(data)
    assert rev64(carry_less_multiply(placeholder_q, CRC32_BE_INV)) == (carry_less_multiply(rev32(placeholder_q), CRC32_BE_INV_REV) << 1)
    print(f"CRC32_BE_INV_REV = 0x{CRC32_BE_INV_REV:x}")

    # Single byte data
    for data_rev in [0x08, 0x80, 0x1, 0x71]:
        data_bytes_rev = [data_rev] + [0, 0, 0]

        # First, we compute the reference CRC32_LE value of the single byte data
        ref_crc32_le = crc32_le(0, data_bytes_rev, CRC32_POLY_LE)
        # Then, we compute the same value but using carry-less multiply with the barrett's constant
        clmul_crc32_le = crc32_le_clmul(data_rev)
        print(f"crc32_le(0x{data_rev:x} / {data_bytes_rev}) = 0x{ref_crc32_le:x} (ref) vs 0x{clmul_crc32_le:x} (clmul)")
        assert ref_crc32_le == clmul_crc32_le

    random_bytes = lambda: random.randrange(256)

    # Multi-byte data (4 bytes, corresponding to the CRC width)
    for data_bytes_rev in [[0x0, 0x0, 0x0, 0x1], [0x1, 0x0, 0x0, 0x0], [random_bytes() for _ in range(4)]]:
        data_rev = byte_assemble(data_bytes_rev)

        # First, we compute the reference CRC32_LE value of the multi byte data
        ref_crc32_le = crc32_le(0, data_bytes_rev, CRC32_POLY_LE)
        # Then, we compute the same value but using carry-less multiply with the barrett's constant
        clmul_crc32_le = crc32_le_clmul(data_rev)
        print(f"crc32_le(0x{data_rev:x} / {data_bytes_rev}) = 0x{ref_crc32_le:x} (ref) vs 0x{clmul_crc32_le:x} (clmul)")
        assert ref_crc32_le == clmul_crc32_le

    # Multi-byte data (4 bytes, corresponding to the CRC width)
    # FOR CRC32C
    for data_bytes_rev in [[0, 0, 0, 0], [0x0, 0x0, 0x0, 0x1], [0x1, 0x0, 0x0, 0x0], [random_bytes() for _ in range(4)]]:
        data_rev = byte_assemble(data_bytes_rev)

        # First, we compute the reference CRC32_LE value of the multi byte data
        ref_crc32c_le = crc32c(0, data_bytes_rev)
        # Then, we compute the same value but using carry-less multiply with the barrett's constant
        clmul_crc32c_le = crc32_le_clmul_generic(data_rev, CRC32C_POLY_LE)
        print(f"crc32c_le(0x{data_rev:x} / {data_bytes_rev}) = 0x{ref_crc32c_le:x} (ref) vs 0x{clmul_crc32c_le:x} (clmul)")
        assert ref_crc32c_le == clmul_crc32c_le

        clmul_crc32c = crc32c_clmul(data_rev)
        print(f"crc32c(0x{data_rev:x} / {data_bytes_rev}) = 0x{ref_crc32c_le:x} (ref) vs 0x{clmul_crc32c:x} (clmul crc32c specific)")
        assert ref_crc32c_le == clmul_crc32c

    # More agressive CRC32C testing
    NUM_TESTS = 100000
    for data_bytes_rev in [[random_bytes() for _ in range(4)] for _ in range(NUM_TESTS)]:
        data_rev = byte_assemble(data_bytes_rev)

        # First, we compute the reference CRC32_LE value of the multi byte data
        ref_crc32c_le = crc32c(0, data_bytes_rev)
        # Then, we compute the same value but using carry-less multiply with the barrett's constant
        clmul_crc32c = crc32c_clmul(data_rev)

        # checks
        assert ref_crc32c_le == clmul_crc32c
