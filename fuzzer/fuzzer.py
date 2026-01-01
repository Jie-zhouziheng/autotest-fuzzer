# fuzzer/fuzzer.py
import os
import time
from typing import List
from .config import *
from .executor import run_target
from .mutator import mutate
from .scheduler import pick_seed, should_retire
from .seed import Seed
from .utils import save_crash, ensure_dirs

class Fuzzer:
    def __init__(self):
        self.queue: List[Seed] = []
        self.observed_coverage = set()
        self.total_execs = 0
        self.crash_count = 0

    def load_seeds(self):
        if not os.path.exists(SEEDS_DIR):
            print(f"[!] Seeds directory not found: {SEEDS_DIR}")
            return
        for fname in os.listdir(SEEDS_DIR):
            path = os.path.join(SEEDS_DIR, fname)
            with open(path, 'rb') as f:
                self.queue.append(Seed(f.read()))
        print(f"[+] Loaded {len(self.queue)} seeds.")

    def run(self):
        ensure_dirs()
        self.load_seeds()

        if not self.queue:
            print("[-] No seeds to start fuzzing. Exiting.")
            return

        print(f"[=] Starting fuzzing for up to {MAX_EXECUTIONS} executions...")
        start_time = time.time()

        while self.total_execs < MAX_EXECUTIONS and self.queue:
            # 从队列选一个种子（简单轮询）
            seed = self.queue[0]
            seed.execs += 1

            # 能量调度：favored 种子变异更多
            power = 20 if seed.favored else 5

            # 变异
            inputs = mutate(seed.data, power)

            # 测试执行
            for inp in inputs:
                if self.total_execs >= MAX_EXECUTIONS:
                    break

                self.total_execs += 1
                is_crash, cov, _ = run_target(inp)

                # 执行结果监控组件（保存崩溃）
                if is_crash:
                    save_crash(inp)
                    self.crash_count += 1
                    print(f"[!] Crash #{self.crash_count} at exec #{self.total_execs}")

                # 新覆盖？加入队列
                if cov - self.observed_coverage:
                    self.observed_coverage |= cov
                    new_seed = Seed(inp)
                    new_seed.mark_favored()
                    self.queue.append(new_seed)

            # （可选）种子退休：防止队列爆炸
            if len(self.queue) > MAX_QUEUE_SIZE:
                old_len = len(self.queue)
                self.queue = [s for s in self.queue if not should_retire(s)]
                if len(self.queue) < old_len:
                    print(f"[-] Retired seeds: {old_len} → {len(self.queue)}")

        # === 打印总结 ===
        elapsed = time.time() - start_time
        print("\n[=] Fuzzing finished!")
        print(f"    Total executions : {self.total_execs}")
        print(f"    Crashes found    : {self.crash_count}")
        print(f"    Unique paths     : {len(self.observed_coverage)}")
        print(f"    Final queue size : {len(self.queue)}")
        print(f"    Time elapsed     : {elapsed:.2f} seconds")