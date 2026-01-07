import os

# --- 1. 默认值配置 ---
DEFAULT_TARGET_PATH = "./target_program"
DEFAULT_SEEDS_DIR = "./seeds/test"
DEFAULT_OUTPUT_DIR = "./output/test"
DEFAULT_TIMEOUT_SEC = 2
DEFAULT_MAX_QUEUE_SIZE = 500
DEFAULT_TOTAL_TIMEOUT = 86400  # 默认 24 小时 (86400秒)
DEFAULT_TARGET_CMD = ""
DEFAULT_MAX_EXECUTIONS = 500

# --- 2. 内部加载类 ---
class _ConfigLoader:
    def __init__(self):
        self.TARGET_PATH = os.getenv('FUZZ_TARGET_PATH') or DEFAULT_TARGET_PATH
        self.SEEDS_DIR = os.getenv('FUZZ_SEEDS_DIR') or DEFAULT_SEEDS_DIR
        self.OUTPUT_DIR = os.getenv('FUZZ_OUTPUT_DIR') or DEFAULT_OUTPUT_DIR
        self.TARGET_CMD = os.getenv('FUZZ_TARGET_CMD') or DEFAULT_TARGET_CMD
        
        try:
            self.TIMEOUT_SEC = int(os.getenv('FUZZ_TIMEOUT_SEC') or DEFAULT_TIMEOUT_SEC)
        except ValueError:
            self.TIMEOUT_SEC = DEFAULT_TIMEOUT_SEC
        
        try:
            self.MAX_QUEUE_SIZE = int(os.getenv('FUZZ_MAX_QUEUE_SIZE') or DEFAULT_MAX_QUEUE_SIZE)
        except ValueError:
            self.MAX_QUEUE_SIZE = DEFAULT_MAX_QUEUE_SIZE
        
        try:
            self.TOTAL_TIMEOUT = int(os.getenv('FUZZ_TOTAL_TIMEOUT') or DEFAULT_TOTAL_TIMEOUT)
        except ValueError:
            self.TOTAL_TIMEOUT = DEFAULT_TOTAL_TIMEOUT

        self.MAX_EXECUTIONS = DEFAULT_MAX_EXECUTIONS

# --- 3. 实例化并导出为模块级变量 ---
_loaded_cfg = _ConfigLoader()

TARGET_PATH = _loaded_cfg.TARGET_PATH
SEEDS_DIR = _loaded_cfg.SEEDS_DIR
OUTPUT_DIR = _loaded_cfg.OUTPUT_DIR
# 子目录
CRASH_DIR = os.path.join(OUTPUT_DIR, "crashes")
QUEUE_DIR = os.path.join(OUTPUT_DIR, "queue")
HANG_DIR  = os.path.join(OUTPUT_DIR, "hangs")
PLOT_DIR  = os.path.join(OUTPUT_DIR, "plot_data")
# 临时输入文件
CUR_INPUT = os.path.join(OUTPUT_DIR, ".cur_input")
# 配置参数
TIMEOUT_SEC = _loaded_cfg.TIMEOUT_SEC
MAX_QUEUE_SIZE = _loaded_cfg.MAX_QUEUE_SIZE
TOTAL_TIMEOUT = _loaded_cfg.TOTAL_TIMEOUT
TARGET_CMD = _loaded_cfg.TARGET_CMD
MAX_EXECUTIONS = _loaded_cfg.MAX_EXECUTIONS

MAP_SIZE = 65536

def get_frequency_by_timeout(total_timeout_seconds: int = None) -> str:
    if total_timeout_seconds is None:
        total_timeout_seconds = TOTAL_TIMEOUT
    
    if total_timeout_seconds < 3600:  # < 1 hour
        return 'seconds'
    elif total_timeout_seconds < 43200:  # < 12 hours
        return 'minutes'
    else:  # >= 12 hours
        return 'hours'

def show_config():
    print(f"--- Loaded Configuration ---")
    print(f"TARGET_PATH: {TARGET_PATH}")
    print(f"SEEDS_DIR:   {SEEDS_DIR}")
    print(f"OUTPUT_DIR:  {OUTPUT_DIR}")
    print(f"TIMEOUT_SEC: {TIMEOUT_SEC}")
    print(f"MAX_QUEUE_SIZE: {MAX_QUEUE_SIZE}")
    print(f"TOTAL_TIMEOUT: {TOTAL_TIMEOUT} seconds ({TOTAL_TIMEOUT/3600:.2f} hours)")
    print(f"Frequency: {get_frequency_by_timeout()}")