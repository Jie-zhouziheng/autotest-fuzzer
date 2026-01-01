from typing import List
from .seed import Seed

def pick_seed(queue: List[Seed]) -> Seed:
    """简单轮询（可升级为按 favored 权重选择）"""
    # TODO: 实现基于 coverage 或 execs 的排序
    return queue[0]

def should_retire(seed: Seed) -> bool:
    """低效种子退休：未 favored 且执行多次无新覆盖"""
    return not seed.favored and seed.execs > 10