#include <stdio.h>
#include <string.h>
#include "pico/stdlib.h"
#include "pico/stdio_usb.h"
#include "hardware/pwm.h"
#include "hardware/clocks.h"
#include "fixture.h"
#include "protocol.h"
#include "gpio_fixture.h"
#define SAMPLE_MAX 300

/* Return 0 on success, 1 on timeout, 2 on USB disconnect. */
static int capture_pulse(unsigned pin, uint64_t limit, uint64_t *period, uint64_t *high) {
    uint64_t rise = 0, fall = 0, next = 0;
    bool prev = gpio_get(pin);
    while (time_us_64() < limit) {
        if (!stdio_usb_connected()) return 2;
        bool cur = gpio_get(pin);
        if (cur != prev) {
            uint64_t now = time_us_64();
            if (cur && !rise) rise = now;
            else if (!cur && rise && !fall) fall = now;
            else if (cur && fall) { next = now; break; }
            prev = cur;
        }
    }
    if (!next || next <= rise) return 1;
    *period = next - rise; *high = fall - rise;
    return 0;
}

void gpio_fixture_command(unsigned long id, const char *cmd, char *save) {
    if (!strcmp(cmd, "GPIO_BUTTON_TEST")) {
        char *p = strtok_r(NULL, " ", &save), *extra = strtok_r(NULL, " ", &save);
        unsigned long hold;
        if (extra || !protocol_number(p, 5000, &hold) || hold < 2000) {
            protocol_error(id, "INVALID", "button_hold_ms"); return;
        }
        fixture_safe();
        if (!fixture_claim(12) || !fixture_claim(5)) { protocol_error(id, "CONFLICT", "pin_owned"); return; }
        gpio_put(12, 0); gpio_set_dir(12, GPIO_OUT);
        uint64_t start = time_us_64(), end = start + hold * 1000ULL;
        unsigned samples = 0, high = 0;
        while (time_us_64() < end) {
            if (!stdio_usb_connected()) { fixture_safe(); return; }
            if (time_us_64() - start >= 1500000ULL) { samples++; high += gpio_get(5) ? 1 : 0; }
            sleep_ms(10);
        }
        fixture_safe();
        printf("%lu OK pin=12 level=0 hold_ms=%lu observe_pin=5 samples=%u high=%u safe=1\n", id, hold, samples, high);
    } else if (!strcmp(cmd, "GPIO_STATE")) {
        char *p = strtok_r(NULL, " ", &save), *extra = strtok_r(NULL, " ", &save);
        unsigned long pin;
        if (extra || !protocol_number(p, 29, &pin) || !fixture_allowed(pin)) {
            protocol_error(id, "INVALID", "state_arguments"); return;
        }
        printf("%lu OK pin=%lu output=%u pull_up=%u pull_down=%u\n", id, pin,
               gpio_get_dir(pin) == GPIO_OUT, gpio_is_pulled_up(pin), gpio_is_pulled_down(pin));
    } else if (!strcmp(cmd, "GPIO_DRIVE") || !strcmp(cmd, "GPIO_LOOPBACK")) {
        bool loop = !strcmp(cmd, "GPIO_LOOPBACK");
        char *a = strtok_r(NULL, " ", &save);
        char *b = strtok_r(NULL, " ", &save);
        char *c = strtok_r(NULL, " ", &save);
        char *d = loop ? strtok_r(NULL, " ", &save) : NULL;
        char *extra = strtok_r(NULL, " ", &save);
        unsigned long pin, input = 0, level, duration;
        if (!protocol_number(a, 29, &pin) || !fixture_allowed(pin) ||
            (loop && (!protocol_number(b, 29, &input) || !fixture_allowed(input))) ||
            !protocol_number(loop ? c : b, 1, &level) ||
            !protocol_number(loop ? d : c, 2000, &duration) || duration < 10 || extra) {
            protocol_error(id, "INVALID", "drive_arguments"); return;
        }
        if (loop && pin == input) { protocol_error(id, "CONFLICT", "same_pin"); return; }
        /* DUT input/ADC pins require the documented external circuit and target configuration. */
        if (pin != 12 && pin != 13 && pin != 16 && pin != 17) { protocol_error(id, "UNSUPPORTED", "drive_pin"); return; }
        fixture_safe();
        if (!fixture_claim(pin) || (loop && !fixture_claim(input))) { protocol_error(id, "CONFLICT", "pin_owned"); return; }
        gpio_put(pin, level);
        gpio_set_dir(pin, GPIO_OUT);
        absolute_time_t until = make_timeout_time_ms(duration);
        unsigned low = 0, high = 0;
        while (absolute_time_diff_us(get_absolute_time(), until) > 0) {
            if (!stdio_usb_connected()) { fixture_safe(); return; }
            if (loop) { if (gpio_get(input)) high++; else low++; }
            sleep_ms(1);
        }
        fixture_safe();
        if (loop) printf("%lu OK pin=%lu input=%lu level=%lu duration_ms=%lu low=%u high=%u safe=1\n", id, pin, input, level, duration, low, high);
        else printf("%lu OK pin=%lu level=%lu duration_ms=%lu safe=1\n", id, pin, level, duration);
    } else if (!strcmp(cmd, "GPIO_SELFTEST_PWM")) {
        char *a = strtok_r(NULL, " ", &save), *b = strtok_r(NULL, " ", &save);
        char *d = strtok_r(NULL, " ", &save), *frequency = strtok_r(NULL, " ", &save);
        char *extra = strtok_r(NULL, " ", &save);
        unsigned long output, input, duty, hz = 100;
        if (extra || !protocol_number(a, 29, &output) || !protocol_number(b, 29, &input) ||
            !protocol_number(d, 90, &duty) || duty < 10 ||
            (frequency && (!protocol_number(frequency, 10000, &hz) || (hz != 100 && hz != 10000))) ||
            (output != 16 && output != 17) || !fixture_allowed(input)) {
            protocol_error(id, "INVALID", "selftest_arguments"); return;
        }
        if (output == input) { protocol_error(id, "CONFLICT", "same_pin"); return; }
        fixture_safe();
        if (!fixture_claim(output) || !fixture_claim(input)) { protocol_error(id, "CONFLICT", "pin_owned"); return; }
        unsigned slice = pwm_gpio_to_slice_num(output);
        pwm_config config = pwm_get_default_config();
        pwm_config_set_clkdiv(&config, (float)clock_get_hz(clk_sys) / 1000000.0f);
        unsigned wrap = (unsigned)(1000000 / hz) - 1;
        pwm_config_set_wrap(&config, wrap);
        pwm_init(slice, &config, false);
        pwm_set_gpio_level(output, (uint16_t)(duty * (wrap + 1) / 100));
        gpio_set_function(output, GPIO_FUNC_PWM);
        pwm_set_enabled(slice, true);
        uint64_t period = 0, high = 0;
        int capture = capture_pulse((unsigned)input, time_us_64() + 500000, &period, &high);
        pwm_set_enabled(slice, false);
        if (capture == 2) { fixture_safe(); return; }
        if (capture) { protocol_error(id, "TIMEOUT", "selftest_edges"); return; }
        fixture_safe();
        printf("%lu OK output=%lu input=%lu target_hz=%lu target_duty=%lu period_us=%llu high_us=%llu duty_ppm=%llu safe=1\n",
               id, output, input, hz, duty, (unsigned long long)period, (unsigned long long)high,
               (unsigned long long)(high * 1000000ULL / period));
    } else if (!strcmp(cmd, "GPIO_PULSE")) {
        char *p = strtok_r(NULL, " ", &save), *t = strtok_r(NULL, " ", &save);
        char *extra = strtok_r(NULL, " ", &save);
        unsigned long pin, timeout;
        if (extra || !protocol_number(p, 29, &pin) || !fixture_allowed(pin) ||
            !protocol_number(t, 5000, &timeout) || timeout < 10) {
            protocol_error(id, "INVALID", "pulse_arguments"); return;
        }
        fixture_safe();
        if (!fixture_claim(pin)) { protocol_error(id, "CONFLICT", "pin_owned"); return; }
        uint64_t period = 0, high = 0;
        int capture = capture_pulse((unsigned)pin, time_us_64() + timeout * 1000ULL, &period, &high);
        if (capture == 2) { fixture_safe(); return; }
        if (capture) { protocol_error(id, "TIMEOUT", "pulse_edges"); return; }
        fixture_safe();
        printf("%lu OK pin=%lu period_us=%llu high_us=%llu frequency_millihz=%llu duty_ppm=%llu safe=1\n", id, pin,
               (unsigned long long)period, (unsigned long long)high,
               (unsigned long long)(1000000000ULL / period), (unsigned long long)(high * 1000000ULL / period));
    } else if (!strcmp(cmd, "GPIO_SAMPLE") || !strcmp(cmd, "GPIO_SEQUENCE")) {
        char *p = strtok_r(NULL, " ", &save), *c = strtok_r(NULL, " ", &save);
        char *d = strtok_r(NULL, " ", &save), *extra = strtok_r(NULL, " ", &save);
        unsigned long pin, count, interval;
        if (extra || !protocol_number(p, 29, &pin) || !protocol_number(c, SAMPLE_MAX, &count) || !count ||
            !protocol_number(d, 100000, &interval) || interval < 1000 || !fixture_allowed(pin)) {
            protocol_error(id, "INVALID", "sample_arguments"); return;
        }
        fixture_safe();
        if (!fixture_claim(pin)) { protocol_error(id, "CONFLICT", "pin_owned"); return; }
        char samples[SAMPLE_MAX + 1];
        for (unsigned i = 0; i < count; i++) {
            if (!stdio_usb_connected()) { fixture_safe(); return; }
            int cancel = getchar_timeout_us(0);
            if (cancel == '!') { protocol_error(id, "CANCELED", "host_request"); return; }
            if (cancel != PICO_ERROR_TIMEOUT) { protocol_error(id, "INVALID", "busy_input"); return; }
            samples[i] = gpio_get((unsigned)pin) ? '1' : '0';
            if (i + 1 < count) sleep_us((uint64_t)interval);
        }
        samples[count] = 0; fixture_safe();
        printf("%lu OK pin=%lu count=%lu interval_us=%lu samples=%s\n", id, pin, count, interval, samples);
    } else protocol_error(id, "UNSUPPORTED", "command");
}
