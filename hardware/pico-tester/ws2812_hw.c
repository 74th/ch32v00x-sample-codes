/* Pico side of the WS2812 decoder: PIO1 pulse-width measurement + DMA, and the SPI0 loopback sender for the self-test. */
#include <string.h>
#include "pico/stdlib.h"
#include "pico/stdio_usb.h"
#include "hardware/clocks.h"
#include "hardware/dma.h"
#include "hardware/pio.h"
#include "hardware/spi.h"
#include "fixture.h"
#include "ws2812_fixture.h"
#include "ws2812_decode.pio.h"

#define GAP_LIMIT_COUNTS 3125u        /* 3125 loops x 2 cycles x 8 ns = 50 us of Low ends a frame */
#define SYNC_QUIET_US 200u

typedef void (*feeder_t)(void *ctx);

static ws2812_hw_status_t run_decoder(unsigned pin, unsigned want_words, unsigned timeout_ms, feeder_t feeder, void *ctx,
                                      uint32_t *words, unsigned *n_words, unsigned *ns_per_count) {
    PIO pio = pio1;
    *n_words = 0;
    *ns_per_count = (unsigned)(2000000000ull / clock_get_hz(clk_sys));
    fixture_safe();
    int sm = pio_claim_unused_sm(pio, false);
    int ch = dma_claim_unused_channel(false);
    if (sm < 0 || ch < 0) {
        if (sm >= 0) pio_sm_unclaim(pio, sm);
        if (ch >= 0) dma_channel_unclaim(ch);
        return WS2812_HW_BUSY;
    }
    unsigned offset = pio_add_program(pio, &ws2812_decode_program);
    pio_sm_config c = ws2812_decode_program_get_default_config(offset);
    sm_config_set_in_pins(&c, pin);
    sm_config_set_jmp_pin(&c, pin);
    sm_config_set_in_shift(&c, false, false, 32);
    /* Do not join the FIFOs: the gap limit goes through the TX FIFO (a joined RX FIFO leaves TX with depth 0 and
       pio_sm_put_blocking would wait forever). DMA drains the 4-word RX FIFO fast enough for 2 words per 1.33 us. */
    pio_gpio_init(pio, pin);
    pio_sm_set_consecutive_pindirs(pio, sm, pin, 1, false);
    gpio_disable_pulls(pin);

    /* Frame alignment: if the line has been Low for SYNC_QUIET_US we are between frames; otherwise wait for a reset gap. */
    bool synced = true;
    uint64_t t0 = time_us_64();
    while (time_us_64() - t0 < SYNC_QUIET_US) if (gpio_get(pin)) { synced = false; break; }

    pio_sm_init(pio, sm, offset, &c);
    pio_sm_put_blocking(pio, sm, GAP_LIMIT_COUNTS);
    pio_sm_set_enabled(pio, sm, true);

    uint64_t deadline = time_us_64() + (uint64_t)timeout_ms * 1000ULL;
    ws2812_hw_status_t st = WS2812_HW_OK;
    while (!synced && st == WS2812_HW_OK) {
        if (!pio_sm_is_rx_fifo_empty(pio, sm) && pio_sm_get(pio, sm) == WS2812_MARKER) { synced = true; break; }
        if (!stdio_usb_connected()) st = WS2812_HW_DISCONNECTED;
        else if (time_us_64() >= deadline) st = WS2812_HW_TIMEOUT;
    }
    if (st == WS2812_HW_OK) {
        dma_channel_config dc = dma_channel_get_default_config(ch);
        channel_config_set_transfer_data_size(&dc, DMA_SIZE_32);
        channel_config_set_read_increment(&dc, false);
        channel_config_set_write_increment(&dc, true);
        channel_config_set_dreq(&dc, pio_get_dreq(pio, sm, false));
        pio_sm_clear_fifos(pio, sm);                 /* drop words that arrived while syncing: the marker itself ended a frame */
        dma_channel_configure(ch, &dc, words, &pio->rxf[sm], want_words, true);
        if (feeder) feeder(ctx);
        /* Stop at the first frame-end marker (a frame may or may not be followed by one more, idle-High, pulse). */
        unsigned scanned = 0, found = 0;
        bool have_marker = false;
        while (dma_channel_is_busy(ch) && !have_marker) {
            unsigned written = (unsigned)((dma_channel_hw_addr(ch)->write_addr - (uint32_t)(uintptr_t)words) / 4);
            for (; scanned < written; scanned++)
                if (words[scanned] == WS2812_MARKER && (scanned & 1)) { have_marker = true; found = scanned + 1; scanned++; break; }
            if (have_marker) break;
            if (!stdio_usb_connected()) { st = WS2812_HW_DISCONNECTED; break; }
            if (time_us_64() >= deadline) { st = WS2812_HW_TIMEOUT; break; }
        }
        *n_words = have_marker ? found : want_words - dma_channel_hw_addr(ch)->transfer_count;
        dma_channel_abort(ch);
    }
    pio_sm_set_enabled(pio, sm, false);
    pio_remove_program(pio, &ws2812_decode_program, offset);
    pio_sm_unclaim(pio, sm);
    dma_channel_unclaim(ch);
    fixture_safe();
    return st;
}

ws2812_hw_status_t ws2812_hw_capture(unsigned pin, unsigned want_words, unsigned timeout_ms,
                                     uint32_t *words, unsigned *n_words, unsigned *ns_per_count) {
    return run_decoder(pin, want_words, timeout_ms, NULL, NULL, words, n_words, ns_per_count);
}

/* ---- self-test sender: helper-style encoding, 4 SPI bits per data bit (1 -> 1110, 0 -> 1000) at about 3 MHz ---- */
typedef struct { ws2812_test_mode_t mode; const uint8_t *tx; unsigned baud; } send_ctx_t;

static void send_frame(void *p) {
    send_ctx_t *s = p;
    if (s->mode == WS2812_TEST_TIMEOUT) return;
    uint16_t out[12];
    for (unsigned i = 0; i < 6; i++) {
        for (unsigned nib = 0; nib < 2; nib++) {
            uint16_t w = 0;
            for (unsigned b = 0; b < 4; b++) {
                unsigned bit = (s->tx[i] >> (7 - (nib * 4 + b))) & 1;
                uint16_t group = bit ? 0xE : 0x8;
                if (s->mode == WS2812_TEST_BADWIDTH && i == 0 && nib == 0 && b == 0) group = 0xC;   /* 667 ns High */
                w = (uint16_t)((w << 4) | group);
            }
            out[i * 2 + nib] = w;
        }
    }
    s->baud = spi_init(spi0, 3000000);
    spi_set_format(spi0, 16, SPI_CPOL_0, SPI_CPHA_0, SPI_MSB_FIRST);
    gpio_set_function(19, GPIO_FUNC_SPI);
    spi_write16_blocking(spi0, out, 12);
    sleep_us(10);
    spi_deinit(spi0);
}

ws2812_hw_status_t ws2812_hw_selftest(ws2812_test_mode_t mode, uint32_t *words, unsigned *n_words, unsigned *ns_per_count,
                                      unsigned *baud, uint8_t tx[6]) {
    static const uint8_t pattern[6] = {0x00, 0xFF, 0xA5, 0x5A, 0x01, 0x80};
    memcpy(tx, pattern, 6);
    send_ctx_t s = {mode, tx, 0};
    ws2812_hw_status_t st = run_decoder(20, 6 * 8 * 2 + 2, mode == WS2812_TEST_TIMEOUT ? 50 : 200, send_frame, &s,
                                        words, n_words, ns_per_count);
    *baud = s.baud;
    return st;
}
