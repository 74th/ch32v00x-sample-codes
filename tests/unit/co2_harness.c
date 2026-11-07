/* stdin: 18 hex digits (one 9-byte sensor response). Prints "status=<n> ppm=<n> checksum=<hex>". */
#include <stdio.h>
#include "co2.h"
int main(void) {
    uint8_t f[CO2_FRAME_LEN]; unsigned v;
    for (int i = 0; i < CO2_FRAME_LEN; i++) { if (scanf("%2x", &v) != 1) return 1; f[i] = (uint8_t)v; }
    uint16_t ppm = 0; co2_status_t st = co2_parse(f, &ppm);
    printf("status=%d ppm=%u checksum=%02x\n", st, ppm, co2_checksum(f));
    return 0;
}
