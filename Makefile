CC = afl-cc
CXX = afl-c++
TARGET_BIN = target_program
SOURCE_C  = test_program/target.c

.PHONY: fuzz clean-crash clean-all setup quick-test

fuzz: $(TARGET_BIN)
	python main.py

$(TARGET_BIN): $(SOURCE_C)
	$(CC) -o $@ -fno-stack-protector -z execstack -no-pie $<

clean-crash:
	rm -f crashes/crash_*

setup:
	mkdir -p seeds crashes
	@echo "✅ Directories created: seeds/, crashes/"

quick-test: clean-crash fuzz

clean:
	rm -f $(TARGET_BIN)
