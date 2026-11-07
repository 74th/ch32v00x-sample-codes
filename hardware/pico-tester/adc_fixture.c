#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "pico/stdlib.h"
#include "pico/stdio_usb.h"
#include "hardware/pwm.h"
#include "hardware/clocks.h"
#include "hardware/uart.h"
#include "fixture.h"
#include "adc_fixture.h"

static bool parse_num(const char *s, unsigned long max, unsigned long *out) {
    if (!s || !*s) return false;
    for (const char *p = s; *p; p++) if (*p < '0' || *p > '9') return false;
    errno = 0; char *end; unsigned long n = strtoul(s, &end, 10);
    if (errno == ERANGE || *end || n > max) return false;
    *out = n; return true;
}
static int nibble(char c) {
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return -1;
}
void adc_fixture_observe(unsigned long id, char *args) {
    char *save = NULL, *d = strtok_r(args, " ", &save), *s = strtok_r(NULL, " ", &save);
    char *t = strtok_r(NULL, " ", &save), *extra = strtok_r(NULL, " ", &save);
    unsigned long duty, settle, timeout;
    if (extra || !parse_num(d, 90, &duty) || duty < 10 ||
        !parse_num(s, 2000, &settle) || settle < 100 ||
        !parse_num(t, 3000, &timeout) || timeout < 300) {
        fixture_safe(); printf("%lu ERR INVALID adc_arguments\n", id); return;
    }
    fixture_safe();
    unsigned actual = uart_init(uart1, 115200);
    uart_set_format(uart1, 8, 1, UART_PARITY_NONE); uart_set_fifo_enabled(uart1, true);
    gpio_set_function(9, GPIO_FUNC_UART); /* RX only, GP8 remains input. */
    unsigned slice = pwm_gpio_to_slice_num(13);
    pwm_config config = pwm_get_default_config();
    pwm_config_set_clkdiv(&config, (float)clock_get_hz(clk_sys) / 1000000.0f);
    pwm_config_set_wrap(&config, 99);
    pwm_init(slice, &config, false);
    pwm_set_gpio_level(13, duty);
    gpio_set_function(13, GPIO_FUNC_PWM);
    pwm_set_enabled(slice, true);
    bool disconnected = false, success = false; unsigned errors = 0, used = 0, value = 0;
    uint64_t end = time_us_64() + settle * 1000ULL;
    while (time_us_64() < end) {
        if (!stdio_usb_connected()) { disconnected = true; goto cleanup; }
        sleep_ms(1);
    }
    while (uart_is_readable(uart1)) (void)uart_get_hw(uart1)->dr;
    uart_get_hw(uart1)->rsr = 0xff;
    end = time_us_64() + timeout * 1000ULL;
    while (time_us_64() < end) {
        if (!stdio_usb_connected()) { disconnected = true; goto cleanup; }
        if (!uart_is_readable(uart1)) continue;
        uint32_t raw = uart_get_hw(uart1)->dr;
        errors |= (raw >> 8) & 15;
        int v = nibble((char)raw);
        if (v >= 0 && used < 3) { value = (value << 4) | v; used++; }
        else if ((char)raw == '\n' && used == 3 && value <= 1023) { success = true; break; }
        else { used = 0; value = 0; }
    }
cleanup:
    pwm_set_enabled(slice, false); uart_deinit(uart1); fixture_safe();
    if (disconnected) return;
    if (errors) printf("%lu ERR UART uart_errors=0x%x safe=1\n", id, errors);
    else if (!success) printf("%lu ERR TIMEOUT adc_report safe=1\n", id);
    else printf("%lu OK duty=%lu pwm_hz=10000 settle_ms=%lu adc=%u actual_baud=%u calibrated=0 safe=1\n", id, duty, settle, value, actual);
}
