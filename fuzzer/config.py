import os

# --- 1. 默认值配置 ---
DEFAULT_TARGET_PATH = "./target_program"
DEFAULT_SEEDS_DIR = "./seeds/test"
DEFAULT_CRASHES_DIR = "./crashes"
DEFAULT_OUTPUT_DIR = "./output"
DEFAULT_TIMEOUT_SEC = 1
DEFAULT_MAX_QUEUE_SIZE = 500
DEFAULT_MAX_EXECUTIONS = 500
DEFAULT_TOTAL_TIMEOUT = 4  # 默认 24 小时 (86400秒)
DEFAULT_TARGET_CMD = ""

# --- 2. 内部加载类 (仅用于封装逻辑) ---
class _ConfigLoader:
    def __init__(self):
        # 优先从环境变量读取，否则使用默认值
        # 使用 or 确保环境变量为空字符串时也回退到默认值
        self.TARGET_PATH = os.getenv('FUZZ_TARGET_PATH') or DEFAULT_TARGET_PATH
        self.SEEDS_DIR = os.getenv('FUZZ_SEEDS_DIR') or DEFAULT_SEEDS_DIR
        self.CRASHES_DIR = os.getenv('FUZZ_CRASHES_DIR') or DEFAULT_CRASHES_DIR
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
# 当其他文件 import config 时，下面这段代码会自动运行
_loaded_cfg = _ConfigLoader()

TARGET_PATH = _loaded_cfg.TARGET_PATH
SEEDS_DIR = _loaded_cfg.SEEDS_DIR
CRASHES_DIR = _loaded_cfg.CRASHES_DIR
OUTPUT_DIR = _loaded_cfg.OUTPUT_DIR
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
    print(f"CRASHES_DIR: {CRASHES_DIR}")
    print(f"OUTPUT_DIR:  {OUTPUT_DIR}")
    print(f"----------------------------")