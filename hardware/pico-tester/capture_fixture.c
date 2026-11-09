/* Edge-time measurement, background capture (edge widths / UART receive) and I2C bus hold.
 * One PIO1 state machine + one DMA channel serve both the single-shot measurement and the background capture. */
#include <stdio.h>
#include <string.h>
#include "pico/stdlib.h"
#include "pico/stdio_usb.h"
#include "hardware/clocks.h"
#include "hardware/dma.h"
#include "hardware/pio.h"
#include "hardware/pwm.h"
#include "fixture.h"
#include "protocol.h"
#include "capture_fixture.h"
#include "capture.pio.h"

/* Fixed cycle overheads of edge_len, in PIO cycles (see capture.pio): a measured period is
 * 2 * (high_count + low_count) + EDGE_K_PERIOD cycles, a High width is 2 * high_count + EDGE_K_HIGH cycles.
 * The values come from cycle accounting and are confirmed by `EDGE_SELFTEST` (same clock for PWM and PIO). */
#define EDGE_K_PERIOD 9
#define EDGE_K_HIGH 4

typedef enum { KIND_NONE, KIND_EDGE, KIND_UART } kind_t;

static const unsigned uart_rx_pins[] = {5, 6, 7, 9, 10, 11, 14, 15, 17, 18, 20, 21, 22};

static uint32_t edge_buf[CAPTURE_EDGE_WORDS];
static uint8_t uart_buf[CAPTURE_UART_BYTES];

static struct {
    bool active;            /* SM and DMA are claimed and running */
    bool valid;             /* buffer holds data of `kind` */
    kind_t kind;
    unsigned pin, baud, sm, ch, offset, capacity, received;
    bool overflow, frame_error;
    PIO pio;
} bg = {.pio = pio1};

static bool uart_pin_ok(unsigned pin) {
    for (unsigned i = 0; i < sizeof uart_rx_pins / sizeof uart_rx_pins[0]; i++) if (uart_rx_pins[i] == pin) return true;
    return false;
}

bool capture_fixture_active(void) { return bg.active; }

/* Refresh received/overflow/frame_error from the hardware. */
static void bg_update(void) {
    if (!bg.active) return;
    bg.received = bg.capacity - dma_channel_hw_addr(bg.ch)->transfer_count;
    bool stalled = (bg.pio->fdebug & (1u << (PIO_FDEBUG_RXSTALL_LSB + bg.sm))) != 0;
    bool full = bg.received >= bg.capacity;
    if (stalled || (full && !pio_sm_is_rx_fifo_empty(bg.pio, bg.sm))) bg.overflow = true;
    if (bg.kind == KIND_UART && pio_interrupt_get(bg.pio, 4 + bg.sm)) bg.frame_error = true;
}

static void bg_release(void) {
    if (!bg.active) return;
    bg_update();
    pio_sm_set_enabled(bg.pio, bg.sm, false);
    dma_channel_abort(bg.ch);
    if (bg.kind == KIND_EDGE) pio_remove_program(bg.pio, &edge_len_program, bg.offset);
    else pio_remove_program(bg.pio, &uart_rx_program, bg.offset);
    pio_interrupt_clear(bg.pio, 4 + bg.sm);
    pio_sm_unclaim(bg.pio, bg.sm);
    dma_channel_unclaim(bg.ch);
    gpio_disable_pulls(bg.pin);
    bg.active = false;
}

void capture_fixture_halt(void) { bg_release(); }

/* Start capturing. `count` is the number of 32-bit words (edge) or bytes (uart) to collect. Returns false if no
 * state machine, DMA channel or program space is free. */
static bool bg_start(kind_t kind, unsigned pin, unsigned baud, unsigned count) {
    PIO pio = pio1;
    const pio_program_t *prog = kind == KIND_EDGE ? &edge_len_program : &uart_rx_program;
    if (!pio_can_add_program(pio, prog)) return false;
    int sm = pio_claim_unused_sm(pio, false);
    int ch = dma_claim_unused_channel(false);
    if (sm < 0 || ch < 0) {
        if (sm >= 0) pio_sm_unclaim(pio, sm);
        if (ch >= 0) dma_channel_unclaim(ch);
        return false;
    }
    unsigned offset = pio_add_program(pio, prog);
    pio_sm_config c = kind == KIND_EDGE ? edge_len_program_get_default_config(offset)
                                        : uart_rx_program_get_default_config(offset);
    sm_config_set_in_pins(&c, pin);
    sm_config_set_jmp_pin(&c, pin);
    if (kind == KIND_EDGE) sm_config_set_in_shift(&c, false, false, 32);
    else {
        sm_config_set_in_shift(&c, true, false, 8);
        sm_config_set_clkdiv(&c, (float)clock_get_hz(clk_sys) / (8.0f * (float)baud));
    }
    pio_gpio_init(pio, pin);
    pio_sm_set_consecutive_pindirs(pio, sm, pin, 1, false);
    if (kind == KIND_UART) gpio_pull_up(pin); else gpio_disable_pulls(pin);
    pio_sm_clear_fifos(pio, sm);
    pio->fdebug = 1u << (PIO_FDEBUG_RXSTALL_LSB + sm);
    pio_interrupt_clear(pio, 4 + sm);
    pio_sm_init(pio, sm, offset, &c);

    dma_channel_config dc = dma_channel_get_default_config(ch);
    channel_config_set_read_increment(&dc, false);
    channel_config_set_write_increment(&dc, true);
    channel_config_set_dreq(&dc, pio_get_dreq(pio, sm, false));
    if (kind == KIND_EDGE) {
        channel_config_set_transfer_data_size(&dc, DMA_SIZE_32);
        dma_channel_configure(ch, &dc, edge_buf, &pio->rxf[sm], count, true);
    } else {
        channel_config_set_transfer_data_size(&dc, DMA_SIZE_8);
        dma_channel_configure(ch, &dc, uart_buf, (io_rw_8 *)&pio->rxf[sm] + 3, count, true);
    }
    bg.pio = pio; bg.kind = kind; bg.pin = pin; bg.baud = baud; bg.sm = (unsigned)sm; bg.ch = (unsigned)ch;
    bg.offset = offset; bg.capacity = count; bg.received = 0; bg.overflow = false; bg.frame_error = false;
    bg.active = true; bg.valid = true;
    pio_sm_set_enabled(pio, sm, true);
    return true;
}

static unsigned long long cycles_to_ps(unsigned long long cycles) {
    return cycles * 1000000000000ULL / clock_get_hz(clk_sys);
}

typedef struct {
    unsigned periods;
    unsigned long long period_min, period_max, period_sum, high_min, high_max, high_sum;   /* PIO cycles */
} edge_stats_t;

typedef enum { MEAS_OK, MEAS_TIMEOUT, MEAS_BUSY, MEAS_DISCONNECTED } meas_t;

/* Capture periods + 1 High/Low pairs on `pin` and reduce them. The first pair is dropped: it starts at a rising edge
 * found by `wait`, so its latency differs from the steady-state loop. */
static meas_t measure_edges(unsigned pin, unsigned periods, unsigned timeout_ms, edge_stats_t *s, unsigned *edges_seen) {
    unsigned words = (periods + 1) * 2;
    memset(s, 0, sizeof *s);
    if (!bg_start(KIND_EDGE, pin, 0, words)) return MEAS_BUSY;
    uint64_t deadline = time_us_64() + (uint64_t)timeout_ms * 1000ULL;
    meas_t st = MEAS_OK;
    while (dma_channel_is_busy(bg.ch)) {
        if (!stdio_usb_connected()) { st = MEAS_DISCONNECTED; break; }
        if (time_us_64() >= deadline) { st = MEAS_TIMEOUT; break; }
    }
    bg_update();
    unsigned got = bg.received;
    bg_release();
    if (edges_seen) *edges_seen = got;
    if (st != MEAS_OK) return st;
    s->periods = periods;
    s->period_min = s->high_min = ~0ULL;
    for (unsigned i = 1; i <= periods; i++) {
        unsigned long long nh = edge_buf[2 * i], nl = edge_buf[2 * i + 1];
        unsigned long long p = 2 * (nh + nl) + EDGE_K_PERIOD, h = 2 * nh + EDGE_K_HIGH;
        if (p < s->period_min) s->period_min = p;
        if (p > s->period_max) s->period_max = p;
        if (h < s->high_min) s->high_min = h;
        if (h > s->high_max) s->high_max = h;
        s->period_sum += p; s->high_sum += h;
    }
    return MEAS_OK;
}

static void print_stats(const edge_stats_t *s) {
    printf(" periods=%u res_ps=%llu period_ps_min=%llu period_ps_max=%llu period_ps_avg=%llu high_ps_min=%llu high_ps_max=%llu high_ps_avg=%llu duty_ppm=%llu",
           s->periods, cycles_to_ps(2), cycles_to_ps(s->period_min), cycles_to_ps(s->period_max),
           cycles_to_ps(s->period_sum / s->periods), cycles_to_ps(s->high_min), cycles_to_ps(s->high_max),
           cycles_to_ps(s->high_sum / s->periods), s->high_sum * 1000000ULL / s->period_sum);
}

void capture_fixture_edge_measure(unsigned long id, char *args) {
    char *save = NULL, *p = strtok_r(args, " ", &save), *n = strtok_r(NULL, " ", &save), *t = strtok_r(NULL, " ", &save);
    char *extra = strtok_r(NULL, " ", &save);
    unsigned long pin, periods, timeout;
    if (extra || !protocol_number(p, 29, &pin) || !fixture_allowed(pin) || !protocol_number(n, EDGE_PERIODS_MAX, &periods) ||
        !periods || !protocol_number(t, 5000, &timeout) || timeout < 10) {
        protocol_error(id, "INVALID", "edge_arguments"); return;
    }
    if (bg.active) { protocol_error(id, "CONFLICT", "capture_active"); return; }
    edge_stats_t s; unsigned seen;
    meas_t st = measure_edges((unsigned)pin, (unsigned)periods, (unsigned)timeout, &s, &seen);
    if (st == MEAS_DISCONNECTED) { fixture_safe(); return; }
    if (st == MEAS_BUSY) { protocol_error(id, "BUSY", "pio_unavailable"); return; }
    if (st == MEAS_TIMEOUT) { printf("%lu ERR TIMEOUT edge_words=%u of=%lu\n", id, seen, (periods + 1) * 2); return; }
    printf("%lu OK pin=%lu", id, pin);
    print_stats(&s);
    printf(" safe=1\n");
}

void capture_fixture_edge_selftest(unsigned long id, char *args) {
    char *save = NULL, *o = strtok_r(args, " ", &save), *i = strtok_r(NULL, " ", &save);
    char *h = strtok_r(NULL, " ", &save), *d = strtok_r(NULL, " ", &save), *extra = strtok_r(NULL, " ", &save);
    unsigned long out, in, hz, duty;
    if (extra || !protocol_number(o, 29, &out) || (out != 16 && out != 17) || !protocol_number(i, 29, &in) ||
        !fixture_allowed(in) || !protocol_number(h, 2000000, &hz) || hz < 2000 || !protocol_number(d, 90, &duty) || duty < 10) {
        protocol_error(id, "INVALID", "edge_selftest_arguments"); return;
    }
    if (out == in) { protocol_error(id, "CONFLICT", "same_pin"); return; }
    if (bg.active) { protocol_error(id, "CONFLICT", "capture_active"); return; }
    fixture_safe();
    if (!fixture_claim(out) || !fixture_claim(in)) { protocol_error(id, "CONFLICT", "pin_owned"); return; }
    unsigned long sys = clock_get_hz(clk_sys);
    unsigned period_cycles = (unsigned)((sys + hz / 2) / hz);   /* PWM at clkdiv 1: one period = wrap + 1 cycles */
    unsigned slice = pwm_gpio_to_slice_num(out);
    pwm_config config = pwm_get_default_config();
    pwm_config_set_clkdiv(&config, 1.0f);
    pwm_config_set_wrap(&config, (uint16_t)(period_cycles - 1));
    pwm_init(slice, &config, false);
    unsigned high_cycles = period_cycles * (unsigned)duty / 100;
    pwm_set_gpio_level(out, (uint16_t)high_cycles);
    gpio_set_function(out, GPIO_FUNC_PWM);
    pwm_set_enabled(slice, true);
    edge_stats_t s; unsigned seen;
    meas_t st = measure_edges((unsigned)in, 100, 500, &s, &seen);
    pwm_set_enabled(slice, false);
    if (st == MEAS_DISCONNECTED) { fixture_safe(); return; }
    if (st == MEAS_BUSY) { protocol_error(id, "BUSY", "pio_unavailable"); return; }
    if (st == MEAS_TIMEOUT) { protocol_error(id, "TIMEOUT", "selftest_edges"); return; }
    fixture_safe();
    printf("%lu OK output=%lu input=%lu target_hz=%lu target_duty=%lu target_period_ps=%llu target_high_ps=%llu", id, out, in,
           hz, duty, cycles_to_ps(period_cycles), cycles_to_ps(high_cycles));
    print_stats(&s);
    printf(" safe=1\n");
}

void capture_fixture_start(unsigned long id, char *args) {
    char *save = NULL, *k = strtok_r(args, " ", &save), *p = strtok_r(NULL, " ", &save), *b = strtok_r(NULL, " ", &save);
    char *extra = strtok_r(NULL, " ", &save);
    unsigned long pin, baud = 0;
    bool edge = k && !strcmp(k, "EDGE"), uart = k && !strcmp(k, "UART");
    if (extra || (!edge && !uart) || !protocol_number(p, 29, &pin) || !fixture_allowed(pin) ||
        (edge && b) ||
        (uart && (!uart_pin_ok(pin) || !protocol_number(b, CAPTURE_UART_BAUD_MAX, &baud) || baud < CAPTURE_UART_BAUD_MIN))) {
        protocol_error(id, "INVALID", "capture_arguments"); return;
    }
    if (bg.active) { protocol_error(id, "CONFLICT", "capture_active"); return; }
    if (!bg_start(edge ? KIND_EDGE : KIND_UART, (unsigned)pin, (unsigned)baud,
                  edge ? CAPTURE_EDGE_WORDS : CAPTURE_UART_BYTES)) {
        protocol_error(id, "BUSY", "pio_unavailable"); return;
    }
    printf("%lu OK kind=%s pin=%lu capacity=%u", id, k, pin, bg.capacity);
    if (uart) printf(" baud=%lu", baud);
    else printf(" res_ps=%llu k_period=%d k_high=%d", cycles_to_ps(2), EDGE_K_PERIOD, EDGE_K_HIGH);
    printf(" active=1\n");
}

void capture_fixture_read(unsigned long id, char *args) {
    char *save = NULL, *o = strtok_r(args, " ", &save), *n = strtok_r(NULL, " ", &save), *extra = strtok_r(NULL, " ", &save);
    unsigned long offset, count;
    if (extra || !protocol_number(o, 100000, &offset) || !protocol_number(n, CAPTURE_READ_MAX, &count)) {
        protocol_error(id, "INVALID", "capture_read_arguments"); return;
    }
    if (!bg.valid) { protocol_error(id, "INVALID", "no_capture"); return; }
    bg_update();
    if (offset > bg.received) { protocol_error(id, "INVALID", "capture_offset"); return; }
    if (offset + count > bg.received) count = bg.received - offset;
    bool edge = bg.kind == KIND_EDGE;
    printf("%lu OK kind=%s pin=%u active=%d received=%u capacity=%u full=%d overflow=%d", id, edge ? "EDGE" : "UART",
           bg.pin, bg.active, bg.received, bg.capacity, bg.received >= bg.capacity, bg.overflow);
    if (!edge) printf(" frame_errors=%d", bg.frame_error);
    printf(" offset=%lu count=%lu data=", offset, count);
    if (!count) putchar('-');
    for (unsigned long i = 0; i < count; i++) {
        if (edge) printf("%s%lu", i ? "," : "", (unsigned long)edge_buf[offset + i]);
        else printf("%02x", uart_buf[offset + i]);
    }
    putchar('\n');
}

void capture_fixture_stop(unsigned long id, char *args) {
    if (strtok(args, " ")) { protocol_error(id, "INVALID", "arguments"); return; }
    bool was_active = bg.active;
    bg_release();
    printf("%lu OK was_active=%d valid=%d received=%u overflow=%d active=0\n", id, was_active, bg.valid, bg.received, bg.overflow);
}

void capture_fixture_i2c_hold(unsigned long id, char *args) {
    char *save = NULL, *l = strtok_r(args, " ", &save), *m = strtok_r(NULL, " ", &save), *extra = strtok_r(NULL, " ", &save);
    unsigned long ms;
    bool sda = l && (!strcmp(l, "SDA") || !strcmp(l, "BOTH")), scl = l && (!strcmp(l, "SCL") || !strcmp(l, "BOTH"));
    if (extra || (!sda && !scl) || !protocol_number(m, 2000, &ms) || ms < 10) { protocol_error(id, "INVALID", "hold_arguments"); return; }
    fixture_safe();
    if ((sda && !fixture_claim(10)) || (scl && !fixture_claim(11))) { protocol_error(id, "CONFLICT", "pin_owned"); return; }
    /* Open-drain by hand: the output latch is only ever 0, direction toggles between driven-Low and input. */
    if (sda) { gpio_put(10, 0); gpio_set_dir(10, GPIO_OUT); }
    if (scl) { gpio_put(11, 0); gpio_set_dir(11, GPIO_OUT); }
    absolute_time_t until = make_timeout_time_ms(ms);
    while (absolute_time_diff_us(get_absolute_time(), until) > 0) {
        if (!stdio_usb_connected()) { fixture_safe(); return; }
        sleep_ms(1);
    }
    unsigned during_sda = gpio_get(10), during_scl = gpio_get(11);
    fixture_safe();     /* back to input, no pulls */
    sleep_us(200);      /* let the external 4.7 kOhm pull-ups restore High */
    printf("%lu OK line=%s hold_ms=%lu during_sda=%u during_scl=%u after_sda=%u after_scl=%u safe=1\n", id, l, ms,
           during_sda, during_scl, gpio_get(10), gpio_get(11));
}
