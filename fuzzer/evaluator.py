# 评估组件
import os
import time
import matplotlib.pyplot as plt
import numpy as np
from .config import OUTPUT_DIR

class FuzzEvaluator:
    def __init__(self, output_dir: str = OUTPUT_DIR):
        self.start_time = time.time()
        self.output_dir = output_dir

    def start_fuzzing(self):
        self.start_time = time.time()

    def generate_report(self, monitor_stats: dict, final_queue_size: int):
        """由 Fuzzer 在结束时调用，传入 monitor 的完整统计"""
        
        elapsed = time.time() - self.start_time if self.start_time else 0
        exec_speed = monitor_stats['total_execs'] / elapsed if elapsed > 0 else 0

        print("\n[=] Fuzzing finished!")
        print(f"    Total executions : {monitor_stats['total_execs']}")
        print(f"    Exec Speed       : {exec_speed:.2f} execs/s") # 性能指标
        print(f"    Crashes found    : {monitor_stats['crash_count']}")
        print(f"    Hang found       : {monitor_stats['hang_count']}")
        print(f"    Unique paths     : {monitor_stats['unique_paths']}")
        print(f"    Final queue size : {final_queue_size}")
        print(f"    Time elapsed     : {elapsed:.2f} seconds")

        # 生成覆盖率曲线
        history = monitor_stats["coverage_history"]
        if history:
            times = [0.0] + [h[0] for h in history]
            coverages = [0] + [h[1] for h in history]
            
            total_elapsed = time.time() - self.start_time
            times.append(total_elapsed)
            coverages.append(coverages[-1])

            # --- 核心修复：转换为 numpy 数组 ---
            x = np.array(times)
            y = np.array(coverages)

            plt.figure(figsize=(10, 6))
            
            # 使用转换后的 x, y
            plt.plot(x, y, label="Edges Discovered", color='#1f77b4', linewidth=2)

            # 图表装饰
            plt.xlabel("Time (seconds)", fontsize=11)
            plt.ylabel("Cumulative Unique Edges", fontsize=11)
            plt.title("Coverage Growth Curve", fontsize=13, fontweight='bold')
            plt.grid(True)
            plt.legend(loc='lower right')
            
            plt.xlim(0, max(elapsed, 1.0))
            if len(y) > 0:
                plt.ylim(0, max(y) * 1.1) # 留出 10% 顶部空间

            plot_path = os.path.join(self.output_dir, "plot_data", "coverage_curve.png")
            plt.savefig(plot_path)
            print(f"[+] Coverage curve saved to {self.output_dir}/coverage_curve.png")