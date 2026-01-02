# fuzzer/fuzzer.py
import os
import time
from typing import List
from .config import *
from .executor import run_target
from .mutator import mutate
from .scheduler import pick_seed, should_retire, cal_power
from .seed import Seed
from .utils import save_crash, ensure_dirs, ExecutionResult

class Fuzzer:
    def __init__(self):
        self.queue: List[Seed] = []
        self.observed_coverage = set()
        self.total_execs = 0
        self.crash_count = 0

        self.count_class_lookup = self._build_count_class_lookup()

    def load_seeds(self):
        if not os.path.exists(SEEDS_DIR):
            print(f"[!] Seeds directory not found: {SEEDS_DIR}")
            return
        for fname in os.listdir(SEEDS_DIR):
            path = os.path.join(SEEDS_DIR, fname)
            if os.path.isfile(path):  # 只处理普通文件，跳过目录、符号链接等
                with open(path, 'rb') as f:
                    self.queue.append(Seed(f.read()))
        print(f"[+] Loaded {len(self.queue)} seeds.")
    
    def _build_count_class_lookup(self) -> List[int]:
        """
        构建 AFL 的 hit count bucket 查找表
        将 0-255 的执行次数映射到对应的 bucket
        """
        lookup = [0] * 256
        lookup[0] = 0
        lookup[1] = 1
        lookup[2] = 2
        lookup[3] = 3
        
        for i in range(4, 8):
            lookup[i] = 4
        for i in range(8, 16):
            lookup[i] = 8
        for i in range(16, 32):
            lookup[i] = 16
        for i in range(32, 128):
            lookup[i] = 32
        for i in range(128, 256):
            lookup[i] = 128
        
        return lookup

    def has_new_coverage(self, trace_bits: bytes) -> bool:
        """
        5.执行结果监控组件
        从 64KB trace_bits 中提取 hit edges，并判断是否有新路径。
        """
        has_new = False
        
        for i, byte_val in enumerate(trace_bits):
            if byte_val == 0:
                continue
            
            # 使用查找表快速获取 bucket
            bucket = self.count_class_lookup[byte_val]
            
            # 构建唯一标识：(edge_id, bucket)
            edge_signature = (i, bucket)
            
            # 检查是否是新的覆盖
            if edge_signature not in self.observed_coverage:
                self.observed_coverage.add(edge_signature)
                has_new = True
        
        if has_new:
            # 统计唯一 edge 数量（不考虑 bucket）
            unique_edges = len(set(sig[0] for sig in self.observed_coverage))
            print(f"[+] New coverage! Unique edges: {unique_edges}, "
                  f"Total (edge, bucket) pairs: {len(self.observed_coverage)}")
            return True
        
        return False

    def run(self):
        ensure_dirs()
        self.load_seeds()

        if not self.queue:
            print("[-] No seeds to start fuzzing. Exiting.")
            return

        print(f"[=] Starting fuzzing for up to {MAX_EXECUTIONS} executions...")
        start_time = time.time()

        while self.total_execs < MAX_EXECUTIONS and self.queue:
            # 1.种子排序组件
            seed = pick_seed(self.queue)

            # 2.能量调度组件
            power = cal_power(seed)

            # 3.变异组件
            inputs = mutate(seed.data, power)

            for inp in inputs:
                if self.total_execs >= MAX_EXECUTIONS:
                    break

                # 4.测试执行组件
                self.total_execs += 1
                res: ExecutionResult = run_target(inp)

                # 5.执行结果监控组件
                if res.is_crash:
                    save_crash(inp)
                    self.crash_count += 1
                    print(f"[!] Crash #{self.crash_count} at exec #{self.total_execs}")

                # 新覆盖？加入队列
                if self.has_new_coverage(res.trace_bits):
                    new_seed = Seed(inp)
                    self.queue.append(new_seed)

            # （可选）种子退休：防止队列爆炸
            #if len(self.queue) > MAX_QUEUE_SIZE:
            #    old_len = len(self.queue)
            #    self.queue = [s for s in self.queue if not should_retire(s)]
            #    if len(self.queue) < old_len:
            #        print(f"[-] Retired seeds: {old_len} → {len(self.queue)}")

        # === 打印总结 ===
        elapsed = time.time() - start_time
        print("\n[=] Fuzzing finished!")
        print(f"    Total executions : {self.total_execs}")
        print(f"    Crashes found    : {self.crash_count}")
        print(f"    Unique paths     : {len(self.observed_coverage)}")
        print(f"    Final queue size : {len(self.queue)}")
        print(f"    Time elapsed     : {elapsed:.2f} seconds")