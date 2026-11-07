/* stdin: 12 hex digits (SHT31 6-byte reply). Prints "t=<n> h=<n>". */
#include <stdio.h>
#include "sht31.h"
int main(void) {
    uint8_t f[6]; unsigned v; uint32_t t, h;
    for (int i = 0; i < 6; i++) { if (scanf("%2x", &v) != 1) return 1; f[i] = (uint8_t)v; }
    sht31_convert(f, &t, &h);
    printf("t=%lu h=%lu\n", (unsigned long)t, (unsigned long)h);
    return 0;
}
