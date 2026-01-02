import os
from .config import CRASHES_DIR
from dataclasses import dataclass


def ensure_dirs():
    os.makedirs(CRASHES_DIR, exist_ok=True)

def save_crash(data: bytes):
    idx = len(os.listdir(CRASHES_DIR))
    path = os.path.join(CRASHES_DIR, f"crash_{idx:06d}")
    with open(path, 'wb') as f:
        f.write(data)

@dataclass
class ExecutionResult:
    is_crash: bool
    exit_code: int
    exec_time_ns: int
    is_timeout: bool
    trace_bits: bytes  # ← 关键：64KB 原始 coverage 数据