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
