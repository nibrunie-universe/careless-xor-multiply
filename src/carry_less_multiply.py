from bit_manip_utils import lzc, lop

def carry_less_multiply(a, b) -> int:
    """ Carry-less multiplication of a and b """
    acc = 0
    _a = a
    _b = b
    while _b != 0:
        if _b & 1:
            acc ^= _a
        _b >>= 1
        _a <<= 1
    return acc


def carry_less_divrem(a, d) -> int:
    """ Carry-less division of dividend a by divisor d, return the quotient and the remainder """
    if d == 0:
        return (None, a)
    lop_a = lop(a)
    lop_d = lop(d)
    # if the degree of the divisor stricly exceeds the degree of the dividend, the quotient is 0
    if lop_d > lop_a:
        return (0, a)
    lop_delta = lop_a - lop_d
    remainder = a
    current_divisor = d << lop_delta
    msb_mask = 1 << lop_a
    quotient = 0
    for _ in range(lop_delta + 1):
        quotient <<= 1
        if remainder & msb_mask:
            quotient |= 1
            remainder ^= current_divisor
        remainder <<= 1
    remainder >>= (lop_delta + 1)
    assert remainder == 0 or (lop(remainder) < lop_d)
    return quotient, remainder

def carry_less_divide(a, d) -> int:
    """ Carry-less division of dividend a by divisor d, return the quotient """
    quotient, _ = carry_less_divrem(a, d)
    return quotient

def carry_less_remainder(a, d) -> int:
    """ Carry-less division of dividend a by divisor d, return the remainder """
    _, remainder = carry_less_divrem(a, d)
    return remainder
    
