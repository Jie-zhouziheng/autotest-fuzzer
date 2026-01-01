import random
from typing import Set, List

def mutate(seed_data: bytes, power: int = 5) -> Set[bytes]:
    """生成多个变异体"""
    results = set()
    data = bytearray(seed_data)
    for _ in range(power):
        mutated = data.copy()
        # 策略1: 随机翻转字节
        if len(mutated) > 0:
            i = random.randint(0, len(mutated) - 1)
            mutated[i] ^= random.randint(1, 255)
        results.add(bytes(mutated))
        
        # 可扩展：插入、删除、字典变异等
    return results