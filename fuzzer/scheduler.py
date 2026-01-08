from typing import List
from .seed import SeedQueue, Seed
import math

# ----- seed scheduler -----
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


class AFLSmartScheduler(SeedScheduler):
    def __init__(self):
        self.idx = 0

    def pick(self, queue: SeedQueue) -> Seed:
        """
        优先寻找并返回队列中的 favored 种子。
        在多个 favored 种子中，选择质量更好的（execs 更少、exec_time_ns 更短等）。
        """
        if len(queue) == 0:
            raise RuntimeError("Empty seed queue")

        max_search = len(queue)
        search_count = 0
        
        favored_candidates = []
        
        while search_count < max_search:
            if self.idx >= len(queue):
                self.idx = 0

            seed = queue.queue[self.idx]
            
            if seed.favored:
                favored_candidates.append(seed)
            
            self.idx += 1
            search_count += 1
            
            if favored_candidates and search_count >= len(queue):
                break

        # 如果有 favored 种子，选择最好的
        if favored_candidates:
            # 优先选择：execs 更少、exec_time_ns 更短、depth 更浅、bitmap_size 更大
            best_seed = min(favored_candidates, key=lambda s: (
                s.execs,                    # 执行次数越少越好
                s.exec_time_ns,             # 执行时间越短越好
                s.depth,                    # 深度越浅越好
                -s.bitmap_size              # bitmap_size 越大越好（取负号）
            ))
            best_seed.execs += 1
            self.idx = (queue.queue.index(best_seed) + 1) % len(queue.queue)
            return best_seed

        # 如果没有 favored 种子，退化为 Round Robin
        if self.idx >= len(queue):
            self.idx = 0

        seed = queue.queue[self.idx]
        self.idx += 1
        seed.execs += 1
        return seed

class AFLPlusPlusScheduler(SeedScheduler):
    """
    基于 AFL++ 策略的简化版种子调度器。
    
    策略：
    1. 如果有 favored 种子，选择 execs 最小的 favored 种子（O(1)）
    2. 否则，选择 execs 最小的非 favored 种子
    """
    
    def pick(self, queue: SeedQueue) -> Seed:
        if len(queue) == 0:
            raise RuntimeError("Empty seed queue")
        
        # 策略 1: 优先选择 smallest_favored
        if queue.smallest_favored_index is not None:
            seed = queue.queue[queue.smallest_favored_index]
            seed.execs += 1
            return seed
        
        # 策略 2: 选择 execs 最小的非 favored 种子
        min_execs = float('inf')
        best_seed = None
        
        for seed in queue.queue:
            if not seed.favored and seed.execs < min_execs:
                min_execs = seed.execs
                best_seed = seed
        
        if best_seed:
            best_seed.execs += 1
            return best_seed
        
        seed = queue.queue[0]
        seed.execs += 1
        return seed


# ----- power scheduler -----

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

        # 使用 exec_time_ns（已修正）
        exec_time = seed.exec_time_ns
        bitmap_size = seed.bitmap_size

        # 只有被评估过的种子才进行详细打分
        if exec_time > 0 and exec_time < 1_000_000_000:  # 有效执行时间范围
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
        if seed.execs > 4:
            decay_factor = 1 / math.log(seed.execs, 4)
            score *= max(0.2, decay_factor)
        elif seed.execs == 0:
            # 新种子，给予初始奖励
            score *= 1.2

        # 5. 将分数映射到变异次数（能量）
        power = int((score / 100.0) * 64)
        power = max(self.MIN_MUTATIONS, min(self.MAX_MUTATIONS, power))

        return power