#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>

int main() {
    char input[64];
    ssize_t n = read(0, input, 63);
    if (n <= 0) return 0;

    if (input[0] == 'F') {
        if (n > 1 && input[1] == 'U') {
            if (n > 2 && input[2] == 'C') {
                volatile int* p = (int*)0;
                *p = 42;
            }
            if (n > 2 && input[2] == 'K') {
                abort();
            }
        }
    }

    if (input[0] == 'X' && n > 2 && input[1] == 'Y' && input[2] == 'Z') {
        int a = 1 / 0;
    }

    return 0;
}