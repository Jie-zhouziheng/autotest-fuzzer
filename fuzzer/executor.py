import hashlib
import subprocess
import os
from .config import TARGET_PATH, TIMEOUT_SEC

def run_target(input_data: bytes) -> tuple[bool, set[str], int]:
    """
    执行目标程序，返回 (is_crash, coverage_set, exit_code)
    - coverage_set: 模拟的“路径覆盖”（可用 stdout 哈希、或未来 SHM 实现）
    """
    try:
        result = subprocess.run(
            [TARGET_PATH],
            input=input_data,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=TIMEOUT_SEC,
            preexec_fn=os.setsid  # 便于超时 kill 整个进程组
        )
        is_crash = result.returncode != 0
        # 简化版：用 stdout 的哈希代表行为（可替换为真实插桩）
        coverage = {hashlib.sha1(result.stdout).hexdigest()[:8]} if result.stdout else set()
        return is_crash, coverage, result.returncode
    except subprocess.TimeoutExpired:
        return True, set(), -1  # 超时视为 crash
    except Exception:
        return True, set(), -2