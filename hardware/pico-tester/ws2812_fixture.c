#include <stdio.h>
#include <string.h>
#include "fixture.h"
#include "protocol.h"
#include "ws2812_fixture.h"

static uint32_t words[2 * WS2812_MAX_BITS + 2];

static void print_hex(const uint8_t *b, unsigned n) {
    if (!n) { putchar('-'); return; }
    for (unsigned i = 0; i < n; i++) printf("%02x", b[i]);
}

void ws2812_fixture_capture(unsigned long id, char *args) {
    char *save = NULL, *p = strtok_r(args, " ", &save), *b = strtok_r(NULL, " ", &save), *t = strtok_r(NULL, " ", &save);
    char *extra = strtok_r(NULL, " ", &save);
    unsigned long pin, bytes, timeout;
    fixture_safe();
    if (extra || !protocol_number(p, 20, &pin) || (pin != 7 && pin != 20) || !protocol_number(b, 96, &bytes) || bytes < 3 ||
        !protocol_number(t, 5000, &timeout) || timeout < 10) {
        printf("%lu ERR INVALID ws2812_capture_arguments\n", id); return;
    }
    unsigned n = 0, npc = 16, expected_bits = (unsigned)bytes * 8;
    ws2812_hw_status_t st = ws2812_hw_capture((unsigned)pin, expected_bits * 2 + 2, (unsigned)timeout, words, &n, &npc);
    fixture_safe();
    if (st == WS2812_HW_DISCONNECTED) return;
    if (st == WS2812_HW_BUSY) { printf("%lu ERR BUSY pio_unavailable safe=1\n", id); return; }
    uint8_t rx[96]; ws2812_decode_t r;
    ws2812_classify(words, n, npc, rx, sizeof rx, &r);
    if (r.ended && r.bits != expected_bits) {
        printf("%lu ERR WS2812 frame_bits=%u expected=%u bad_pulses=%u tail_bits=%u tail=%02x last_high_ns=%u idle_high=%d rx=", id, r.bits, expected_bits,
               r.bad_pulses, r.tail_bits, r.tail, r.last_high_ns, r.idle_high);
        print_hex(rx, r.bytes); printf(" safe=1\n"); return;
    }
    if (!r.ended) {
        if (st == WS2812_HW_TIMEOUT) printf("%lu ERR TIMEOUT ws2812 bits=%u safe=1\n", id, n / 2);
        else printf("%lu ERR WS2812 frame_too_long expected=%u safe=1\n", id, expected_bits);
        return;
    }
    printf("%lu %s pin=%lu bytes=%lu bits=%u bad_pulses=%u idle_high=%d t0h_ns=%u t1h_ns=%u threshold_ns=%u ns_per_count=%u "
           "h0_ns=%u-%u h1_ns=%u-%u l0_ns=%u-%u l1_ns=%u-%u rx=", id,
           r.bad_pulses ? "ERR WS2812" : "OK", pin, bytes, r.bits, r.bad_pulses, r.idle_high, r.t0h_ns, r.t1h_ns, WS2812_THRESHOLD_NS, npc,
           r.h0_min, r.h0_max, r.h1_min, r.h1_max, r.l0_min, r.l0_max, r.l1_min, r.l1_max);
    print_hex(rx, r.bytes); printf(" safe=1\n");
}

void ws2812_fixture_selftest(unsigned long id, char *args) {
    char *save = NULL, *m = strtok_r(args, " ", &save), *extra = strtok_r(NULL, " ", &save);
    ws2812_test_mode_t mode;
    fixture_safe();
    if (extra || !m) { printf("%lu ERR INVALID ws2812_selftest_arguments\n", id); return; }
    if (!strcmp(m, "OK")) mode = WS2812_TEST_OK;
    else if (!strcmp(m, "BADWIDTH")) mode = WS2812_TEST_BADWIDTH;
    else if (!strcmp(m, "TIMEOUT")) mode = WS2812_TEST_TIMEOUT;
    else { printf("%lu ERR INVALID ws2812_selftest_arguments\n", id); return; }
    unsigned n = 0, npc = 16, baud = 0; uint8_t tx[6] = {0}, rx[96]; ws2812_decode_t r;
    ws2812_hw_status_t st = ws2812_hw_selftest(mode, words, &n, &npc, &baud, tx);
    fixture_safe();
    if (st == WS2812_HW_DISCONNECTED) return;
    if (st == WS2812_HW_BUSY) { printf("%lu ERR BUSY pio_unavailable safe=1\n", id); return; }
    ws2812_classify(words, n, npc, rx, sizeof rx, &r);
    bool ok;
    switch (mode) {
    case WS2812_TEST_OK: ok = st == WS2812_HW_OK && r.ended && r.bits == 48 && r.bad_pulses == 0 && !memcmp(rx, tx, 6); break;
    case WS2812_TEST_BADWIDTH: ok = st == WS2812_HW_OK && r.ended && r.bits == 48 && r.bad_pulses == 1; break;
    default: ok = st == WS2812_HW_TIMEOUT && n == 0; break;
    }
    printf("%lu %s mode=%s baud=%u bits=%u bad_pulses=%u t0h_ns=%u t1h_ns=%u words=%u tx=", id, ok ? "OK" : "ERR WS2812 selftest", m,
           baud, r.bits, r.bad_pulses, r.t0h_ns, r.t1h_ns, n);
    if (mode == WS2812_TEST_TIMEOUT) putchar('-'); else print_hex(tx, 6);
    printf(" rx="); print_hex(rx, r.bytes); printf(" safe=1\n");
}
