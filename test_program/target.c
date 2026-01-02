#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>

int main() {
    char input[64];
    ssize_t n = read(0, input, 63);
    if (n <= 0) return 0;

    if (input[0] == 'F') {
        printf("ffd\n");
        if (n > 1 && input[1] == 'U') {
            printf("u\n");
            if (n > 2 && input[2] == 'C') {
                printf("c\n");
                volatile int* p = (int*)0;
                abort();
            }
            if (n > 2 && input[2] == 'K') {
                printf("k\n");
                abort();
            }
        }
    }

    if (input[0] == 'X' && n > 2 && input[1] == 'Y' && input[2] == 'Z') {
        printf("xyz\n");
        abort();
        int a = 1 / 0;
    }

    printf("success\n");
    return 0;
}