


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

