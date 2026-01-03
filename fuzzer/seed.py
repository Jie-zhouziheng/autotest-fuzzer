from dataclasses import dataclass, field
from typing import Set
from fuzzer.monitor import ExecutionFeedback

@dataclass
class Seed:
    data: bytes
    execs: int = 0
    favored: bool = False
    crashed: bool = False
    coverage: Set[str] = field(default_factory=set)  # 模拟覆盖边集合
    # 使用一个元组来存储 (执行时间ns, bitmap大小)
    # 初始值为-1，表示尚未评估

    performance: tuple[int, int] = field(default=(-1, -1))

    def mark_favored(self):
        self.favored = True

    def mark_crash(self):
        self.crashed = True

    def __hash__(self):
        return hash(self.data)

    def __eq__(self, other):
        return isinstance(other, Seed) and self.data == other.data



class SeedQueue:
    def __init__(self):
        self.queue: list[Seed] = []
        self.seen = set()

    def add(self, seed: Seed):
        if seed in self.seen:
            return
        self.queue.append(seed)
        self.seen.add(seed)

    def __iter__(self):
        return iter(self.queue)

    def __len__(self):
        return len(self.queue)

    def favored_seeds(self):
        return [s for s in self.queue if s.favored]
    
    def update(self, data: bytes, parent_seed: Seed, feedback: ExecutionFeedback) -> bool:
        if feedback.crashed:
            parent_seed.mark_crash()
        
        if feedback.new_coverage:
            new_seed = Seed(data)
            #初始化性能数据
            new_seed.mark_favored()
            self.queue.append(new_seed) 
            return True
        return False