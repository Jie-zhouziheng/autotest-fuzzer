from typing import List
from .seed import SeedQueue, Seed

class SeedScheduler:
    def pick(self, queue: "SeedQueue") -> Seed:
        raise NotImplementedError
    
class RoundRobinScheduler(SeedScheduler):
    def __init__(self):
        self.idx = 0

    def pick(self, queue: SeedQueue) -> Seed:
        if not queue.queue:
            raise RuntimeError("Empty seed queue")

        seed = queue.queue[self.idx % len(queue.queue)]
        self.idx += 1
        seed.execs += 1
        return seed

    
class PowerScheduler:
    def assign(self, seed: Seed) -> int:
        raise NotImplementedError
    
class SimplePowerScheduler(PowerScheduler):
    def assign(self, seed: Seed) -> int:
        base = 5
        if seed.favored:
            base *= 4
        if seed.execs > 100:
            base //= 2
        return max(1, base)