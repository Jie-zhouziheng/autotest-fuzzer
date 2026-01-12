from .config import *
from .executor import Executor
from .mutator import Mutator
from .scheduler import SeedQueue, SeedScheduler, PowerScheduler
from .seed import Seed
from .monitor import CoverageMonitor      
from .evaluator import FuzzEvaluator    
from .utils import *

class Fuzzer:

    def __init__(
        self,
        queue: SeedQueue,
        scheduler: SeedScheduler,
        power_scheduler: PowerScheduler,
        mutator: Mutator,
        executor: Executor,
        monitor: CoverageMonitor,
        evaluator: FuzzEvaluator,
        frequency: str = None
    ):
        self.queue = queue
        self.scheduler = scheduler
        self.power_scheduler = power_scheduler
        self.mutator = mutator
        self.executor = executor
        self.monitor = monitor
        self.evaluator = evaluator
        self._should_stop = False  # 信号停止标志

        if frequency is None:
            self.frequency = get_frequency_by_timeout()
        else:
            self.frequency = frequency
    
    def run(self):
        self.monitor.start_monitoring()

        try:
            while self.monitor.should_continue() and not self._should_stop:
                self.fuzz_once()
                self.monitor.log_status(len(self.queue), self.frequency)
        except KeyboardInterrupt:
            print("\n[!] Interrupted by user (Ctrl+C)")
            self._should_stop = True
        finally:
            # 无论正常结束还是被中断，都生成报告
            self.evaluator.generate_report(
                self.monitor.get_stats(),
                len(self.queue)
            )

    def stop(self):
        """外部调用停止 fuzzer"""
        self._should_stop = True

    def fuzz_once(self):
        seed = self.scheduler.pick(self.queue)
        power = self.power_scheduler.assign(seed)
        inputs = self.mutator.mutate(seed, self.queue, power)

        for data in inputs:
            if not self.monitor.should_continue() or self._should_stop:
                break
            result = self.executor.run(data)
            feedback = self.monitor.process_execution(data, result)

            self.queue.update(data, seed, feedback)