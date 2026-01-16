from dataclasses import dataclass, field
from fuzzer.utils import ExecutionFeedback
from typing import List, Set, Dict, Optional, Tuple

@dataclass
class Seed:
    data: bytes
    execs: int = 0
    favored: bool = False
    crashed: bool = False
    disabled: bool = False
    exec_time_ns: int = 1_000_000_000  # 默认 1 秒（纳秒）
    bitmap_size: int = 0
    coverage: Set[Tuple[int, int]] = field(default_factory=set)  # 边签名集合 (i, bucket)
    depth: int = 0  # 种子深度（从初始种子开始的变异轮数）
    total_new_coverage: int = 0  # 该种子产生的所有新覆盖边总数

    def mark_favored(self):
        self.favored = True

    def mark_crash(self):
        """标记种子为 crash,并自动设置为 disabled"""
        self.crashed = True
        self.disabled = True
        self.favored = False  # Crash 绝不可能是 favored

    def __hash__(self):
        return hash(self.data)

    def __eq__(self, other):
        return isinstance(other, Seed) and self.data == other.data


class SeedQueue:
    def __init__(self):
        self.queue: list[Seed] = []
        self.seen = set()
        # Key: edge (Tuple[int, int]), Value: Seed
        self.top_rated: Dict[Tuple[int, int], Seed] = {}
        
        # 用于控制 cull() 调用频率
        self.new_coverage_since_cull = 0

         # AFL++：execs 最小的 favored 种子索引
        self.smallest_favored_index: Optional[int] = None
        self.queued_items: int = 0


    def add(self, seed: Seed):
        if seed in self.seen:
            return

        self.queue.append(seed)
        self.seen.add(seed)

        self._update_bitmap_score(seed)

    def __iter__(self):
        return iter(self.queue)

    def __len__(self):
        return len(self.queue)

    def favored_seeds(self):
        return [s for s in self.queue if s.favored]

    def _calculate_metric(self, seed: Seed) -> float:
        """
        计算种子的"代价"。
        """
        if seed.exec_time_ns <= 0:
            return float('inf')
        return seed.exec_time_ns * len(seed.data)

    def _update_bitmap_score(self, seed: Seed):
        """
        检查当前种子覆盖的每一条边，看它是否比该边目前的"擂主"更高效。
        AFL++ 策略：disabled 种子不应该成为 top_rated。
        """
        if seed.disabled:
            return

        current_metric = self._calculate_metric(seed)

        for edge in seed.coverage:
            if edge not in self.top_rated:
                self.top_rated[edge] = seed
            else:
                rival = self.top_rated[edge]
                # 如果现在的擂主被 disable 了，或者当前种子更优
                if rival.disabled or current_metric < self._calculate_metric(rival):
                    self.top_rated[edge] = seed

    def cull(self):
        """
        AFL++ 的 cull_queue 逻辑。
        1. 清除所有 favored 标记。
        2. 遍历 top_rated，标记 winners 为 favored（跳过 disabled 种子）。
        3. 更新 smallest_favored 辅助索引。
        """
        # 1. 重置所有 favored 标记
        for seed in self.queue:
            seed.favored = False

        # 2. 遍历 top_rated 字典
        self.smallest_favored_index = None
        min_execs = float('inf')
        
        for edge, best_seed in self.top_rated.items():
            if best_seed.disabled:
                continue
            
            if not best_seed.favored:
                best_seed.mark_favored()
            
            # 找到 execs 最小的 favored 种子
            try:
                seed_idx = self.queue.index(best_seed)
                if best_seed.execs < min_execs:
                    min_execs = best_seed.execs
                    self.smallest_favored_index = seed_idx
            except ValueError:
                # 如果种子不在队列中（不应该发生），跳过
                continue


    def update(self, data: bytes, parent_seed: Seed, feedback: ExecutionFeedback) -> bool:
        """
        Fuzzer 主循环调用的更新逻辑
        AFL++ 策略：crash 种子自动标记为 disabled
        """
        # 更新父种子的统计信息
        parent_seed.execs += 1
        if feedback.exec_time_ns > 0:
            # 更新执行时间
            parent_seed.exec_time_ns = feedback.exec_time_ns
        
        if feedback.crashed:
            # AFL++ 策略：crash 种子自动标记为 disabled
            parent_seed.mark_crash()

        if feedback.new_coverage:
            new_seed = Seed(data)
            new_seed.exec_time_ns = feedback.exec_time_ns
            new_seed.coverage = feedback.coverage  # 直接使用解析好的 coverage 集合
            new_seed.bitmap_size = feedback.bitmap_size
            new_seed.depth = parent_seed.depth + 1
            new_seed.total_new_coverage = feedback.new_coverage
            
            # AFL++ 策略：如果种子是 crash，自动标记为 disabled
            if feedback.crashed:
                new_seed.mark_crash() 

            self.add(new_seed)  # add 方法里会自动调用 _update_bitmap_score

            # 控制 cull() 调用频率：每新增一定数量的覆盖边才调用一次
            self.new_coverage_since_cull += feedback.new_coverage
            if self.new_coverage_since_cull >= 100:  # 每新增 100 条边调用一次
                self.cull()
                self.new_coverage_since_cull = 0

            return True
        return False
    
    def get_enabled_seeds_count(self) -> int:
        """返回非 disabled 种子的数量（AFL++ 策略：确保至少有一个有效种子）"""
        return sum(1 for seed in self.queue if not seed.disabled)
