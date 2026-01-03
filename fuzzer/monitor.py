# monitor.py
import time
from typing import Optional
from .utils import ExecutionResult, save_crash
from .config import MAX_EXECUTIONS, TOTAL_TIMEOUT
from dataclasses import dataclass

@dataclass
class ExecutionFeedback:
    new_coverage: bool
    crashed: bool

class CoverageMonitor:
    def __init__(self, max_executions: int = MAX_EXECUTIONS,timeout: Optional[float] = None):
        self.observed_coverage = set()
        self.count_class_lookup = self._build_count_class_lookup()
        self.max_executions = max_executions
        self.start_time = time.time()
        self.timeout = timeout
        self.total_execs = 0
        self.crash_count = 0
        self.unique_paths = 0
        self.coverage_history = []  # [(time_sec, unique_paths)]

    def start_monitoring(self):
        """由 Fuzzer 在开始时调用"""
        self.start_time = time.time()
    
    def get_elapsed(self) -> float:
        """安全地获取已运行时间"""
        if self.start_time is None:
            return 0.0
        return time.time() - self.start_time

    def should_continue(self) -> bool:
        """ 由 Monitor 自己判断是否继续 fuzzing"""
        #if self.total_execs >= self.max_executions:
        #    return False
        #if self.timeout and (time.time() - self.start_time) > self.timeout:
        #    return False
        #return True
        elapsed = time.time() - (self.start_time or time.time())
        if elapsed > TOTAL_TIMEOUT:
            return False
        return True

    def process_execution(self, input_data: bytes, res: ExecutionResult):
        """
        处理一次执行结果，完成所有监控逻辑：
        - 分析 coverage
        - 判断是否 crash / hang / new path
        - 保存特殊输入
        - 更新内部统计
        """
        if self.start_time is None:
            raise RuntimeError("Monitor not started! Call start_monitoring() first.")
        elapsed = self.get_elapsed()
        self.total_execs += 1

        # 1. 检查 crash
        if res.is_crash:
            self.crash_count += 1
            save_crash(input_data)  # 监控组件自己保存

        # 2. 分析 coverage
        has_new = False
        if res.trace_bits:
            for i, byte_val in enumerate(res.trace_bits):
                if byte_val == 0:
                    continue
                bucket = self.count_class_lookup[byte_val]
                edge_sig = (i, bucket)
                if edge_sig not in self.observed_coverage:
                    self.observed_coverage.add(edge_sig)
                    has_new = True
        # 3. 保存新路径
        if has_new:
            self.unique_paths = len(set(sig[0] for sig in self.observed_coverage))
            self.coverage_history.append((elapsed, self.unique_paths))

        # 返回是否发现新 coverage（供 Fuzzer 决定是否入队）
        return ExecutionFeedback(
            new_coverage=has_new,
            crashed=res.is_crash
        )

    def get_stats(self) -> dict:
        return {
            "total_execs": self.total_execs,
            "crash_count": self.crash_count,
            "unique_paths": self.unique_paths,
            "coverage_history": self.coverage_history,
        }

    def _build_count_class_lookup(self):
        # 同 AFL 的 hit count 分类逻辑
        lookup = [0] * 256
        for i in range(256):
            if i == 0:
                lookup[i] = 0
            elif i == 1:
                lookup[i] = 1
            elif i < 4:
                lookup[i] = 2
            elif i < 8:
                lookup[i] = 3
            elif i < 16:
                lookup[i] = 4
            elif i < 32:
                lookup[i] = 5
            elif i < 128:
                lookup[i] = 6
            else:
                lookup[i] = 7
        return lookup
    