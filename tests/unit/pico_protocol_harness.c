/* Host harness: execute the real request parser with hardware actions stubbed. */
#include <stdio.h>
#include <string.h>
#include "protocol.h"
#include "ssd1306_fixture.h"
#include "ws2812_fixture.h"
#include "capture_fixture.h"
void fixture_safe(void) {}
void gpio_fixture_command(unsigned long id, const char *cmd, char *args) {(void)id;(void)cmd;(void)args;}
#define STUB(name) void name(unsigned long id, char *args) {(void)id;(void)args;}
STUB(uart_fixture_xfer)
STUB(adc_fixture_observe)
STUB(i2c_fixture_selftest)
STUB(i2c_fixture_faulttest)
STUB(i2c_fixture_probe)
STUB(i2c_fixture_master)
STUB(i2c_fixture_slave)
STUB(spi_fixture_selftest)
STUB(spi_fixture_slave)
/* Capture stubs: only the dispatch is real. CAPTURE_START marks the PIO as owned until CAPTURE_STOP or RESET_SAFE. */
static bool capture_on;
bool capture_fixture_active(void) { return capture_on; }
void capture_fixture_halt(void) { capture_on = false; }
#define CAPTURE_STUB(name, tag, on) void name(unsigned long id, char *args) {(void)args; capture_on = on; printf("%lu OK stub=" tag "\n", id);}
CAPTURE_STUB(capture_fixture_edge_measure, "EDGE_MEASURE", capture_on)
CAPTURE_STUB(capture_fixture_edge_selftest, "EDGE_SELFTEST", capture_on)
CAPTURE_STUB(capture_fixture_start, "CAPTURE_START", true)
CAPTURE_STUB(capture_fixture_read, "CAPTURE_READ", capture_on)
CAPTURE_STUB(capture_fixture_stop, "CAPTURE_STOP", false)
CAPTURE_STUB(capture_fixture_i2c_hold, "I2C_HOLD", capture_on)
/* Stub hardware hook: timeout_ms==77 simulates silence; otherwise feed `frames` full frames of a known pattern. */
bool ssd1306_hw_capture(ssd1306_model_t *m, unsigned frames, unsigned timeout_ms, bool wait_init, unsigned *overflow) {
    ssd1306_model_init(m); *overflow = 0; (void)wait_init;
    if (timeout_ms == 77) return true;
    const uint8_t off[] = {0x00, 0xAE}, mode[] = {0x00, 0x20, 0x00}, on[] = {0x00, 0xAF};
    ssd1306_model_transfer(m, off, 2); ssd1306_model_transfer(m, mode, 3); ssd1306_model_transfer(m, on, 2);
    for (unsigned f = 0; f < frames; f++) {
        const uint8_t win[] = {0x00, 0x21, 0, 127}, pg[] = {0x00, 0x22, 0, 7};
        ssd1306_model_transfer(m, win, 4); ssd1306_model_transfer(m, pg, 4);
        for (unsigned i = 0; i < 1024; i += 32) {
            uint8_t b[33] = {0x40};
            for (unsigned j = 0; j < 32; j++) b[1 + j] = (uint8_t)((i + j) * 3);
            ssd1306_model_transfer(m, b, 33);
        }
    }
    return true;
}
/* Stub: pretend the loopback self-test saw a correct run (real behaviour needs hardware). */
void ssd1306_hw_selftest(ssd1306_selftest_result_t *r) {
    r->frames = 2; r->unknown = 1; r->crc32 = r->expected_crc32 = 0x12345678; r->wrong_address_rc = -1;
}
/* WS2812 stub: builds a decoder word stream for a frame of `nbytes` bytes (0xA5, 0x5A, ... alternating) at 16 ns/count.
 * timeout_ms selects a scenario: 77 silence (TIMEOUT), 78 short frame by one byte, 79 long frame (no marker where expected),
 * 80 one out-of-range pulse, anything else a clean frame. */
static unsigned ws_frame(uint32_t *w, unsigned nbytes, bool marker, int bad_bit, uint8_t *tx) {
    unsigned n = 0;
    for (unsigned i = 0; i < nbytes; i++) {
        uint8_t byte = (i & 1) ? 0x5A : 0xA5;
        if (tx && i < 6) tx[i] = byte;
        for (int b = 7; b >= 0; b--) {
            unsigned bit = (byte >> b) & 1, k = i * 8 + (7 - b);
            uint32_t h = (int)k == bad_bit ? 42 : bit ? 62 : 21;
            w[n++] = h; w[n++] = (marker && i == nbytes - 1 && b == 0) ? 0xFFFFFFFFu : 30;
        }
    }
    return n;
}
ws2812_hw_status_t ws2812_hw_capture(unsigned pin, unsigned want_words, unsigned timeout_ms, uint32_t *words, unsigned *n_words, unsigned *ns_per_count) {
    (void)pin; *ns_per_count = 16; unsigned nbytes = want_words / 16;
    switch (timeout_ms) {
    case 77: *n_words = 0; return WS2812_HW_TIMEOUT;
    case 78: *n_words = ws_frame(words, nbytes - 1, true, -1, 0); return WS2812_HW_TIMEOUT;
    case 79: *n_words = ws_frame(words, nbytes, false, -1, 0); return WS2812_HW_OK;
    case 80: *n_words = ws_frame(words, nbytes, true, 3, 0); return WS2812_HW_OK;
    default: *n_words = ws_frame(words, nbytes, true, -1, 0); return WS2812_HW_OK;
    }
}
ws2812_hw_status_t ws2812_hw_selftest(ws2812_test_mode_t mode, uint32_t *words, unsigned *n_words, unsigned *ns_per_count, unsigned *baud, uint8_t tx[6]) {
    *ns_per_count = 16; *baud = 2976190;
    if (mode == WS2812_TEST_TIMEOUT) { *n_words = 0; return WS2812_HW_TIMEOUT; }
    *n_words = ws_frame(words, 6, true, mode == WS2812_TEST_BADWIDTH ? 0 : -1, tx);
    return WS2812_HW_OK;
}
int main(void) {
    char line[256];
    while (fgets(line, sizeof line, stdin)) {
        line[strcspn(line, "\n")] = 0;
        protocol_process(line);
    }
    return 0;
}
