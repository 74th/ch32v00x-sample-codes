#ifndef WS2812_FIXTURE_H
#define WS2812_FIXTURE_H
#include <stdbool.h>
#include <stdint.h>
#include "ws2812_classify.h"
void ws2812_fixture_capture(unsigned long id, char *args);
void ws2812_fixture_selftest(unsigned long id, char *args);

typedef enum { WS2812_HW_OK, WS2812_HW_TIMEOUT, WS2812_HW_BUSY, WS2812_HW_DISCONNECTED } ws2812_hw_status_t;
typedef enum { WS2812_TEST_OK, WS2812_TEST_BADWIDTH, WS2812_TEST_TIMEOUT } ws2812_test_mode_t;

/* Hardware hooks (ws2812_hw.c on the Pico, stubs in host tests).
 * capture: decode `pin` into `words` (pairs, see ws2812_decode.pio), wanting max_words words. Returns OK when all words
 * arrived, TIMEOUT when timeout_ms elapsed (n_words holds what arrived), DISCONNECTED on USB loss (no response). */
ws2812_hw_status_t ws2812_hw_capture(unsigned pin, unsigned want_words, unsigned timeout_ms,
                                     uint32_t *words, unsigned *n_words, unsigned *ns_per_count);
/* selftest: Pico-only loopback, SPI0 TX GP19 -> decoder on GP20. Sends tx (6 bytes; BADWIDTH makes the first data bit
 * 667 ns wide; TIMEOUT sends nothing) and decodes. */
ws2812_hw_status_t ws2812_hw_selftest(ws2812_test_mode_t mode, uint32_t *words, unsigned *n_words, unsigned *ns_per_count,
                                      unsigned *baud, uint8_t tx[6]);
#endif
