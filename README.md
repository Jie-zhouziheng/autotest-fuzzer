# 简易 Python 模糊测试器（Fuzzer）

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
  my-afl-fuzzer-test \
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
# 使用默认配置（1小时，超时2秒，队列500）
make TARGET=T10 fuzz

# 自定义所有参数
make TARGET=T10 fuzz TIME=86400 TIMEOUT=5 QUEUE=1000
```

**参数说明：**
- `TIME`: 总运行时间（秒），默认 3600（1小时）
- `TIMEOUT`: 单次执行超时（秒），默认 2
- `QUEUE`: 最大队列大小，默认 500

#### 通过环境变量配置

```bash
export FUZZ_TOTAL_TIMEOUT=86400    # 总运行时间（秒）
export FUZZ_TIMEOUT_SEC=5          # 单次执行超时（秒）
export FUZZ_MAX_QUEUE_SIZE=1000   # 最大队列大小
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

## Makefile 命令

| 命令 | 说明 |
|------|------|
| `make TARGET=TXX fuzz` | 编译目标并启动模糊测试 |
| `make TARGET=TXX fuzz TIME=86400 TIMEOUT=5 QUEUE=1000` | 带自定义参数的模糊测试 |
| `make TARGET=TXX analysis` | 性能分析（cProfile） |
| `make TARGET=TXX build` | 仅编译目标程序 |
| `make TARGET=TXX setup` | 创建输出目录 |
| `make quick-test` | 运行示例目标快速测试 |
| `make clean` | 清理所有二进制文件和输出 |
| `make clean-results` | 仅清理测试结果（保留二进制） |
| `make install` | 安装 Python 依赖 |

## 配置说明

所有配置参数在 `fuzzer/config.py` 中定义，支持通过环境变量覆盖：

| 环境变量 | 说明 | 默认值 |
|---------|------|--------|
| `FUZZ_TARGET_PATH` | 目标程序路径 | `./target_program` |
| `FUZZ_TARGET_CMD` | 目标程序命令行参数 | `""` |
| `FUZZ_SEEDS_DIR` | 种子目录 | `./seeds/test` |
| `FUZZ_OUTPUT_DIR` | 输出目录 | `./output/test` |
| `FUZZ_TIMEOUT_SEC` | 单次执行超时（秒） | `2` |
| `FUZZ_MAX_QUEUE_SIZE` | 最大队列大小 | `500` |
| `FUZZ_TOTAL_TIMEOUT` | 总运行时间（秒） | `86400` (24小时) |
| `FUZZ_MAX_EXECUTIONS` | 最大执行次数 | `500` |

## 注意事项

1. **种子文件**: 确保在 `seeds/{target_name}/` 目录中有有效的初始种子文件
2. **目标编译**: 目标程序需要使用 `afl-cc` 或 `afl-c++` 编译以启用覆盖率插桩
3. **长时间运行**: 建议使用 `screen` 或 `tmux` 运行长时间测试
4. **资源监控**: 长时间运行请监控磁盘空间和内存使用情况