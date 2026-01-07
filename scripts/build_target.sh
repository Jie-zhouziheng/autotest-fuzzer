#!/bin/bash
set -euo pipefail

SRC_DIR="$1"
TARGET_NAME="$2"
OUTPUT_BIN="$3"

# --- 辅助函数 ---
error_exit() {
    echo "❌ Error: $1" >&2
    popd >/dev/null 2>&1 || true
    exit 1
}

run_configure() {
    local config_cmd="$1"
    local project_name="${2:-project}"
    if [ ! -f Makefile ]; then
        echo "  [1/2] Configuring..."
        eval "$config_cmd" || error_exit "$project_name configure failed"
    fi
}

run_make() {
    local make_target="${1:-}"
    local project_name="${2:-project}"
    echo "  [2/2] Compiling (this may take a while)..."
    if [ -n "$make_target" ]; then
        make -j$(nproc) "$make_target" || error_exit "$project_name build failed"
    else
        make -j$(nproc) || error_exit "$project_name build failed"
    fi
}

run_autogen() {
    local project_name="${1:-project}"
    if [ ! -f configure ]; then
        ./autogen.sh 2>/dev/null || autoreconf -ivf || error_exit "$project_name autogen failed"
    fi
}

deliver_binary() {
    local built_file="$1"
    if [ -z "$built_file" ]; then
        error_exit "BUILT_FILE is empty (unsupported target?)"
    fi
    
    # 处理可能的多个位置
    local actual_file=""
    if [ -f "$built_file" ]; then
        actual_file="$built_file"
    elif [ -f ".libs/$built_file" ]; then
        actual_file=".libs/$built_file"
    else
        error_exit "Build failed - $built_file not found in $(pwd)"
    fi
    
    cp "$actual_file" "$OUTPUT_BIN" || error_exit "Failed to copy $actual_file to $OUTPUT_BIN"
    [ -f "$OUTPUT_BIN" ] || error_exit "Output binary $OUTPUT_BIN was not created"
    echo "✅ Build Success: $OUTPUT_BIN created."
}

# --- 主逻辑 ---
echo "--- [Build Script] Building $TARGET_NAME ---"
echo "Source: $SRC_DIR"
echo "Output: $OUTPUT_BIN"

# 1. 检查参数
[ -n "$SRC_DIR" ] && [ -n "$TARGET_NAME" ] && [ -n "$OUTPUT_BIN" ] || \
    error_exit "Missing arguments. (SRC=$SRC_DIR, NAME=$TARGET_NAME, OUT=$OUTPUT_BIN)"

export CC=afl-cc CXX=afl-c++ AFL_HARDEN=1

# 2. 进入目录并确保输出目录存在且可写
pushd "$SRC_DIR" >/dev/null || error_exit "Cannot enter $SRC_DIR"
OUTPUT_DIR="$(dirname "$OUTPUT_BIN")"
mkdir -p "$OUTPUT_DIR"
[ -w "$OUTPUT_DIR" ] || error_exit "Output directory $OUTPUT_DIR is not writable"

# 3. 检查产物是否已存在
if [ -f "$OUTPUT_BIN" ]; then
    echo "♻️  Found pre-built binary at $OUTPUT_BIN. Skipping build process."
    if nm "$OUTPUT_BIN" 2>/dev/null | grep -q "__afl_area_ptr"; then
        echo "🛡️  Verified: Pre-built binary is instrumented."
    else
        echo "⚠️  Warning: Pre-built binary found but might NOT be instrumented."
    fi
    popd >/dev/null
    exit 0
fi

# 4. 针对不同项目的构建逻辑
BUILT_FILE=""

if [[ "$SRC_DIR" == *"binutils"* ]]; then
    # T01-T04: binutils
    echo "🔧 Building binutils with global static config..."
    run_configure './configure --disable-shared CFLAGS="-g -static" CXXFLAGS="-g -static" LDFLAGS="-static"' "binutils"
    run_make "" "binutils"
    BUILT_FILE="binutils/$TARGET_NAME"

elif [[ "$SRC_DIR" == *"libjpeg"* ]]; then
    # T05: libjpeg-turbo
    echo "🔧 Building libjpeg-turbo with static config..."
    cmake -G "Unix Makefiles" \
        -DCMAKE_C_COMPILER=afl-cc \
        -DCMAKE_C_FLAGS="-g -static" \
        -DENABLE_SHARED=OFF \
        -DENABLE_STATIC=ON \
        . || error_exit "libjpeg-turbo cmake failed"
    run_make "djpeg-static" "libjpeg-turbo"
    BUILT_FILE="djpeg-static"

elif [[ "$SRC_DIR" == *"lua"* ]]; then
    # T08: lua
    echo "🔧 Building lua..."
    make clean 2>/dev/null || true
    make -j$(nproc) CC="$CC" linux || error_exit "lua build failed"
    BUILT_FILE="src/lua"

elif [[ "$SRC_DIR" == *"mjs"* ]]; then
    # T09: mjs
    echo "🔧 Building mjs..."
    rm -f mjs
    $CC -DMJS_MAIN mjs.c -ldl -g -o mjs || error_exit "mjs build failed"
    BUILT_FILE="mjs"

elif [[ "$SRC_DIR" == *"tcpdump"* ]]; then
    # T10: tcpdump
    echo "🔧 Building tcpdump..."
    run_autogen "tcpdump"
    run_configure './configure CFLAGS="-g" CC="$CC"' "tcpdump"
    make clean 2>/dev/null || true
    run_make "" "tcpdump"
    BUILT_FILE="tcpdump"

elif [[ "$TARGET_NAME" == "readpng" ]]; then
    # T06: readpng
    echo "🔧 Building readpng..."
    run_configure './configure --disable-shared CFLAGS="-g" LDFLAGS="-static"' "libpng"
    make clean 2>/dev/null || true
    run_make "" "libpng"
    $CC -o readpng ./contrib/libtests/readpng.c ./.libs/libpng16.a -lz -lm || \
        error_exit "readpng linking failed"
    BUILT_FILE="readpng"

else
    # T07: xmllint
    echo "🔧 Building libxml2 (xmllint)..."
    if [ ! -f configure ]; then
        NOCONFIGURE=1 ./autogen.sh 2>/dev/null || autoreconf -ivf || \
            error_exit "libxml2 autogen failed"
    fi
    run_configure './configure --disable-shared --without-python CFLAGS="-g -static" LDFLAGS="-static"' "libxml2"
    make clean 2>/dev/null || true
    run_make "" "libxml2"
    BUILT_FILE="xmllint"
fi

# 5. 交付产物
deliver_binary "$BUILT_FILE"
popd >/dev/null
exit 0