CC = afl-cc
CXX = afl-c++
TARGET_BIN = target_program
TARGET_SRC  = test_program/target.c

.PHONY: fuzz clean-crash clean-all setup quick-test

fuzz: $(TARGET_BIN)
	python main.py

$(TARGET_BIN): $(TARGET_SRC)
	$(CC) -o $@ -fno-stack-protector -z execstack -no-pie $<

clean-crash:
	rm -f crashes/crash_*

setup:
	mkdir -p seeds crashes
	@echo "✅ Directories created: seeds/, crashes/"

# only for test
TEST_BIN = target_program
TEST_SRC  = test_program/target.c

test: $(TEST_BIN)
	python main.py

$(TEST_BIN): $(TEST_SRC)
	$(CC) -o $@ -fno-stack-protector -z execstack -no-pie $<

quick-test: clean-crash test

clean:
	rm -f $(TARGET_BIN)
