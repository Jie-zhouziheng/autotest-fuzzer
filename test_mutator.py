import sys
import os
import struct

# 1. 确保能导入 fuzzer 模块
sys.path.append(os.getcwd())

try:
    # 尝试导入你的类
    from fuzzer.mutator import Mutator
    from fuzzer.seed import Seed
except ImportError:
    # 如果还没有编写 Seed 类，这里提供一个 Mock (模拟) 类以便测试 Mutator
    class Seed:
        def __init__(self, data):
            self.data = data
            self.energy = 1


    print("Warning: 使用 Mock Seed 类进行测试")


def test_mutator():
    print("=== 开始测试 Mutator 组件 ===")

    # 初始化
    mutator = Mutator()

    # 准备测试数据
    original_data = b"Hello World"
    seed = Seed(original_data)

    # 准备 Population (用于测试 Splice)
    # 创建几个完全不同的种子，方便观察拼接效果
    pop_seed1 = Seed(b"AAAAAAAAAAAAAAAAAAAA")
    pop_seed2 = Seed(b"BBBBBBBBBBBBBBBBBBBB")
    population = [pop_seed1, pop_seed2]

    print(f"原始数据: {original_data}")

    # --- 测试 1: 基础变异生成 ---
    print("\n[Test 1] 生成 10 个变异体...")
    mutated_list = mutator.mutate(seed, population, power=10)

    assert len(mutated_list) == 10, "生成的变异体数量不正确"

    diff_count = 0
    for idx, m_data in enumerate(mutated_list):
        if m_data != original_data:
            diff_count += 1
        # 简单打印前3个看看效果
        if idx < 3:
            print(f"  变异体 {idx}: {m_data}")

    if diff_count > 0:
        print(f"  √ 成功生成了 {diff_count} 个不同的数据")
    else:
        print("  x 警告：所有变异体都和原数据一样（如果是概率问题请多跑几次）")

    # --- 测试 2: 边界值 (Interest) ---
    # 我们没法强制指定策略，但可以通过跑很多次来撞概率
    print("\n[Test 2] 检查特殊值插入 (Interest/Arithmetic)...")
    found_special = False

    # 跑 100 次，只要发现长度变了(Havoc插入/删除) 或者 含有特殊字符
    for _ in range(100):
        res = mutator.mutate(seed, population, power=1)[0]
        # 检查是否包含了一些特殊整数的字节表现，例如 0xFF, 0x7F 等
        if b'\xff' in res or b'\x00' in res or b'\x80' in res:
            found_special = True
            break

    if found_special:
        print("  √ 检测到特殊值变异")
    else:
        print("  ? 未检测到明显特殊值 (属于概率事件)")

    # --- 测试 3: 拼接 (Splice) ---
    print("\n[Test 3] 检查拼接 (Splice)...")
    # 为了测试拼接，我们传入一个非常独特的种子作为 population
    target_pattern = b"BBBB"
    found_splice = False

    for _ in range(200):  # 增加次数以命中 Splice 策略
        res_list = mutator.mutate(seed, population, power=1)
        res = res_list[0]
        # 如果结果里既有原始数据的特征，又有 population 的特征
        if b"Hello" in res and b"AAAA" in res:
            print(f"  √ 捕捉到拼接: {res}")
            found_splice = True
            break
        if b"Hello" in res and b"BBBB" in res:
            print(f"  √ 捕捉到拼接: {res}")
            found_splice = True
            break

    if not found_splice:
        print("  ? 未捕捉到拼接 (Splice 概率较低，属正常)")

    # --- 测试 4: 空输入处理 ---
    print("\n[Test 4] 测试空种子...")
    empty_seed = Seed(b"")
    res = mutator.mutate(empty_seed, population, power=5)
    if res == []:
        print("  √ 空种子返回空列表，处理正确")
    else:
        print(f"  x 空种子处理异常: {res}")


if __name__ == "__main__":
    test_mutator()