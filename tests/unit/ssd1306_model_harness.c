/* Text harness for ssd1306_model.c. stdin lines: R (reset) | T <hex transfer> | S (stats) | P <page> (page hex). */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "ssd1306_model.h"
static ssd1306_model_t m;
static int hexv(char c) { return c >= '0' && c <= '9' ? c - '0' : c >= 'a' && c <= 'f' ? c - 'a' + 10 : -1; }
int main(void) {
    char line[4096]; ssd1306_model_init(&m);
    while (fgets(line, sizeof line, stdin)) {
        line[strcspn(line, "\n")] = 0;
        if (line[0] == 'R') ssd1306_model_init(&m);
        else if (line[0] == 'T') {
            uint8_t buf[1500]; size_t n = 0;
            for (const char *p = line + 2; p[0] && p[1] && n < sizeof buf; p += 2) buf[n++] = (uint8_t)((hexv(p[0]) << 4) | hexv(p[1]));
            ssd1306_model_transfer(&m, buf, n);
        } else if (line[0] == 'S') {
            printf("transfers=%u cmds=%u data=%u unknown=%u bad_control=%u frames=%u display_on=%d seen=%d charge_pump=%d mode=%u col=%u page=%u crc=%08x unk=",
                   m.transfers, m.cmds, m.data_bytes, m.unknown, m.bad_control, m.frames, m.display_on, m.display_on_seen,
                   m.charge_pump, m.mode, m.col, m.page, ssd1306_model_crc32(&m));
            for (unsigned i = 0; i < m.unknown && i < SSD1306_MODEL_UNKNOWN_KEEP; i++) printf("%02x", m.unknown_first[i]);
            printf("\n");
        } else if (line[0] == 'P') {
            int pg = atoi(line + 2);
            for (int i = 0; i < SSD1306_MODEL_W; i++) printf("%02x", m.fb[pg * SSD1306_MODEL_W + i]);
            printf("\n");
        }
    }
    return 0;
}
