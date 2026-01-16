CC = afl-cc
CXX = afl-c++

# 自动检测 Python 命令：优先使用 python3，如果不存在则使用 python
PYTHON := python3

.PHONY: fuzz clean-crash clean-all setup quick-test

# ---------------------- config ----------------------
TARGET ?= T01
TIME ?= 86400      # 总运行时间（秒），默认 24 小时
TIMEOUT ?= 2         # 单次执行超时（秒）
QUEUE ?= 500         # 最大队列大小

ifeq ($(TARGET), T01)
    TNAME := cxxfilt
    TSRC  := targets/binutils-2.28
    TCMD  := 
	TIMEOUT := 2
else ifeq ($(TARGET), T02)
    TNAME := readelf
    TSRC  := targets/binutils-2.28
    TCMD  := -a @@ @@
	TIMEOUT := 3
else ifeq ($(TARGET), T03)
    TNAME := nm-new
    TSRC  := targets/binutils-2.28
    TCMD  := @@
	TIMEOUT := 2
else ifeq ($(TARGET), T04)
    TNAME := objdump
    TSRC  := targets/binutils-2.28
    TCMD  := -d @@
	TIMEOUT := 5
else ifeq ($(TARGET), T05)
    TNAME := djpeg
    TSRC  := targets/libjpeg-turbo-3.0.4
    TCMD  := @@
	TIMEOUT := 5
else ifeq ($(TARGET), T06)
    TNAME := readpng
    TSRC  := targets/libpng-1.6.29
    TCMD  := 
	TIMEOUT := 5
else ifeq ($(TARGET), T07)
    TNAME := xmllint
    TSRC  := targets/libxml2-2.13.4
    TCMD  := @@
	TIMEOUT := 5
else ifeq ($(TARGET), T08)
    TNAME := lua
    TSRC  := targets/lua-5.4.7
    TCMD  := @@
	TIMEOUT := 8
else ifeq ($(TARGET), T09)
    TNAME := mjs
    TSRC  := targets/mjs-2.20.0
    TCMD  := -f @@
	TIMEOUT := 5
else ifeq ($(TARGET), T10)
    TNAME := tcpdump
    TSRC  := targets/tcpdump-tcpdump-4.99.5
    TCMD  := -nr @@
	TIMEOUT := 5
endif

# ---------------------- path ----------------------
OUTPUT_DIR := $(abspath output)
BIN_OUT := $(abspath targets/build/$(TNAME))
SDIR    := $(abspath seeds/$(TNAME))
ODIR    := $(abspath output/$(TNAME))
TSRC    := $(abspath $(TSRC))


# ---------------------- fuzzing ----------------------
.PHONY: fuzz build setup clean

fuzz: build setup
	@echo "🚀 Fuzzing $(TNAME) with CMD: $(TNAME) $(TCMD)"
	@echo "⚙️  Configuration: TIME=$(TIME)s, TIMEOUT=$(TIMEOUT)s, QUEUE=$(QUEUE)"
	@export FUZZ_TARGET_PATH=$(BIN_OUT) \
	        FUZZ_TARGET_CMD="$(TCMD)" \
	        FUZZ_SEEDS_DIR=$(SDIR) \
	        FUZZ_OUTPUT_DIR=$(ODIR) \
	        FUZZ_TOTAL_TIMEOUT=$(TIME) \
	        FUZZ_TIMEOUT_SEC=$(TIMEOUT) \
	        FUZZ_MAX_QUEUE_SIZE=$(QUEUE); \
	$(PYTHON) main.py

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

# ---------------------- afl-fuzz ----------------------
# afl-fuzz -i seeds/tcpdump -o output/tcpdump -- ./tcpdump -nr @@
# hidden command for afl-fuzz
AFL_OUTPUT_DIR := $(abspath afl-out/$(TNAME))

afl-fuzz-target: build
	@echo "🚀 Starting AFL++ fuzzing on $(TNAME)..."
	@echo "📁 Input seeds: $(SDIR)"
	@echo "📁 Output directory: $(AFL_OUTPUT_DIR)"
	@echo "⚙️  Command: $(BIN_OUT) $(TCMD)"
	@echo "⏱️  Timeout: $(TIMEOUT)s ($$(($(TIMEOUT) * 1000))ms)"
	@mkdir -p $(SDIR) $(AFL_OUTPUT_DIR)
	@chmod -R a+rwX $(AFL_OUTPUT_DIR) 2>/dev/null || true
	@if [ -z "$$(ls -A $(SDIR) 2>/dev/null)" ]; then \
		echo "⚠️  Warning: Seed directory is empty, creating default seed..."; \
		echo "test" > $(SDIR)/default; \
	fi
	@if [ -n "$(TCMD)" ]; then \
		echo "💡 Using file-based fuzzing (with @@)"; \
		AFL_I_DONT_CARE_ABOUT_MISSING_CRASHES=1 afl-fuzz -t $$(($(TIMEOUT) * 1000)) -i $(SDIR) -o $(AFL_OUTPUT_DIR) -- $(BIN_OUT) $(subst @@,@@,$(TCMD)); \
	else \
		echo "💡 Using stdin-based fuzzing"; \
		AFL_I_DONT_CARE_ABOUT_MISSING_CRASHES=1 afl-fuzz -t $$(($(TIMEOUT) * 1000)) -i $(SDIR) -o $(AFL_OUTPUT_DIR) -- $(BIN_OUT); \
	fi


# ---------------------- only for test ----------------------
TEST_BIN = target_program
TEST_SRC  = test_program/target.c

test: $(TEST_BIN)
	$(PYTHON) main.py

$(TEST_BIN): $(TEST_SRC)
	$(CC) -o $@ -fno-stack-protector -z execstack -no-pie $<

quick-test: clean-results test

clean:
	@echo "🧹 Cleaning all built binaries in targets/build..."
	@rm -rf targets/build/*
	@echo "🗑️  Cleaning all fuzzing outputs in $(OUTPUT_DIR)..."
	@rm -rf $(OUTPUT_DIR)
	@echo "🔧 Cleaning build artifacts in target source directories..."


clean-results:
	@echo "🧹 Cleaning results only..."
	rm -rf $(ODIR)/crashes/*
	rm -rf $(ODIR)/queue/*
	rm -rf $(ODIR)/hangs/*
	rm -rf $(ODIR)/plot_data/*
	rm -f $(ODIR)/.cur_input