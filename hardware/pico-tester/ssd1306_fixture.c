#include <stdio.h>
#include <string.h>
#include "fixture.h"
#include "protocol.h"
#include "ssd1306_fixture.h"

static ssd1306_model_t model;
static bool have_capture;

void ssd1306_fixture_capture(unsigned long id, char *args) {
    char *save = NULL, *f = strtok_r(args, " ", &save), *t = strtok_r(NULL, " ", &save), *opt = strtok_r(NULL, " ", &save);
    char *extra = opt ? strtok_r(NULL, " ", &save) : NULL;
    unsigned long frames, timeout;
    fixture_safe();
    if (extra || (opt && strcmp(opt, "INIT")) || !protocol_number(f, 8, &frames) || frames < 1 ||
        !protocol_number(t, 5000, &timeout) || timeout < 10) {
        printf("%lu ERR INVALID ssd1306_capture_arguments\n", id); return;
    }
    unsigned overflow = 0;
    have_capture = false;
    if (!ssd1306_hw_capture(&model, (unsigned)frames, (unsigned)timeout, opt != NULL, &overflow)) return;
    have_capture = true;
    fixture_safe();
    bool ok = model.frames >= frames;
    printf("%lu %s frames=%u transfers=%u cmds=%u data=%u unknown=%u bad_control=%u overflow=%u display_on=%d display_on_seen=%d charge_pump=%d crc32=%08x safe=1\n",
           id, ok ? "OK" : "ERR TIMEOUT", (unsigned)model.frames, (unsigned)model.transfers, (unsigned)model.cmds,
           (unsigned)model.data_bytes, (unsigned)model.unknown, (unsigned)model.bad_control, overflow,
           model.display_on, model.display_on_seen, model.charge_pump, (unsigned)ssd1306_model_crc32(&model));
}

void ssd1306_fixture_page(unsigned long id, char *args) {
    char *save = NULL, *p = strtok_r(args, " ", &save), *extra = strtok_r(NULL, " ", &save);
    unsigned long page;
    fixture_safe();
    if (extra || !protocol_number(p, SSD1306_MODEL_PAGES - 1, &page)) {
        printf("%lu ERR INVALID ssd1306_page_arguments\n", id); return;
    }
    if (!have_capture) { printf("%lu ERR INVALID no_capture\n", id); return; }
    printf("%lu OK page=%lu fb=", id, page);
    for (unsigned i = 0; i < SSD1306_MODEL_W; i++) printf("%02x", model.fb[page * SSD1306_MODEL_W + i]);
    printf(" safe=1\n");
}

void ssd1306_fixture_selftest(unsigned long id, char *args) {
    fixture_safe();
    if (args && *args) { printf("%lu ERR INVALID arguments\n", id); return; }
    ssd1306_selftest_result_t r = {0};
    ssd1306_hw_selftest(&r);
    fixture_safe();
    if (r.disconnected) return;
    bool ok = r.frames == 2 && r.unknown == 1 && r.bad_control == 0 && r.overflow == 0 && r.crc32 == r.expected_crc32 &&
              r.wrong_address_rc == -1 /* NACK; -2 would be a timeout */ && r.idle_frames == 0;
    printf("%lu %s frames=%u unknown=%u bad_control=%u overflow=%u crc32=%08x expected_crc32=%08x wrong_address_rc=%d idle_frames=%u safe=1\n",
           id, ok ? "OK" : "ERR I2C selftest", r.frames, r.unknown, r.bad_control, r.overflow, r.crc32, r.expected_crc32,
           r.wrong_address_rc, r.idle_frames);
}
