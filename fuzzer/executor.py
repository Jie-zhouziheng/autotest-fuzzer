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
    def __init__(self, target_path: str = TARGET_PATH, timeout: int = TIMEOUT_SEC):
        self.target_path = target_path
        self.timeout = timeout
    
    def run(self, input_data: bytes) -> ExecutionResult:
        """
        4.测试执行组件
        创建子进程运行模糊目标，监控执行结果和覆盖率
        """
        # 初始化返回值
        shm_id = None
        shm = None
        trace_bits = bytes(MAP_SIZE)

        is_crash = False
        is_timeout = False
        exit_code = 0
        exec_time_ns = 0
        temp_input = None
        
        try:
            # 1. 创建共享内存（64KB bitmap）
            shm = sysv_ipc.SharedMemory(
                None,  # 自动分配key
                sysv_ipc.IPC_CREX, 
                size=MAP_SIZE
            )
            shm_id = shm.id
            shm.write(b'\x00' * MAP_SIZE)
            
            # 将输入数据写入临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix='.input') as f:
                temp_input = f.name
                f.write(input_data)
            
            # 设置环境变量，传递SHM ID给插装后的目标程序
            env = os.environ.copy()
            env['__AFL_SHM_ID'] = str(shm_id)
            
            # 执行模糊目标，记录执行时间
            start_time = time.perf_counter_ns()
            
            try:
                with open(temp_input, "rb") as fin:
                    result = subprocess.run(
                        [self.target_path],
                        stdin=fin,
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
            trace_bits = shm.read(MAP_SIZE)
            
        except sysv_ipc.ExistentialError:
            # 共享内存创建失败
            print("[!] Failed to create shared memory")
            trace_bits = bytes(MAP_SIZE)
        
        except Exception as e:
            print(f"[!] Unexpected error in run_target: {e}")
            trace_bits = bytes(MAP_SIZE)
        
        finally:
            # 清理资源
            if shm:
                try:
                    shm.detach()
                    shm.remove()
                except:
                    pass
            # 删除临时输入文件
            if temp_input and os.path.exists(temp_input):
                try:
                    os.unlink(temp_input)
                except Exception:
                    pass
        
        return ExecutionResult(
            is_crash=is_crash,
            exit_code=exit_code,
            exec_time_ns=exec_time_ns,
            is_timeout=is_timeout,
            trace_bits=trace_bits
        )