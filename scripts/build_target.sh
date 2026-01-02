#!/bin/bash
# scripts/build_target.sh

# 1. 接收参数
SRC_DIR=$1       # 例如: target/binutils-2.28
TARGET_NAME=$2   # 例如: cxxfilt
OUTPUT_BIN=$3    # 例如: target/build/cxxfilt

echo "--- [Build Script] Building $TARGET_NAME ---"
echo "Source: $SRC_DIR"
echo "Output: $OUTPUT_BIN"

# 检查编译器
export CC=afl-cc
export CXX=afl-c++

# 2. 准备目录
mkdir -p $(dirname "$OUTPUT_BIN")

# 3. 进入源码目录进行构建
# 注意：Binutils 建议在源码外构建，或者直接在源码内 configure
cd "$SRC_DIR" || exit 1

# 如果没有 Makefile，则运行 configure (静态链接方便 fuzz)
if [ ! -f Makefile ]; then
    echo "Configuring..."
    ./configure --disable-shared CFLAGS="-static" CXXFLAGS="-static" > /dev/null 2>&1
fi

# 4. 编译特定目标 (利用 make -j 加速)
echo "Compiling..."
make -j$(nproc) > /dev/null 2>&1

# 5. 查找并移动生成的二进制文件
# binutils 中 cxxfilt 通常生成在 binutils/cxxfilt
BUILT_FILE="binutils/$TARGET_NAME"

# 处理可能不在子目录的情况（针对不同项目）
if [ ! -f "$BUILT_FILE" ]; then
    BUILT_FILE="$TARGET_NAME"
fi

if [ -f "$BUILT_FILE" ]; then
    # 回到项目根目录层级来复制文件 (或者直接用绝对路径)
    cp "$BUILT_FILE" "$OUTPUT_BIN"
    echo "✅ Build Success: $OUTPUT_BIN created."
else
    echo "❌ Build Failed: Could not find compiled binary '$BUILT_FILE'"
    exit 1
fi