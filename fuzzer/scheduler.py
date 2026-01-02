from typing import List
from .seed import Seed

def pick_seed(queue: List[Seed]) -> Seed:
    """简单轮询（可升级为按 favored 权重选择）"""
    # TODO: 实现基于 coverage 或 execs 的排序
    for s in queue:
        if s.execs == 0:
            s.execs += 1
            return s
    queue[0].execs += 1
    return queue[0]


def cal_power(seed: Seed) -> int:
    return 20 if seed.favored else 5

def should_retire(seed: Seed) -> bool:
    """低效种子退休：未 favored 且执行多次无新覆盖"""
    return not seed.favored and seed.execs > 10