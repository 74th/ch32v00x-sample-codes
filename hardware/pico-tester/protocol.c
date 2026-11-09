#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include "fixture.h"
#include "uart_fixture.h"
#include "adc_fixture.h"
#include "i2c_fixture.h"
#include "spi_fixture.h"
#include "protocol.h"
#include "gpio_fixture.h"
#include "ssd1306_fixture.h"
#include "ws2812_fixture.h"
#include "capture_fixture.h"

bool protocol_number(const char *s, unsigned long max, unsigned long *out) {
    if (!s || !*s) return false;
    for (const char *p = s; *p; p++) if (*p < '0' || *p > '9') return false;
    char *end;
    errno = 0;
    unsigned long n = strtoul(s, &end, 10);
    if (errno == ERANGE || *end || n > max) return false;
    *out = n; return true;
}
void protocol_error(unsigned long id, const char *kind, const char *message) {
    fixture_safe();
    printf("%lu ERR %s %s\n", id, kind, message);
}
void protocol_process(char *line) {
    char *save = NULL;
    char *idstr = strtok_r(line, " ", &save);
    char *cmd = strtok_r(NULL, " ", &save);
    unsigned long id;
    if (!protocol_number(idstr, 4294967295UL, &id)) { protocol_error(0, "INVALID", "request_id"); return; }
    if (!cmd) { protocol_error(id, "INVALID", "command"); return; }
    if (!strcmp(cmd, "CAPS")) {
        if (strtok_r(NULL, " ", &save)) { protocol_error(id, "INVALID", "arguments"); return; }
        fixture_safe();
        printf("%lu OK proto=2 fw=pico_fixture cap_gpio=2 cmds=CAPS,RESET_SAFE,GPIO_SAMPLE,GPIO_SEQUENCE,GPIO_DRIVE,GPIO_BUTTON_TEST,GPIO_LOOPBACK,GPIO_PULSE,GPIO_STATE,GPIO_SELFTEST_PWM,UART_XFER,ADC_OBSERVE,I2C_SELFTEST,I2C_MASTER,I2C_SLAVE,I2C_PROBE,I2C_FAULTTEST,SPI_SELFTEST,SPI_SLAVE,SSD1306_CAPTURE,SSD1306_PAGE,SSD1306_SELFTEST,WS2812_CAPTURE,WS2812_SELFTEST,EDGE_MEASURE,EDGE_SELFTEST,CAPTURE_START,CAPTURE_READ,CAPTURE_STOP,I2C_HOLD cap_spi=1 cap_i2c=1 cap_adc=1 cap_uart=1 uart_modes=LOOPBACK,DUT uart_baud_min=1200 uart_baud_max=921600 uart_bytes_max=32 pins=0,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,26 sample_max=300 interval_us_min=1000 interval_us_max=100000 drive_pins=12,13,16,17 drive_ms_min=10 drive_ms_max=2000 pulse_timeout_ms_min=10 pulse_timeout_ms_max=5000 cap_edge=1 edge_periods_max=255 edge_res_ps=16000 capture_edge_words=4096 capture_uart_bytes=4096 capture_uart_pins=5,6,7,9,10,11,14,15,17,18,20,21,22 capture_uart_baud_min=1200 capture_uart_baud_max=921600 capture_read_max=256 i2c_hold_pins=10,11 i2c_hold_ms_min=10 i2c_hold_ms_max=2000\n", id);
    } else if (!strcmp(cmd, "RESET_SAFE")) {
        if (strtok_r(NULL, " ", &save)) { protocol_error(id, "INVALID", "arguments"); return; }
        capture_fixture_halt(); fixture_safe(); printf("%lu OK safe=1\n", id);
    } else if (!strcmp(cmd, "SPI_SLAVE")) {
        spi_fixture_slave(id, save);
    } else if (!strcmp(cmd, "SPI_SELFTEST")) {
        spi_fixture_selftest(id, save);
    } else if (!strcmp(cmd, "I2C_FAULTTEST")) {
        i2c_fixture_faulttest(id, save);
    } else if (!strcmp(cmd, "I2C_PROBE")) {
        i2c_fixture_probe(id, save);
    } else if (!strcmp(cmd, "I2C_MASTER")) {
        i2c_fixture_master(id, save);
    } else if (!strcmp(cmd, "I2C_SLAVE")) {
        i2c_fixture_slave(id, save);
    } else if (!strcmp(cmd, "SSD1306_CAPTURE")) {
        ssd1306_fixture_capture(id, save);
    } else if (!strcmp(cmd, "EDGE_MEASURE")) {
        capture_fixture_edge_measure(id, save);
    } else if (!strcmp(cmd, "EDGE_SELFTEST")) {
        capture_fixture_edge_selftest(id, save);
    } else if (!strcmp(cmd, "CAPTURE_START")) {
        capture_fixture_start(id, save);
    } else if (!strcmp(cmd, "CAPTURE_READ")) {
        capture_fixture_read(id, save);
    } else if (!strcmp(cmd, "CAPTURE_STOP")) {
        capture_fixture_stop(id, save);
    } else if (!strcmp(cmd, "I2C_HOLD")) {
        capture_fixture_i2c_hold(id, save);
    } else if (!strcmp(cmd, "WS2812_CAPTURE") || !strcmp(cmd, "WS2812_SELFTEST")) {
        /* PIO1 is shared with the background capture. */
        if (capture_fixture_active()) { protocol_error(id, "CONFLICT", "capture_active"); return; }
        if (!strcmp(cmd, "WS2812_CAPTURE")) ws2812_fixture_capture(id, save);
        else ws2812_fixture_selftest(id, save);
    } else if (!strcmp(cmd, "SSD1306_SELFTEST")) {
        ssd1306_fixture_selftest(id, save);
    } else if (!strcmp(cmd, "SSD1306_PAGE")) {
        ssd1306_fixture_page(id, save);
    } else if (!strcmp(cmd, "I2C_SELFTEST")) {
        i2c_fixture_selftest(id, save);
    } else if (!strcmp(cmd, "ADC_OBSERVE")) {
        adc_fixture_observe(id, save);
    } else if (!strcmp(cmd, "UART_XFER")) {
        uart_fixture_xfer(id, save);
    } else if (!strncmp(cmd, "GPIO_", 5)) {
        gpio_fixture_command(id, cmd, save);
    } else protocol_error(id, "UNSUPPORTED", "command");
}
