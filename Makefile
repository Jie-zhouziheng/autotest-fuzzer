CC = afl-cc
CXX = afl-c++

.PHONY: fuzz clean-crash clean-all setup quick-test

TARGET ?= T01

# 1. 找到目标文件
ifeq ($(TARGET), T01)
    TNAME := cxxfilt
    TSRC  := targets/binutils-2.28
endif

# 2. 定义路径
BIN_OUT := $(abspath targets/build/$(TNAME))
SDIR    := $(abspath seeds/$(TNAME))
CDIR    := $(abspath crashes/$(TNAME))
ODIR    := $(abspath output/$(TNAME))
TSRC    := $(abspath $(TSRC))

.PHONY: fuzz build setup

# 执行模糊测试
fuzz: build setup
	@echo "Running Fuzzer for $(TNAME)..."
	@# 通过环境变量将配置注入 config.py
	@export FUZZ_TARGET_PATH=$(BIN_OUT) \
	        FUZZ_SEEDS_DIR=$(SDIR) \
	        FUZZ_CRASHES_DIR=$(CDIR) \
	        FUZZ_OUTPUT_DIR=$(ODIR) \
	        FUZZ_TIMEOUT_SEC=1; \
	python3 main.py

# 编译脚本
build:
	@chmod +x scripts/build_target.sh
	@./scripts/build_target.sh $(TSRC) $(TNAME) $(BIN_OUT)

# 环境准备
setup:
	@mkdir -p $(SDIR) $(CDIR) $(ODIR)
	@if [ ! -f $(SDIR)/seed1 ]; then echo "_Z1fv" > $(SDIR)/seed1; fi

# only for test
TEST_BIN = target_program
TEST_SRC  = test_program/target.c

test: $(TEST_BIN)
	python main.py

$(TEST_BIN): $(TEST_SRC)
	$(CC) -o $@ -fno-stack-protector -z execstack -no-pie $<

quick-test: clean-crash test

clean-crash:
	@echo "🧹 Cleaning all crash records in $(abspath crashes)..."
	rm -rf crashes/*

clean:
	@echo "🧹 Cleaning all built binaries in $(abspath target/build)..."
	rm -rf target/build/*