#ifndef SSD1306_FIXTURE_H
#define SSD1306_FIXTURE_H
#include <stdbool.h>
#include "ssd1306_model.h"
void ssd1306_fixture_capture(unsigned long id, char *args);
void ssd1306_fixture_page(unsigned long id, char *args);
void ssd1306_fixture_selftest(unsigned long id, char *args);
typedef struct {
    unsigned frames, unknown, bad_control, overflow;
    unsigned crc32, expected_crc32;
    int wrong_address_rc;       /* SDK return of a write to 0x3D (expected: PICO_ERROR_GENERIC) */
    unsigned idle_frames;       /* frames seen in a capture with no traffic (expected: 0) */
    bool disconnected;
} ssd1306_selftest_result_t;
/* Pico-only loopback: I2C0 master GP16/GP17 -> I2C1 slave GP18/GP19 (needs the I2C loopback wiring and pull-ups). */
void ssd1306_hw_selftest(ssd1306_selftest_result_t *r);
/* Hardware hook (ssd1306_hw.c on the Pico, a stub in host tests): reset *m, act as an SSD1306 at 0x3C on
 * GP10/GP11 and feed each I2C transfer to the model until m->frames >= frames or timeout_ms elapses.
 * wait_init (INIT option): ignore transfers until a display-off command (0x00 0xAE) arrives, and clear the model at
 * every later display-off, so counters and frames refer to the most recent initialisation sequence.
 * Further transfers are ignored once the target is reached. Returns false on USB disconnect (no response is sent). */
bool ssd1306_hw_capture(ssd1306_model_t *m, unsigned frames, unsigned timeout_ms, bool wait_init, unsigned *overflow);
#endif
