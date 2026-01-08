# 评估组件
import os
import time
import matplotlib.pyplot as plt
import numpy as np
import csv
from .config import OUTPUT_DIR, PLOT_DIR

class FuzzEvaluator:
    def __init__(self, output_dir: str = OUTPUT_DIR):
        self.start_time = time.time()
        self.output_dir = output_dir
        self.log_file_path = os.path.join(PLOT_DIR, "logfile.txt")

    def start_fuzzing(self):
        self.start_time = time.time()

    def read_log_file(self):
        """从 log_file 读取数据，返回解析后的数据列表"""
        log_data = []
        if not os.path.exists(self.log_file_path):
            return log_data
        
        try:
            with open(self.log_file_path, "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    log_data.append({
                        'unix_time': float(row['unix_time']),
                        'elapsed_time': float(row['elapsed_time']),
                        'unique_edges': int(row['unique_edges']),
                        'total_execs': int(row['total_execs']),
                        'crash_count': int(row['crash_count']),
                        'hang_count': int(row['hang_count']),
                        'exec_speed': float(row['exec_speed'])
                    })
        except Exception as e:
            print(f"[!] Warning: Failed to read log file: {e}")
        
        return log_data

    def generate_report(self, monitor_stats: dict = None, final_queue_size: int = 0, time_unit: str = 'hours'):
        """
        由 Fuzzer 在结束时调用：
        - 总体数据从 monitor_stats 获取（用于打印统计信息）
        - 图表数据从 log_file 读取（用于绘制曲线）
        
        Args:
            monitor_stats: 监控统计数据
            final_queue_size: 最终队列大小
            time_unit: 时间单位，可选 'seconds', 'minutes', 'hours'，默认为 'hours'
        """
        # 从 log_file 读取数据用于绘制图表
        log_data = self.read_log_file()
        
        # 总体数据从 monitor_stats 获取
        if monitor_stats:
            elapsed = monitor_stats.get('elapsed_time', time.time() - self.start_time if self.start_time else 0)
            total_execs = monitor_stats.get('total_execs', 0)
            crash_count = monitor_stats.get('crash_count', 0)
            hang_count = monitor_stats.get('hang_count', 0)
            unique_paths = monitor_stats.get('unique_paths', 0)
            exec_speed = total_execs / elapsed if elapsed > 0 else 0

        print("\n[=] Fuzzing finished!")
        print(f"    Total executions : {total_execs}")
        print(f"    Exec Speed       : {exec_speed:.2f} execs/s")
        print(f"    Crashes found    : {crash_count}")
        print(f"    Hang found       : {hang_count}")
        print(f"    Unique paths     : {unique_paths}")
        print(f"    Final queue size : {final_queue_size}")
        print(f"    Time elapsed     : {elapsed:.2f} seconds")
        
        
        # 从 log_file 数据生成图表
        if log_data:
            self._plot_from_log_data(log_data, time_unit)
        else:
            print("[!] Warning: No log data available for plotting")

    def _plot_from_log_data(self, log_data, time_unit: str = 'hours'):
        """
        从 log_file 数据绘制覆盖率曲线和其他图表
        
        Args:
            log_data: 从 log_file 读取的数据列表
            time_unit: 时间单位，可选 'seconds', 'minutes', 'hours'
        """
        if not log_data:
            return
        
        # 提取数据（按照时间排序，确保曲线单调向前）
        log_data_sorted = sorted(log_data, key=lambda e: e['elapsed_time'])
        elapsed_times = np.array([entry['elapsed_time'] for entry in log_data_sorted])
        unique_edges = np.array([entry['unique_edges'] for entry in log_data_sorted])
        crash_counts = np.array([entry['crash_count'] for entry in log_data_sorted])
        
        # 根据时间单位转换时间
        if time_unit == 'minutes':
            time_data = elapsed_times / 60.0
            time_label = "Time (minutes)"
        elif time_unit == 'hours':
            time_data = elapsed_times / 3600.0
            time_label = "Time (hours)"
        else:  # 'seconds' 或其他，默认使用秒
            time_data = elapsed_times
            time_label = "Time (seconds)"
        
        # 确保目录存在
        plot_dir = os.path.join(self.output_dir, "plot_data")
        if not os.path.exists(plot_dir):
            os.makedirs(plot_dir)
        
        # 在时间轴起点补一个 t=0 的点，让曲线从 0 开始更平滑
        if len(time_data) > 0:
            # 覆盖率在 0 时刻使用第一个观测值，crash 数量从 0 开始
            time_data = np.insert(time_data, 0, 0.0)
            unique_edges = np.insert(unique_edges, 0, unique_edges[0])
            crash_counts = np.insert(crash_counts, 0, 0)
        
        # 1. 覆盖率曲线 - 独立图表
        plt.figure(figsize=(10, 6))
        plt.plot(time_data, unique_edges, label="Edges Discovered", color='#1f77b4', linewidth=2)
        plt.xlabel(time_label, fontsize=11)
        plt.ylabel("Cumulative Unique Edges", fontsize=11)
        plt.title("Coverage Growth Curve", fontsize=13, fontweight='bold')
        plt.grid(True)
        plt.legend(loc='lower right')
        if len(time_data) > 0:
            plt.xlim(0, max(time_data) * 1.05)
        if len(unique_edges) > 0:
            plt.ylim(0, max(unique_edges) * 1.1)
        
        plt.tight_layout()
        coverage_plot_path = os.path.join(plot_dir, "coverage_curve.png")
        plt.savefig(coverage_plot_path, dpi=150)
        plt.close()
        print(f"[+] Coverage plot saved to: {coverage_plot_path}")
        
        # 2. Crash 数量曲线 - 独立图表
        plt.figure(figsize=(10, 6))
        plt.plot(time_data, crash_counts, label="Crashes Found", color='#d62728', linewidth=2)
        plt.xlabel(time_label, fontsize=11)
        plt.ylabel("Cumulative Crashes", fontsize=11)
        plt.title("Crash Discovery Over Time", fontsize=13, fontweight='bold')
        plt.grid(True)
        plt.legend(loc='lower right')
        if len(time_data) > 0:
            plt.xlim(0, max(time_data) * 1.05)
        if len(crash_counts) > 0:
            ymax = max(crash_counts)
            if ymax > 0:
                plt.ylim(0, ymax * 1.1)
            else:
                # 全程无 crash，固定在 [0,1] 避免出现负坐标和 warning
                plt.ylim(0, 1.0)
        
        plt.tight_layout()
        crash_plot_path = os.path.join(plot_dir, "crash_curve.png")
        plt.savefig(crash_plot_path, dpi=150)
        plt.close()
        print(f"[+] Crash plot saved to: {crash_plot_path}")