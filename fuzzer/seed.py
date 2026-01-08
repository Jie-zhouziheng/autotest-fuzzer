from dataclasses import dataclass, field
from fuzzer.utils import ExecutionFeedback
from typing import List, Set, Dict, Optional, Tuple

@dataclass
class Seed:
    data: bytes
    execs: int = 0
    favored: bool = False
    crashed: bool = False
    exec_time_ns: int = 1_000_000_000  # 默认 1 秒（纳秒）
    bitmap_size: int = 0
    coverage: Set[Tuple[int, int]] = field(default_factory=set)  # 边签名集合 (i, bucket)
    depth: int = 0  # 种子深度（从初始种子开始的变异轮数）
    total_new_coverage: int = 0  # 该种子产生的所有新覆盖边总数
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

        # 记录每条边对应的"最佳"种子
        # Key: edge (Tuple[int, int]), Value: Seed
        self.top_rated: Dict[Tuple[int, int], Seed] = {}
        
        # 用于控制 cull() 调用频率
        self.new_coverage_since_cull = 0

         # AFL++：execs 最小的 favored 种子索引
        self.smallest_favored_index: Optional[int] = None


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
        计算种子的“代价”。
        """
        exec_time_ns = seed.exec_time_ns
        if exec_time_ns <= 0:
            # 如果还没执行过或数据无效，给一个默认惩罚值
            return float('inf')

        length = len(seed.data)
        return exec_time_ns * length

    def _update_bitmap_score(self, seed: Seed):
        """
        检查当前种子覆盖的每一条边，看它是否比该边目前的“擂主”更高效。
        """

        current_metric = self._calculate_metric(seed)

        # 遍历这个种子覆盖的所有边
        for edge in seed.coverage:
            if edge not in self.top_rated:
                # 这条边之前没见过，或者还没有归属，直接占领
                self.top_rated[edge] = seed
            else:
                rival = self.top_rated[edge]
                rival_metric = self._calculate_metric(rival)

                # 如果当前种子比之前的擂主更“快且小”
                if current_metric < rival_metric:
                    self.top_rated[edge] = seed

    def cull(self):
        """
        根据 top_rated 榜单，重新标记 favored 种子。
        只保留那些处于 top_rated 榜单中的种子作为 favored。
        """
        # 1. 先把所有种子的 favored 标记清除 (除了刚开始的初始种子可能想保留)
        for seed in self.queue:
            seed.favored = False

        # 2. 遍历 top_rated 字典
        self.smallest_favored_index = None
        min_execs = float('inf')
        
        for edge, best_seed in self.top_rated.items():
            if not best_seed.favored:
                best_seed.mark_favored()
            
            # 找到 execs 最小的 favored 种子
            seed_idx = self.queue.index(best_seed)
            if best_seed.execs < min_execs:
                min_execs = best_seed.execs
                self.smallest_favored_index = seed_idx


    def update(self, data: bytes, parent_seed: Seed, feedback: ExecutionFeedback) -> bool:
        """
        Fuzzer 主循环调用的更新逻辑
        """
        # 更新父种子的统计信息
        parent_seed.execs += 1
        if feedback.exec_time_ns > 0:
            # 更新执行时间（可以用平均值或最新值，这里用最新值）
            parent_seed.exec_time_ns = feedback.exec_time_ns
        
        if feedback.crashed:
            parent_seed.mark_crash()

        if feedback.new_coverage:
            new_seed = Seed(data)
            new_seed.exec_time_ns = feedback.exec_time_ns
            new_seed.crashed = feedback.crashed
            new_seed.coverage = feedback.coverage  # 直接使用解析好的 coverage 集合
            new_seed.bitmap_size = feedback.bitmap_size
            new_seed.depth = parent_seed.depth + 1
            new_seed.total_new_coverage = feedback.new_coverage
            
            self.add(new_seed)  # add 方法里会自动调用 _update_bitmap_score

            # 控制 cull() 调用频率：每新增一定数量的覆盖边才调用一次
            self.new_coverage_since_cull += feedback.new_coverage
            if self.new_coverage_since_cull >= 100:  # 每新增 100 条边调用一次
                self.cull()
                self.new_coverage_since_cull = 0

            return True
        return False
