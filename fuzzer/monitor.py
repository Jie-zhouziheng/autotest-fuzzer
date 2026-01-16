# monitor.py
import os
import sys
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

        # 跟踪时间戳（相对时间，从开始到现在经过的秒数）
        self.last_saved_crash_time: Optional[float] = None
        self.last_saved_hang_time: Optional[float] = None
        self.last_new_find_time: Optional[float] = None  # AFL++ 中 last new find 指上次发现新路径的时间
        # log 
        self.last_print_time = self.start_time
        self.last_log_time = self.start_time
        self.print_interval = 0.1
        self.log_file_path = os.path.join(PLOT_DIR, "logfile.txt")
        if not os.path.exists(PLOT_DIR):
            os.makedirs(PLOT_DIR)
        with open(self.log_file_path, "w") as f:
            f.write("elapsed_time,unique_edges,total_execs,crash_count,hang_count,exec_speed,queue_size,last_new_find,last_crash,last_hang\n")
        self._first_status_print = True  # 标记是否是第一次打印状态
    
    def start_monitoring(self):
        self.start_time = time.time()
        self.last_print_time = self.start_time # 重置打印时间
        self.last_log_time = self.start_time # 重置日志时间
        with open(self.log_file_path, "a") as f:
            f.write(f"{0.00:.2f},0,0,0,0,0.00,0,0.00,0.00,0.00\n")

    def _format_time(self, seconds: float) -> str:
        """格式化时间为 days, hrs, min, sec 格式"""
        if seconds is None or seconds <= 0:
            return "none seen yet"
        
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if days > 0:
            return f"{days} days, {hours} hrs, {minutes} min, {secs} sec"
        elif hours > 0:
            return f"{hours} hrs, {minutes} min, {secs} sec"
        elif minutes > 0:
            return f"{minutes} min, {secs} sec"
        else:
            return f"{secs} sec"

    def _get_log_interval(self, elapsed: float, time_unit: str, exec_speed: float) -> float:
        """
        根据记录的时间单位与当前执行速度，决定日志记录频率（间隔，单位：秒）
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

    def log_status(self, queue_size: int = 0, time_unit: str = "seconds"):
        """
        显示和记录状态信息（原地刷新）
        queue_size: 种子队列大小（需要从外部传入）
        """
        current_time = time.time()
        elapsed = current_time - self.start_time
        exec_speed = self.total_execs / elapsed if elapsed > 0 else 0.0
        log_interval = self._get_log_interval(elapsed, time_unit, exec_speed)
        
        should_log = current_time - self.last_log_time >= log_interval
        should_print = current_time - self.last_print_time >= self.print_interval

        
        if should_print or should_log:
            exec_speed = self.total_execs / elapsed if elapsed > 0 else 0
            
            # 计算相对时间（从开始到现在经过的秒数）
            last_new_find_elapsed = self.last_new_find_time - self.start_time if self.last_new_find_time else None
            last_crash_elapsed = self.last_saved_crash_time - self.start_time if self.last_saved_crash_time else None
            last_hang_elapsed = self.last_saved_hang_time - self.start_time if self.last_saved_hang_time else None
            
            # 格式化显示（限制长度以确保对齐）
            run_time_str = self._format_time(elapsed)[:38]
            last_new_find_str = (self._format_time(last_new_find_elapsed) if last_new_find_elapsed is not None else "none seen yet")[:38]
            last_crash_str = (self._format_time(last_crash_elapsed) if last_crash_elapsed is not None else "none seen yet")[:38]
            last_hang_str = (self._format_time(last_hang_elapsed) if last_hang_elapsed is not None else "none seen yet")[:38]
            
            # AFL++ 风格的状态显示（原地刷新）
            # 不要动了，已经对齐了！！！
            if should_print:
                status_lines = [
                    "┌─ process timing ──────────────────────────┬──────────── overall results ─────┐",
                    f"│        run time : {run_time_str:<20}    │    corpus count  : {queue_size:5d}         │",
                    f"│   last new find : {last_new_find_str:<20}    │    saved crashes : {self.crash_count:5d}         │",
                    f"│last saved crash : {last_crash_str:<20}    │    saved hangs   : {self.hang_count:5d}         │",
                    f"│ last saved hang : {last_hang_str:<20}    │                                  │",
                    "├─ map coverage ────────────────────────────┼─ execution stats ────────────────┤",
                    f"│    map density : {self.unique_edges:>5d} edges              │ total execs : {self.total_execs:>10,}         │",
                    f"│                                           │  exec speed : {exec_speed:>8.0f}/sec       │",
                    "└───────────────────────────────────────────┴──────────────────────────────────┘"
                ]
                
                if self._first_status_print:
                    status_text = "\n".join(status_lines)
                    self._first_status_print = False
                else:
                    # 向上移动 8 行（状态框的行数），然后覆盖
                    status_text = f"\033[8A\r" + "\n".join(status_lines)
                
                sys.stdout.write(status_text)
                sys.stdout.flush()

                self.last_print_time = current_time
            
            # 写入结构化的 CSV 格式到 log_file
            if should_log:
                last_new_find_val = last_new_find_elapsed if last_new_find_elapsed is not None else 0.00
                last_crash_val = last_crash_elapsed if last_crash_elapsed is not None else 0.00
                last_hang_val = last_hang_elapsed if last_hang_elapsed is not None else 0.00
                with open(self.log_file_path, "a") as f:
                    f.write(f"{elapsed:.2f},{self.unique_edges},{self.total_execs},{self.crash_count},{self.hang_count},{exec_speed:.2f},{queue_size},{last_new_find_val:.2f},{last_crash_val:.2f},{last_hang_val:.2f}\n")
                self.last_log_time = current_time
    
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

        # 2. 文件保存并更新时间戳
        current_time = time.time()
        if new_cov > 0:
            self.data_id += 1 # 也作为 queue 的计数器
            save_data(input_data, 'queue', self.data_id)
            self.last_new_find_time = current_time  # 更新最后发现新路径的时间
            
        if res.is_crash:
            self.crash_count += 1
            save_data(input_data, 'crash', self.crash_count)
            self.last_saved_crash_time = current_time
            
        if res.is_timeout:
            self.hang_count += 1
            save_data(input_data, 'hang', self.hang_count)
            self.last_saved_hang_time = current_time  # 更新最后保存超时的时间

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
        """返回完整的统计信息，用于生成报告和 fuzzer_stats"""
        current_time = time.time()
        elapsed = self.get_elapsed()
        exec_speed = self.total_execs / elapsed if elapsed > 0 else 0.0
        
        return {
            "total_execs": self.total_execs,
            "crash_count": self.crash_count,
            "hang_count": self.hang_count,
            "unique_paths": self.unique_edges,
            "unique_edges": self.unique_edges,  # 别名，保持一致性
            "elapsed_time": elapsed,
            "exec_speed": exec_speed,
            "start_time": int(self.start_time) if self.start_time else int(current_time),
            "last_update": int(current_time),
            "last_new_find_time": int(self.last_new_find_time) if self.last_new_find_time else None,
            "last_saved_crash_time": int(self.last_saved_crash_time) if self.last_saved_crash_time else None,
            "last_saved_hang_time": int(self.last_saved_hang_time) if self.last_saved_hang_time else None,
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