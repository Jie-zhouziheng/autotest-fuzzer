# 简易 Python 模糊测试器（Fuzzer）
这是一个轻量级、基于路径反馈的模糊测试工具，用 Python 实现，灵感来源于 AFL。它通过变异输入种子、执行目标程序、监控崩溃，并利用标准输出模拟覆盖率反馈，自动发现新路径和漏洞。

## 项目结构
```
.
├── Makefile
├── main.py                 # 模糊器入口
├── target_program          # 目标程序二进制（自动生成）
├── test_program/
│   └── target.c            # 含漏洞的目标程序源码
├── seeds/                  # 初始测试用例（需手动放入种子）
├── crashes/                # 崩溃输入保存目录（自动生成）
└── fuzzer/                 # 核心模块
    ├── config.py           # 配置参数
    ├── executor.py         # 执行目标程序
    ├── mutator.py          # 输入变异逻辑
    ├── scheduler.py        # 种子调度策略
    ├── seed.py             # 种子数据结构
    ├── fuzzer.py           # 主模糊循环
    └── utils.py            # 工具函数
```
## 快速开始
- 准备环境
    仅需 Python 3.8+ 和 GCC，无需额外依赖。
- 编译并运行模糊器
```bash
make fuzz
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
## Makefile 命令
| 命令 | 说明 |
|------|------|
| make fuzz | 编译目标程序并启动模糊测试 |
| make setup | 创建 seeds/ 和 crashes/ 目录 |
| make quick-test | 清除旧崩溃记录并重新运行 |
| make clean-crash | 删除所有已保存的崩溃文件 |
| make clean | 清理二进制文件和崩溃记录 |

## 配置参数  
修改 fuzzer/config.py 可调整：
- 总执行次数（MAX_EXECUTIONS）
- 单次执行超时（TIMEOUT_SEC）
- 队列大小限制、变异强度等

## 未来任务
- 使用afl++的seed
- 利用afl-cc编译target
- 完成执行结果监控组件
- 完成评估组件
- 完善已有框架