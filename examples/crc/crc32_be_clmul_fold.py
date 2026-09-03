import random

from bit_manip_utils import byte_assemble
from carry_less_multiply import carry_less_divide, carry_less_multiply
from crc32_be_clmul64 import crc32_be_clmul64
from crc_model import crc32_be, CRC32_POLY_BE

def crc32_be_clmul_fold(data_bytes: list[int]) -> int:
    # For short lengths, we shift the data and use the 64-bit dedicated function
    if len(data_bytes) <= 8:
        data = byte_assemble(data_bytes[::-1])
        return crc32_be_clmul64(data)

    if len(data_bytes) <= 16:
        hi_len = len(data_bytes) - 8
        hi_data = byte_assemble(data_bytes[:hi_len][::-1])
        hi_crc = crc32_be_clmul64(hi_data)
        data = byte_assemble(data_bytes[hi_len:][::-1]) ^ (hi_crc << 32)
        return crc32_be_clmul64(data)

    if len(data_bytes) < 32:
        return crc32_be(0, data_bytes, CRC32_POLY_BE)

    # For length over 16 bytes, we use folding method
    # we load M, m-bit of the message
    # M.X^m = Q.(P.X^32) ^ R64
    # 
    # We use X^n = P'.(P.X^32) ^ T64 
    #
    # M.P'.X^m = Q.(P.X^32).P' ^ R64.P'
    #          = Q.(X^n ^ T64) ^ R64.P'
    #          = Q.X^n ^ Q.T64) ^ R64.P'
    FULL_CRC32_POLY_BE = (1 << 32) | CRC32_POLY_BE
    # P' of degree 128
    CRC32_BE_FOLD_CST = carry_less_divide(1 << 192, FULL_CRC32_POLY_BE << 32)
    print(f"CRC32_BE_FOLD_CST={hex(CRC32_BE_FOLD_CST)}")
    MASK_64 = 2**64 - 1

    acc_hi = 0
    acc_lo = 0
    while len(data_bytes) >= 32:
        data_hi = byte_assemble(data_bytes[:8][::-1])
        data_lo = byte_assemble(data_bytes[8:16][::-1])
        acc_hi ^= data_hi
        acc_lo ^= data_lo
        # More than one multiplication are required to get each Q value,
        # because multiplication by P' is problematic because CRC32_BE_FOLD_CST is larger than 64-bit
        q_hi_lsb = (carry_less_multiply(acc_hi, CRC32_BE_FOLD_CST & MASK_64) >> 64) & MASK_64
        q_hi_lsb ^= (carry_less_multiply(acc_hi, (CRC32_BE_FOLD_CST >> 64) & MASK_64)) & MASK_64
        q_lo_lsb = (carry_less_multiply(acc_lo, CRC32_BE_FOLD_CST & MASK_64) >> 64) & MASK_64
        q_lo_lsb ^= (carry_less_multiply(acc_lo, (CRC32_BE_FOLD_CST >> 64) & MASK_64)) & MASK_64
        print(f"q_hi_lsb={hex(q_hi_lsb)}")
        print(f"q_lo_lsb={hex(q_lo_lsb)}")
        r64_hi = carry_less_multiply(q_hi_lsb, FULL_CRC32_POLY_BE << 32) & MASK_64
        r64_lo = carry_less_multiply(q_lo_lsb, FULL_CRC32_POLY_BE << 32) & MASK_64
        print(f"r64_hi={hex(r64_hi)}")
        print(f"r64_lo={hex(r64_lo)}")
        acc_hi = r64_hi
        acc_lo = r64_lo

        data_bytes = data_bytes[16:]

    # 16 <= len(data_bytes) < 32
    data_hi = byte_assemble(data_bytes[:8][::-1])
    data_lo = byte_assemble(data_bytes[8:16][::-1])
    acc_hi ^= data_hi
    acc_lo ^= data_lo

    crc_hi = crc32_be_clmul64(acc_hi)
    crc_lo = crc32_be_clmul64(acc_lo ^ (crc_hi << 32))

    return crc32_be(crc_lo, data_bytes[16:], CRC32_POLY_BE)


if __name__ == "__main__":
    random_bytes = lambda: random.randrange(256)

    NUM_TESTS = 10

    for _ in range(NUM_TESTS):
        data_len = random.randrange(1, 100)
        data_bytes = [random_bytes() for _ in range(data_len)]

        # First, we compute the reference CRC32_LE value of the single byte data
        ref_crc32_be = crc32_be(0, data_bytes, CRC32_POLY_BE)
        # Then, we compute the same value but using carry-less multiply with the barrett's constant
        clmul_fold_crc32_be = crc32_be_clmul_fold(data_bytes)
        print(f"{len(data_bytes)}-byte crc32_be({data_bytes}) = 0x{ref_crc32_be:x} (ref) vs 0x{clmul_fold_crc32_be:x} (clmul_fold)")
        assert ref_crc32_be == clmul_fold_crc32_be