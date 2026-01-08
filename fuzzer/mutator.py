import random
import struct
import math
from typing import List, Optional
from .seed import Seed, SeedQueue

class Mutator:
    def mutate(self, seed: Seed, population: SeedQueue, power: int = 5) -> List[bytes]:
        raise NotImplementedError


class RanDomMutator(Mutator):
    def __init__(self):
        self.INTERESTING_8 = [
            -128, -1, 0, 1, 16, 32, 64, 100, 127
        ]
        self.INTERESTING_16 = [
            -32768, -129, 128, 255, 256, 512, 1000, 1024, 4096, 32767
        ]
        self.INTERESTING_32 = [
            -2147483648, -100663046, -32769, 32768, 65535, 65536, 100663045, 2147483647
        ]

    def mutate(self, seed: Seed, population: SeedQueue, power: int = 5) -> List[bytes]:
        """
        1. BitFlip (位翻转)
        2. Arithmetic (算术加减)
        3. Interest (感兴趣/特殊数值)
        4. Havoc (大破坏)
        5. Splice (拼接)
        """
        seed_data = bytearray(seed.data)
        if not seed_data:
            return []

        results = list()
        length = len(seed_data)

        for _ in range(power):
            mutated = seed_data.copy()
            strategy = random.randint(0, 4)

            if strategy == 0:
                pos = random.randint(0, length - 1)
                bit = random.randint(0, 7)
                mutated[pos] ^= (1 << bit)

            elif strategy == 1:
                pos = random.randint(0, length - 1)
                val = random.randint(1, 35)
                if random.choice([True, False]):
                    mutated[pos] = (mutated[pos] + val) % 256
                else:
                    mutated[pos] = (mutated[pos] - val) % 256

            elif strategy == 2:
                width = random.choice([1, 2, 4])
                if length >= width:
                    pos = random.randint(0, length - width)
                    if width == 1:
                        val = random.choice(self.INTERESTING_8)
                        mutated[pos] = val & 0xFF
                    elif width == 2:
                        val = random.choice(self.INTERESTING_16)
                        new_bytes = struct.pack('<h', val)
                        mutated[pos:pos + 2] = new_bytes
                    elif width == 4:
                        val = random.choice(self.INTERESTING_32)
                        new_bytes = struct.pack('<i', val)
                        mutated[pos:pos + 4] = new_bytes

            elif strategy == 3:
                havoc_cycles = random.randint(1, 4)
                for _ in range(havoc_cycles):
                    m_len = len(mutated)
                    if m_len == 0: break
                    op = random.randint(0, 2)

                    if op == 0:
                        pos = random.randint(0, m_len - 1)
                        mutated[pos] = random.randint(0, 255)
                    elif op == 1:
                        if m_len > 2:
                            del_len = random.randint(1, min(m_len, 4))
                            pos = random.randint(0, m_len - del_len)
                            del mutated[pos:pos + del_len]
                    elif op == 2:
                        pos = random.randint(0, m_len)
                        insert_len = random.randint(1, 4)
                        to_insert = bytearray(random.getrandbits(8) for _ in range(insert_len))
                        mutated[pos:pos] = to_insert

            elif strategy == 4:
                if len(population.queue) > 1:
                    target = random.choice(population.queue)
                    if target.data and len(target.data) > 1 and len(mutated) > 1:
                        target_data = target.data
                        split_at_1 = random.randint(1, len(mutated) - 1)
                        split_at_2 = random.randint(1, len(target_data) - 1)
                        mutated = mutated[:split_at_1] + target_data[split_at_2:]

            results.append(bytes(mutated))
        
        return results

class AFLPlusPlusMutator(Mutator):
    def __init__(self):
        self.INTERESTING_8 = [
            -128, -1, 0, 1, 16, 32, 64, 100, 127
        ]
        self.INTERESTING_16 = [
            -32768, -129, 128, 255, 256, 512, 1000, 1024, 4096, 32767
        ]
        self.INTERESTING_32 = [
            -2147483648, -100663046, -32769, 32768, 65535, 65536, 100663045, 2147483647
        ]
        self.HAVOC_CYCLES = 1024  # 基础 havoc 循环次数
        self.HAVOC_DIV = 8        # havoc 除数
        self.HAVOC_MIN = 16       # 最小 havoc 次数
        self.ARITH_MAX = 35        # 算术操作最大值

    def _calculate_mutation_score(self, seed: Seed) -> float:
        """
        根据 seed 的属性计算变异分数，类似 AFL++ 的 perf_score。
        分数越高，变异次数越多。
        """
        score = 100.0  # 基础分数
        
        # 1. Favored 种子给予奖励
        if seed.favored:
            score *= 2.5
        
        # 2. 执行时间短（执行快）的种子给予奖励
        if seed.exec_time_ns > 0 and seed.exec_time_ns < 1_000_000_000:
            if seed.exec_time_ns < 10_000_000:  # < 10ms
                score *= 1.3
            elif seed.exec_time_ns > 100_000_000:  # > 100ms
                score *= 0.7
        
        # 3. 覆盖密度大的种子给予奖励
        if seed.bitmap_size > 500:
            score *= 1.3
        elif seed.bitmap_size < 50:
            score *= 0.7
        
        # 4. 产生新覆盖多的种子给予奖励
        if seed.total_new_coverage > 0:
            score *= (1.0 + math.log(1 + seed.total_new_coverage) / 10.0)
        
        # 5. 深度浅的种子给予奖励（更接近初始种子）
        if seed.depth == 0:
            score *= 1.2
        elif seed.depth > 0:
            score *= (1.0 / (1.0 + seed.depth * 0.1))
        
        # 6. 执行次数少的种子给予奖励（还未充分探索）
        if seed.execs == 0:
            score *= 1.2
        elif seed.execs > 4:
            # 已执行多次的种子，分数衰减
            decay = 1.0 / math.log(seed.execs, 4)
            score *= max(0.2, decay)
        
        return max(10.0, score)  # 确保最小分数

    def _determine_havoc_cycles(self, seed: Seed, base_power: int) -> int:
        """
        根据 seed 的分数和 base_power 决定 havoc 阶段的变异次数。
        类似 AFL++: stage_max = (HAVOC_CYCLES * perf_score / havoc_div) >> 8
        """
        score = self._calculate_mutation_score(seed)
        
        # 基础变异次数由 power_scheduler 决定
        # 但我们可以根据 score 调整
        adjusted_power = int((score / 100.0) * base_power)
        
        # 对于高质量种子，增加变异次数
        if seed.favored and seed.execs < 10:
            adjusted_power = int(adjusted_power * 1.5)
        
        return max(self.HAVOC_MIN, adjusted_power)

    def _determine_stack_power(self, seed: Seed, data_len: int) -> int:
        """
        决定每次 havoc 操作的堆叠次数（类似 AFL++ 的 stack_max）。
        高质量种子可以使用更多堆叠操作。
        """
        base_pow2 = 1  # 基础是 2^1 = 2 次操作
        
        # 根据种子质量调整
        if seed.favored:
            base_pow2 = 2  # 2^2 = 4 次操作
        elif seed.exec_time_ns < 10_000_000:  # 执行快的种子
            base_pow2 = 2
        
        # 根据数据长度调整
        if data_len < 64:
            base_pow2 = max(0, base_pow2 - 1)
        elif data_len > 8096:
            base_pow2 += 1
        
        return 1 << (1 + random.randint(0, base_pow2))

    def _select_mutation_strategy(self, seed: Seed) -> int:
        """
        根据 seed 属性智能选择变异策略。
        """
        # 如果种子执行时间短，可以尝试更复杂的操作
        if seed.exec_time_ns > 0 and seed.exec_time_ns < 10_000_000:
            # 执行快的种子，增加 havoc 和 splice 的概率
            weights = [0.15, 0.15, 0.15, 0.35, 0.20]  # bitflip, arith, interest, havoc, splice
        elif seed.favored:
            # Favored 种子，增加 havoc 概率
            weights = [0.20, 0.20, 0.15, 0.35, 0.10]
        elif seed.depth == 0:
            # 初始种子，尝试更多基础操作
            weights = [0.25, 0.25, 0.25, 0.20, 0.05]
        else:
            # 默认权重
            weights = [0.20, 0.20, 0.20, 0.30, 0.10]
        
        return random.choices(range(5), weights=weights)[0]

    def mutate(self, seed: Seed, population: SeedQueue, power: int = 5) -> List[bytes]:
        """
        智能变异：根据 seed 的属性调整变异策略和次数。
        """
        seed_data = bytearray(seed.data)
        if not seed_data:
            return []

        results = []
        length = len(seed_data)
        
        # 根据 seed 属性决定实际变异次数
        actual_power = self._determine_havoc_cycles(seed, power)
        
        for _ in range(actual_power):
            mutated = seed_data.copy()

            # 智能选择变异策略
            strategy = self._select_mutation_strategy(seed)

            # --- 策略 1: BitFlip (位翻转) ---
            if strategy == 0:
                pos = random.randint(0, length - 1)
                bit = random.randint(0, 7)
                mutated[pos] ^= (1 << bit)

            # --- 策略 2: Arithmetic (算术加减) ---
            elif strategy == 1:
                pos = random.randint(0, length - 1)
                val = random.randint(1, self.ARITH_MAX)
                if random.choice([True, False]):
                    mutated[pos] = (mutated[pos] + val) % 256
                else:
                    mutated[pos] = (mutated[pos] - val) % 256

            # --- 策略 3: Interest (感兴趣数值替换) ---
            elif strategy == 2:
                width = random.choice([1, 2, 4])
                if length >= width:
                    pos = random.randint(0, length - width)
                    if width == 1:
                        val = random.choice(self.INTERESTING_8)
                        mutated[pos] = val & 0xFF
                    elif width == 2:
                        val = random.choice(self.INTERESTING_16)
                        new_bytes = struct.pack('<h', val)
                        mutated[pos:pos + 2] = new_bytes
                    elif width == 4:
                        val = random.choice(self.INTERESTING_32)
                        new_bytes = struct.pack('<i', val)
                        mutated[pos:pos + 4] = new_bytes

            # --- 策略 4: Havoc (随机大破坏)---
            elif strategy == 3:
                # 根据种子质量决定堆叠次数
                stack_power = self._determine_stack_power(seed, length)
                
                for _ in range(stack_power):
                    m_len = len(mutated)
                    if m_len == 0:
                        break
                    
                    # 根据种子属性选择操作类型
                    if seed.exec_time_ns < 10_000_000 and m_len > 4:
                        # 执行快的种子，可以尝试更复杂的操作
                        op = random.randint(0, 4)
                    else:
                        op = random.randint(0, 2)
                    
                    if op == 0:  # 随机替换字节
                        pos = random.randint(0, m_len - 1)
                        mutated[pos] = random.randint(0, 255)
                    elif op == 1:  # 随机删除一段
                        if m_len > 2:
                            max_del = max(1, min(m_len // 4, 4))
                            del_len = random.randint(1, max_del)
                            pos = random.randint(0, m_len - del_len)
                            del mutated[pos:pos + del_len]
                    elif op == 2:  # 随机插入一段
                        pos = random.randint(0, m_len)
                        max_insert = max(1, min(4, m_len // 4))
                        insert_len = random.randint(1, max_insert)
                        to_insert = bytearray(random.getrandbits(8) for _ in range(insert_len))
                        mutated[pos:pos] = to_insert
                    elif op == 3:  # 字节交换（仅对执行快的种子）
                        if m_len >= 2:
                            i = random.randint(0, m_len - 1)
                            j = random.randint(0, m_len - 1)
                            mutated[i], mutated[j] = mutated[j], mutated[i]
                    elif op == 4:  # 块复制（仅对执行快的种子）
                        if m_len >= 4:
                            max_copy = max(1, min(m_len // 4, 4))
                            copy_len = random.randint(1, max_copy)
                            src = random.randint(0, m_len - copy_len)
                            dst = random.randint(0, m_len - copy_len)
                            if src != dst:
                                mutated[dst:dst + copy_len] = mutated[src:src + copy_len]

            # --- 策略 5: Splice (拼接) ---
            elif strategy == 4:
                if len(population.queue) > 1:
                    # 优先选择 favored 或高质量的种子进行拼接
                    candidates = [s for s in population.queue 
                                 if s.data and len(s.data) > 1 
                                 and s != seed]
                    
                    if candidates:
                        # 如果有 favored 种子，优先选择
                        favored_candidates = [s for s in candidates if s.favored]
                        if favored_candidates and random.random() < 0.7:
                            target = random.choice(favored_candidates)
                        else:
                            target = random.choice(candidates)
                        
                        target_data = target.data
                        if len(mutated) > 1 and len(target_data) > 1:
                            # 根据种子深度调整拼接策略
                            if seed.depth == 0:
                                # 初始种子，保守拼接
                                split_at_1 = random.randint(1, len(mutated) - 1)
                                split_at_2 = random.randint(1, len(target_data) - 1)
                                mutated = mutated[:split_at_1] + target_data[split_at_2:]
                            else:
                                # 深度种子，可以更激进的拼接
                                split_at_1 = random.randint(0, len(mutated))
                                split_at_2 = random.randint(0, len(target_data))
                                mutated = mutated[:split_at_1] + target_data[split_at_2:]

            results.append(bytes(mutated))

        return results