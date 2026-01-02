from fuzzer.fuzzer import Fuzzer
from fuzzer.config import *
from fuzzer.executor import *
from fuzzer.mutator import *
from fuzzer.scheduler import *
from fuzzer.seed import *
from fuzzer.monitor import *
from fuzzer.evaluator import *    
from fuzzer.utils import ensure_dirs, ExecutionResult

def load_seeds(seed_dir: str, queue: SeedQueue):
    if not os.path.exists(seed_dir):
        raise FileNotFoundError(f"Seed dir not found: {seed_dir}")

    count = 0
    for fname in os.listdir(seed_dir):
        path = os.path.join(seed_dir, fname)
        if not os.path.isfile(path):
            continue
        with open(path, "rb") as f:
            queue.add(Seed(f.read()))
            count += 1

    print(f"[+] Loaded {count} initial seeds from {seed_dir}")

def main():
    # 1. 初始化配置
    show_config()

    seed_queue = SeedQueue()
    load_seeds(SEEDS_DIR, seed_queue)
    if len(seed_queue) == 0:
        print("[-] No initial seeds, aborting.")
        return
    
    scheduler = RoundRobinScheduler()
    power_scheduler = SimplePowerScheduler()
    mutator = Mutator()

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
    fuzzer.run()

if __name__ == "__main__":
    main()