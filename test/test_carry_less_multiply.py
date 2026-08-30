import random

from carry_less_multiply import carry_less_multiply, carry_less_divide, carry_less_remainder
from bit_manip_utils import bit_reverse

def test_carry_less_multiply():
    assert carry_less_multiply(0, 0) == 0
    assert carry_less_multiply(1, 1) == 1
    assert carry_less_multiply(3, 2) == 6
    assert carry_less_multiply(3, 3) == 5 # (X + 1) * (X +1) = X^2 + 2 X + 1, since 2 congruent to 0 


def test_carry_less_divider():
    assert carry_less_divide(17, 0) == None
    assert carry_less_divide(3, 17) == 0
    assert carry_less_divide(8, 2) == 4
    quotient = 17
    divisor = 37
    clmul_result = carry_less_multiply(quotient, divisor)
    assert carry_less_divide(clmul_result, divisor) == quotient
    assert carry_less_divide(clmul_result ^ (divisor >> 1), divisor) == quotient


def test_carry_less_remainder():
    assert carry_less_remainder(17, 0) == 17
    assert carry_less_remainder(3, 17) == 3
    assert carry_less_remainder(8, 2) == 0
    quotient = 17
    divisor = 37
    clmul_result = carry_less_multiply(quotient, divisor)
    assert carry_less_remainder(clmul_result, divisor) == 0
    assert carry_less_remainder(clmul_result ^ (divisor >> 1), divisor) == (divisor >> 1)


def test_carry_less_multiply_reverse():
    # carry-less multiply has an interesting property
    # for a n-bit operand A and a m-bit operand B
    #    bit_reverse(clmul(A,B), n+m-1) = clmul(bit_reverse(A, n), bit_reverse(B, m))
    # this can be rewritten as: 
    #    bit_reverse(clmul(A,B), n+m) = (clmul(bit_reverse(A, n), bit_reverse(B, m))) << 1
    a = random.randrange(2**32)
    b = random.randrange(2**32)
    rev64 = lambda v: bit_reverse(v, 64)
    rev32 = lambda v: bit_reverse(v, 32)
    assert rev64(a << 32) == rev32(a)
    assert rev64(carry_less_multiply(a, b)) == (carry_less_multiply(rev32(a), rev32(b)) << 1)