import os

# --- 1. 默认值配置 ---
DEFAULT_TARGET_PATH = "./target_program"
DEFAULT_SEEDS_DIR = "./seeds/test"
DEFAULT_OUTPUT_DIR = "./output/test"
DEFAULT_TIMEOUT_SEC = 2
DEFAULT_MAX_QUEUE_SIZE = 500
DEFAULT_MAX_EXECUTIONS = 500
DEFAULT_TOTAL_TIMEOUT = 15  # 默认 24 小时 (86400秒)
DEFAULT_TARGET_CMD = ""

# --- 2. 内部加载类 ---
class _ConfigLoader:
    def __init__(self):
        # 优先从环境变量读取，否则使用默认值
        self.TARGET_PATH = os.getenv('FUZZ_TARGET_PATH') or DEFAULT_TARGET_PATH
        self.SEEDS_DIR = os.getenv('FUZZ_SEEDS_DIR') or DEFAULT_SEEDS_DIR
        self.OUTPUT_DIR = os.getenv('FUZZ_OUTPUT_DIR') or DEFAULT_OUTPUT_DIR
        self.TARGET_CMD = os.getenv('FUZZ_TARGET_CMD') or DEFAULT_TARGET_CMD
        
        try:
            self.TIMEOUT_SEC = int(os.getenv('FUZZ_TIMEOUT_SEC') or DEFAULT_TIMEOUT_SEC)
        except ValueError:
            self.TIMEOUT_SEC = DEFAULT_TIMEOUT_SEC
            
        self.MAX_QUEUE_SIZE = DEFAULT_MAX_QUEUE_SIZE
        self.MAX_EXECUTIONS = DEFAULT_MAX_EXECUTIONS
        self.TOTAL_TIMEOUT = DEFAULT_TOTAL_TIMEOUT

# --- 3. 实例化并导出为模块级变量 ---
_loaded_cfg = _ConfigLoader()

TARGET_PATH = _loaded_cfg.TARGET_PATH
SEEDS_DIR = _loaded_cfg.SEEDS_DIR
OUTPUT_DIR = _loaded_cfg.OUTPUT_DIR
# 子目录定义
CRASH_DIR = os.path.join(OUTPUT_DIR, "crashes")
QUEUE_DIR = os.path.join(OUTPUT_DIR, "queue")
HANG_DIR  = os.path.join(OUTPUT_DIR, "hangs")
PLOT_DIR  = os.path.join(OUTPUT_DIR, "plot_data")
# 正在执行的临时输入文件 (通常放在根目录或临时目录)
CUR_INPUT = os.path.join(OUTPUT_DIR, ".cur_input")
#
TIMEOUT_SEC = _loaded_cfg.TIMEOUT_SEC
MAX_QUEUE_SIZE = _loaded_cfg.MAX_QUEUE_SIZE
MAX_EXECUTIONS = _loaded_cfg.MAX_EXECUTIONS
TOTAL_TIMEOUT = _loaded_cfg.TOTAL_TIMEOUT
TARGET_CMD = _loaded_cfg.TARGET_CMD

# 提供一个打印函数方便调试
def show_config():
    print(f"--- Loaded Configuration ---")
    print(f"TARGET_PATH: {TARGET_PATH}")
    print(f"SEEDS_DIR:   {SEEDS_DIR}")
    print(f"OUTPUT_DIR:  {OUTPUT_DIR}")