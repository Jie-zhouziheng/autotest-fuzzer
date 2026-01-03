import random
import struct
from typing import List, Optional
from .seed import Seed


class Mutator:
    def __init__(self):
        # 模拟 8-bit, 16-bit, 32-bit 的溢出或特殊值
        self.INTERESTING_8 = [
            -128, -1, 0, 1, 16, 32, 64, 100, 127
        ]
        self.INTERESTING_16 = [
            -32768, -129, 128, 255, 256, 512, 1000, 1024, 4096, 32767
        ]
        self.INTERESTING_32 = [
            -2147483648, -100663046, -32769, 32768, 65535, 65536, 100663045, 2147483647
        ]

    def mutate(self,  seed: Seed, population: List[Seed], power: int = 5) -> List[bytes]:
        """
        1. BitFlip (位翻转)
        2. Arithmetic (算术加减)
        3. Interest (感兴趣/特殊数值) - [Missing in your code]
        4. Havoc (大破坏) - [Enhanced]
        5. Splice (拼接) - [Missing in your code]
        """
        seed_data = bytearray(seed.data)
        if not seed_data:
            return []

        results = list()
        length = len(seed_data)

        for _ in range(power):
            mutated = seed_data.copy()

            # 随机选择一种变异策略 (0-4)
            strategy = random.randint(0, 4)

            # --- 策略 1: BitFlip (位翻转) ---
            if strategy == 0:
                pos = random.randint(0, length - 1)
                bit = random.randint(0, 7)
                mutated[pos] ^= (1 << bit)

            # --- 策略 2: Arithmetic (算术加减) ---
            elif strategy == 1:
                pos = random.randint(0, length - 1)
                val = random.randint(1, 35)
                # 模拟 8bit 加减，注意要在 0-255 之间循环
                if random.choice([True, False]):
                    mutated[pos] = (mutated[pos] + val) % 256
                else:
                    mutated[pos] = (mutated[pos] - val) % 256

            # --- 策略 3: Interest (感兴趣数值替换) [新增] ---
            elif strategy == 2:
                # 随机选择 8/16/32 位替换
                width = random.choice([1, 2, 4])
                if length >= width:
                    pos = random.randint(0, length - width)
                    if width == 1:
                        val = random.choice(self.INTERESTING_8)
                        mutated[pos] = val & 0xFF
                    elif width == 2:
                        val = random.choice(self.INTERESTING_16)
                        # 大端或小端随机，这里简化处理
                        new_bytes = struct.pack('<h', val)
                        mutated[pos:pos + 2] = new_bytes
                    elif width == 4:
                        val = random.choice(self.INTERESTING_32)
                        new_bytes = struct.pack('<i', val)
                        mutated[pos:pos + 4] = new_bytes

            # --- 策略 4: Havoc (随机大破坏) [增强] ---
            elif strategy == 3:
                # Havoc 通常是多次随机操作的叠加
                havoc_cycles = random.randint(1, 4)
                for _ in range(havoc_cycles):
                    m_len = len(mutated)
                    if m_len == 0: break
                    op = random.randint(0, 2)

                    if op == 0:  # 随机替换字节
                        pos = random.randint(0, m_len - 1)
                        mutated[pos] = random.randint(0, 255)
                    elif op == 1:  # 随机删除一段 (Block Deletion)
                        if m_len > 2:
                            del_len = random.randint(1, min(m_len, 4))
                            pos = random.randint(0, m_len - del_len)
                            del mutated[pos:pos + del_len]
                    elif op == 2:  # 随机插入一段 (Block Insertion)
                        pos = random.randint(0, m_len)
                        insert_len = random.randint(1, 4)
                        # 插入随机内容或重复内容
                        to_insert = bytearray(random.getrandbits(8) for _ in range(insert_len))
                        mutated[pos:pos] = to_insert

            # --- 策略 5: Splice (拼接) [新增] ---
            elif strategy == 4:
                # 需要种子队列中至少还有其他种子
                if len(population.queue) > 1:
                    target = random.choice(population.queue)
                    # 避免选到自己，或者选到太短的
                    if target.data and len(target.data) > 1 and len(mutated) > 1:
                        target_data = target.data
                        # 随机选择两个切分点
                        split_at_1 = random.randint(1, len(mutated) - 1)
                        split_at_2 = random.randint(1, len(target_data) - 1)

                        # 拼接：前半部分用自己的，后半部分用别人的
                        mutated = mutated[:split_at_1] + target_data[split_at_2:]

            results.append(bytes(mutated))

        return results