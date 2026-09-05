from bit_manip_utils import bit_reverse
from bit_manip_utils import byte_assemble
from crc_model import CRC32_POLY_BE, crc32_be
from carry_less_multiply import carry_less_divide, carry_less_multiply
import random
from test_utils import random_byte, random_bytes

# computing X^63 / CRC32_POLY_BE
CRC32_BE_INV = carry_less_divide(1 << 63, (1 << 32) | CRC32_POLY_BE)

def crc32_be_clmul(data: int) -> int:
    """ Using a carry-less multiply and a Barrett's constant to compute
        CRC32_BE for a data less than 4 bytes wide """
    
    # data is a 32-bit value
    assert data < 2**32
    # data.X^32 = Q*P ^ crc
    # data.CRC32_BE_INV.x^32 = Q.(P.CRC32_BE_INV) ^ crc
    # data.CRC32_BE_INV.x^32 = Q.(X^63 ^ R32) ^ crc; R32 is a degree 31 polynomial
    # data.CRC32_BE_INV.x^32 = Q.X^63 ^ Q.R32 ^ crc
    # One thing to note is that both operands fit on 32-bit
    data_times_crc32_be_inv = carry_less_multiply(data, CRC32_BE_INV)
    quotient = data_times_crc32_be_inv >> 31
    print(f"q({hex(data)}) = {hex(quotient)} / rev32(q) = {hex(bit_reverse(quotient, 32))}")
    crc32_be_full_poly = (1 << 32) | CRC32_POLY_BE
    # One of the issue with the following carry-less multiply is that the right
    # hand side operand (crc32_be_full_poly) is more than 32-bit wide
    # it can be decomposed into X^32 ^ CRC32_POLY_BE
    # and the multiplication becomes
    #     quotient . crc32_be_full_poly = quotient . (X^32 ^ CRC32_POLY_BE)
    #                                   = quotient . X^32 ^ quotient . CRC32_POLY_BE
    #                                   = (quotient << 32) ^ (quotient . CRC32_POLY_BE)
    # where quotient . CRC32_POLY_BE is a polynomial of degree 31 + 31 = 62
    # quotient.X^32 has the property to cancel the MSB (bit 63) of the product
    # Since we know the cancellation to be exact, we can actually limit the computation
    # to the lower 32-bit of the remainder and discard both (message << 32) and (quotient << 32)
    remainder = (data << 32) ^ carry_less_multiply(quotient, crc32_be_full_poly)
    remainder_opt = carry_less_multiply(quotient, CRC32_POLY_BE) & 0xffffffff
    # the remainder should be 32-bit or less as the MSBs should have been exactly cancelled
    # by the subtraction 
    assert remainder < 2**32
    assert remainder == remainder_opt
    return remainder_opt


    



if __name__ == "__main__":
    # Single byte data
    for data in [0x1, 0x80, 0x17]:
        data_bytes = [data]
        # First, we compute the reference CRC32_BE value of the single byte data
        ref_crc32_be = crc32_be(0, data_bytes, CRC32_POLY_BE)
        # Then, we compute the same value but using carry-less multiply with the barrett's constant
        clmul_crc32_be = crc32_be_clmul(data)
        print(f"crc32_be(0x{data:x} / {data_bytes}) = 0x{ref_crc32_be:x} (ref) vs 0x{clmul_crc32_be:x} (clmul)")
        assert ref_crc32_be == clmul_crc32_be



    # Multi-byte data (4 bytes, corresponding to the CRC width)
    for data_bytes in [[0x0, 0x0, 0x0, 0x1], [0x1, 0x0, 0x0, 0x0], random_bytes(4)]:
        assert len(data_bytes) <= 4
        # assembling data, they byte list needs to be reversed, since the first byte the crc32_be considers
        # is actually the one with highest index in the message
        data = byte_assemble(data_bytes[::-1])
        # First, we compute the reference CRC32_BE value of the single byte data
        ref_crc32_be = crc32_be(0, data_bytes, CRC32_POLY_BE)
        # Then, we compute the same value but using carry-less multiply with the barrett's constant
        clmul_crc32_be = crc32_be_clmul(data)
        print(f"crc32_be(0x{data:x} / {data_bytes}) = 0x{ref_crc32_be:x} (ref) vs 0x{clmul_crc32_be:x} (clmul)")
        assert ref_crc32_be == clmul_crc32_be
    


