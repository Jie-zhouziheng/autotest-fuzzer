#!/bin/bash

SRC_DIR="$1"
TARGET_NAME="$2"
OUTPUT_BIN="$3"

echo "--- [Build Script] Building $TARGET_NAME ---"
echo "Source: $SRC_DIR"
echo "Output: $OUTPUT_BIN"

# 1. 检查参数
if [ -z "$SRC_DIR" ] || [ -z "$TARGET_NAME" ] || [ -z "$OUTPUT_BIN" ]; then
    echo "❌ Error: Missing arguments. (SRC=$SRC_DIR, NAME=$TARGET_NAME, OUT=$OUTPUT_BIN)"
    exit 1
fi

export CC=afl-cc
export CXX=afl-c++
export AFL_HARDEN=1

# 2. 进入目录并确保输出目录存在
pushd "$SRC_DIR" || { echo "❌ Error: Cannot enter $SRC_DIR"; exit 1; }
mkdir -p "$(dirname "$OUTPUT_BIN")"

# 3. 检查产物是否已存在
if [ -f "$OUTPUT_BIN" ]; then
    echo "♻️  Found pre-built binary at $OUTPUT_BIN. Skipping build process."
    # 检查是否包含 AFL 插装符号
    if nm "$OUTPUT_BIN" 2>/dev/null | grep -q "__afl_area_ptr"; then
        echo "🛡️  Verified: Pre-built binary is instrumented."
    else
        echo "⚠️  Warning: Pre-built binary found but might NOT be instrumented."
    fi
    popd > /dev/null
    exit 0
fi

# 4. 针对不同项目的构建逻辑
BUILT_FILE=""

if [[ "$SRC_DIR" == *"binutils"* ]]; then
    # T01-T04: binutils
    echo "🔧 Building binutils with global static config..."
    if [ ! -f Makefile ]; then
        echo "  [1/2] Configuring..."
        ./configure --disable-shared CFLAGS="-g -static" CXXFLAGS="-g -static" > /dev/null 2>&1
    fi
    echo "  [2/2] Compiling (this may take a while)..."
    make -j$(nproc) > /dev/null 2>&1

    BUILT_FILE="binutils/$TARGET_NAME"

elif [[ "$SRC_DIR" == *"libjpeg"* ]]; then
    # T05: libjpeg-turbo
    cmake -G "Unix Makefiles" -DCMAKE_C_COMPILER=afl-cc -DENABLE_SHARED=OFF .
    make -j$(nproc) djpeg-static
    BUILT_FILE="djpeg-static"

elif [[ "$SRC_DIR" == *"lua"* ]]; then
    # T08: lua
    make clean
    make -j$(nproc) CC="$CC" linux
    BUILT_FILE="src/lua"

elif [[ "$SRC_DIR" == *"mjs"* ]]; then
    # T09: mjs
    rm -f mjs
    $CC -DMJS_MAIN mjs.c -ldl -g -o mjs
    BUILT_FILE="mjs"

elif [[ "$SRC_DIR" == *"tcpdump"* ]]; then
    # T10: tcpdump
    echo "🔧 Preparing tcpdump (Dynamic Link Mode)..."
    if [ ! -f configure ]; then
        ./autogen.sh || autoreconf -ivf
    fi
    ./configure CFLAGS="-g" CC="$CC"
    make clean
    make -j$(nproc)
    BUILT_FILE="tcpdump"

else
    # T06 (readpng)
    if [[ "$TARGET_NAME" == "readpng" ]]; then
        # 1. 编译 libpng 静态库
        [ ! -f Makefile ] && ./configure --disable-shared CFLAGS="-g"
        make clean
        make -j$(nproc)
        # 2. 手动链接：核心库用静态 (.a)，系统库用动态 (-lz -lm)
        $CC -o readpng ./contrib/libtests/readpng.c ./.libs/libpng16.a -lz -lm
        BUILT_FILE="readpng"
    else
    # T07: xmllint
        echo "🔧 Preparing libxml2 (T07)..."
        if [ ! -f configure ]; then
            NOCONFIGURE=1 ./autogen.sh || autoreconf -ivf
        fi
        
        [ ! -f Makefile ] && ./configure --disable-shared --without-python CFLAGS="-g -static"
        make clean
        make -j$(nproc)
        
        if [ -f "xmllint" ]; then
            BUILT_FILE="xmllint"
        else
            BUILT_FILE=".libs/xmllint"
        fi
    fi
fi

# --- 5. 交付产物 ---
if [ -n "$BUILT_FILE" ] && [ -f "$BUILT_FILE" ]; then
    # 统一使用 OUTPUT_BIN
    cp "$BUILT_FILE" "$OUTPUT_BIN"
    echo "✅ Build Success: $OUTPUT_BIN created."
    popd > /dev/null
    exit 0
else
    echo "❌ Build Failed: $BUILT_FILE not found in $(pwd)"
    popd > /dev/null
    exit 1
fi