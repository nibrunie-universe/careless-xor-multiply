# This file contains a set of utility functions to manipulate value at the bit level (reversal, split)


def bit_reverse(_data: int, size: int) -> int:
    """ bit-reverse a size-bit data value """
    reversed_data = 0
    data = _data
    for i in range(size):
        if (data >> i) & 1:
            reversed_data |= (1 << (size - 1 - i))
    return reversed_data 

def byte_split(_data: int) -> list[int]:
    """ split data into a list of bytes (least significant byte first) """
    data = _data
    byte_list = []
    if data == 0:
        return [0]
    while data !=0:
        byte_list.append(data & 0xff)
        data >>= 8
    return byte_list

def lzc(data: int, n: int) -> int:
    """ Leading zero count of the lowest n bits of data """
    _data = bit_reverse(data, n)
    count = 0
    while _data & 1 == 0 and count < n:
        count += 1
        _data >>= 1
    return count

def lop(data: int) -> int:
    """ Leading one position (bit index) for the most significant bit of data """
    if data == 0:
        return None
    _data = data
    index = -1
    while _data != 0:
        index += 1
        _data >>= 1
    return index
    

