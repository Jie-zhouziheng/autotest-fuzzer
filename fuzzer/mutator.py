import random
from .seed import Seed

class Mutator:
    def mutate(self, seed: Seed, power: int = 5) -> list[bytes]:
        """生成多个变异体"""
        seed_data = seed.data
        results = list()
        data = bytearray(seed_data)
        for _ in range(power):
            mutated = data.copy()
            # 策略1: 随机翻转字节
            if len(mutated) > 0:
                i = random.randint(0, len(mutated) - 1)
                mutated[i] ^= random.randint(1, 255)
                results.append(bytes(mutated))
                
                # 可扩展：插入、删除、字典变异等
        return results