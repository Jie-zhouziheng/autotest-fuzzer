# 评估组件
import os
import time
import matplotlib.pyplot as plt

class FuzzEvaluator:
    def __init__(self, output_dir: str = "./output"):
        self.start_time = None
        self.output_dir = output_dir

    def start_fuzzing(self):
        self.start_time = time.time()

    def generate_report(self, monitor_stats: dict, final_queue_size: int):
        """由 Fuzzer 在结束时调用，传入 monitor 的完整统计"""
        os.makedirs("output", exist_ok=True)
        
        elapsed = time.time() - self.start_time if self.start_time else 0

        print("\n[=] Fuzzing finished!")
        print(f"    Total executions : {monitor_stats['total_execs']}")
        print(f"    Crashes found    : {monitor_stats['crash_count']}")
        print(f"    Unique paths     : {monitor_stats['unique_paths']}")
        print(f"    Final queue size : {final_queue_size}")
        print(f"    Time elapsed     : {elapsed:.2f} seconds")

        # 生成覆盖率曲线
        history = monitor_stats["coverage_history"]
        if history:
            times, coverages = zip(*history)
            plt.figure(figsize=(10, 6))
            plt.plot(times, coverages, label="Unique Paths")
            plt.xlabel("Time (seconds)")
            plt.ylabel("Unique Paths")
            plt.title("Coverage Growth Over Time")
            plt.legend()
            plt.grid(True)
            plt.savefig(f"{self.output_dir}/coverage_curve.png")
            print(f"[+] Coverage curve saved to {self.output_dir}/coverage_curve.png")