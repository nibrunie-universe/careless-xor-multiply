


def bit_reverse(data: int, size: int) -> int:
    """ bit-reverse a size-bit data value """
    reversed_data = 0
    for i in range(size):
        if (data >> i) & 1:
            reversed_data |= (1 << (size - 1 - i))
    return reversed_data 

def byte_split(data: int) -> list[int]:
    """ split data into a list of bytes (least significant byte first) """
    byte_list = []
    while data !=0:
        new_byte = data & 0xff
        data >>= 8
        byte_list.append(new_byte)
    return byte_list


# unit tests

def test_bit_reverse():
    assert bit_reverse(0b1010, 4) == 0b0101
    assert bit_reverse(0b1111, 4) == 0b1111
    assert bit_reverse(0b0000, 4) == 0b0000

def test_byte_split():
    assert byte_split(0x12345678) == [0x78, 0x56, 0x34, 0x12]
    assert byte_split(0x0) == [0]