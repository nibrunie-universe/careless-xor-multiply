from carry_less_multiply import carry_less_multiply

def test_carry_less_multiply():
    assert carry_less_multiply(0, 0) == 0
    assert carry_less_multiply(1, 1) == 1
    assert carry_less_multiply(3, 2) == 6
    assert carry_less_multiply(3, 3) == 5 # (X + 1) * (X +1) = X^2 + 2 X + 1, since 2 congruent to 0 