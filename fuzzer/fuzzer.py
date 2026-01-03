# fuzzer/fuzzer.py
import os
from .config import *
from .executor import Executor
from .mutator import Mutator
from .scheduler import SeedQueue, SeedScheduler, PowerScheduler
from .seed import Seed
from .monitor import CoverageMonitor      
from .evaluator import FuzzEvaluator    
from .utils import ensure_dirs, ExecutionResult

class Fuzzer:

    def __init__(
        self,
        queue: SeedQueue,
        scheduler: SeedScheduler,
        power_scheduler: PowerScheduler,
        mutator: Mutator,
        executor: Executor,
        monitor: CoverageMonitor,
        evaluator: FuzzEvaluator
    ):
        self.queue = queue
        self.scheduler = scheduler
        self.power_scheduler = power_scheduler
        self.mutator = mutator
        self.executor = executor
        self.monitor = monitor
        self.evaluator = evaluator
    
    def run(self):
        self.monitor.start_monitoring()
        self.evaluator.start_fuzzing()

        while self.monitor.should_continue():
            self.fuzz_once()

        self.evaluator.generate_report(
            self.monitor.get_stats(),
            len(self.queue)
        )

    def fuzz_once(self):
        seed = self.scheduler.pick(self.queue)
        power = self.power_scheduler.assign(seed)
        inputs = self.mutator.mutate(seed, self.queue, power)

        for data in inputs:
            if not self.monitor.should_continue():
                break
            result = self.executor.run(data)
            feedback = self.monitor.process_execution(data, result)

            if feedback.new_coverage:
                new_seed = Seed(data)
                #初始化性能数据
                new_seed.performance = (result.exec_time_ns, len(result.trace_bits) - result.trace_bits.count(b'\0'))
                new_seed.mark_favored()
                self.queue.add(new_seed)
            if feedback.crashed:
                    seed.mark_crash()