CC = afl-cc
CXX = afl-c++

.PHONY: fuzz clean-crash clean-all setup quick-test

TARGET ?= T01
# 1. 找到目标文件

# --- 目标元数据映射 ---
ifeq ($(TARGET), T01)
    TNAME := cxxfilt
    TSRC  := targets/binutils-2.28
    TCMD  := 
else ifeq ($(TARGET), T02)
    TNAME := readelf
    TSRC  := targets/binutils-2.28
    TCMD  := -a @@ @@
else ifeq ($(TARGET), T03)
    TNAME := nm-new
    TSRC  := targets/binutils-2.28
    TCMD  := @@
else ifeq ($(TARGET), T04)
    TNAME := objdump
    TSRC  := targets/binutils-2.28
    TCMD  := -d @@
else ifeq ($(TARGET), T05)
    TNAME := djpeg
    TSRC  := targets/libjpeg-turbo-3.0.4
    TCMD  := @@
else ifeq ($(TARGET), T06)
    TNAME := readpng
    TSRC  := targets/libpng-1.6.29
    TCMD  := 
else ifeq ($(TARGET), T07)
    TNAME := xmllint
    TSRC  := targets/libxml2-2.13.4
    TCMD  := @@
else ifeq ($(TARGET), T08)
    TNAME := lua
    TSRC  := targets/lua-5.4.7
    TCMD  := @@
else ifeq ($(TARGET), T09)
    TNAME := mjs
    TSRC  := targets/mjs-2.20.0
    TCMD  := -f @@
else ifeq ($(TARGET), T10)
    TNAME := tcpdump
    TSRC  := targets/tcpdump-tcpdump-4.99.5
    TCMD  := -nr @@
endif

# --- 路径处理 (全部转为绝对路径) ---
OUTPUT_DIR := $(abspath output)
BIN_OUT := $(abspath targets/build/$(TNAME))
SDIR    := $(abspath seeds/$(TNAME))
ODIR    := $(abspath output/$(TNAME))
TSRC    := $(abspath $(TSRC))

.PHONY: fuzz build setup clean

fuzz: build setup
	@echo "🚀 Fuzzing $(TNAME) with CMD: $(TNAME) $(TCMD)"
	@export FUZZ_TARGET_PATH=$(BIN_OUT) \
	        FUZZ_TARGET_CMD="$(TCMD)" \
	        FUZZ_SEEDS_DIR=$(SDIR) \
	        FUZZ_OUTPUT_DIR=$(ODIR); \
	python3 main.py

.PHONY: analysis

analysis: build setup
	@echo "🔍 Starting Performance Analysis for $(TNAME)..."
	@echo "📊 Mode: cProfile + Execution Speed Stats"
	@export FUZZ_TARGET_PATH=$(BIN_OUT) \
	        FUZZ_TARGET_CMD="$(TCMD)" \
	        FUZZ_SEEDS_DIR=$(SDIR) \
	        FUZZ_OUTPUT_DIR=$(ODIR); \
	python3 -m cProfile -o perf.prof main.py --analyze

build:
	@if [ -f $(BIN_OUT) ]; then \
		echo "✅ Pre-compiled binary found at $(BIN_OUT), skipping build."; \
	else \
		echo "🛠️ Building $(TNAME)..."; \
		chmod +x ./scripts/build_target.sh && \
		bash ./scripts/build_target.sh "$(TSRC)" "$(TNAME)" "$(BIN_OUT)" && \
		[ -f $(BIN_OUT) ] || (echo "❌ Error: Build completed but binary not found at $(BIN_OUT)" && exit 1); \
	fi

setup:
	@echo "🧹 Resetting output directory for $(TNAME) at $(ODIR)..."
	@rm -rf $(ODIR)
	@mkdir -p $(SDIR) $(ODIR)
	@if [ -z "$$(ls -A $(SDIR))" ] && [ ! -z $(TSEED) ]; then \
		echo -n $(TSEED) > $(SDIR)/seed_init; \
	fi

install:
	pip install sysv-ipc
	pip install matplotlib
	pip install snakeviz
# apt-get update && apt-get install -y libpcap-dev

# only for test
TEST_BIN = target_program
TEST_SRC  = test_program/target.c

test: $(TEST_BIN)
	python main.py

$(TEST_BIN): $(TEST_SRC)
	$(CC) -o $@ -fno-stack-protector -z execstack -no-pie $<

quick-test: clean-results test

clean:
	@echo "🧹 Cleaning all built binaries in targets/build..."
	rm -rf targets/build/*
	@echo "🗑️  Cleaning all fuzzing outputs in $(OUTPUT_DIR)..."
	rm -rf $(OUTPUT_DIR)
	@echo "✨ Clean done."

clean-results:
	@echo "🧹 Cleaning results only..."
	rm -rf $(ODIR)/crashes/*
	rm -rf $(ODIR)/queue/*
	rm -rf $(ODIR)/hangs/*
	rm -rf $(ODIR)/plot_data/*
	rm -f $(ODIR)/.cur_input
