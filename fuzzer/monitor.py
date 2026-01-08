# monitor.py
import os
import time
from typing import Optional
from .utils import ExecutionResult, ExecutionFeedback, save_data
from .config import *

class CoverageMonitor:
    def __init__(self, max_executions: int = MAX_EXECUTIONS,timeout: Optional[float] = None):
        self.observed_coverage = set()
        self.count_class_lookup = self._build_count_class_lookup()

        self.max_executions = max_executions
        self.start_time = time.time()
        self.timeout = timeout
        self.total_execs = 0

        self.hang_count = 0
        self.crash_count = 0
        self.data_id = 0
        self.unique_edges = 0

        # log 
        self.last_print_time = self.start_time
        self.log_file_path = os.path.join(PLOT_DIR, "logfile.txt")
        if not os.path.exists(PLOT_DIR):
            os.makedirs(PLOT_DIR)
        with open(self.log_file_path, "w") as f:
            f.write("unix_time,elapsed_time,unique_edges,total_execs,crash_count,hang_count,exec_speed\n")

    def start_monitoring(self):
        self.start_time = time.time()
        self.last_print_time = self.start_time # 重置打印时间

        with open(self.log_file_path, "a") as f:
            f.write(f"{self.start_time},0.00,0,0,0,0,0.00\n")

    def _get_log_interval(self, elapsed: float, time_unit: str, exec_speed: float) -> float:
        """
        根据记录的时间单位与当前执行速度，决定日志记录频率（间隔，单位：秒）
        - seconds: 前几秒高频记录，之后目标是每 ~50 次执行记录一次，区间 [0.1s, 0.5s]
        - minutes: 目标是每 ~1000 次执行记录一次，区间 [10s, 120s]，长时间运行时略放宽
        - hours  : 使用「原先」的自适应机制（<10min/10s，<1h/30s，其后/60s），适合超长时间运行
        """
        if time_unit == "seconds":
            if elapsed < 5.0:
                return 0.05
            if exec_speed <= 0:
                return 0.5
            interval = 50.0 / exec_speed  # 希望每条日志约覆盖 50 次执行
            return max(0.1, min(0.5, interval))
        elif time_unit == "minutes":
            if exec_speed <= 0:
                base = 30.0
            else:
                base = 1000.0 / exec_speed
            base = max(10.0, min(120.0, base))
            if elapsed > 3600:
                base = max(30.0, min(180.0, base))
            return base
        elif time_unit == "hours":
            if elapsed < 600:      # < 10 min
                return 10.0
            elif elapsed < 3600:   # 10 min ~ 1 h
                return 30.0
            else:                  # > 1 h
                return 60.0
        # default to seconds
        return 1.0

    def log_status(self, time_unit: str = "seconds"):
        current_time = time.time()
        elapsed = current_time - self.start_time
        exec_speed = self.total_execs / elapsed if elapsed > 0 else 0.0
        interval = self._get_log_interval(elapsed, time_unit, exec_speed)
        
        if current_time - self.last_print_time >= interval:
            exec_speed = self.total_execs / elapsed if elapsed > 0 else 0
            time_str = time.strftime('%H:%M:%S')

            status_msg = (
                f"[{time_str}] "
                f"Execs: {self.total_execs} | "
                f"Speed: {exec_speed:.2f} exec/s | "
                f"Paths: {self.unique_edges} | "
                f"Crashes: {self.crash_count} | "
                f"Hangs: {self.hang_count}"
            )
            print(status_msg)
            
            # 写入结构化的 CSV 格式到 log_file，方便 evaluator 解析
            with open(self.log_file_path, "a") as f:
                f.write(f"{current_time},{elapsed:.2f},{self.unique_edges},{self.total_execs},{self.crash_count},{self.hang_count},{exec_speed:.2f}\n")
            
            self.last_print_time = current_time
    
    def get_elapsed(self) -> float:
        if self.start_time is None:
            return 0.0
        return time.time() - self.start_time

    def should_continue(self) -> bool:
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

        # 1. 分析 coverage
        new_cov = 0
        bitmap_size = 0
        coverage_set = set()
        if res.trace_bits:
            for i, byte_val in enumerate(res.trace_bits):
                if byte_val == 0:
                    continue
                bitmap_size += 1
                bucket = self.count_class_lookup[byte_val]
                edge_sig = (i, bucket)
                coverage_set.add(edge_sig)
                if edge_sig not in self.observed_coverage:
                    self.observed_coverage.add(edge_sig)
                    new_cov += 1
        self.unique_edges = len(self.observed_coverage)

        is_crash = res.is_crash
        is_hang = res.is_timeout

        # 2. 文件保存
        if new_cov > 0:
            self.data_id += 1 # 也可以作为 queue 的计数器
            save_data(input_data, 'queue', self.data_id)
        if res.is_crash:
            self.crash_count += 1
            save_data(input_data, 'crash', self.crash_count)
        if res.is_timeout:
            self.hang_count += 1
            save_data(input_data, 'hang', self.hang_count)

        # 3. 组装反馈
        return ExecutionFeedback(
            new_coverage=new_cov,
            total_unique_edges=self.unique_edges,
            coverage=coverage_set,
            crashed=is_crash,
            time_out=is_hang,
            exec_time_ns=res.exec_time_ns,
            bitmap_size=bitmap_size
        )

    def get_stats(self) -> dict:
        return {
            "total_execs": self.total_execs,
            "crash_count": self.crash_count,
            "hang_count" : self.hang_count,
            "unique_paths": self.unique_edges,
            "elapsed_time": self.get_elapsed(),
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
    