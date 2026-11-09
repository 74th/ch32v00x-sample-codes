#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "pico/stdlib.h"
#include "pico/stdio_usb.h"
#include "hardware/uart.h"
#include "fixture.h"
#include "uart_fixture.h"

#define UART_BYTES_MAX 32
#define UART_BAUD_MAX 921600
static bool parse_num(const char *s, unsigned long max, unsigned long *out) {
    if (!s || !*s) return false;
    for (const char *p = s; *p; p++) if (*p < '0' || *p > '9') return false;
    errno = 0; char *end; unsigned long n = strtoul(s, &end, 10);
    if (errno == ERANGE || *end || n > max) return false;
    *out = n; return true;
}
static int hex_digit(char c) {
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return -1;
}
void uart_fixture_xfer(unsigned long id, char *args) {
    char *save = NULL;
    char *mode = strtok_r(args, " ", &save), *rate = strtok_r(NULL, " ", &save);
    char *bits = strtok_r(NULL, " ", &save), *parity = strtok_r(NULL, " ", &save);
    char *stop = strtok_r(NULL, " ", &save), *data = strtok_r(NULL, " ", &save);
    char *expected = strtok_r(NULL, " ", &save), *timeout = strtok_r(NULL, " ", &save);
    char *extra = strtok_r(NULL, " ", &save);
    unsigned long baud, nbits, stops, want, timeout_ms;
    uint8_t tx[UART_BYTES_MAX], rx[UART_BYTES_MAX];
    unsigned txlen = 0, rxlen = 0, errors = 0;
    if (!mode || (strcmp(mode, "LOOPBACK") && strcmp(mode, "DUT")) || !parse_num(rate, UART_BAUD_MAX, &baud) || baud < 1200 ||
        !parse_num(bits, 8, &nbits) || nbits < 7 || !parity || strlen(parity) != 1 ||
        !strchr("NEO", parity[0]) || !parse_num(stop, 2, &stops) || stops < 1 || !data ||
        !parse_num(expected, UART_BYTES_MAX, &want) || !parse_num(timeout, 5000, &timeout_ms) ||
        timeout_ms < 10 || extra) goto invalid;
    if (strcmp(data, "-")) {
        size_t len = strlen(data);
        if (!len || len % 2 || len > UART_BYTES_MAX * 2) goto invalid;
        for (unsigned i = 0; i < len; i += 2) {
            int hi = hex_digit(data[i]), lo = hex_digit(data[i + 1]);
            if (hi < 0 || lo < 0) goto invalid;
            tx[txlen++] = (uint8_t)((hi << 4) | lo);
            if (nbits == 7 && tx[txlen - 1] > 127) goto invalid;
        }
    }
    if (!txlen && !want) goto invalid;
    fixture_safe();
    bool is_dut = !strcmp(mode, "DUT");
    uart_inst_t *uart = is_dut ? uart1 : uart0;
    unsigned tx_pin = is_dut ? 8 : 16, rx_pin = is_dut ? 9 : 17;
    unsigned actual = uart_init(uart, (uint)baud);
    uart_set_format(uart, (uint)nbits, (uint)stops,
                    parity[0] == 'N' ? UART_PARITY_NONE : parity[0] == 'E' ? UART_PARITY_EVEN : UART_PARITY_ODD);
    uart_set_fifo_enabled(uart, true);
    gpio_set_function(tx_pin, GPIO_FUNC_UART);
    /* Establish UART idle before connecting RX, then discard startup transients. */
    sleep_ms(2);
    gpio_set_function(rx_pin, GPIO_FUNC_UART);
    sleep_ms(25);
    while (uart_is_readable(uart)) (void)uart_get_hw(uart)->dr;
    uart_get_hw(uart)->rsr = 0xff;
    uint64_t end = time_us_64() + timeout_ms * 1000ULL;
    unsigned sent = 0; bool timed_out = false, disconnected = false;
    while (sent < txlen || rxlen < want || (uart_get_hw(uart)->fr & UART_UARTFR_BUSY_BITS)) {
        if (!stdio_usb_connected()) { disconnected = true; break; }
        if (time_us_64() >= end) { timed_out = true; break; }
        while (uart_is_readable(uart)) {
            uint32_t raw = uart_get_hw(uart)->dr;
            errors |= (raw >> 8) & 15;
            if (rxlen < UART_BYTES_MAX) rx[rxlen++] = (uint8_t)raw;
            else errors |= 16;
        }
        if (sent < txlen && uart_is_writable(uart)) uart_get_hw(uart)->dr = tx[sent++];
    }
    uart_deinit(uart); fixture_safe();
    if (disconnected) return;
    printf("%lu %s", id, (timed_out || errors) ? "ERR" : "OK");
    if (timed_out) printf(" TIMEOUT"); else if (errors) printf(" UART");
    printf(" mode=%s baud=%lu actual_baud=%u bits=%lu parity=%s stop=%lu sent=%u received=%u uart_errors=0x%x rx=", mode, baud, actual, nbits, parity, stops, sent, rxlen, errors);
    if (!rxlen) putchar('-');
    for (unsigned i = 0; i < rxlen; i++) printf("%02x", rx[i]);
    printf(" safe=1\n");
    return;
invalid:
    fixture_safe(); printf("%lu ERR INVALID uart_arguments\n", id);
}
