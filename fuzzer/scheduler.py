from typing import List
from .seed import SeedQueue, Seed
import math
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

#class SimplePowerScheduler(PowerScheduler):
#   def assign(self, seed: Seed) -> int:
#        base = 5
#        if seed.favored:
#            base *= 4
#        if seed.execs > 100:
#            base //= 2
##       return max(1, base)

class AFLPowerScheduler(PowerScheduler):
    """
    一个受AFL启发式能量调度启发的调度器。
    所有逻辑都封装在此类中，只依赖 Seed 对象的属性。
    """

    # 定义一些性能阈值和参数
    FAST_EXEC_NS = 10 * 1_000_000  # 10ms
    SLOW_EXEC_NS = 100 * 1_000_000  # 100ms
    HIGH_BITMAP_SIZE = 500
    LOW_BITMAP_SIZE = 50
    MIN_MUTATIONS = 16
    MAX_MUTATIONS = 256

    def assign(self, seed: Seed) -> int:
        """根据种子的各项指标计算一个性能分数，并分配能量"""

        score = 100  # 基础分

        # 从 performance 字段解包数据
        exec_time, bitmap_size = seed.performance

        # 只有被评估过的种子才进行详细打分
        if exec_time != -1:
            # 1. 执行速度奖励/惩罚
            if exec_time < self.FAST_EXEC_NS:
                score *= 1.3
            elif exec_time > self.SLOW_EXEC_NS:
                score *= 0.7

            # 2. 覆盖范围奖励/惩罚
            if bitmap_size > self.HIGH_BITMAP_SIZE:
                score *= 1.3
            elif bitmap_size < self.LOW_BITMAP_SIZE:
                score *= 0.7

        # 3. 对Favored种子给予巨大奖励 (favored 是最重要的指标)
        if seed.favored:
            score *= 2.5

        # 4. 对已经大量执行的种子进行衰减
        if seed.execs > 5:
            # 使用log函数进行平滑衰减
            decay_factor = 1 / math.log(seed.execs, 4) if seed.execs > 4 else 0.5
            score *= max(0.2, decay_factor)

        # 5. 将分数映射到变异次数（能量）
        # 简单的线性映射，假设基础分100对应约64次变异
        power = int((score / 100.0) * 64)

        # 6. 限制在预设的范围内
        power = max(self.MIN_MUTATIONS, min(self.MAX_MUTATIONS, power))

        return power
