# 简易 Python 模糊测试器（Fuzzer）
这是一个轻量级、基于路径反馈的模糊测试工具，用 Python 实现，灵感来源于 AFL。它通过变异输入种子、执行目标程序、监控崩溃，并利用标准输出模拟覆盖率反馈，自动发现新路径和漏洞。

## 项目结构
```
.
├── Makefile
├── scripts                 # 脚本
├── Dockerfile
├── README.md
├── devlog.md
├── main.py                 # 模糊器入口
├── targets/                # 测试目标
├── test_program/
│   └── target.c            # 示例测试目标源码
├── seeds/                  # 初始测试用例（需手动放入种子）
├── crashes/                # 崩溃输入保存目录（自动生成）
├── output/                 # 统计图表
└── fuzzer/                 # 核心模块
    ├── config.py           # 配置参数
    ├── evaluator.py        # 评估组件
    ├── executor.py         # 执行组件
    ├── mutator.py          # 变异组件
    ├── scheduler.py        # 种子选择组件与调度组件
    ├── seed.py             # 种子结构
    ├── fuzzer.py           # 主模糊循环
    └── utils.py            # 工具函数与结构
```
## 环境准备
1. 构建镜像
```bash
docker pull aflplusplus/aflplusplus
```
或者使用Dockerfile
```bash
docker build -t my-afl-fuzzer .
```

2. 交互式运行
```bash
docker run -it --rm \
  -v "$(pwd)":/src \
  -w /src \
  aflplusplus/aflplusplus \
  bash
```

## 运行示例目标
- 编译并运行模糊器
```bash
make quick-test
```
模糊器将：
从 seeds/ 加载初始种子
最多执行 10,000 次 变异测试
自动保存触发崩溃的输入到 crashes/
运行结束后打印统计摘要并退出
查看结果
```bash
ls crashes/        # 查看发现的崩溃用例
cat crashes/*      # 查看具体崩溃输入内容
```
## 运行目标

```bash
maks TARGET=TXX fuzz
```
模糊器将:识别目标名字TNAME,编译目标到targets/build文件夹，从seeds/$TNAME中获取种子，将崩溃输出到crash/$TNAME，将图表输出到output/$TNAME。

## Makefile 命令
| 命令 | 说明 |
|------|------|
| make TARGET=TXX fuzz | 编译第XX个目标程序并启动模糊测试 |
| make setup | 创建 seeds/ 和 crashes/ 目录 |
| make quick-test | 进行一次简单的测试 |
| make clean-crash | 删除所有已保存的崩溃文件 |
| make clean | 清理二进制文件和崩溃记录 |

## 配置参数  
修改 fuzzer/config.py 可调整：
- 总执行次数（MAX_EXECUTIONS）
- 单次执行超时（TIMEOUT_SEC）
- 总执行时间（DEFAULT_TOTAL_TIMEOUT）

## 未来任务
- 完善现有框架
- 完成十个样例的脚本