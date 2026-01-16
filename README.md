# 简易 Python 模糊测试器

这是一个轻量级、基于覆盖率引导的模糊测试工具，用 Python 实现，参考 AFL++ 的设计思想。它通过变异输入种子、执行目标程序、监控覆盖率反馈，自动发现新路径和漏洞。

## 项目结构

```
.
├── Makefile                # 构建和运行脚本
├── scripts/                # 构建脚本
│   └── build_target.sh    # 目标程序编译脚本
├── Dockerfile              # Docker 镜像配置
├── README.md               # 本文件
├── devlog.md               # 开发日志
├── main.py                 # 模糊器入口程序
├── targets/                # 测试目标程序源码
├── test_program/           # 示例测试目标
│   └── target.c
├── seeds/                  # 初始测试用例（种子文件）
├── output/                 # 测试输出目录
└── fuzzer/                 # 核心模块
    ├── config.py           # 配置参数（支持环境变量）
    ├── fuzzer.py           # 主模糊循环
    ├── executor.py         # 测试执行组件
    ├── mutator.py          # 变异组件
    ├── scheduler.py        # 种子选择与能量调度组件
    ├── seed.py             # 种子数据结构与队列
    ├── monitor.py          # 覆盖率监控组件
    ├── evaluator.py        # 评估与报告生成组件
    └── utils.py            # 工具函数与数据结构
```
## 环境准备

### 1，使用 Docker

#### 1. 构建 Docker 镜像

```bash
# 使用项目提供的 Dockerfile
docker build -t my-afl-fuzzer .

# 或使用官方 AFL++ 镜像
docker pull aflplusplus/aflplusplus
```

#### 2. 运行容器

```bash
# 交互式运行（推荐用于开发和测试）
docker run -it --rm \
  -v "$(pwd)":/src \
  -w /src \
  my-afl-fuzzer \
  bash

# 或使用官方镜像
docker run -it --rm \
  -v "$(pwd)":/src \
  -w /src \
  aflplusplus/aflplusplus \
  bash
```

### 2.本地部署

如果需要在本地系统直接运行，需要手动安装所有依赖。

#### 1. 安装系统依赖

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y \
    build-essential \
    python3 \
    python3-pip \
    python3-dev \
    git \
    wget \
    clang \
    libtool-bin \
    automake \
    pkg-config \
    autoconf \
    cmake \
    libfreetype6-dev \
    libpng-dev \
    libxft-dev \
    libpcap-dev
```

#### 2. 安装 Python 依赖

```bash
pip3 install sysv-ipc matplotlib numpy

# 或使用 Makefile
make install
```

#### 3. 编译安装 AFL++

```bash
git clone https://github.com/AFLplusplus/AFLplusplus.git
cd AFLplusplus
make distrib
sudo make install
# 验证
afl-cc --version
```

#### 4. 准备种子文件

将初始测试用例放入 `seeds/{target_name}/` 目录中。例如：
- `seeds/tcpdump/` - tcpdump 的种子文件
- `seeds/objdump/` - objdump 的种子文件

## 使用方法

### 快速开始

#### 1. 运行示例目标（快速测试）

```bash
make quick-test
```

这会编译 `test_program/target.c` 并运行一次简短的模糊测试。

#### 2. 运行预定义目标

```bash
# 运行 T01 (cxxfilt)
make TARGET=T01 fuzz

# 运行 T10 (tcpdump)
make TARGET=T10 fuzz
```

**支持的目标：**
- `T01`: cxxfilt
- `T02`: readelf
- `T03`: nm-new
- `T04`: objdump
- `T05`: djpeg
- `T06`: readpng
- `T07`: xmllint
- `T08`: lua
- `T09`: mjs
- `T10`: tcpdump

### 配置参数

#### 通过 Makefile 参数配置

```bash
# 使用默认配置（1小时，超时2秒）
make TARGET=T10 fuzz

# 自定义所有参数
make TARGET=T10 fuzz TIME=86400 TIMEOUT=5
```

**参数说明：**
- `TIME`: 总运行时间（秒），默认 86400 
- `TIMEOUT`: 单次执行超时（秒），默认 2

#### 通过环境变量配置

```bash
export FUZZ_TOTAL_TIMEOUT=86400    # 总运行时间（秒）
export FUZZ_TIMEOUT_SEC=5          # 单次执行超时（秒）
export FUZZ_TARGET_PATH=/path/to/target
export FUZZ_TARGET_CMD="-nr @@"
export FUZZ_SEEDS_DIR=/path/to/seeds
export FUZZ_OUTPUT_DIR=/path/to/output

python3 main.py
```

### 输出说明

运行后，结果保存在 `output/{target_name}/` 目录：

- **`crashes/`**: 触发崩溃的输入文件
- **`hangs/`**: 触发超时的输入文件
- **`queue/`**: 发现新覆盖的输入文件
- **`plot_data/`**: 
  - `logfile.txt`: CSV 格式的统计数据
  - `coverage_curve.png`: 覆盖率增长曲线
  - `crash_curve.png`: 崩溃发现曲线
  - `exec_speed_curve.png`：执行速度曲线
  - `queue_size_curve.png`：队列大小曲线
  - `hang_curve.png`: 超时数量曲线（若有hang）
  - `fuzzer_stats`：最终状态

## Makefile 命令

| 命令 | 说明 |
|------|------|
| `make TARGET=TXX fuzz` | 编译目标并启动模糊测试 |
| `make TARGET=TXX fuzz TIME=86400 TIMEOUT=5` | 带自定义参数的模糊测试 |
| `make TARGET=TXX build` | 仅编译目标程序 |
| `make TARGET=TXX setup` | 创建输出目录 |
| `make quick-test` | 运行示例目标快速测试 |
| `make clean` | 清理所有二进制文件和输出 |
| `make clean-results` | 仅清理测试结果（保留二进制） |

## 配置说明

所有配置参数在 `fuzzer/config.py` 中定义，支持通过环境变量覆盖：

| 环境变量 | 说明 | 默认值 |
|---------|------|--------|
| `FUZZ_TARGET_PATH` | 目标程序路径 | `./target_program` |
| `FUZZ_TARGET_CMD` | 目标程序命令行参数 | `""` |
| `FUZZ_SEEDS_DIR` | 种子目录 | `./seeds/test` |
| `FUZZ_OUTPUT_DIR` | 输出目录 | `./output/test` |
| `FUZZ_TIMEOUT_SEC` | 单次执行超时（秒） | `2` |
| `FUZZ_TOTAL_TIMEOUT` | 总运行时间（秒） | `86400` (24小时) |

## 项目设计方案

### 系统架构

本工具采用模块化设计，核心组件包括：

1. **插装组件**：使用 AFL++ 的 `afl-cc` 编译器对目标程序进行插装
2. **测试执行组件**：负责运行插装后的目标程序并收集执行结果
3. **执行结果监控组件**：分析覆盖率反馈，识别新路径、崩溃和超时
4. **变异组件**：对种子进行多种策略的变异操作
5. **种子排序组件**：从种子队列中选择下一个要变异的种子
6. **能量调度组件**：为每个种子分配变异次数（能量）
7. **评估组件**：统计运行结果并生成可视化报告

### 工作流程

```
0. 编译并插装目标程序（使用 afl-cc）

1. 初始化阶段（main.py）
   ├─ 加载初始种子文件
   ├─ 初始化fuzzer

2. 主循环（Fuzzing Loop）
   ├─ 种子选择：从队列中选择一个种子
   ├─ 能量分配：为种子计算变异次数
   ├─ 变异生成：对种子进行变异，生成多个测试用例
   ├─ 执行测试：运行目标程序，收集覆盖率信息
   ├─ 结果分析：判断是否发现新路径、崩溃或超时
   └─ 队列更新：将发现新路径的输入加入队列

3. 结束阶段
   ├─ 生成统计报告
   ├─ 绘制覆盖率曲线等图表
   └─ 保存所有发现的崩溃和超时输入
```

### 类层次结构

```
Fuzzer (主控制器)
├── SeedQueue (种子队列管理)
│   └── Seed (种子数据结构)
├── SeedScheduler (种子选择策略)
│   ├── RoundRobinScheduler 
│   ├── AFLSmartScheduler 
│   └── AFLPlusPlusScheduler 
├── PowerScheduler (能量调度策略)
│   ├── SimplePowerScheduler
│   └── AFLPowerScheduler 
├── Mutator（变异策略）
│   ├── RanDomMutator
│   └── AFLPlusPlusMutator
├── Executor (测试执行)
├── CoverageMonitor (覆盖率监控)
└── FuzzEvaluator (评估与报告)
```

## 核心组件说明

### 1. 测试执行组件 (Executor)

**功能**：运行插装后的目标程序，传递测试输入，并收集执行结果和覆盖率反馈。

**主要特性**：
- 支持文件参数模式（`@@`）和标准输入模式
- 通过共享内存读取覆盖率 bitmap
- 检测程序崩溃（异常退出）和超时

### 2. 执行结果监控组件 (CoverageMonitor)

**功能**：分析每次执行的覆盖率反馈，识别新发现的代码路径、崩溃和超时。

**主要功能**：
- 解析覆盖率 bitmap，提取边覆盖信息
- 判断是否发现新的代码路径
- 统计崩溃和超时数量
- 实时显示运行状态（类似 AFL++ 的状态面板）
- 记录运行日志（CSV 格式）

### 3. 变异组件 (Mutator)

**功能**：对种子进行变异，生成新的测试用例。

**变异策略**：
- **BitFlip**：位翻转
- **Arithmetic**：算术运算（加减）
- **Interest**：替换为特殊数值（边界值）
- **Havoc**：随机破坏（替换、删除、插入字节）
- **Splice**：拼接两个种子

**实现**：提供 `RanDomMutator`和 `AFLPlusPlusMutator`

### 5. 种子排序组件 (SeedScheduler)

**功能**：从种子队列中选择下一个要变异的种子。

**实现策略**：
- **RoundRobinScheduler**：按入队顺序轮询选择
- **AFLSmartScheduler**：优先选择 favored 种子，在 favored 种子中选择质量更好的
- **AFLPlusPlusScheduler**：参考 AFL++ 策略
  - 优先选择 execs 最小的 favored 种子
  - 从 favored 种子中加权随机选择
  - 从非 disabled 种子中加权随机选择

### 6. 能量调度组件 (PowerScheduler)

**功能**：为每个种子分配变异次数（能量），决定对该种子进行多少次变异操作。

**实现策略**：
- **SimplePowerScheduler**：基于 favored 状态和执行次数简单分配
- **AFLPowerScheduler**：启发式调度，考虑以下因素：
  - 执行速度（执行时间短 → 更多能量）
  - 覆盖范围（覆盖边数多 → 更多能量）
  - Favored 状态（favored 种子 → 更多能量）
  - 执行次数（已执行多次 → 能量衰减）

### 7. 评估组件 (FuzzEvaluator)

**功能**：统计模糊测试的运行结果，生成可视化报告和统计图表。

**输出内容**：
- **统计信息**：总执行次数、执行速度、发现的崩溃/超时数量、唯一路径数等
- **可视化图表**：
  - 覆盖率增长曲线（覆盖边数随时间变化）
  - 崩溃发现曲线
  - 执行速度曲线
  - 队列大小曲线
- **数据文件**：
  - `logfile.txt`：CSV 格式的运行日志
  - `fuzzer_stats`：最终统计信息（AFL++ 格式）
