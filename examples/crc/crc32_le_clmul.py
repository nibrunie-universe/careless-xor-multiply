from carry_less_multiply import carry_less_multiply
import random

from bit_manip_utils import bit_reverse, byte_assemble
from crc_model import CRC32_POLY_LE, crc32_le, crc32_be, CRC32_POLY_BE
from crc_intro import CRC32_BE_INV, crc32_be_clmul

CRC32_BE_INV_REV = bit_reverse(CRC32_BE_INV, 32)

def crc32_le_clmul(rev_data: int) -> int:
    assert rev_data < 2**32
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
    #    rev64(data.X^32) = rev64(Q*P ^ crc)
    #    rev32(data) = rev64(Q.P) ^ (rev32(crc) << 32)
    #
    #    rev64(Q.P) = (rev32(Q).rev32(P)) << 1
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
    rev32_q = carry_less_multiply(rev_data, CRC32_BE_INV_REV) & 0xffffffff
    print(f"rev32_q({hex(rev_data)}) = {hex(rev32_q)}")

    # computing the remainder
    #    rev64(data.X^32) = rev64(Q*P ^ crc)
    #    rev32(data) = rev64(Q.P) ^ (rev32(crc) << 32)
    #    crc is the upper 32 bits of rev64(Q.P) (since rev32(data) has no upper 32 bits)
    #
    #    rev64(Q.P) << 1 = rev32(Q) . rev32(P)
    remainder_rev = carry_less_multiply(rev32_q, CRC32_BE_INV_REV) >> 33
    return remainder_rev
    


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
    for data_rev in [0x08]:
        data_bytes_rev = [data_rev] + [0, 0, 0]
        data_bytes = [bit_reverse(b, 8) for b in data_bytes_rev]

        # CRC32 BE version

        # assembling data, they byte list needs to be reversed, since the first byte the crc32_be considers
        # is actually the one with highest index in the message
        data = byte_assemble(data_bytes[::-1])
        # First, we compute the reference CRC32_BE value of the single byte data
        ref_crc32_be = crc32_be(0, data_bytes, CRC32_POLY_BE)
        # Then, we compute the same value but using carry-less multiply with the barrett's constant
        clmul_crc32_be = crc32_be_clmul(data)
        print(f"crc32_be(0x{data:x} / {data_bytes}) = 0x{ref_crc32_be:x} (ref) vs 0x{clmul_crc32_be:x} (clmul)")
        assert ref_crc32_be == clmul_crc32_be

        # First, we compute the reference CRC32_BE value of the single byte data
        ref_crc32_le = crc32_le(0, data_bytes_rev, CRC32_POLY_LE)
        # Then, we compute the same value but using carry-less multiply with the barrett's constant
        clmul_crc32_le = crc32_le_clmul(data_rev)
        print(f"crc32_le(0x{data_rev:x} / {data_bytes_rev}) = 0x{ref_crc32_le:x} (ref) vs 0x{clmul_crc32_le:x} (clmul)")
        assert ref_crc32_le == clmul_crc32_le

