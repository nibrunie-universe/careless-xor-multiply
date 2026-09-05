import random

def random_byte() -> int:
    return random.randrange(256)

def random_bytes(n: int) -> list[int]:
    return [random_byte() for _ in range(n)]
