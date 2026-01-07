import os
from .config import *
from dataclasses import dataclass


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
    执行反馈，不包含 trace_bits 以避免数据复制。
    其他组件应通过 SHMAccessor 接口访问 trace_bits。
    """
    # 覆盖相关
    new_coverage: int              # 本次新增的边数量
    total_unique_edges: int        # 当前全局唯一边总数
    # 结果相关
    crashed: bool                  
    time_out: bool              
    # 性能相关
    exec_time_ns: float        
    # 覆盖"密度"相关（本次执行激活了多少边）
    bitmap_size: int
    trace_bits: bytes