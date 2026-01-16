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
        if not os.path.exists(self.log_file_path):
            return []

        try:
            with open(self.log_file_path, "r") as f:
                reader = csv.DictReader(f)
                return [
                    {
                        'elapsed_time': float(row['elapsed_time']),
                        'unique_edges': int(row['unique_edges']),
                        'total_execs': int(row['total_execs']),
                        'crash_count': int(row['crash_count']),
                        'hang_count': int(row['hang_count']),
                        'exec_speed': float(row['exec_speed']),
                        'queue_size': int(row['queue_size']),
                        'last_new_find': float(row['last_new_find']),
                        'last_crash': float(row['last_crash']),
                        'last_hang': float(row['last_hang']),
                    }
                    for row in reader
                ]
        except Exception as e:
            print(f"[!] Warning: Failed to read log file: {e}")
            return []

    def generate_report(self, monitor_stats: dict = None, final_queue_size: int = 0):
        """
        由 Fuzzer 在结束时调用：
        - 总体数据从 monitor_stats 获取（用于打印统计信息）
        - 图表数据从 log_file 读取（用于绘制曲线）
        - 根据实际执行时间自动选择合适的时间单位
        """
        # 从 log_file 读取数据用于绘制图表
        log_data = self.read_log_file()
        
        if not monitor_stats:
            print("[!] Warning: No monitor stats available")
            return
        
        # 统一提取统计数据
        stats = self._extract_stats(monitor_stats, final_queue_size)
        
        # 打印统计信息
        print("\n[=] Fuzzing finished!")
        print(f"    Total executions : {stats['total_execs']}")
        print(f"    Exec Speed       : {stats['exec_speed']:.2f} execs/s")
        print(f"    Crashes found    : {stats['crash_count']}")
        print(f"    Hang found       : {stats['hang_count']}")
        print(f"    Unique paths     : {stats['unique_paths']}")
        print(f"    Final queue size : {final_queue_size}")
        print(f"    Time elapsed     : {stats['elapsed_time']:.2f} seconds")
        
        self._save_fuzzer_stats(stats)

        # 从 log_file 数据生成图表（自动确定时间单位）
        if log_data:
            time_unit = self._determine_time_unit(stats['elapsed_time'])
            self._plot_from_log_data(log_data, time_unit)
        else:
            print("[!] Warning: No log data available for plotting")

    def _extract_stats(self, monitor_stats: dict, final_queue_size: int) -> dict:
        """统一提取和计算统计数据"""
        current_time = int(time.time())
        elapsed = monitor_stats.get('elapsed_time', 0)
        total_execs = monitor_stats.get('total_execs', 0)
        
        return {
            'start_time': monitor_stats.get('start_time', current_time),
            'last_update': monitor_stats.get('last_update', current_time),
            'run_time': int(elapsed),
            'elapsed_time': elapsed,  # 保留原始浮点数用于显示
            'total_execs': total_execs,
            'exec_speed': monitor_stats.get('exec_speed', total_execs / elapsed if elapsed > 0 else 0.0),
            'crash_count': monitor_stats.get('crash_count', 0),
            'hang_count': monitor_stats.get('hang_count', 0),
            'unique_paths': monitor_stats.get('unique_paths', 0),
            'unique_edges': monitor_stats.get('unique_edges', monitor_stats.get('unique_paths', 0)),
            'corpus_count': final_queue_size,
            'last_find': monitor_stats.get('last_new_find_time') or 0,
            'last_crash': monitor_stats.get('last_saved_crash_time') or 0,
            'last_hang': monitor_stats.get('last_saved_hang_time') or 0,
        }

    def _save_fuzzer_stats(self, stats: dict):
        """保存 fuzzer_stats 文件，参考 AFL++ 格式"""
        stats_file_path = os.path.join(PLOT_DIR, "fuzzer_stats")
        
        # 定义字段映射（字段名: (显示名, 格式化函数)）
        fields = [
            ('start_time', 'start_time', lambda x: x),
            ('last_update', 'last_update', lambda x: x),
            ('run_time', 'run_time', lambda x: x),
            ('total_execs', 'execs_done', lambda x: x),
            ('exec_speed', 'execs_per_sec', lambda x: f"{x:.2f}"),
            ('corpus_count', 'corpus_count', lambda x: x),
            ('crash_count', 'saved_crashes', lambda x: x),
            ('hang_count', 'saved_hangs', lambda x: x),
            ('unique_edges', 'edges_found', lambda x: x),
            ('last_find', 'last_find', lambda x: x or 0),
            ('last_crash', 'last_crash', lambda x: x or 0),
            ('last_hang', 'last_hang', lambda x: x or 0),
        ]
        
        with open(stats_file_path, "w") as f:
            for key, display_name, formatter in fields:
                value = stats.get(key, 0)
                f.write(f"{display_name:<18} : {formatter(value)}\n")
        
        print(f"[+] Fuzzer stats saved to: {stats_file_path}")

    def _determine_time_unit(self, elapsed_seconds: float) -> str:
        if elapsed_seconds < 60:
            return 'seconds'
        elif elapsed_seconds < 3600:  # 1 hour
            return 'minutes'
        else:
            return 'hours'

    def _plot_from_log_data(self, log_data, time_unit: str = 'hours'):
        """
        从 log_file 数据绘制覆盖率曲线和其他图表
        """
        if not log_data:
            return
        
        # 提取数据（按照时间排序，确保曲线单调向前）
        log_data_sorted = sorted(log_data, key=lambda e: e['elapsed_time'])
        elapsed_times = np.array([entry['elapsed_time'] for entry in log_data_sorted])
        unique_edges = np.array([entry['unique_edges'] for entry in log_data_sorted])
        crash_counts = np.array([entry['crash_count'] for entry in log_data_sorted])
        hang_counts = np.array([entry['hang_count'] for entry in log_data_sorted])
        exec_speeds = np.array([entry['exec_speed'] for entry in log_data_sorted])
        queue_sizes = np.array([entry.get('queue_size', 0) for entry in log_data_sorted])
        
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
            time_data = np.insert(time_data, 0, 0.0)
            unique_edges = np.insert(unique_edges, 0, unique_edges[0] if len(unique_edges) > 0 else 0)
            crash_counts = np.insert(crash_counts, 0, 0)
            hang_counts = np.insert(hang_counts, 0, 0)
            exec_speeds = np.insert(exec_speeds, 0, exec_speeds[0] if len(exec_speeds) > 0 else 0)
            queue_sizes = np.insert(queue_sizes, 0, queue_sizes[0] if len(queue_sizes) > 0 else 0)
        
        # 1. 覆盖率曲线 
        plt.figure(figsize=(10, 6))
        plt.plot(time_data, unique_edges, label="Edges Discovered", color='#1f77b4', linewidth=2)
        plt.xlabel(time_label, fontsize=11)
        plt.ylabel("Cumulative Unique Edges", fontsize=11)
        plt.title("Coverage Growth Curve", fontsize=13, fontweight='bold')
        plt.grid(True, alpha=0.3)
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
        
        # 2. Crash 数量曲线
        plt.figure(figsize=(10, 6))
        plt.plot(time_data, crash_counts, label="Crashes Found", color='#d62728', linewidth=2)
        plt.xlabel(time_label, fontsize=11)
        plt.ylabel("Cumulative Crashes", fontsize=11)
        plt.title("Crash Discovery Over Time", fontsize=13, fontweight='bold')
        plt.grid(True, alpha=0.3)
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
        
        # 3. Hang 数量曲线
        if len(hang_counts) > 0 and max(hang_counts) > 0:
            plt.figure(figsize=(10, 6))
            plt.plot(time_data, hang_counts, label="Hangs Found", color='#ff7f0e', linewidth=2)
            plt.xlabel(time_label, fontsize=11)
            plt.ylabel("Cumulative Hangs", fontsize=11)
            plt.title("Hang Discovery Over Time", fontsize=13, fontweight='bold')
            plt.grid(True, alpha=0.3)
            plt.legend(loc='lower right')
            if len(time_data) > 0:
                plt.xlim(0, max(time_data) * 1.05)
            ymax = max(hang_counts)
            if ymax > 0:
                plt.ylim(0, ymax * 1.1)
            else:
                plt.ylim(0, 1.0)
            
            plt.tight_layout()
            hang_plot_path = os.path.join(plot_dir, "hang_curve.png")
            plt.savefig(hang_plot_path, dpi=150)
            plt.close()
            print(f"[+] Hang plot saved to: {hang_plot_path}")
        
        # 4. 执行速度曲线
        if len(exec_speeds) > 0 and max(exec_speeds) > 0:
            plt.figure(figsize=(10, 6))
            plt.plot(time_data, exec_speeds, label="Execution Speed", color='#2ca02c', linewidth=2)
            plt.xlabel(time_label, fontsize=11)
            plt.ylabel("Executions per Second", fontsize=11)
            plt.title("Execution Speed Over Time", fontsize=13, fontweight='bold')
            plt.grid(True, alpha=0.3)
            plt.legend(loc='upper right')
            if len(time_data) > 0:
                plt.xlim(0, max(time_data) * 1.05)
            if len(exec_speeds) > 0:
                ymax = max(exec_speeds)
                plt.ylim(0, ymax * 1.1)
            
            plt.tight_layout()
            speed_plot_path = os.path.join(plot_dir, "exec_speed_curve.png")
            plt.savefig(speed_plot_path, dpi=150)
            plt.close()
            print(f"[+] Execution speed plot saved to: {speed_plot_path}")
        
        # 5. 队列大小曲线
        if len(queue_sizes) > 0 and max(queue_sizes) > 0:
            plt.figure(figsize=(10, 6))
            plt.plot(time_data, queue_sizes, label="Queue Size", color='#9467bd', linewidth=2)
            plt.xlabel(time_label, fontsize=11)
            plt.ylabel("Seed Queue Size", fontsize=11)
            plt.title("Seed Queue Growth Over Time", fontsize=13, fontweight='bold')
            plt.grid(True, alpha=0.3)
            plt.legend(loc='lower right')
            if len(time_data) > 0:
                plt.xlim(0, max(time_data) * 1.05)
            if len(queue_sizes) > 0:
                ymax = max(queue_sizes)
                plt.ylim(0, ymax * 1.1)
            
            plt.tight_layout()
            queue_plot_path = os.path.join(plot_dir, "queue_size_curve.png")
            plt.savefig(queue_plot_path, dpi=150)
            plt.close()
            print(f"[+] Queue size plot saved to: {queue_plot_path}")