from bit_manip_utils import bit_reverse, byte_split, lzc

def test_bit_reverse():
    assert bit_reverse(0b1010, 4) == 0b0101
    assert bit_reverse(0b1111, 4) == 0b1111
    assert bit_reverse(0b0000, 4) == 0b0000

def test_byte_split():
    assert byte_split(0x12345678) == [0x78, 0x56, 0x34, 0x12]
    assert byte_split(0x0) == [0]


def test_lzc():
    assert lzc(1, 1) == 0
    assert lzc(1, 17) == 16
    assert lzc(0, 17) == 17
    assert lzc(3, 3) == 1
    assert lzc (8, 5) == 1 
