from fuzzer.fuzzer import Fuzzer
from fuzzer.config import *
from fuzzer.executor import *
from fuzzer.mutator import *
from fuzzer.scheduler import *
from fuzzer.seed import *
from fuzzer.monitor import *
from fuzzer.evaluator import *
from fuzzer.utils import *
import os
import signal
import sys

_fuzzer_instance = None

def signal_handler(signum, frame):
    """处理中断信号（SIGINT, SIGTERM）"""
    print(f"\n[!] Received signal {signum}, gracefully stopping fuzzer...")
    if _fuzzer_instance:
        _fuzzer_instance.stop()
    # 不立即退出，让 fuzzer.run() 的 finally 块处理

def load_seeds(seed_dir: str, queue: SeedQueue):
    if not os.path.exists(seed_dir):
        raise FileNotFoundError(f"Seed dir not found: {seed_dir}")

    count = 0
    # os.walk 会递归遍历 seed_dir
    for root, dirs, fnames in os.walk(seed_dir):
        for fname in fnames:
            if fname.startswith('.'):
                continue
            path = os.path.join(root, fname)
            
            try:
                with open(path, "rb") as f:
                    data = f.read()
                    if not data: # 跳过空文件
                        continue
                    queue.add(Seed(data))
                    count += 1
            except (IOError, OSError) as e:
                print(f"[!] Warning: Could not read seed {path}: {e}")

    print(f"[+] Loaded {count} initial seeds recursively from {seed_dir}")

def main():
    global _fuzzer_instance
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # kill 命令
    
    # 1. 初始化配置
    show_config()
    initialize_directories()

    seed_queue = SeedQueue()
    load_seeds(SEEDS_DIR, seed_queue)
    if len(seed_queue) == 0:
        print("[-] No initial seeds, aborting.")
        return
    
    scheduler = AFLPlusPlusScheduler()
    power_scheduler = AFLPowerScheduler()
    mutator = AFLPlusPlusMutator()

    executor = Executor(
        target_path=TARGET_PATH,
        timeout=TIMEOUT_SEC
    )
    monitor = CoverageMonitor(
        max_executions=MAX_EXECUTIONS,
        timeout=None
    )
    evaluator = FuzzEvaluator(output_dir=OUTPUT_DIR)

    fuzzer = Fuzzer(
        queue=seed_queue,
        scheduler=scheduler,
        power_scheduler=power_scheduler,
        mutator=mutator,
        executor=executor,
        monitor=monitor,
        evaluator=evaluator
    )
    
    _fuzzer_instance = fuzzer  # 保存全局引用
    fuzzer.run()

if __name__ == "__main__":
    main()