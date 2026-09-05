from crc32_be_clmul64 import crc32_be_clmul64_v2
import random
from test_utils import random_bytes

from bit_manip_utils import byte_assemble
from carry_less_multiply import carry_less_divide, carry_less_multiply, carry_less_remainder
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
    # n=192, P' of degree 128
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
        # so it must be divided into two operations (data x lo) >> 64 and (data x hi) and the two
        # results must be added (xor-ed) together.
        q_hi_lsb = (carry_less_multiply(acc_hi, CRC32_BE_FOLD_CST & MASK_64) >> 64) & MASK_64
        q_hi_lsb ^= (carry_less_multiply(acc_hi, (CRC32_BE_FOLD_CST >> 64) & MASK_64)) & MASK_64
        q_lo_lsb = (carry_less_multiply(acc_lo, CRC32_BE_FOLD_CST & MASK_64) >> 64) & MASK_64
        q_lo_lsb ^= (carry_less_multiply(acc_lo, (CRC32_BE_FOLD_CST >> 64) & MASK_64)) & MASK_64
        #print(f"q_hi_lsb={hex(q_hi_lsb)}")
        #print(f"q_lo_lsb={hex(q_lo_lsb)}")
        r64_hi = carry_less_multiply(q_hi_lsb, FULL_CRC32_POLY_BE << 32) & MASK_64
        r64_lo = carry_less_multiply(q_lo_lsb, FULL_CRC32_POLY_BE << 32) & MASK_64
        #print(f"r64_hi={hex(r64_hi)}")
        #print(f"r64_lo={hex(r64_lo)}")
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


def crc32_be_clmul_fold_v2(data_bytes: list[int]) -> int:
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
    # 
    # we pre-compute Rm as the module of X^m by the CRC polynomial
    # Rm degree is at most 31
    # X^m = Qm.P ^ Rm
    #
    # M.X^m = M.Qm.P ^ Rm.M
    # CRC(M.X^m) = CRC(Rm.M)
    MASK_64 = 2**64 - 1
    m = 128
    FULL_CRC32_POLY_BE = (1 << 32) | CRC32_POLY_BE
    Rm = carry_less_remainder(1 << m, FULL_CRC32_POLY_BE)
    Qm = carry_less_divide(1 << m, FULL_CRC32_POLY_BE)
    R64 = carry_less_remainder(1 << 64, FULL_CRC32_POLY_BE)

    assert Rm < 2**32
    assert (1 << m) == carry_less_multiply(Qm, FULL_CRC32_POLY_BE) ^ Rm

    acc_hi = 0
    acc_lo = 0
    while len(data_bytes) >= 32:
        data_hi = byte_assemble(data_bytes[:8][::-1])
        data_lo = byte_assemble(data_bytes[8:16][::-1])
        acc_hi ^= data_hi
        acc_lo ^= data_lo
        # More than one multiplication are required to get each Q value,
        # because multiplication by P' is problematic because CRC32_BE_FOLD_CST is larger than 64-bit
        # so it must be divided into two operations (data x lo) >> 64 and (data x hi) and the two
        # results must be added (xor-ed) together.
        folded_rem_hi = carry_less_multiply(acc_hi, Rm) # 2 operations: clm hi and lo
        folded_rem_lo = carry_less_multiply(acc_lo, Rm) # 2 operations: clm hi and lo

        acc_hi = folded_rem_hi & MASK_64
        acc_lo = folded_rem_lo & MASK_64
        # the upper part (only 32-bit wide) of folded_rem's needs to be folded.
        # We use the same operation (rather than xor-ing folded_rem_lo and acc_hi)
        # because this way, it can be vectorized
        # 
        # We have several way of computing the remainder of the hi part,
        # Either we compute its CRC with a fast method, but this requires to shift the result 
        # left by 32 bits, or we compute an extended 64-bit remainder by the CRC polynomial
        # which is narrow enough to be directly xor-ed with the accumulators
        hi_lo_rem = crc32_be_clmul64_v2(folded_rem_hi >> 64) << 32
        lo_lo_rem = crc32_be_clmul64_v2(folded_rem_lo >> 64) << 32
        hi_lo_rem_opt = carry_less_multiply(folded_rem_hi >> 64, R64)
        lo_lo_rem_opt = carry_less_multiply(folded_rem_lo >> 64, R64)
        assert hi_lo_rem_opt < 2**64
        assert lo_lo_rem_opt < 2**64
        assert carry_less_remainder(hi_lo_rem, FULL_CRC32_POLY_BE) == carry_less_remainder(hi_lo_rem_opt, FULL_CRC32_POLY_BE)
        assert carry_less_remainder(lo_lo_rem, FULL_CRC32_POLY_BE) == carry_less_remainder(lo_lo_rem_opt, FULL_CRC32_POLY_BE)
        acc_hi ^= hi_lo_rem_opt
        acc_lo ^= lo_lo_rem_opt 

        # the total is 3 vector clm64 (2 vclmul, and 1 vclmuh)
        # and 2 vector xor (one for the initial input injection and one for folding the hi part
        # of the first set of wide multiply)
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

    NUM_TESTS = 1000

    for _ in range(NUM_TESTS):
        data_len = random.randrange(1, 100)
        data_bytes = random_bytes(data_len)

        # First, we compute the reference CRC32_LE value of the single byte data
        ref_crc32_be = crc32_be(0, data_bytes, CRC32_POLY_BE)
        # Then, we compute the same value but using carry-less multiply with the barrett's constant
        clmul_fold_crc32_be = crc32_be_clmul_fold(data_bytes)
        print(f"{len(data_bytes)}-byte crc32_be({data_bytes}) = 0x{ref_crc32_be:x} (ref) vs 0x{clmul_fold_crc32_be:x} (clmul_fold)")
        assert ref_crc32_be == clmul_fold_crc32_be

        clmul_fold_crc32_be_v2 = crc32_be_clmul_fold_v2(data_bytes)
        print(f"{len(data_bytes)}-byte crc32_be({data_bytes}) = 0x{ref_crc32_be:x} (ref) vs 0x{clmul_fold_crc32_be_v2:x} (clmul_fold_v2)")
        assert ref_crc32_be == clmul_fold_crc32_be_v2