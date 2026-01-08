import os
from .config import *
from dataclasses import dataclass
from typing import Set, Tuple


def initialize_directories():
    """
    初始化模糊测试所需的目录结构
    """
    # 需要创建的目录列表
    dirs_to_create = [
        OUTPUT_DIR,
        QUEUE_DIR,     # 对应 output/queue
        CRASH_DIR,     # 对应 output/crashes
        HANG_DIR,      # 对应 output/hangs
        PLOT_DIR       # 对应 output/plot_data
    ]
    
    for d in dirs_to_create:
        if not os.path.exists(d):
            os.makedirs(d, exist_ok=True)
            print(f"[+] Created directory: {d}")
        else:
            # 可选：如果目录已存在，是否需要清空旧的实验数据？
            # print(f"[*] Directory already exists: {d}")
            pass
    if not os.path.exists(SEEDS_DIR):
        print(f"[!] Warning: Seed directory {SEEDS_DIR} not found!")

def save_data(data: bytes, category: str, index: int):
        """
        category: 'queue', 'crash', or 'hang'
        """
        mapping = {
        'queue': (QUEUE_DIR, "id"),
        'crash': (CRASH_DIR, "crash"),
        'hang': (HANG_DIR, "hang")
        }
        
        if category not in mapping:
            return None

        folder, prefix = mapping[category]
        file_name = f"{prefix}:{index:06d}"
        file_path = os.path.join(folder, file_name)

        with open(file_path, "wb") as f:
            f.write(data)
        
        return file_name

@dataclass
class ExecutionResult:
    is_crash: bool
    exit_code: int
    exec_time_ns: int
    is_timeout: bool
    trace_bits: bytes

@dataclass
class ExecutionFeedback:
    """
    执行反馈，包含解析好的 coverage 集合，避免在 seed.py 中重复解析。
    """
    # 覆盖相关
    new_coverage: int              # 本次新增的边数量
    total_unique_edges: int        # 当前全局唯一边总数
    coverage: Set[Tuple[int, int]] # 本次执行激活的边集合（解析为 (i, bucket) 签名）
    # 稳定性 / 结果相关
    crashed: bool                  # 是否 crash
    time_out: bool                 # 是否超时
    # 性能相关
    exec_time_ns: int              # 本次执行耗时
    # 覆盖"密度"相关
    bitmap_size: int               # 本次 trace_bits 中非零字节数量