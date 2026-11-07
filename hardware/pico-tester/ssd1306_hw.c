/* Pico side of the SSD1306 stand-in: I2C1 slave 0x3C on GP10 (SDA) / GP11 (SCL), no internal pull-ups. */
#include "pico/stdlib.h"
#include "pico/stdio_usb.h"
#include <string.h>
#include "hardware/i2c.h"
#include "pico/i2c_slave.h"
#include "fixture.h"
#include "ssd1306_fixture.h"

#define XFER_MAX 256
static ssd1306_model_t *cap_model;
static unsigned cap_target;
static volatile unsigned cap_overflow;
static uint8_t xfer[XFER_MAX];
static unsigned xfer_len;
static bool xfer_overflowed;
static volatile bool cap_init_mode, cap_synced;   /* INIT option: restart at every display-off command */

static void flush_transfer(void) {
    if (cap_init_mode && !xfer_overflowed && xfer_len >= 2 && xfer[0] == 0x00 && xfer[1] == 0xAE &&
        cap_model->frames < cap_target) {
        ssd1306_model_init(cap_model);               /* a new initialisation: forget everything before it */
        cap_synced = true;
    }
    if (xfer_len && !xfer_overflowed && (!cap_init_mode || cap_synced) && cap_model->frames < cap_target)
        ssd1306_model_transfer(cap_model, xfer, xfer_len);
    if (xfer_overflowed) cap_overflow++;
    xfer_len = 0; xfer_overflowed = false;
}

static void slave_event(i2c_inst_t *bus, i2c_slave_event_t event) {
    if (event == I2C_SLAVE_RECEIVE) {
        uint8_t b = i2c_read_byte_raw(bus);
        if (xfer_len < XFER_MAX) xfer[xfer_len++] = b; else xfer_overflowed = true;
    } else if (event == I2C_SLAVE_REQUEST) {
        i2c_write_byte_raw(bus, 0xff);
    } else if (event == I2C_SLAVE_FINISH) {
        flush_transfer();
    }
}

static void slave_begin(ssd1306_model_t *m, unsigned frames, unsigned sda, unsigned scl, bool wait_init) {
    ssd1306_model_init(m);
    cap_model = m; cap_target = frames; cap_overflow = 0; cap_init_mode = wait_init; cap_synced = false; xfer_len = 0; xfer_overflowed = false;
    fixture_safe();
    i2c_init(i2c1, 100000);
    gpio_disable_pulls(sda); gpio_disable_pulls(scl);
    gpio_set_function(sda, GPIO_FUNC_I2C); gpio_set_function(scl, GPIO_FUNC_I2C);
    i2c_slave_init(i2c1, 0x3C, slave_event);
}

bool ssd1306_hw_capture(ssd1306_model_t *m, unsigned frames, unsigned timeout_ms, bool wait_init, unsigned *overflow) {
    slave_begin(m, frames, 10, 11, wait_init);
    uint64_t end = time_us_64() + (uint64_t)timeout_ms * 1000ULL;
    bool connected = true;
    while (m->frames < frames && time_us_64() < end) {
        if (!stdio_usb_connected()) { connected = false; break; }
        sleep_ms(1);
    }
    i2c_slave_deinit(i2c1); i2c_deinit(i2c1); fixture_safe();
    *overflow = cap_overflow;
    return connected;
}

/* ---- Pico-only loopback self-test ---- */
static ssd1306_model_t selftest_model, idle_model;

static void master_write(const uint8_t *b, size_t n) { i2c_write_timeout_us(i2c0, 0x3C, b, n, false, 100000); }

void ssd1306_hw_selftest(ssd1306_selftest_result_t *r) {
    static uint8_t pattern[SSD1306_MODEL_FB_SIZE];
    for (unsigned i = 0; i < sizeof pattern; i++) pattern[i] = (uint8_t)(i * 5 + 1);
    ssd1306_model_t crc_ref; ssd1306_model_init(&crc_ref);
    memcpy(crc_ref.fb, pattern, sizeof pattern);
    r->expected_crc32 = ssd1306_model_crc32(&crc_ref);

    /* slave_begin() calls fixture_safe(), which resets every pin: set up the master pins afterwards. */
    slave_begin(&selftest_model, 2, 18, 19, false);
    i2c_init(i2c0, 100000);
    for (unsigned pin = 16; pin <= 17; pin++) { gpio_disable_pulls(pin); gpio_set_function(pin, GPIO_FUNC_I2C); }
    /* One command per transfer, as the helper sends them; the 0xDC command is unknown to the model. */
    static const uint8_t c_off[] = {0x00, 0xAE}, c_mode[] = {0x00, 0x20}, c_mode0[] = {0x00, 0x00}, c_unk[] = {0x00, 0xDC},
                         c_on[] = {0x00, 0xAF}, c_col[] = {0x00, 0x21}, c_col0[] = {0x00, 0x00}, c_col1[] = {0x00, 0x7F},
                         c_pg[] = {0x00, 0x22}, c_pg0[] = {0x00, 0x00}, c_pg1[] = {0x00, 0x07};
    const uint8_t *init[] = {c_off, c_mode, c_mode0, c_unk, c_on};
    for (unsigned i = 0; i < 5; i++) master_write(init[i], 2);
    for (unsigned f = 0; f < 2; f++) {
        const uint8_t *win[] = {c_col, c_col0, c_col1, c_pg, c_pg0, c_pg1};
        for (unsigned i = 0; i < 6; i++) master_write(win[i], 2);
        for (unsigned off = 0; off < sizeof pattern; off += 32) {
            uint8_t b[33] = {0x40};
            memcpy(b + 1, pattern + off, 32);
            master_write(b, 33);
        }
    }
    uint64_t end = time_us_64() + 200000;
    while (selftest_model.frames < 2 && time_us_64() < end) {
        if (!stdio_usb_connected()) { r->disconnected = true; break; }
        sleep_ms(1);
    }
    r->frames = selftest_model.frames; r->unknown = selftest_model.unknown; r->bad_control = selftest_model.bad_control;
    r->overflow = cap_overflow; r->crc32 = ssd1306_model_crc32(&selftest_model);
    const uint8_t any[] = {0x00, 0xAE};
    r->wrong_address_rc = i2c_write_timeout_us(i2c0, 0x3D, any, 2, false, 100000);
    i2c_slave_deinit(i2c1); i2c_deinit(i2c1);

    /* Idle: slave armed, nothing sent -> no frames. */
    slave_begin(&idle_model, 1, 18, 19, false);
    sleep_ms(50);
    r->idle_frames = idle_model.frames;
    i2c_slave_deinit(i2c1); i2c_deinit(i2c1); i2c_deinit(i2c0);
    fixture_safe();
}
