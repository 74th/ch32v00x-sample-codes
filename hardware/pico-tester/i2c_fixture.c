#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <string.h>
#include "pico/stdlib.h"
#include "pico/stdio_usb.h"
#include "hardware/i2c.h"
#include "pico/i2c_slave.h"
#include "fixture.h"
#include "i2c_fixture.h"

#define I2C_DATA_MAX 32
static volatile uint8_t received[I2C_DATA_MAX], reply[I2C_DATA_MAX];
static volatile unsigned rx_count, tx_count, finishes, reply_len;
static volatile bool echo_reply;
static void slave_event(i2c_inst_t *bus, i2c_slave_event_t event) {
    if (event == I2C_SLAVE_RECEIVE) {
        uint8_t b = i2c_read_byte_raw(bus);
        if (rx_count < I2C_DATA_MAX) received[rx_count] = b;
        rx_count++;
    } else if (event == I2C_SLAVE_REQUEST) {
        unsigned n = tx_count++;
        i2c_write_byte_raw(bus, n < reply_len ? (echo_reply ? received[n] : reply[n]) : 0xff);
    } else if (event == I2C_SLAVE_FINISH) {
        finishes++;
    }
}
void i2c_fixture_selftest(unsigned long id, char *args) {
    char *save = NULL, *role = strtok_r(args, " ", &save), *extra = strtok_r(NULL, " ", &save);
    if (!role || (strcmp(role, "MASTER0") && strcmp(role, "MASTER1")) || extra) {
        fixture_safe(); printf("%lu ERR INVALID i2c_selftest_arguments\n", id); return;
    }
    fixture_safe();
    i2c_inst_t *master = !strcmp(role, "MASTER0") ? i2c0 : i2c1;
    i2c_inst_t *slave = master == i2c0 ? i2c1 : i2c0;
    rx_count = tx_count = finishes = 0; reply_len = 2; echo_reply = true; received[0] = received[1] = 0;
    i2c_init(i2c0, 100000); i2c_init(i2c1, 100000);
    for (unsigned pin = 16; pin <= 19; pin++) {
        gpio_disable_pulls(pin); gpio_set_function(pin, GPIO_FUNC_I2C);
    }
    i2c_slave_init(slave, 0x42, slave_event);
    const uint8_t bytes[2] = {0x55, 0xaa}; uint8_t back[2] = {0, 0};
    int wr = i2c_write_timeout_us(master, 0x42, bytes, 2, false, 100000);
    int rd = wr == 2 ? i2c_read_timeout_us(master, 0x42, back, 2, false, 100000) : -99;
    int wrong = i2c_write_timeout_us(master, 0x43, bytes, 1, false, 100000);
    bool connected = stdio_usb_connected();
    i2c_slave_deinit(slave); i2c_deinit(i2c0); i2c_deinit(i2c1); fixture_safe();
    if (!connected) return;
    if (wr != 2 || rd != 2 || rx_count != 2 || back[0] != bytes[0] || back[1] != bytes[1] || wrong != PICO_ERROR_GENERIC) {
        printf("%lu ERR I2C selftest write_rc=%d read_rc=%d rx_count=%u rx=%02x%02x wrong_rc=%d safe=1\n", id, wr, rd, rx_count, back[0], back[1], wrong); return;
    }
    printf("%lu OK role=%s address=0x42 write=55aa read=%02x%02x wrong_address_rc=%d safe=1\n", id, role, back[0], back[1], wrong);
}


static bool parse_number(const char *s, unsigned long max, unsigned long *out) {
    if (!s || !*s) return false;
    for (const char *p = s; *p; p++) if (*p < '0' || *p > '9') return false;
    errno = 0; char *end; unsigned long n = strtoul(s, &end, 10);
    if (errno == ERANGE || *end || n > max) return false;
    *out = n; return true;
}
static int hex_value(char c) {
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return -1;
}
static bool parse_bytes(const char *s, uint8_t *data, unsigned *n) {
    if (!s) return false;
    *n = 0;
    if (!strcmp(s, "-")) return true;
    size_t len = strlen(s);
    if (!len || len % 2 || len > I2C_DATA_MAX * 2) return false;
    for (unsigned i = 0; i < len; i += 2) {
        int hi = hex_value(s[i]), lo = hex_value(s[i + 1]);
        if (hi < 0 || lo < 0) return false;
        data[(*n)++] = (uint8_t)((hi << 4) | lo);
    }
    return true;
}
static void init_dut_bus(void) {
    fixture_safe(); i2c_init(i2c1, 100000);
    gpio_disable_pulls(10); gpio_disable_pulls(11);
    gpio_set_function(10, GPIO_FUNC_I2C); gpio_set_function(11, GPIO_FUNC_I2C);
}
void i2c_fixture_master(unsigned long id, char *args) {
    char *save = NULL, *a = strtok_r(args, " ", &save), *w = strtok_r(NULL, " ", &save);
    char *r = strtok_r(NULL, " ", &save), *t = strtok_r(NULL, " ", &save), *extra = strtok_r(NULL, " ", &save);
    unsigned long addr, want, timeout; unsigned len; uint8_t bytes[I2C_DATA_MAX], back[I2C_DATA_MAX];
    if (extra || !parse_number(a, 119, &addr) || addr < 8 || !parse_bytes(w, bytes, &len) ||
        !parse_number(r, I2C_DATA_MAX, &want) || !parse_number(t, 1000, &timeout) || timeout < 10 || (!len && !want)) {
        fixture_safe(); printf("%lu ERR INVALID i2c_master_arguments\n", id); return;
    }
    init_dut_bus();
    int wr = len ? i2c_write_timeout_us(i2c1, addr, bytes, len, want != 0, timeout * 1000) : 0;
    int rd = want && wr == (int)len ? i2c_read_timeout_us(i2c1, addr, back, want, false, timeout * 1000) : 0;
    bool connected = stdio_usb_connected(); i2c_deinit(i2c1); fixture_safe();
    if (!connected) return;
    bool timed_out = wr == PICO_ERROR_TIMEOUT || rd == PICO_ERROR_TIMEOUT;
    bool ok = wr == (int)len && rd == (int)want;
    printf("%lu %s", id, ok ? "OK" : timed_out ? "ERR TIMEOUT" : "ERR I2C");
    printf(" addr=%lu write_rc=%d read_rc=%d rx=", addr, wr, rd);
    if (rd <= 0) putchar('-');
    for (int i = 0; i < rd; i++) printf("%02x", back[i]);
    printf(" safe=1\n");
}
void i2c_fixture_slave(unsigned long id, char *args) {
    char *save = NULL, *a = strtok_r(args, " ", &save), *w = strtok_r(NULL, " ", &save);
    char *r = strtok_r(NULL, " ", &save), *t = strtok_r(NULL, " ", &save), *extra = strtok_r(NULL, " ", &save);
    unsigned long addr, expect, timeout; unsigned len; uint8_t data[I2C_DATA_MAX];
    if (extra || !parse_number(a, 119, &addr) || addr < 8 || !parse_number(w, I2C_DATA_MAX, &expect) ||
        !parse_bytes(r, data, &len) || !parse_number(t, 5000, &timeout) || timeout < 10 || (!expect && !len)) {
        fixture_safe(); printf("%lu ERR INVALID i2c_slave_arguments\n", id); return;
    }
    rx_count = tx_count = finishes = 0; reply_len = len; echo_reply = false;
    for (unsigned i = 0; i < len; i++) reply[i] = data[i];
    init_dut_bus(); i2c_slave_init(i2c1, (uint8_t)addr, slave_event);
    uint64_t end = time_us_64() + timeout * 1000ULL; bool disconnected = false;
    while (time_us_64() < end && !(rx_count >= expect && tx_count >= len && finishes >= (expect && len ? 2u : 1u))) {
        if (!stdio_usb_connected()) { disconnected = true; break; }
        sleep_ms(1);
    }
    i2c_slave_deinit(i2c1); i2c_deinit(i2c1); fixture_safe();
    if (disconnected) return;
    bool extra_data = rx_count > expect || tx_count > len;
    bool ok = rx_count == expect && tx_count == len && finishes >= (expect && len ? 2u : 1u);
    printf("%lu %s addr=%lu received=%u sent=%u finishes=%u rx=", id, ok ? "OK" : extra_data ? "ERR I2C" : "ERR TIMEOUT", addr, rx_count, tx_count, finishes);
    if (!rx_count) putchar('-');
    for (unsigned i = 0; i < rx_count && i < I2C_DATA_MAX; i++) printf("%02x", received[i]);
    printf(" safe=1\n");
}


static void od_low(unsigned pin) { gpio_put(pin, 0); gpio_set_dir(pin, GPIO_OUT); }
static void od_release(unsigned pin) { gpio_set_dir(pin, GPIO_IN); }
static bool clock_high(unsigned scl, uint64_t deadline) {
    od_release(scl);
    while (!gpio_get(scl)) {
        if (!stdio_usb_connected() || time_us_64() >= deadline) return false;
    }
    return true;
}
/* Returns 0 for a sampled ACK/NACK, 1 for timeout, 2 for a bus conflict. */
static int probe_bus(unsigned sda, unsigned scl, unsigned addr, uint64_t deadline, bool *ack) {
    if (!clock_high(scl, deadline)) return 1;
    if (!gpio_get(sda)) return 2;
    od_low(sda); sleep_us(5); od_low(scl); sleep_us(5);
    uint8_t address_byte = (uint8_t)(addr << 1);
    for (unsigned i = 0; i < 8; i++) {
        bool bit = (address_byte & (0x80u >> i)) != 0;
        if (bit) od_release(sda); else od_low(sda);
        sleep_us(5);
        if (!clock_high(scl, deadline)) return 1;
        sleep_us(5);
        if (bit && !gpio_get(sda)) return 2;
        od_low(scl);
    }
    od_release(sda); sleep_us(5);
    if (!clock_high(scl, deadline)) return 1;
    sleep_us(5); *ack = !gpio_get(sda); od_low(scl);
    od_low(sda); sleep_us(5);
    if (!clock_high(scl, deadline)) return 1;
    sleep_us(5); od_release(sda); sleep_us(5);
    return 0;
}
void i2c_fixture_probe(unsigned long id, char *args) {
    char *save = NULL, *a = strtok_r(args, " ", &save), *t = strtok_r(NULL, " ", &save);
    char *extra = strtok_r(NULL, " ", &save); unsigned long addr, timeout;
    if (extra || !parse_number(a, 119, &addr) || addr < 8 ||
        !parse_number(t, 1000, &timeout) || timeout < 10) {
        fixture_safe(); printf("%lu ERR INVALID i2c_probe_arguments\n", id); return;
    }
    fixture_safe(); bool ack = false;
    int result = probe_bus(10, 11, addr, time_us_64() + timeout * 1000ULL, &ack);
    fixture_safe();
    if (!stdio_usb_connected()) return;
    if (result == 1) printf("%lu ERR TIMEOUT scl_stuck safe=1\n", id);
    else if (result == 2) printf("%lu ERR I2C bus_conflict safe=1\n", id);
    else printf("%lu OK addr=%lu ack=%u safe=1\n", id, addr, ack);
}
void i2c_fixture_faulttest(unsigned long id, char *args) {
    char *save = NULL, *line = strtok_r(args, " ", &save), *extra = strtok_r(NULL, " ", &save);
    if (!line || (strcmp(line, "SDA") && strcmp(line, "SCL")) || extra) {
        fixture_safe(); printf("%lu ERR INVALID i2c_fault_arguments\n", id); return;
    }
    fixture_safe();
    bool is_sda = !strcmp(line, "SDA");
    od_low(is_sda ? 18 : 19);
    bool ack = false;
    int result = probe_bus(16, 17, 66, time_us_64() + 10000, &ack);
    fixture_safe();
    if (!stdio_usb_connected()) return;
    if (result != (is_sda ? 2 : 1)) {
        printf("%lu ERR I2C fault_not_detected observed=%d safe=1\n", id, result); return;
    }
    printf("%lu OK fault=%s observed=%s safe=1\n", id, line, is_sda ? "BUS_CONFLICT" : "TIMEOUT");
}
