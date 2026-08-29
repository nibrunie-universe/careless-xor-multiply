# Careless XOR Multiply

A Python library for performing carry-less arithmetic operations (such as carry-less multiplication, division, and remainder) and bit-level manipulation utilities over GF(2).

## Features
- **Bit Manipulation:** Utilities for bit reversal, byte splitting, leading zero count (`lzc`), and leading one position (`lop`).
- **Carry-Less Arithmetic:** Multiply, divide, and calculate remainders using XOR without carry.

## Usage

```python
from carry_less_multiply import carry_less_multiply, carry_less_divide, carry_less_remainder

# Carry-less multiplication
result = carry_less_multiply(3, 2) # Returns 6

# Carry-less division
quotient = carry_less_divide(8, 2) # Returns 4
```

## Testing
Tests are written using `pytest`. Run them from the project root:
```bash
pytest
```
