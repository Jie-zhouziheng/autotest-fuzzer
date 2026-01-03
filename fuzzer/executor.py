import os
import time
import subprocess
import tempfile
import signal
import sysv_ipc

from .config import *
from .utils import ExecutionResult

MAP_SIZE = 65536

class Executor:
    def __init__(self, target_path: str = TARGET_PATH, timeout: float = TIMEOUT_SEC):
        self.target_path = target_path
        self.timeout = timeout
        self.target_cmd_template = TARGET_CMD
        self.input_dir = CUR_INPUT

        self.shm = sysv_ipc.SharedMemory(None, sysv_ipc.IPC_CREX, size=MAP_SIZE)
        self.shm_id = self.shm.id
    
    def run(self, input_data: bytes) -> ExecutionResult:
        """
        4.测试执行组件
        创建子进程运行模糊目标，监控执行结果和覆盖率
        """
        # 初始化返回值
        trace_bits = bytes(MAP_SIZE)

        is_crash = False
        is_timeout = False
        exit_code = 0
        exec_time_ns = 0
        
        self.shm.write(b'\x00' * MAP_SIZE)
            
        # 设置环境变量，传递SHM ID给插装后的目标程序
        env = os.environ.copy()
        env['__AFL_SHM_ID'] = str(self.shm_id)

        # 将输入数据写入临时文件
        with open(self.input_dir, "wb") as f:
            f.write(input_data)
        
        # --- 核心逻辑：根据是否有 @@ 构建执行命令 ---
        full_cmd = [self.target_path]
        use_stdin = True
        if "@@" in self.target_cmd_template:
            # 模式 A: 文件参数模式 (T02, T03, T04, T05, T07, T08, T09, T10)
            use_stdin = False
            processed_args = self.target_cmd_template.replace("@@", self.input_dir).split()
            full_cmd.extend(processed_args)
        else:
            # 模式 B: 标准输入模式 (T01, T06)
            if self.target_cmd_template.strip():
                full_cmd.extend(self.target_cmd_template.split())
        
        # 3 执行模糊目标，记录执行时间
        start_time = time.perf_counter_ns()
        
        try:
            if use_stdin:
                # Stdin 模式：重定向文件到 stdin
                with open(self.input_dir, "rb") as fin:
                    result = subprocess.run(
                        full_cmd,
                        stdin=fin,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=self.timeout,
                        env=env
                    )
            else:
                # 参数模式：直接运行，stdin 指向空
                result = subprocess.run(
                    full_cmd,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=self.timeout,
                    env=env
                )

            exec_time_ns = time.perf_counter_ns() - start_time
            exit_code = result.returncode

            # AFL 风格 crash 判断：signal
            if exit_code < 0:
                is_crash = True
            
        except subprocess.TimeoutExpired:
            exec_time_ns = time.perf_counter_ns() - start_time
            is_timeout = True
            exit_code = -1
            
        except Exception as e:
            exec_time_ns = time.perf_counter_ns() - start_time
            is_crash = True
            exit_code = -2
        
        # 从共享内存读取覆盖率bitmap
        trace_bits = self.shm.read(MAP_SIZE)
            
        
        return ExecutionResult(
            is_crash=is_crash,
            exit_code=exit_code,
            exec_time_ns=exec_time_ns,
            is_timeout=is_timeout,
            trace_bits=trace_bits
        )
    
    def __del__(self):
        # 清理 SHM
        if hasattr(self, 'shm'):
            self.shm.detach()
            self.shm.remove()